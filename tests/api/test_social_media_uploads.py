"""Mock-only media upload state machines: no live Meta/Google requests."""
import sys
from pathlib import Path
from hashlib import sha256
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_media_uploads import InstagramReelUpload, YouTubeResumableUpload, BinaryUploadRequest, YouTubeResumeStatus
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



def test_ig_second_container_create_intent_is_ambiguous_not_safe_to_retry():
    state=InstagramState()
    attempts=[]
    def timeout(req):
        attempts.append(req)
        raise TimeoutError("remote may have accepted container")
    u=InstagramReelUpload(transport=timeout,storage=state,
        graph_version="v26.0",supabase_origin="https://retail.supabase.co")
    with pytest.raises(ProviderFailure,match="CONTAINER_RESULT_UNCERTAIN") as first:
        u.create_container(job_id=JOB,ig_account_id=IG,token=TOKEN,
            video_url=URL,caption="Approved video")
    assert first.value.definitely_not_sent is False
    with pytest.raises(ProviderFailure,match="CONTAINER_CREATION_MAY_HAVE_OCCURRED") as replay:
        u.create_container(job_id=JOB,ig_account_id=IG,token=TOKEN,
            video_url=URL,caption="Approved video")
    assert replay.value.definitely_not_sent is False
    assert len(attempts)==1


def test_youtube_duplicate_session_init_intent_is_ambiguous_not_safe_to_retry():
    state=YouTubeState()
    requests=[]
    def timeout(req):
        requests.append(req)
        raise TimeoutError("YouTube may already have returned a session")
    u=YouTubeResumableUpload(transport=timeout,storage=state)
    with pytest.raises(ProviderFailure,match="UPLOAD_INITIALIZATION_UNCERTAIN") as first:
        u.initialize(job_id=JOB,token=TOKEN,title="Reviewed video",
            description="Approved",size_bytes=1234)
    assert first.value.definitely_not_sent is False
    with pytest.raises(ProviderFailure,match="UPLOAD_SESSION_INIT_MAY_HAVE_OCCURRED") as again:
        u.initialize(job_id=JOB,token=TOKEN,title="Reviewed video",
            description="Approved",size_bytes=1234)
    assert again.value.definitely_not_sent is False
    assert len(requests)==1


@pytest.mark.parametrize("remote_range, expected",[
    (None,0),("bytes=0-0",1),("bytes=0-99",100),
    ("bytes=0-319",320),
])
def test_youtube_308_range_is_remote_confirmed_read_only_offset(remote_range,expected):
    state=YouTubeState();state.url=SESSION
    seen=[]
    def transport(req):
        seen.append(req)
        assert req.data==b"" and req.method=="PUT"
        assert req.headers["Content-Range"]=="bytes */321"
        return 308,{},({} if remote_range is None else {"Range":remote_range})
    u=YouTubeResumableUpload(transport=transport,storage=state)
    result=u.probe_interrupted_detail(job_id=JOB,token=TOKEN,size_bytes=321)
    assert isinstance(result,YouTubeResumeStatus)
    assert (result.next_byte,result.total_bytes,result.state)==(
        expected,321,"INCOMPLETE_RECONCILE_REQUIRED")
    assert TOKEN not in str(result)
    assert SESSION not in str(result)
    assert len(seen)==1
    assert state.receipt is None
    assert state.intent is False


@pytest.mark.parametrize("remote_headers",[
    {"Range":"bytes=0-320"},    # 308 contradicts full transfer
    {"Range":"bytes=0-321"},    # larger than file
    {"Range":"bytes=1-20"},     # not a contiguous prefix
    {"Range":"bytes=0-01"},     # ambiguous noncanonical range
    {"Range":"bytes=0--1"},
    {"Range":"bytes=0-10000000000000000000"},
    {"range":"bytes=0-10","Range":"bytes=0-99"},
    {"Range":["bytes=0-99"]},
    {"Range":"bytes=0-99\r\nInjected: yes"},
])
def test_youtube_308_invalid_range_fails_closed_without_upload(remote_headers):
    state=YouTubeState();state.url=SESSION
    calls=[]
    u=YouTubeResumableUpload(
        transport=lambda req:calls.append(req) or (308,{},remote_headers),
        storage=state)
    with pytest.raises(ProviderFailure,match="UPLOAD_STATUS_UNKNOWN") as e:
        u.probe_interrupted_detail(job_id=JOB,token=TOKEN,size_bytes=321)
    assert e.value.definitely_not_sent is False
    assert len(calls)==1 and calls[0].data==b""
    assert state.intent is False and state.receipt is None


def test_youtube_308_detail_completed_response_commits_remote_receipt_once():
    state=YouTubeState();state.url=SESSION
    seen=[]
    uploader=YouTubeResumableUpload(
        transport=lambda req:seen.append(req) or (201,{"id":VIDEOID},{}),
        storage=state)
    found=uploader.probe_interrupted_detail(job_id=JOB,token=TOKEN,size_bytes=321)
    assert found.remote_id==VIDEOID and found.status=="PUBLISHED"
    assert state.receipt==VIDEOID
    assert len(seen)==1 and seen[0].data==b""


