"""Offline contract of the service-role scoped P2 media review adapter."""
import json
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from social_video_review_store import ScopedSocialVideoReviewStore
from tenant_store import StorageUnavailable

SHOP="31000000-0000-4000-8000-000000000001"
JOB="62000000-0000-4000-8000-000000000001"
ACTOR="ffffffff-ffff-4fff-8fff-ffffffffffff"
ASSET="81000000-0000-4000-8000-000000000001"
OTHER="30000000-0000-4000-8000-000000000002"
ORIGIN="https://retail.test.supabase.co"

class Response:
    status=200
    def __init__(self,url,body):
        self.url=url;self.body=BytesIO(json.dumps(body).encode())
    def geturl(self):return self.url
    def read(self,n):return self.body.read(n)
    def __enter__(self):return self
    def __exit__(self,*args):return False

def fixture():
    calls=[]
    rows={
        "p2_social_video_review_candidate":{
            "shop_id":SHOP,"job_id":JOB,"media_asset_id":ASSET,
            "revision":1,"source":"GENERATED","storage_bucket":"retailgrowth-media",
            "object_path":SHOP+"/renders/91000000-0000-4000-8000-000000000001.mp4",
            "scheduled_at":"2026-10-26T16:00:00Z"},
        "p2_social_video_render_receipt":{
            "shop_id":SHOP,"media_asset_id":ASSET,
            "source_sha256":"ab"*32,"source":"PART1_RENDER_FINALIZED",
            "object_path":SHOP+"/renders/91000000-0000-4000-8000-000000000001.mp4"},
        "p2_social_video_rights_for_review":{
            "shop_id":SHOP,"media_asset_id":ASSET,"reviewed_by":ACTOR,
            "revision":1,"rights_kind":"GENERATED_RIGHTS_VERIFIED",
            "rights_evidence_sha256":"cd"*32,
            "rights_expires_at":"2026-10-29T00:00:00Z"},
        "p2_record_social_media_review":True,
        "p2_bind_social_video_review":True,
    }
    def transport(req,timeout):
        assert timeout==10
        assert req.get_header("Apikey")=="sb_secret_testing"
        name=req.full_url.rsplit("/",1)[1]
        calls.append((name,json.loads(req.data)))
        return Response(req.full_url,rows[name])
    store=ScopedSocialVideoReviewStore(ORIGIN,"sb_secret_testing",
             shop_id=SHOP,job_id=JOB,reviewer_id=ACTOR,transport=transport)
    return store,calls,rows

def test_private_review_sources_are_scoped_and_typed():
    store,calls,rows=fixture()
    source=store.get_source(SHOP,JOB,ACTOR)
    assert source["scheduled_at"]==datetime(2026,10,26,16,tzinfo=timezone.utc)
    receipt=store.get_render_receipt(SHOP,ASSET)
    assert receipt["source_sha256"]=="ab"*32
    rights=store.get_clearance(SHOP,ASSET,ACTOR,1)
    assert rights["rights_expires_at"].tzinfo is not None
    assert store.record_review(SHOP,ASSET,ACTOR,"ab"*32,"cd"*32,
      "GENERATED_RIGHTS_VERIFIED",{"video_codec":"h264"},
      rights["rights_expires_at"]) is True
    assert store.bind_review(SHOP,JOB,ACTOR,1,"ab"*32) is True
    assert [n for n,_ in calls]==[
      "p2_social_video_review_candidate","p2_social_video_render_receipt",
      "p2_social_video_rights_for_review","p2_record_social_media_review",
      "p2_bind_social_video_review"]
    assert calls[-1][1]["p_job"]==JOB

def test_other_shop_actor_job_or_asset_denied_before_sensitive_request():
    store,calls,rows=fixture()
    for method,args in [
      (store.get_source,(OTHER,JOB,ACTOR)),
      (store.get_source,(SHOP,OTHER,ACTOR)),
      (store.get_source,(SHOP,JOB,OTHER)),
      (store.get_render_receipt,(SHOP,OTHER)),
      (store.get_clearance,(SHOP,OTHER,ACTOR,1)),
      (store.record_review,(OTHER,ASSET,ACTOR,"a"*64,"c"*64,
                           "OWNER_ATTESTED",{},datetime.now(timezone.utc))),
      (store.bind_review,(SHOP,OTHER,ACTOR,1,"a"*64))
    ]:
        if method in (store.get_render_receipt,store.get_clearance):
            # These methods fetch a service-authoritative response and
            # reject any result for the wrong requested asset.
            with pytest.raises(StorageUnavailable):
                method(*args)
        else:
            with pytest.raises((ValueError,StorageUnavailable)):
                method(*args)
    assert all(k not in ("p2_record_social_media_review","p2_bind_social_video_review")
               for k,_ in calls)

def test_tampered_backend_data_or_refused_cas_denied():
    store,calls,rows=fixture()
    rows["p2_social_video_render_receipt"]["media_asset_id"]=OTHER
    with pytest.raises(StorageUnavailable,match="mismatched asset"):
        store.get_render_receipt(SHOP,ASSET)
    rows["p2_social_video_review_candidate"]["scheduled_at"]="not-a-date"
    with pytest.raises(StorageUnavailable,match="timestamp"):
        store.get_source(SHOP,JOB,ACTOR)
    rows["p2_record_social_media_review"]=False
    assert not store.record_review(SHOP,ASSET,ACTOR,"ab"*32,"cd"*32,
        "OWNER_ATTESTED",{},datetime(2026,10,29,tzinfo=timezone.utc))
    rows["p2_bind_social_video_review"]=False
    assert not store.bind_review(SHOP,JOB,ACTOR,1,"ab"*32)

@pytest.mark.parametrize("origin",[
 "http://retail.test.supabase.co",
 "https://retail.test.supabase.co:444",
 "https://retail.test.supabase.co@evil.invalid",
 "https://retail.test.supabase.co/path",
 "https://retail.test.supabase.co\n",
])
def test_origins_fail_closed(origin):
    with pytest.raises(ValueError):
        ScopedSocialVideoReviewStore(origin,"sb_secret_testing",
            shop_id=SHOP,job_id=JOB,reviewer_id=ACTOR)
