"""Offline Part 2 queue/timer orchestration and provider receipt safety."""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_worker_runtime import (
    SocialWorkerRuntime, SocialWorkerDisabled, require_social_release,
    build_social_worker, REQUIRED_SWITCHES)
from social_dispatch import Delivery, ProviderFailure

JOB="13000000-0000-4000-8000-000000000001"
NOW=datetime(2026,10,23,12,tzinfo=timezone.utc)


class Repository:
    def __init__(self, context, marker=True):
        self.state="APPROVED";self.events=[];self.context=context;self.marker=marker
    def claim(self,job_id):
        assert job_id==JOB
        if self.state!="APPROVED":return None
        self.state="CLAIMED";self.events.append("CLAIM")
        return {"job_id":JOB,"claim_token":"70000000-0000-4000-8000-000000000001"}
    def load_context(self,*args):self.events.append("LOAD");return self.context
    def mark_external_inflight(self,*args):
        self.events.append("SENDING")
        if self.marker:self.state="SENDING"
        return self.marker
    def record_receipt(self,*args):self.events.append("RECEIPT");self.state="PUBLISHED"
    def fail_claim(self,*args):self.events.append("FAILED");self.state="FAILED"
    def retry_no_send(self,*args):self.events.append("RETRY");self.state="RETRYABLE"
    def require_reconciliation(self,*args):self.events.append("RECONCILE");self.state="RECONCILE"


class Due:
    def due(self,limit):assert limit==20;return [JOB]


class Queue:
    def __init__(self):self.sent=[]
    def enqueue(self,job):self.sent.append(job)


class Publisher:
    def __init__(self, repository, response=None):
        self.repo=repository;self.calls=0;self.response=response
    def publish(self,job,context):
        self.calls+=1
        assert self.repo.events[-1]=="SENDING" and self.repo.state=="SENDING"
        if isinstance(self.response,Exception):raise self.response
        return self.response or Delivery(remote_id="123456789_999",status="PUBLISHED")


def approval():
    from social_publish_policy import approved_digest
    sid="10000000-0000-4000-8000-000000000001"
    acc="20000000-0000-4000-8000-000000000001"
    day="30000000-0000-4000-8000-000000000001"
    actor="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    scheduled=NOW-timedelta(minutes=2)
    job={"shop_id":sid,"social_account_id":acc,"campaign_day_id":day,
         "provider":"facebook","approved_by":actor,
         "approved_at":NOW-timedelta(hours=1),
         "status":"APPROVED","caption":"Reviewed promotion",
         "media_asset_id":None,"scheduled_at":scheduled,
         "timezone":"Asia/Kolkata","revision":1,"quota_reserved":True}
    job["approved_content_sha256"]=approved_digest(
        shop_id=sid,day_id=day,account_id=acc,platform="facebook",
        caption=job["caption"],media_asset_id=None,scheduled_at=scheduled,
        timezone_name="Asia/Kolkata",revision=1)
    return dict(job=job,shop_id=sid,
                account={"id":acc,"shop_id":sid,"provider":"facebook",
                         "connection_status":"CONNECTED","granted_scopes":["pages_manage_posts"]},
                membership={"shop_id":sid,"user_id":actor,"active":True,"role":"OWNER"},
                entitlement={"shop_id":sid,"status":"ACTIVE",
                             "valid_until":NOW+timedelta(days=1)},
                media=None,required_scopes=frozenset({"pages_manage_posts"}),
                provider_access_token="NEVER_LOG_PROVIDER_TOKEN")


def runtime(repository,publisher):
    return SocialWorkerRuntime(repository=repository,publisher=publisher,
        due_store=Due(),queue=Queue(),clock=lambda:NOW)


