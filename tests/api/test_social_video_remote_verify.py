"""Offline only: provider reads never authorize or repeat a publish/upload."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))

from social_video_remote_verify import ReadOnlyVideoReceiptObserver, RemoteReceiptDenied
from social_media_transport import MediaNetworkTransport
from social_dispatch import ProviderFailure
from social_providers import ProviderRequest

JOB="62000000-0000-4000-8000-000000000001"
LEASE="92000000-0000-4000-8000-000000000001"
SHOP="31000000-0000-4000-8000-000000000001"
ACCOUNT="72000000-0000-4000-8000-000000000001"
YT_ID="Abc123_XyZ0"
CHANNEL="UCchannel-id"
IG_ID="123456789"
SHA="ab"*32


class Claim:
    def __init__(self, provider="youtube"):
        self.active=True
        self.calls=0
        self.ctx={
            "shop_id":SHOP,"job_id":JOB,"claim_token":LEASE,
            "provider":provider,"social_account_id":ACCOUNT,
            "revision":2,"source_sha256":SHA,"status":"SENDING",
            "connection_status":"CONNECTED","access_token":"private-secret",
            "provider_account_id":CHANNEL if provider=="youtube" else IG_ID,
            "granted_scopes":["youtube.upload","youtube.readonly"]
                if provider=="youtube" else ["instagram_content_publish"],
        }
    def load(self, job, claim):
        assert (job,claim)==(JOB,LEASE)
        return self.ctx
    def allow(self, context):
        self.calls+=1
        return self.active


class StoredReceipt:
    def __init__(self, claim, remote=None):
        self.row={key:claim.ctx[key] for key in (
            "shop_id","job_id","claim_token","provider",
            "social_account_id","revision","source_sha256")}
        self.row["receipt_state"]="REMOTE_ID_KNOWN"
        self.row["remote_id"]=remote or (YT_ID if claim.ctx["provider"]=="youtube" else IG_ID)
    def load(self,job,lease):
        assert (job,lease)==(JOB,LEASE)
        return self.row


def verifier(provider="youtube", result=None, *, callback=None):
    claims=Claim(provider)
    receipt=StoredReceipt(claims)
    requests=[]
    if result is None:
        if provider=="youtube":
            result=(200,{"items":[{"id":YT_ID,
                "snippet":{"channelId":CHANNEL},
                "status":{"privacyStatus":"private"},
                "processingDetails":{"processingStatus":"succeeded"}}]}, {})
        else:
            result=(200,{"status_code":"PUBLISHED","id":IG_ID}, {})
    def transport(request):
        requests.append(request)
        return callback(request) if callback else result
    observer=ReadOnlyVideoReceiptObserver(
        claims=claims, receipts=receipt, transport=transport,
        graph_version="v26.0",enabled=True)
    return observer,claims,receipt,requests


def test_no_implicit_worker_or_provider_and_no_outbound_when_disabled():
    requests=[]
    with pytest.raises(RemoteReceiptDenied,match="DISABLED"):
        ReadOnlyVideoReceiptObserver(claims=Claim(),receipts=object(),
            transport=lambda req:requests.append(req),graph_version="v26.0")
    assert requests==[]


def test_youtube_verified_private_owner_processing_and_read_only_query():
    v,claims,record,calls=verifier()
    observation=v.inspect(job_id=JOB,claim_token=LEASE)
    assert (observation.provider,observation.state,observation.remote_id)==(
        "youtube","PRIVATE_PROCESSED",YT_ID)
    assert claims.calls==2
    assert len(calls)==1
    request=calls[0]
    assert request.method=="GET" and request.body=={}
    assert request.url==(
        "https://www.googleapis.com/youtube/v3/videos?"
        "part=snippet%2Cstatus%2CprocessingDetails&id="+YT_ID)
    assert "private-secret" not in repr(request)
    assert request.headers["Authorization"]=="Bearer private-secret"


def test_youtube_processing_does_not_claim_finished_upload():
    status=(200,{"items":[{"id":YT_ID,"snippet":{"channelId":CHANNEL},
        "status":{"privacyStatus":"private"},
        "processingDetails":{"processingStatus":"processing"}}]}, {})
    v,_,_,_=verifier(result=status)
    assert v.inspect(job_id=JOB,claim_token=LEASE).state=="PRIVATE_PROCESSING"


def test_youtube_failure_processing_requires_operator_review_not_unsent():
    status=(200,{"items":[{"id":YT_ID,"snippet":{"channelId":CHANNEL},
        "status":{"privacyStatus":"private"},
        "processingDetails":{"processingStatus":"failed"}}]}, {})
    v,_,_,_=verifier(result=status)
    r=v.inspect(job_id=JOB,claim_token=LEASE)
    assert (r.state,r.remote_id)==("MANUAL_REVIEW_REQUIRED",None)


@pytest.mark.parametrize("bad",[
    {"items":[]},
    {"items":[{"id":YT_ID}]},
    {"items":[{"id":YT_ID,"snippet":{"channelId":"WRONG"},
        "status":{"privacyStatus":"private"},
        "processingDetails":{"processingStatus":"succeeded"}}]},
    {"items":[{"id":YT_ID,"snippet":{"channelId":CHANNEL},
        "status":{"privacyStatus":"public"},
        "processingDetails":{"processingStatus":"succeeded"}}]},
    {"items":[{"id":"12345678901","snippet":{"channelId":CHANNEL},
        "status":{"privacyStatus":"private"},
        "processingDetails":{"processingStatus":"succeeded"}}]},
    {"items":"bad"},
])
def test_youtube_provider_response_cannot_cross_account_or_claim_publication(bad):
    v,_,_,calls=verifier(result=(200,bad,{}))
    with pytest.raises(RemoteReceiptDenied,match="REMOTE_UNCERTAIN"):
        v.inspect(job_id=JOB,claim_token=LEASE)
    assert len(calls)==1


def test_instagram_container_is_not_a_final_post_receipt_even_if_published():
    v,claims,receipt,calls=verifier("instagram")
    r=v.inspect(job_id=JOB,claim_token=LEASE)
    assert r.provider=="instagram" and r.state=="FINAL_POST_RECEIPT_REQUIRED"
    assert r.remote_id is None
    assert calls[0].method=="GET" and "/"+IG_ID in calls[0].url
    assert len(calls)==1 and claims.calls==2


@pytest.mark.parametrize("status",["FINISHED","IN_PROGRESS","ERROR","EXPIRED"])
def test_instagram_any_container_state_requires_independent_final_receipt(status):
    v,_,_,_=verifier("instagram",result=(200,{"status_code":status,"id":IG_ID},{}))
    assert v.inspect(job_id=JOB,claim_token=LEASE).state=="FINAL_POST_RECEIPT_REQUIRED"


@pytest.mark.parametrize("mutation",[
    lambda c,r:c.ctx.update(connection_status="REAUTH_REQUIRED"),
    lambda c,r:c.ctx.update(granted_scopes=["youtube.upload"]),
    lambda c,r:c.ctx.update(status="CANCELLED"),
    lambda c,r:r.row.update(source_sha256="cd"*32),
    lambda c,r:r.row.update(claim_token="wrong-lease"),
    lambda c,r:r.row.update(receipt_state="BINARY_INTENT"),
    lambda c,r:r.row.update(remote_id="UNTRUSTED-URL"),
])
def test_untrusted_claim_receipt_or_scope_never_reaches_provider(mutation):
    v,c,r,calls=verifier()
    mutation(c,r)
    with pytest.raises(RemoteReceiptDenied,match="SCOPE_DENIED"):
        v.inspect(job_id=JOB,claim_token=LEASE)
    assert calls==[]


def test_revoked_claim_before_or_after_get_is_not_published():
    v,c,_,calls=verifier()
    c.active=False
    with pytest.raises(RemoteReceiptDenied,match="SCOPE_DENIED"):
        v.inspect(job_id=JOB,claim_token=LEASE)
    assert calls==[]
    def revoke(req):
        c.active=False
        return (200,{"items":[{"id":YT_ID,"snippet":{"channelId":CHANNEL},
            "status":{"privacyStatus":"private"},
            "processingDetails":{"processingStatus":"succeeded"}}]}, {})
    v,c,_,calls=verifier(callback=revoke)
    with pytest.raises(RemoteReceiptDenied,match="CLAIM_REVOKED"):
        v.inspect(job_id=JOB,claim_token=LEASE)
    assert len(calls)==1


def test_provider_timeout_is_sanitized_not_an_unsent_grant():
    def timeout(_req):
        raise TimeoutError("Bearer private-secret; upload location secret")
    v,c,_,calls=verifier(callback=timeout)
    with pytest.raises(RemoteReceiptDenied,match="REMOTE_UNCERTAIN") as error:
        v.inspect(job_id=JOB,claim_token=LEASE)
    assert "private-secret" not in str(error.value)
    assert len(calls)==1


class Response:
    def __init__(self, url, body):
        self.url=url
        self.status=200
        self.data=body
        self.headers={}
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def geturl(self):return self.url
    def read(self,n):return self.data[:n]


def test_guarded_https_transport_allows_exact_readonly_google_status_only():
    got=[]
    def opener(req,timeout):
        got.append((req,timeout))
        return Response(req.full_url,b'{"items":[]}')
    transport=MediaNetworkTransport(enabled=True,opener=opener)
    v,c,r,calls=verifier()
    # Original record is server-held, not a caller-provided URL.
    auth_request=ProviderRequest(
        method="GET",
        url=("https://www.googleapis.com/youtube/v3/videos?"
             "part=snippet%2Cstatus%2CprocessingDetails&id="+YT_ID),
        headers={"Authorization":"Bearer secret"},body={})
    assert transport(auth_request)[0]==200
    assert got[0][0].get_method()=="GET" and got[0][0].data is None


@pytest.mark.parametrize("url",[
    "https://evil.example/youtube/v3/videos?part=snippet%2Cstatus%2CprocessingDetails&id="+YT_ID,
    "http://www.googleapis.com/youtube/v3/videos?part=snippet%2Cstatus%2CprocessingDetails&id="+YT_ID,
    "https://www.googleapis.com/youtube/v3/videos?part=snippet%2Cstatus%2CprocessingDetails&id="+YT_ID+"&key=leak",
    "https://www.googleapis.com/youtube/v3/videos?part=snippet,status,processingDetails&id="+YT_ID,
    "https://www.googleapis.com/youtube/v3/videos?part=snippet%2Cstatus%2CprocessingDetails&id="+YT_ID+"%0A",
    "https://www.googleapis.com/youtube/v3/videos?part=snippet%2Cstatus%2CprocessingDetails&id="+YT_ID+"/../bad",
])
def test_readonly_allowlist_rejects_host_query_or_path_injection(url):
    seen=[]
    transport=MediaNetworkTransport(enabled=True,opener=lambda req,timeout: seen.append(req))
    with pytest.raises(ProviderFailure,match="UNAPPROVED_MEDIA_ENDPOINT"):
        transport(ProviderRequest("GET",url,{"Authorization":"Bearer secret"},{}))
    assert seen==[]


def test_readonly_allowlist_rejects_post_and_body_without_socket():
    url="https://www.googleapis.com/youtube/v3/videos?part=snippet%2Cstatus%2CprocessingDetails&id="+YT_ID
    seen=[]
    transport=MediaNetworkTransport(enabled=True,opener=lambda req,timeout:seen.append(req))
    for req in [
        ProviderRequest("POST",url,{"Authorization":"Bearer secret"},{}),
        ProviderRequest("GET",url,{"Authorization":"Bearer secret"},{"evil":True}),
        ProviderRequest("GET",url,{"Authorization":"Bearer secret","X-Extra":"yes"},{}),
    ]:
        with pytest.raises(ProviderFailure,match="UNAPPROVED_MEDIA"):
            transport(req)
    assert seen==[]
