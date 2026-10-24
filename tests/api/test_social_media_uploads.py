"""Mock-only media upload state machines: no live Meta/Google requests."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_media_uploads import InstagramReelUpload, YouTubeResumableUpload, BinaryUploadRequest
from social_dispatch import ProviderFailure
from social_providers import ProviderRequest

JOB="13000000-0000-4000-8000-000000000001"
IG="123456789"
TOKEN="server-held-private-token"
URL="https://retail.supabase.co/storage/v1/object/sign/retailgrowth-media/31000000-0000-4000-8000-000000000001/social-exports/62000000-0000-4000-8000-000000000001/1/abababababababababababababababababababababababababababababababab.mp4?token=signed-token-SIGNED-TOKEN-123456"
SESSION="https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&upload_id=session-123"
VIDEOID="Abc123_XyZ0"


class InstagramState:
    def __init__(self):
        self.open=False;self.container=None;self.intent=False;self.receipt=None
    def begin_container(self,jid,account):
        if self.open:return False
        self.open=True;return True
    def save_container(self,jid,account,container):self.container=container;return True
    def get_container(self,jid,account):return self.container
    def record_publish_intent(self,jid,container):
        if self.intent:return False
        self.intent=True;return True
    def record_publish_receipt(self,jid,container,remote):
        self.receipt=remote;return True


def test_ig_reel_requires_finished_container_and_durable_post_intent():
    state=InstagramState();calls=[]
    def transport(request):
        calls.append(request)
        if request.url.endswith("/media"):
            assert request.method=="POST"
            assert request.body["media_type"]=="REELS"
            return 200,{"id":"987654321"},{}
        if "fields=status_code" in request.url:
            assert request.method=="GET"
            return 200,{"status_code":"FINISHED"},{}
        if request.url.endswith("/media_publish"):
            assert request.body["creation_id"]=="987654321"
            assert state.intent is True
            return 200,{"id":"555444333"},{}
        raise AssertionError("unexpected request "+request.url)
    uploader=InstagramReelUpload(transport=transport,storage=state,
        graph_version="v26.0",supabase_origin="https://retail.supabase.co")
    assert uploader.create_container(job_id=JOB,ig_account_id=IG,
        token=TOKEN,video_url=URL,caption="Reviewed reel")=="987654321"
    receipt=uploader.publish_finished(job_id=JOB,ig_account_id=IG,token=TOKEN)
    assert receipt.remote_id=="555444333" and receipt.status=="PUBLISHED"
    assert state.receipt=="555444333"
    with pytest.raises(ProviderFailure) as denied:
        uploader.publish_finished(job_id=JOB,ig_account_id=IG,token=TOKEN)
    assert denied.value.code=="PUBLISH_INTENT_ALREADY_RECORDED"
    assert [r.method for r in calls]==["POST","GET","POST","GET"]


def test_ig_reject_unlicensed_url_and_unfinished_reel_before_external_post():
    state=InstagramState();calls=[]
    u=InstagramReelUpload(transport=lambda req:calls.append(req) or
        (200,{"status_code":"IN_PROGRESS"},{}),
        storage=state,graph_version="v26.0",
        supabase_origin="https://retail.supabase.co")
    with pytest.raises(ProviderFailure) as denial:
        u.create_container(job_id=JOB,ig_account_id=IG,token=TOKEN,
            video_url="https://attacker.invalid/unlicensed.mp4",caption="Caption")
    assert denial.value.definitely_not_sent and calls==[]
    state.container="987654321"
    with pytest.raises(ProviderFailure) as denial:
        u.publish_finished(job_id=JOB,ig_account_id=IG,token=TOKEN)
    assert denial.value.code=="CONTAINER_NOT_FINISHED"
    assert state.intent is False and len(calls)==1


def test_ig_ambiguous_publish_cannot_repeat_and_never_reveal_secret():
    state=InstagramState();state.container="987654321";requests=[]
    def transport(req):
        requests.append(req)
        if req.method=="GET":return 200,{"status_code":"FINISHED"},{}
        raise TimeoutError("secret provider bearer token DO_NOT_LEAK")
    u=InstagramReelUpload(transport=transport,storage=state,
        graph_version="v26.0",supabase_origin="https://retail.supabase.co")
    with pytest.raises(ProviderFailure) as first:
        u.publish_finished(job_id=JOB,ig_account_id=IG,token=TOKEN)
    assert first.value.code=="INSTAGRAM_PUBLISH_UNCERTAIN"
    with pytest.raises(ProviderFailure) as second:
        u.publish_finished(job_id=JOB,ig_account_id=IG,token=TOKEN)
    assert second.value.code=="PUBLISH_INTENT_ALREADY_RECORDED"
    assert len([x for x in requests if x.method=="POST"])==1
    assert "DO_NOT_LEAK" not in str(first.value)


class YouTubeState:
    def __init__(self):
        self.started=False;self.url=None;self.intent=False;self.receipt=None
    def begin_upload(self,jid,size):
        if self.started:return False
        self.started=True;return True
    def save_session(self,jid,url):self.url=url;return True
    def get_session(self,jid):return self.url
    def record_binary_intent(self,jid,size):
        if self.intent:return False
        self.intent=True;return True
    def record_upload_receipt(self,jid,rid):self.receipt=rid;return True


def test_youtube_init_session_persist_then_binary_put_and_confirm_remote_id():
    state=YouTubeState();calls=[]
    def transport(req):
        calls.append(req)
        if req.method=="POST":
            assert req.body["status"]["privacyStatus"]=="private"
            return 200,{},{"location":SESSION}
        assert isinstance(req,BinaryUploadRequest)
        assert req.url==SESSION and req.data==b"synthetic-video"
        assert state.url==SESSION and state.intent
        return 201,{"id":VIDEOID},{}
    u=YouTubeResumableUpload(transport=transport,storage=state)
    assert u.initialize(job_id=JOB,token=TOKEN,title="My Reel",
        description="Test",size_bytes=len(b"synthetic-video"))=="SESSION_STORED"
    result=u.upload_once(job_id=JOB,token=TOKEN,video_bytes=b"synthetic-video")
    assert result.remote_id==VIDEOID
    assert state.receipt==VIDEOID
    with pytest.raises(ProviderFailure,match="BINARY_SEND_MAY_HAVE_OCCURRED"):
        u.upload_once(job_id=JOB,token=TOKEN,video_bytes=b"synthetic-video")
    assert len(calls)==2


def test_youtube_interrupted_put_status_probe_only_no_automatic_resend():
    state=YouTubeState();state.url=SESSION;calls=[]
    def transport(req):
        calls.append(req)
        assert isinstance(req,BinaryUploadRequest)
        assert req.data==b"" and req.headers["Content-Range"]=="bytes */321"
        return 308,{},{"range":"bytes=0-99"}
    u=YouTubeResumableUpload(transport=transport,storage=state)
    assert u.probe_interrupted(job_id=JOB,token=TOKEN,size_bytes=321)==(
        "INCOMPLETE_RECONCILE_REQUIRED")
    assert len(calls)==1


def test_youtube_completed_but_lost_upload_response_reconciles_remote_id():
    state=YouTubeState();state.url=SESSION
    u=YouTubeResumableUpload(transport=lambda req:(200,{"id":VIDEOID},{}),
        storage=state)
    result=u.probe_interrupted(job_id=JOB,token=TOKEN,size_bytes=321)
    assert result.remote_id==VIDEOID and state.receipt==VIDEOID


def test_youtube_session_must_be_strict_google_upload_url():
    state=YouTubeState()
    u=YouTubeResumableUpload(transport=lambda req:
        (200,{},{"location":"https://googleapis.com.attacker.invalid/steal"}),
        storage=state)
    with pytest.raises(ProviderFailure):
        u.initialize(job_id=JOB,token=TOKEN,title="Test",
            description="Test",size_bytes=20)
    assert state.url is None


def test_youtube_no_second_binary_transfer_when_first_timeout_uncertain():
    state=YouTubeState();state.url=SESSION
    calls=[]
    def fail(req):
        calls.append(req)
        raise TimeoutError("private session URL")
    u=YouTubeResumableUpload(transport=fail,storage=state)
    with pytest.raises(ProviderFailure,match="YOUTUBE_UPLOAD_UNCERTAIN"):
        u.upload_once(job_id=JOB,token=TOKEN,video_bytes=b"video")
    with pytest.raises(ProviderFailure,match="BINARY_SEND_MAY_HAVE_OCCURRED"):
        u.upload_once(job_id=JOB,token=TOKEN,video_bytes=b"video")
    assert len(calls)==1