def test_every_release_switch_is_mandatory_not_one_global_toggle():
    ready={name:"true" for name in REQUIRED_SWITCHES}
    assert require_social_release(ready) is True
    for name in REQUIRED_SWITCHES:
        env=dict(ready)
        env.pop(name)
        with pytest.raises(SocialWorkerDisabled):
            require_social_release(env)
        env[name]="True"
        with pytest.raises(SocialWorkerDisabled):
            build_social_worker(env)
    with pytest.raises(SocialWorkerDisabled):
        build_social_worker({})
    with pytest.raises(SocialWorkerDisabled,match="existing Azure queue"):
        build_social_worker(ready)


def test_source_only_due_scan_never_publishes_and_replay_skips():
    repo=Repository(approval())
    provider=Publisher(repo)
    worker=runtime(repo,provider)
    assert worker.enqueue_due()==1
    assert worker.queue.sent==[JOB]
    assert provider.calls==0 and repo.events==[]
    assert worker.process_queue_body(JOB)=="PUBLISHED"
    assert worker.process_queue_body(JOB)=="SKIPPED"
    assert provider.calls==1
    assert repo.events==["CLAIM","LOAD","SENDING","RECEIPT"]


def test_denied_review_role_has_zero_outbound_post():
    context=approval()
    context["membership"]["active"]=False
    repo=Repository(context)
    provider=Publisher(repo)
    worker=runtime(repo,provider)
    assert worker.process_queue_body(JOB)=="FAILED"
    assert provider.calls==0 and repo.events==["CLAIM","LOAD","FAILED"]


def test_durable_barrier_rejection_stops_provider():
    repo=Repository(approval(),marker=False)
    provider=Publisher(repo)
    worker=runtime(repo,provider)
    with pytest.raises(Exception,match="INFLIGHT_BARRIER_NOT_CONFIRMED"):
        worker.process_queue_body(JOB)
    assert provider.calls==0 and repo.events==["CLAIM","LOAD","SENDING"]


def test_timeout_is_reconcile_never_blindly_retry():
    repo=Repository(approval())
    provider=Publisher(repo,TimeoutError("potentially posted"))
    worker=runtime(repo,provider)
    assert worker.process_queue_body(JOB)=="RECONCILE"
    assert repo.events==["CLAIM","LOAD","SENDING","RECONCILE"]
    assert worker.process_queue_body(JOB)=="SKIPPED"
    assert provider.calls==1


def test_queue_payload_must_be_single_canonical_uuid():
    repo=Repository(approval())
    provider=Publisher(repo)
    worker=runtime(repo,provider)
    with pytest.raises(Exception):
        worker.process_queue_body(b'{"job":"uuid","token":"secret"}')
    assert repo.events==[] and provider.calls==0


def test_poison_requires_durable_db_receipt_and_rejects_untrusted_payload():
    repository=Repository(approval())
    repository.poison_ids=[]
    def record_poison(job):
        repository.poison_ids.append(job)
        return True
    repository.record_poison=record_poison
    worker=runtime(repository,Publisher(repository))
    assert worker.record_poison(JOB) is True
    assert repository.poison_ids==[JOB]
    with pytest.raises(Exception):
        worker.record_poison('{"access_token":"secret"}')
    assert repository.poison_ids==[JOB]
    def failed_receipt(job):raise RuntimeError("database unavailable")
    repository.record_poison=failed_receipt
    with pytest.raises(RuntimeError,match="database unavailable"):
        worker.record_poison(JOB)


def test_publishing_blueprint_registration_requires_explicit_host_switch():
    source=(Path(__file__).resolve().parents[2]/
            "azure-functions/campaign-api/function_app.py").read_text()
    assert 'RETAIL_PART2_FUNCTIONS_REGISTER_ENABLED' in source
    assert 'app.register_functions(social_worker_blueprint)' in source
    assert 'require_social_release(os.environ)' in source
    # Blueprints are never registered by a failing config check.
    assert source.index('require_social_release(os.environ)') < source.index(
        'app.register_functions(social_worker_blueprint)')