def test_youtube_probe_status_result_preserves_legacy_contract():
    state=YouTubeState();state.url=SESSION
    u=YouTubeResumableUpload(
        transport=lambda req:(308,{},{"Range":"bytes=0-99"}),
        storage=state)
    assert u.probe_interrupted(job_id=JOB,token=TOKEN,size_bytes=321)==(
        "INCOMPLETE_RECONCILE_REQUIRED")


class ResumeState(YouTubeState):
    def __init__(self, payload):
        super().__init__()
        self.url=SESSION
        self.source_sha256=sha256(payload).hexdigest()
        self.resume_offset=None
        self.authorized=True
        self.resume_checks=0
    def record_resume_intent(self,jid,next_byte,size,source_sha):
        self.resume_checks+=1
        if (not self.authorized or self.resume_offset is not None
                or source_sha!=self.source_sha256
                or not 0<=next_byte<size):
            return False
        self.resume_offset=next_byte
        return True


def test_youtube_one_shot_resume_revalidates_sha_offset_and_terminal_receipt():
    body=b"private-reviewed-bytes"
    state=ResumeState(body)
    requests=[]
    def provider(req):
        requests.append(req)
        if req.data==b"":
            assert req.headers["Content-Range"]==f"bytes */{len(body)}"
            return 308,{},{"Range":"bytes=0-6"}
        assert req.data==body[7:]
        assert req.headers["Content-Range"]==f"bytes 7-{len(body)-1}/{len(body)}"
        assert req.headers["Content-Length"]==str(len(body)-7)
        assert state.resume_offset==7
        return 201,{"id":VIDEOID},{}
    upload=YouTubeResumableUpload(transport=provider,storage=state)
    result=upload.resume_verified(job_id=JOB,token=TOKEN,video_bytes=body)
    assert result.status=="PUBLISHED" and result.remote_id==VIDEOID
    assert state.receipt==VIDEOID and state.resume_checks==1
    assert [req.data for req in requests]==[b"",body[7:]]
    # Any replay may issue a harmless status-only probe, but NEVER a second PUT.
    with pytest.raises(ProviderFailure,match="RESUME_INTENT_MAY_HAVE_OCCURRED"):
        upload.resume_verified(job_id=JOB,token=TOKEN,video_bytes=body)
    assert [req.data for req in requests]==[b"",body[7:],b""]


def test_youtube_resume_rejects_mutated_source_and_revoked_db_before_bytes():
    body=b"trusted-binary"
    state=ResumeState(body)
    requests=[]
    uploader=YouTubeResumableUpload(
        transport=lambda req:requests.append(req) or
            (308,{},{"Range":"bytes=0-3"}), storage=state)
    with pytest.raises(ProviderFailure,match="UNTRUSTED_VIDEO_BYTES") as err:
        uploader.resume_verified(job_id=JOB,token=TOKEN,video_bytes=body+b"tampered")
    assert err.value.definitely_not_sent is True
    assert requests==[] and state.resume_checks==0
    state.authorized=False
    with pytest.raises(ProviderFailure,match="RESUME_INTENT_MAY_HAVE_OCCURRED"):
        uploader.resume_verified(job_id=JOB,token=TOKEN,video_bytes=body)
    assert len(requests)==1 and requests[0].data==b""
    assert state.resume_offset is None


def test_youtube_uncertain_resumed_put_never_blind_retries_binary():
    body=b"abcdefghi"
    state=ResumeState(body)
    requests=[]
    def provider(req):
        requests.append(req)
        if req.data==b"": return 308,{},{"Range":"bytes=0-2"}
        raise TimeoutError("secret session or bearer token DO_NOT_LOG")
    uploader=YouTubeResumableUpload(transport=provider,storage=state)
    with pytest.raises(ProviderFailure,match="YOUTUBE_RESUME_UNCERTAIN") as err:
        uploader.resume_verified(job_id=JOB,token=TOKEN,video_bytes=body)
    assert "DO_NOT_LOG" not in str(err.value)
    assert state.resume_offset==3 and len(requests)==2
    with pytest.raises(ProviderFailure,match="RESUME_INTENT_MAY_HAVE_OCCURRED"):
        uploader.resume_verified(job_id=JOB,token=TOKEN,video_bytes=body)
    assert [r.data for r in requests]==[b"",body[3:],b""]


def test_youtube_resume_completed_during_status_probe_sends_no_binary():
    body=b"abcdefgh"
    state=ResumeState(body)
    requests=[]
    uploader=YouTubeResumableUpload(
        transport=lambda req:requests.append(req) or (200,{"id":VIDEOID},{}),
        storage=state)
    result=uploader.resume_verified(job_id=JOB,token=TOKEN,video_bytes=body)
    assert result.status=="PUBLISHED" and result.remote_id==VIDEOID
    assert len(requests)==1 and requests[0].data==b""
    assert state.resume_checks==0 and state.receipt==VIDEOID
