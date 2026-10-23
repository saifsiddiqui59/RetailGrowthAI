"""Part 2 dispatch must never duplicate uncertain provider writes."""
from pathlib import Path
import sys
import importlib.util
from datetime import datetime,timedelta,timezone
import pytest
ROOT=Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location("social_dispatch",ROOT/"social_dispatch.py")
d=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=d
spec.loader.exec_module(d)

SHOP="10000000-0000-4000-8000-000000000001"
ACCOUNT="20000000-0000-4000-8000-000000000001"
DAY="30000000-0000-4000-8000-000000000001"
USER="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
JOB="50000000-0000-4000-8000-000000000001"
NOW=datetime(2026,10,23,12,tzinfo=timezone.utc)

import social_publish_policy as policy

def ctx():
    job={"shop_id":SHOP,"social_account_id":ACCOUNT,"campaign_day_id":DAY,
         "provider":"linkedin","approved_by":USER,"approved_at":NOW,
         "status":"APPROVED","caption":"reviewed","media_asset_id":None,
         "scheduled_at":NOW+timedelta(hours=1),"timezone":"Asia/Kolkata",
         "revision":1,"quota_reserved":True}
    job["approved_content_sha256"]=policy.approved_digest(
         shop_id=SHOP,day_id=DAY,account_id=ACCOUNT,platform="linkedin",
         caption=job["caption"],media_asset_id=None,
         scheduled_at=job["scheduled_at"],timezone_name=job["timezone"],revision=1)
    return dict(job=job,shop_id=SHOP,
      account={"id":ACCOUNT,"shop_id":SHOP,"provider":"linkedin",
               "connection_status":"CONNECTED","granted_scopes":["write"]},
      membership={"shop_id":SHOP,"user_id":USER,"active":True,"role":"OWNER"},
      entitlement={"shop_id":SHOP,"status":"TRIAL","valid_until":NOW+timedelta(days=2)},
      media=None,required_scopes={"write"})

class Repo:
    def __init__(self,context=None):
        self.context=context if context is not None else ctx()
        self.state="APPROVED";self.events=[]
    def claim(self,id):
        if self.state!="APPROVED":return None
        self.state="CLAIMED";self.events.append("claim")
        return {"job_id":id,"claim_token":"fixed-lease-123"}
    def load_context(self,*a):return self.context
    def mark_external_inflight(self,*a):self.state="SENDING";self.events.append("inflight")
    def retry_no_send(self,*a):self.state="RETRYABLE";self.events.append("retry")
    def require_reconciliation(self,*a):self.state="RECONCILE";self.events.append("reconcile")
    def fail_claim(self,*a):self.state="FAILED";self.events.append("fail")
    def record_receipt(self,j,c,remote,status):
        self.state=status;self.events.append("receipt")

class Provider:
    def __init__(self,fn):self.fn=fn;self.called=0
    def publish(self,*args):self.called+=1;return self.fn()

def go(repo,provider):return d.process_publish(JOB,repository=repo,provider=provider,clock=lambda:NOW)

def test_exact_uuid_only_no_secret_exfiltration():
    for invalid in (b'{"token":"secret"}',"NOT-AN-ID",'AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA',JOB+"\\n", b"\xff"):
        with pytest.raises(d.DispatchError):
            d.message_uuid(invalid)

def test_approved_post_writes_inflight_before_provider():
    r=Repo()
    def send():
        assert r.events[-1]=="inflight"
        return d.Delivery("remote-1","PUBLISHED")
    p=Provider(send)
    assert go(r,p)=="PUBLISHED"
    assert r.events[:2]==["claim","inflight"]
    assert p.called==1
    assert go(r,p)=="SKIPPED" and p.called==1

def test_uncertain_provider_timeout_reconciles_not_retries():
    for failure in (lambda: (_ for _ in ()).throw(TimeoutError("opaque")),
                    lambda: (_ for _ in ()).throw(d.ProviderFailure("HTTP_TIMEOUT"))):
        r=Repo();p=Provider(failure)
        assert go(r,p)=="RECONCILE"
        assert "reconcile" in r.events
        assert go(r,p)=="SKIPPED"
        assert p.called==1

def test_known_pre_send_failure_can_retry_without_posting_twice():
    r=Repo();p=Provider(lambda: (_ for _ in ()).throw(
        d.ProviderFailure("RATE_LIMIT",definitely_not_sent=True,retryable=True)))
    assert go(r,p)=="RETRYABLE"
    assert r.events==["claim","inflight","retry"]

def test_revoked_or_unapproved_never_reaches_provider():
    for path,value in (("status","DRAFT"),("quota_reserved",False)):
        context=ctx()
        context["job"][path]=value
        r=Repo(context)
        p=Provider(lambda:d.Delivery("id","PUBLISHED"))
        assert go(r,p)=="FAILED"
        assert p.called==0 and r.events==["claim","fail"]
