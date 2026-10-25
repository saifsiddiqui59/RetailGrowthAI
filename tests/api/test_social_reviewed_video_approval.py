"""No-cloud source-only reviewed video approval contract and negative cases."""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_reviewed_video_approval import (
    ReviewedVideoApprovalService, ReviewedVideoApprovalDisabled,
)
from security import AuthenticationError
from tenant_store import SubscriptionDenied
from social_publish_policy import approved_digest

SID="31000000-0000-4000-8000-000000000001"
JID="62000000-0000-4000-8000-000000000001"
AID="81000000-0000-4000-8000-000000000001"
UID="ffffffff-ffff-4fff-8fff-ffffffffffff"
DAY="51000000-0000-4000-8000-000000000001"
ACCOUNT="72000000-0000-4000-8000-000000000001"
SHA="ab"*32
RIGHTS="cd"*32
PATH=SID+"/renders/91000000-0000-4000-8000-000000000001.mp4"
NOW=datetime(2026,10,25,tzinfo=timezone.utc)
SCHEDULE=NOW+timedelta(days=1)

class Tenant:
    authorized=True
    def member(self,token,uid,sid,write):
        assert write and uid==UID
        return self.authorized

class Repo:
    def __init__(self):
        self.calls=[]
        self.approved=True
        self.row={"id":JID,"shop_id":SID,"provider":"instagram",
          "status":"DRAFT","revision":3,"media_asset_id":AID,
          "social_account_id":ACCOUNT,"campaign_day_id":DAY,
          "scheduled_at":SCHEDULE.isoformat(),"caption":"Reviewed sale",
          "timezone":"Asia/Kolkata"}
    def read_job(self,sid,jid):
        assert sid==SID and jid==JID
        self.calls.append(("read",))
        return self.row
    def approve_reviewed_video(self,**kwargs):
        self.calls.append(("approve",kwargs))
        return self.approved

class Source:
    def __init__(self):
        self.candidate={"shop_id":SID,"job_id":JID,"media_asset_id":AID,
          "revision":3,"source":"GENERATED","storage_bucket":"retailgrowth-media",
          "object_path":PATH,"scheduled_at":SCHEDULE}
        self.receipt={"shop_id":SID,"media_asset_id":AID,
          "source_sha256":SHA,"object_path":PATH,
          "source":"PART1_RENDER_FINALIZED"}
        self.clearance={"shop_id":SID,"media_asset_id":AID,
          "reviewed_by":UID,"revision":3,
          "rights_kind":"GENERATED_RIGHTS_VERIFIED",
          "rights_evidence_sha256":RIGHTS,
          "rights_expires_at":SCHEDULE+timedelta(days=3)}
        self.calls=[]
    def get_source(self,sid,jid,actor):
        self.calls.append("source")
        assert (sid,jid,actor)==(SID,JID,UID)
        return self.candidate
    def get_render_receipt(self,sid,aid):
        self.calls.append("receipt")
        assert (sid,aid)==(SID,AID)
        return self.receipt
    def get_clearance(self,sid,aid,actor,revision):
        self.calls.append("rights")
        assert (sid,aid,actor,revision)==(SID,AID,UID,3)
        return self.clearance

def fixture():
    tenant,repo,source=Tenant(),Repo(),Source()
    def verify(token):
        if token!="valid-jwt":
            raise AuthenticationError("invalid")
        return UID
    def store(sid,jid,uid):
        assert (sid,jid,uid)==(SID,JID,UID)
        return source
    service=ReviewedVideoApprovalService(verify,tenant,repo,store,
        enabled=True,clock=lambda:NOW)
    return service,tenant,repo,source

def body():
    return {"shop_id":SID,"job_id":JID,"revision":3}

def test_positive_approval_uses_backend_digest_and_render_receipt_only():
    svc,tenant,repo,src=fixture()
    assert svc.approve("Bearer valid-jwt",body())==(
        200,{"id":JID,"status":"APPROVED","revision":3})
    assert src.calls==["source","receipt","rights"]
    assert [x[0] for x in repo.calls]==["read","approve"]
    sent=repo.calls[1][1]
    assert sent["source_sha256"]==SHA
    assert sent["digest"]==approved_digest(
        shop_id=SID,day_id=DAY,account_id=ACCOUNT,platform="instagram",
        caption="Reviewed sale",media_asset_id=AID,
        scheduled_at=SCHEDULE,timezone_name="Asia/Kolkata",revision=3)
    assert set(sent)=={"shop_id","job_id","actor","revision","digest",
      "caption","scheduled_at","timezone_name","media_id","source_sha256"}
    assert "rights_evidence_sha256" not in sent

@pytest.mark.parametrize("mutation",[
  lambda r,s:r.row.update(shop_id="31000000-0000-4000-8000-000000000002"),
  lambda r,s:r.row.update(status="APPROVED"),
  lambda r,s:r.row.update(revision=4),
  lambda r,s:r.row.update(provider="linkedin"),
  lambda r,s:r.row.update(media_asset_id=None),
  lambda r,s:s.candidate.update(shop_id="31000000-0000-4000-8000-000000000002"),
  lambda r,s:s.candidate.update(object_path="other.mp4"),
  lambda r,s:s.candidate.update(scheduled_at=SCHEDULE+timedelta(minutes=1)),
  lambda r,s:s.receipt.update(source_sha256="not-a-sha"),
  lambda r,s:s.receipt.update(object_path="changed/after/review.mp4"),
  lambda r,s:s.clearance.update(revision=4),
  lambda r,s:s.clearance.update(reviewed_by="31000000-0000-4000-8000-000000000002"),
  lambda r,s:s.clearance.update(rights_evidence_sha256="not-hash"),
  lambda r,s:s.clearance.update(rights_expires_at=SCHEDULE+timedelta(minutes=1)),
  lambda r,s:s.clearance.update(rights_kind="UNREVIEWED"),
])
def test_untrusted_job_or_media_evidence_never_approves(mutation):
    svc,tenant,repo,src=fixture()
    mutation(repo,src)
    status,response=svc.approve("Bearer valid-jwt",body())
    assert status!=200
    assert not any(k=="approve" for k,*_ in repo.calls)

def test_browser_cannot_supply_digest_sha_rights_or_unlock_video():
    svc,tenant,repo,src=fixture()
    for field in ("source_sha256","rights_kind","approved_content_sha256","enabled"):
        supplied=body()|{field:"00"*32}
        assert svc.approve("Bearer valid-jwt",supplied)==(
            400,{"error":"INVALID_REQUEST"})
    assert repo.calls==[]
    with pytest.raises(ReviewedVideoApprovalDisabled):
        ReviewedVideoApprovalService(lambda x:UID,tenant,repo,lambda *args:src)

def test_tenant_revocation_and_invalid_token_checked_before_db():
    svc,tenant,repo,src=fixture()
    assert svc.approve("Bearer bad-jwt",body())[0]==401
    tenant.authorized=False
    assert svc.approve("Bearer valid-jwt",body())[0]==403
    assert repo.calls==[]

def test_denied_quota_and_cas_do_not_return_approved():
    svc,tenant,repo,src=fixture()
    repo.approved=False
    assert svc.approve("Bearer valid-jwt",body())[0]==409
    def unavailable(**kwargs):
        raise SubscriptionDenied("RG001")
    repo.approve_reviewed_video=unavailable
    assert svc.approve("Bearer valid-jwt",body())[0]==402
