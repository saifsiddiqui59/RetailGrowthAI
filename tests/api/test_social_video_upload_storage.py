"""Offline integration between P2 DB state façade and source-only providers."""
from io import BytesIO
from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_video_upload_storage import ScopedVideoUploadStorage,VideoUploadStorageDenied
from social_media_uploads import InstagramReelUpload,YouTubeResumableUpload
from social_dispatch import ProviderFailure
from social_oauth import TokenVault
from tenant_store import StorageUnavailable

SHOP="31000000-0000-4000-8000-000000000001"
JOB="13000000-0000-4000-8000-000000000001"
CLAIM="92000000-0000-4000-8000-000000000001"
ACCOUNT="72000000-0000-4000-8000-000000000001"
IG="123456789"
SHA="ab"*32
URL=("https://retail.test.supabase.co/storage/v1/object/sign/retailgrowth-media/"
    "31000000-0000-4000-8000-000000000001/social-exports/"
    "13000000-0000-4000-8000-000000000001/1/"+SHA+
    ".mp4?token=LONG-SIGNED-MEDIA-TOKEN-123456")
SESSION="https://www.googleapis.com/upload/youtube/v3/videos?upload_id=opaque"
VIDEOID="Abc123_XyZ0"

class Response:
    status=200
    def __init__(self,url,value):
        self.url=url;self.body=BytesIO(json.dumps(value).encode())
    def geturl(self):return self.url
    def read(self,n):return self.body.read(n)
    def __enter__(self):return self
    def __exit__(self,*a):return False

class FakeState:
    def __init__(self,provider):
        self.calls=[]
        self.stage=None
        self.container=None
        self.session_cipher=None
        self.session_version=None
        self.allow=True
        self.provider=provider
        self.media_size=12
        self.remote=None
    def transport(self,req,timeout):
        assert timeout==10 and req.get_header("Apikey")=="sb_secret_testing"
        name=req.full_url.rsplit("/",1)[1]
        data=json.loads(req.data)
        assert data.get("p_job")==JOB and data.get("p_claim")==CLAIM
        self.calls.append((name,data))
        if not self.allow:
            return Response(req.full_url,None)
        if name=="p2_begin_social_video_upload":
            result=self.stage is None and data["p_size"]==self.media_size and data["p_sha"]==SHA
            if result:self.stage="INITIATED"
        elif name=="p2_video_container_for_claim":
            result=self.container if self.stage in ("CONTAINER_KNOWN","PUBLISH_INTENT") else None
        elif name=="p2_advance_social_video_upload":
            result=self.stage==data["p_from"]
            if result:
                self.stage=data["p_to"]
                if self.stage=="CONTAINER_KNOWN":self.container=data["p_remote"]
                if self.stage=="PUBLISHED":self.remote=data["p_remote"]
        elif name=="p2_save_youtube_session":
            result=self.stage=="INITIATED" and data["p_version"]==1
            if result:
                self.stage="SESSION_KNOWN"
                self.session_cipher=data["p_cipher_hex"]
                self.session_version=data["p_version"]
        elif name=="p2_youtube_session_for_claim":
            result=({"ciphertext_hex":self.session_cipher,
                     "key_version":self.session_version}
                    if self.stage in ("SESSION_KNOWN","BINARY_INTENT") else None)
        else:
            raise AssertionError("unapproved RPC invoked")
        return Response(req.full_url,result)

def scoped(provider="instagram",provider_id=IG,size=12):
    state=FakeState(provider);state.media_size=size
    vault=TokenVault(bytes(range(32)),version=1)
    storage=ScopedVideoUploadStorage(
      origin="https://retail.test.supabase.co",service_key="sb_secret_testing",
      shop_id=SHOP,job_id=JOB,claim_token=CLAIM,provider=provider,
      social_account_id=ACCOUNT,provider_account_id=provider_id,
      source_sha256=SHA,media_size=size,vault=vault,
      enabled=True,transport=state.transport)
    return storage,state

def test_instagram_container_and_publish_receipts_use_exact_db_cas():
    storage,state=scoped()
    posts=[]
    def provider(req):
        posts.append(req)
        if req.url.endswith("/media"):return 200,{"id":"987654321"},{}
        if "fields=status_code" in req.url:return 200,{"status_code":"FINISHED"},{}
        if req.url.endswith("/media_publish"):return 200,{"id":"111222333"},{}
        raise AssertionError("unknown provider request")
    upload=InstagramReelUpload(transport=provider,storage=storage,
      graph_version="v26.0",supabase_origin="https://retail.test.supabase.co")
    assert upload.create_container(job_id=JOB,ig_account_id=IG,token="hidden",
        video_url=URL,caption="Reviewed reel")=="987654321"
    receipt=upload.publish_finished(job_id=JOB,ig_account_id=IG,token="hidden")
    assert receipt.remote_id=="111222333"
    assert state.stage=="PUBLISHED" and state.remote=="111222333"
    assert len([x for x in posts if x.method=="POST"])==2
    with pytest.raises(ProviderFailure,match="CONTAINER_CREATION_MAY_HAVE_OCCURRED"):
        upload.create_container(job_id=JOB,ig_account_id=IG,token="hidden",
            video_url=URL,caption="Reviewed reel")
    assert len([x for x in posts if x.method=="POST"])==2

