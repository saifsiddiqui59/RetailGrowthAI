"""Offline API tests for tenant-scoped social authoring and content review."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
from uuid import UUID

import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_jobs_http import SocialJobsAPI, build_social_jobs_api
from tenant_store import SubscriptionDenied

SHOP="10000000-0000-4000-8000-000000000001"
FOREIGN="10000000-0000-4000-8000-000000000002"
USER="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ACCOUNT="11000000-0000-4000-8000-000000000001"
DAY="12000000-0000-4000-8000-000000000001"
JOB="13000000-0000-4000-8000-000000000001"
NOW=datetime(2026,10,23,12,0,tzinfo=timezone.utc)


class Tenant:
    def __init__(self,write=True):self.write=write;self.calls=[]
    def member(self,token,uid,sid,write=False):
        self.calls.append(("member",token,uid,sid,write))
        return self.write and sid==SHOP
    def _request(self,table,token,query):
        self.calls.append(("read",table,query))
        return [{"id":DAY,"shop_id":SHOP}]
    def assets(self,token,sid,ids):
        return sid==SHOP and len(ids)==1


class Repository:
    def __init__(self):self.calls=[];self.can_approve=True;self.can_cancel=True
    def create_draft(self,**kwargs):
        self.calls.append(("create",kwargs))
        return {"id":kwargs["id"],"status":"DRAFT","revision":1}
    def read_job(self,shop_id,job_id):
        self.calls.append(("read",shop_id,job_id))
        return {
            "id":JOB,"shop_id":SHOP,"social_account_id":ACCOUNT,
            "campaign_day_id":DAY,"provider":"linkedin","caption":"Approved caption",
            "media_asset_id":None,"scheduled_at":"2026-10-24T04:30:00+00:00",
            "timezone":"Asia/Kolkata","status":"DRAFT","revision":1,
        }
    def approve(self,**kwargs):
        self.calls.append(("approve",kwargs))
        return self.can_approve
    def cancel(self,**kwargs):
        self.calls.append(("cancel",kwargs))
        return self.can_cancel


def api(tenant=None,repo=None):
    return SocialJobsAPI(
        lambda tok: USER if tok=="valid" else (_ for _ in ()).throw(
            ValueError("jwt invalid")),tenant or Tenant(),repo or Repository(),
        clock=lambda:NOW)


def draft(**updates):
    payload={"shop_id":SHOP,"provider":"linkedin","account_id":ACCOUNT,
        "day_id":DAY,"caption":"Approved caption","media_asset_id":None,
        "day":"2026-10-24","clock":"10:00","timezone":"Asia/Kolkata",
        "idempotency_key":"draft-content-001"}
    payload.update(updates)
    return payload


def test_draft_scheduling_uses_backend_verified_tenant_and_time():
    store=Tenant();repo=Repository();app=api(store,repo)
    code,data=app.handle("create","Bearer valid",draft())
    assert code==201 and data["status"]=="DRAFT"
    assert str(UUID(data["id"]))==data["id"]
    created=repo.calls[0][1]
    assert created["shop_id"]==SHOP and created["actor"]==USER
    assert created["scheduled_at"]==datetime(2026,10,24,4,30,tzinfo=timezone.utc)
    assert "member"==store.calls[0][0] and store.calls[0][-1] is True


def test_foreign_tenant_invalid_date_and_extra_fields_rejected_without_writes():
    repo=Repository();app=api(repo=repo)
    assert app.handle("create","Bearer valid",draft(shop_id=FOREIGN))[0]==403
    assert app.handle("create","Bearer valid",draft(day="2026-10-01"))[0]==400
    assert app.handle("create","Bearer valid",draft(extra="smuggled"))[0]==400
    assert app.handle("create","Bearer valid",draft(provider="instagram"))[0]==400
    assert app.handle("create","Bearer valid",draft(idempotency_key="../escape"))[0]==400
    assert repo.calls==[]


def test_required_same_actor_member_role_and_valid_bearer():
    repo=Repository()
    assert api(repo=repo).handle("create","",draft())[0]==401
    assert api(Tenant(write=False),repo).handle("create","Bearer valid",draft())[0]==403
    assert repo.calls==[]


def test_approve_digest_is_server_computed_and_revision_bound():
    repo=Repository();app=api(repo=repo)
    status,body=app.handle("approve","Bearer valid",{
        "shop_id":SHOP,"job_id":JOB,"revision":1})
    assert status==200 and body["status"]=="APPROVED"
    approved=repo.calls[-1][1]
    assert len(approved["digest"])==32 and isinstance(approved["digest"],bytes)
    assert approved["caption"]=="Approved caption"
    assert approved["revision"]==1 and approved["actor"]==USER
    repo2=Repository();app2=api(repo=repo2)
    assert app2.handle("approve","Bearer valid",{
        "shop_id":SHOP,"job_id":JOB,"revision":2})[0]==409
    assert [call[0] for call in repo2.calls]==["read"]
    repo.can_approve=False
    assert app.handle("approve","Bearer valid",{
        "shop_id":SHOP,"job_id":JOB,"revision":1})[0]==409


def test_cancel_has_stale_or_inflight_failure_not_false_success():
    repo=Repository();app=api(repo=repo)
    assert app.handle("cancel","Bearer valid",{
        "shop_id":SHOP,"job_id":JOB,"revision":1})[0]==200
    repo.can_cancel=False
    assert app.handle("cancel","Bearer valid",{
        "shop_id":SHOP,"job_id":JOB,"revision":1})==(
            409,{"error":"CANNOT_CANCEL_POSSIBLY_SENT"})


def test_server_subscription_quota_errors_are_safe_and_stable():
    class QuotaRepo(Repository):
        def approve(self,**kwargs):raise SubscriptionDenied("RG002")
    assert api(repo=QuotaRepo()).handle("approve","Bearer valid",{
        "shop_id":SHOP,"job_id":JOB,"revision":1})==(
            429,{"error":"PUBLISH_QUOTA_EXCEEDED"})
    with pytest.raises(ValueError):
        build_social_jobs_api({"RETAIL_PART2_SOCIAL_ENABLED":"false"})
