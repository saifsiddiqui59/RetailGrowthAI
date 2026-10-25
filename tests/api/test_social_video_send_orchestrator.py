"""Mock-only E2E: private P1 render -> rights CAS -> Instagram / YouTube receipts.

Never touches real Supabase Storage, OAuth, Azure or provider networks.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_video_send_orchestrator import ReviewedVideoSendOrchestrator, VideoSendDenied
from social_dispatch import Delivery, ProviderFailure

SID="31000000-0000-4000-8000-000000000001"
JOB="62000000-0000-4000-8000-000000000001"
LEASE="92000000-0000-4000-8000-000000000001"
ASSET="81000000-0000-4000-8000-000000000001"
ACCOUNT="72000000-0000-4000-8000-000000000001"
SRC=SID+"/renders/91000000-0000-4000-8000-000000000001.mp4"
BYTES=b"synthetic private media; no live provider request"
SHA=sha256(BYTES).hexdigest()
NOW=datetime(2026,10,25,12,0,tzinfo=timezone.utc)


class Claims:
    def __init__(self,provider):
        self.authorized=True
        self.allow_calls=0
        self.ctx={
            "shop_id":SID,"job_id":JOB,"claim_token":LEASE,
            "provider":provider,"media_asset_id":ASSET,
            "source_sha256":SHA,"source":"PART1_RENDER_FINALIZED",
            "object_path":SRC,"storage_bucket":"retailgrowth-media",
            "revision":2,"status":"SENDING",
            "approved_digest":"ab"*32,
            "scheduled_at":NOW-timedelta(minutes=1),
            "rights_expires_at":NOW+timedelta(days=2),
            "rights_kind":"GENERATED_RIGHTS_VERIFIED",
            "rights_evidence_sha256":"cd"*32,
            "connection_status":"CONNECTED",
            "granted_scopes":["instagram_content_publish"] if provider=="instagram" else ["youtube.upload"],
            "social_account_id":ACCOUNT,
            "provider_account_id":"123456789" if provider=="instagram" else "channel-123",
            "caption":"Reviewed copy","title":"Reviewed video",
            "description":"Licensed creative","access_token":"SUPER-SECRET",
        }
    def load(self,job,lease):
        assert (job,lease)==(JOB,LEASE)
        return self.ctx
    def allow(self,data):
        self.allow_calls+=1
        return self.authorized


class Reader:
    def __init__(self):
        self.content=BYTES
        self.calls=[]
    def download(self,**kwargs):
        self.calls.append(kwargs)
        path=kwargs["destination"]
        path.write_bytes(self.content)
        return {"path":path,"source_sha256":sha256(self.content).hexdigest(),
                "size_bytes":len(self.content)}


class Export:
    def __init__(self):
        self.calls=[]
        self.fail=False
    def create_signed_export(self,**kw):
        self.calls.append(kw)
        if self.fail:
            return {"state":"UNVERIFIED"}
        return {"state":"IMMUTABLE_EXPORT_VERIFIED",
                "source_sha256":SHA,
                "signed_url":"https://safe.supabase.co/storage/v1/object/sign/retailgrowth-media/"
                    +SID+"/social-exports/"+JOB+"/2/"+SHA+".mp4?token=SAFE-TOKEN-LONG"}


class Uploader:
    def __init__(self):
        self.calls=[]
        self.stage="NEW"
        self.timeout_on_create=False
    def create_container(self,**params):
        self.calls.append(("create_container",params))
        if self.stage!="NEW":
            raise ProviderFailure("CONTAINER_CREATION_MAY_HAVE_OCCURRED")
        self.stage="CONTAINER_INTENT"
        if self.timeout_on_create:
            raise ProviderFailure("CONTAINER_RESULT_UNCERTAIN")
        self.stage="CONTAINER_KNOWN"
        return "12345678"
    def publish_finished(self,**params):
        self.calls.append(("publish_finished",params))
        if self.stage!="CONTAINER_KNOWN":
            raise ProviderFailure("PUBLISH_INTENT_ALREADY_RECORDED")
        self.stage="PUBLISH_INTENT"
        self.stage="PUBLISHED"
        return Delivery(remote_id="123456789",status="PUBLISHED")
    def initialize(self,**params):
        self.calls.append(("initialize",params))
        if self.stage!="NEW":
            raise ProviderFailure("UPLOAD_SESSION_INIT_MAY_HAVE_OCCURRED")
        self.stage="SESSION_KNOWN"
        return "SESSION_STORED"
    def upload_once(self,**params):
        self.calls.append(("upload_once",params))
        if self.stage!="SESSION_KNOWN":
            raise ProviderFailure("BINARY_SEND_MAY_HAVE_OCCURRED")
        self.stage="BINARY_INTENT"
        self.stage="PUBLISHED"
        return Delivery(remote_id="Abc123_XyZ0",status="PUBLISHED")


class UploadFactory:
    def __init__(self):
        self.uploader=Uploader()
        self.calls=[]
    def build(self,context):
        self.calls.append(context)
        return self.uploader


def profile(**kwargs):
    assert kwargs["source_path"].read_bytes()==BYTES
    assert kwargs["expected_sha256"]==SHA
    return {"source_sha256":SHA,"ffprobe":{
        "video_codec":"h264","audio_codec":"aac","pixel_format":"yuv420p",
        "width":1080,"height":1920,"duration_seconds":"30.000",
    }}


def fixture(provider="instagram",probe=profile):
    claims=Claims(provider)
    reader,export,factory=Reader(),Export(),UploadFactory()
    worker=ReviewedVideoSendOrchestrator(
        claims=claims,private_reader=reader,
        upload_factory=factory,instagram_export=export,
        probe=probe,clock=lambda:NOW,enabled=True)
    return worker,claims,reader,export,factory


def test_instagram_one_authorized_export_then_remote_container_then_publish():
    worker,claims,reader,export,factory=fixture()
    assert worker.start(job_id=JOB,claim_token=LEASE)=={
        "job_id":JOB,"state":"CONTAINER_PROCESSING"}
    assert len(reader.calls)==len(export.calls)==1
    assert claims.allow_calls>=3
    assert len(factory.uploader.calls)==1
    name,args=factory.uploader.calls[0]
    assert name=="create_container" and args["video_url"].startswith("https://")
    assert args["token"]=="SUPER-SECRET"
    assert worker.finish_instagram(job_id=JOB,claim_token=LEASE)=={
        "job_id":JOB,"state":"PUBLISHED"}
    assert factory.uploader.stage=="PUBLISHED"
    with pytest.raises(ProviderFailure):
        worker.finish_instagram(job_id=JOB,claim_token=LEASE)
    assert len([c for c in factory.uploader.calls if c[0]=="publish_finished"])==2
    # Responses never contain credentials, provider IDs or signed URLs.
    assert "SUPER-SECRET" not in str(worker.finish_instagram.__name__)


def test_youtube_verifies_exact_private_bytes_before_session_and_binary():
    worker,claims,reader,export,factory=fixture("youtube")
    out=worker.start(job_id=JOB,claim_token=LEASE)
    assert out=={"job_id":JOB,"state":"PUBLISHED"}
    assert export.calls==[]
    assert [name for name,_ in factory.uploader.calls]==["initialize","upload_once"]
    assert factory.uploader.calls[1][1]["video_bytes"]==BYTES
    assert factory.uploader.stage=="PUBLISHED"
    with pytest.raises(ProviderFailure,match="MAY_HAVE_OCCURRED"):
        worker.start(job_id=JOB,claim_token=LEASE)
    assert len([c for c in factory.uploader.calls if c[0]=="upload_once"])==1


@pytest.mark.parametrize("change",[
    lambda c:c.ctx.update(shop_id="30000000-0000-4000-8000-000000000001"),
    lambda c:c.ctx.update(job_id="30000000-0000-4000-8000-000000000001"),
    lambda c:c.ctx.update(status="DRAFT"),
    lambda c:c.ctx.update(source="USER_UPLOAD"),
    lambda c:c.ctx.update(revision=True),
    lambda c:c.ctx.update(source_sha256="not-a-sha"),
    lambda c:c.ctx.update(rights_kind="UNREVIEWED"),
    lambda c:c.ctx.update(rights_expires_at=NOW+timedelta(hours=1)),
    lambda c:c.ctx.update(scheduled_at=NOW+timedelta(hours=1)),
    lambda c:c.ctx.update(connection_status="REAUTH_REQUIRED"),
    lambda c:c.ctx.update(granted_scopes=[]),
    lambda c:c.ctx.update(storage_bucket="public-media"),
    lambda c:c.ctx.update(access_token=""),
])
def test_untrusted_claim_never_downloads_or_calls_provider(change):
    worker,claims,reader,export,factory=fixture()
    change(claims)
    with pytest.raises(VideoSendDenied):
        worker.start(job_id=JOB,claim_token=LEASE)
    assert reader.calls==[] and export.calls==[] and factory.calls==[]


def test_revoked_claim_and_tampered_file_never_export_or_send():
    worker,claims,reader,export,factory=fixture()
    claims.authorized=False
    with pytest.raises(VideoSendDenied,match="CLAIM_REVOKED"):
        worker.start(job_id=JOB,claim_token=LEASE)
    assert reader.calls==[]
    worker,claims,reader,export,factory=fixture()
    reader.content=b"edited after review"
    with pytest.raises(VideoSendDenied,match="BYTES_DENIED"):
        worker.start(job_id=JOB,claim_token=LEASE)
    assert export.calls==[] and factory.calls==[]


def test_invalid_profile_and_unsigned_export_cannot_reach_meta():
    worker,claims,reader,export,factory=fixture(
        probe=lambda **kw:{"source_sha256":SHA,
             "ffprobe":{"video_codec":"h264","audio_codec":"mp3"}})
    with pytest.raises(VideoSendDenied,match="PROBE_DENIED"):
        worker.start(job_id=JOB,claim_token=LEASE)
    assert factory.calls==[]
    worker,claims,reader,export,factory=fixture()
    export.fail=True
    with pytest.raises(VideoSendDenied,match="EXPORT_DENIED"):
        worker.start(job_id=JOB,claim_token=LEASE)
    assert factory.uploader.calls==[]


def test_ambiguous_create_is_not_retried_and_stage_stays_uncertain():
    worker,claims,reader,export,factory=fixture()
    factory.uploader.timeout_on_create=True
    with pytest.raises(ProviderFailure,match="RESULT_UNCERTAIN"):
        worker.start(job_id=JOB,claim_token=LEASE)
    assert factory.uploader.stage=="CONTAINER_INTENT"
    with pytest.raises(ProviderFailure,match="MAY_HAVE_OCCURRED"):
        worker.start(job_id=JOB,claim_token=LEASE)
    assert len(factory.uploader.calls)==2  # second rejected BEFORE a remote POST


def test_disabled_without_explicit_release_and_wrong_claim_denied():
    claims=Claims("instagram")
    with pytest.raises(VideoSendDenied,match="RELEASE_DISABLED"):
        ReviewedVideoSendOrchestrator(
            claims=claims,private_reader=Reader(),
            upload_factory=UploadFactory(),instagram_export=Export())
    worker,claims,reader,export,factory=fixture()
    with pytest.raises(VideoSendDenied):
        worker.start(job_id=JOB,claim_token="not-a-uuid")
    assert factory.calls==[]