def test_youtube_private_aes_session_and_resumable_receipt_are_fenced():
    storage,state=scoped("youtube",provider_id="channel123",size=12)
    posted=[]
    def transport(req):
        posted.append(req)
        if req.method=="POST":
            return 200,{},{"location":SESSION}
        return 201,{"id":VIDEOID},{}
    upload=YouTubeResumableUpload(transport=transport,storage=storage)
    assert upload.initialize(job_id=JOB,token="private",title="Short",
        description="Reviewed",size_bytes=12)=="SESSION_STORED"
    assert state.stage=="SESSION_KNOWN"
    assert SESSION not in state.session_cipher
    assert storage.get_session(JOB)==SESSION
    receipt=upload.upload_once(job_id=JOB,token="private",video_bytes=b"synthetic123")
    assert receipt.remote_id==VIDEOID
    assert state.stage=="PUBLISHED" and state.remote==VIDEOID
    assert len(posted)==2

def test_key_version_and_wrong_claim_or_shop_deny_session():
    storage,state=scoped("youtube",provider_id="channel123")
    assert storage.begin_upload(JOB,12)
    assert storage.save_session(JOB,SESSION)
    state.session_version=2
    with pytest.raises(VideoUploadStorageDenied,match="SESSION_KEY_DENIED"):
        storage.get_session(JOB)
    state.session_version=1
    # Ciphertext is AES-GCM tenant/account AAD-bound.
    storage.social_account_id="73000000-0000-4000-8000-000000000001"
    with pytest.raises(VideoUploadStorageDenied,match="SESSION_DECRYPT_DENIED"):
        storage.get_session(JOB)
    with pytest.raises(VideoUploadStorageDenied):
        storage.begin_upload("93000000-0000-4000-8000-000000000001",12)

def test_stage_replay_denied_before_second_provider_side_effect():
    storage,state=scoped()
    assert storage.begin_container(JOB,IG)
    assert not storage.begin_container(JOB,IG)
    assert storage.save_container(JOB,IG,"987654321")
    assert not storage.save_container(JOB,IG,"987654321")
    assert storage.get_container(JOB,IG)=="987654321"
    assert storage.record_publish_intent(JOB,"987654321")
    assert not storage.record_publish_intent(JOB,"987654321")
    assert storage.record_publish_receipt(JOB,"987654321","111222333")

def test_disabled_by_default_and_foreign_provider_scope_denied():
    with pytest.raises(VideoUploadStorageDenied,match="RELEASE_DISABLED"):
        ScopedVideoUploadStorage(
          origin="https://retail.test.supabase.co",service_key="sb_secret_testing",
          shop_id=SHOP,job_id=JOB,claim_token=CLAIM,provider="instagram",
          social_account_id=ACCOUNT,provider_account_id=IG,
          source_sha256=SHA,media_size=12,vault=TokenVault(bytes(range(32)),1))
    storage,state=scoped("youtube",provider_id="channel123")
    with pytest.raises(VideoUploadStorageDenied,match="PROVIDER_INVALID"):
        storage.begin_container(JOB,"channel123")
    assert state.calls==[]

def test_revoked_backend_claim_never_sends_provider_request():
    storage,state=scoped()
    state.allow=False
    requests=[]
    upload=InstagramReelUpload(transport=lambda r:requests.append(r),
        storage=storage,graph_version="v26.0",
        supabase_origin="https://retail.test.supabase.co")
    with pytest.raises(ProviderFailure,match="CONTAINER_CREATION_MAY_HAVE_OCCURRED"):
        upload.create_container(job_id=JOB,ig_account_id=IG,
            token="hidden",video_url=URL,caption="Reviewed")
    assert requests==[]

def test_private_session_ciphertext_never_in_exception():
    storage,state=scoped("youtube",provider_id="channel123")
    assert storage.begin_upload(JOB,12)
    assert storage.save_session(JOB,SESSION)
    state.session_cipher="de"*40
    with pytest.raises(VideoUploadStorageDenied) as err:
        storage.get_session(JOB)
    assert SESSION not in str(err.value)
