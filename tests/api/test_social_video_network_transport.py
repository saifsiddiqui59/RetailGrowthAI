"""No-network negative/positive allowlisted Meta/Google video transport."""
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
import sys,pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_video_network_transport import network_video_transport
from social_dispatch import ProviderFailure
from social_media_uploads import BinaryUploadRequest
from social_providers import (
    ProviderRequest,instagram_container_status_request,
    instagram_reel_container_request,instagram_publish_request,
    youtube_resumable_init_request
)

GRAPH="v26.0"
TOKEN="test-private-server-token"
IG="123456789"
SRC=("https://retail.test.supabase.co/storage/v1/object/sign/retailgrowth-media/"
     "31000000-0000-4000-8000-000000000001/social-exports/"
     "62000000-0000-4000-8000-000000000001/2/"+"ab"*32+
     ".mp4?token=PRIVATE-SIGNED-MEDIA-TOKEN-123456")
SESSION="https://www.googleapis.com/upload/youtube/v3/videos?upload_id=private-upload-id"

class Response:
    def __init__(self,url,code,body=b"{}",headers=None):
        self.url=url;self.status=code;self.stream=BytesIO(body)
        self.headers=headers or {}
    def geturl(self):return self.url
    def read(self,n):return self.stream.read(n)
    def __enter__(self):return self
    def __exit__(self,*args):return False

def ig_create():
    return instagram_reel_container_request(
        ig_user_id=IG,token=TOKEN,caption="Reviewed",
        video_url=SRC,supabase_origin="https://retail.test.supabase.co",
        graph_version=GRAPH)

def test_legitimate_meta_container_status_and_publish_requests():
    calls=[]
    def open_req(req,timeout):
        assert timeout==30
        calls.append((req.get_method(),req.full_url))
        assert req.get_header("Authorization")=="Bearer "+TOKEN
        if req.full_url.endswith("/media"):
            assert req.get_method()=="POST"
            return Response(req.full_url,200,b'{"id":"987654321"}')
        if "fields=status_code" in req.full_url:
            assert req.get_method()=="GET"
            return Response(req.full_url,200,b'{"status_code":"FINISHED"}')
        assert req.full_url.endswith("/media_publish")
        return Response(req.full_url,200,b'{"id":"123456789"}')
    reqs=[ig_create(),
          instagram_container_status_request(
              container_id="987654321",token=TOKEN,graph_version=GRAPH),
          instagram_publish_request(ig_user_id=IG,container_id="987654321",
             container_status="FINISHED",token=TOKEN,graph_version=GRAPH)]
    results=[network_video_transport(r,opener=open_req) for r in reqs]
    assert [r[1] for r in results]==[
      {"id":"987654321"},{"status_code":"FINISHED"},{"id":"123456789"}]
    assert [x[0] for x in calls]==["POST","GET","POST"]


def test_youtube_private_session_and_byte_put_payload_are_bounded():
    calls=[]
    def opener(req,timeout):
        calls.append(req)
        if req.get_method()=="POST":
            assert req.get_header("Authorization")=="Bearer "+TOKEN
            return Response(req.full_url,200,b"{}",{"Location":SESSION})
        assert req.get_method()=="PUT"
        return Response(req.full_url,201,b'{"id":"Abc123_XyZ0"}')
    first=network_video_transport(youtube_resumable_init_request(
        token=TOKEN,title="Video",description="Authorized",size_bytes=5),
        opener=opener)
    assert first[2]["location"]==SESSION
    second=network_video_transport(BinaryUploadRequest(
        "PUT",SESSION,{"Authorization":"Bearer "+TOKEN,
                      "Content-Type":"video/mp4","Content-Length":"5"},
        b"video"),opener=opener)
    assert second[0]==201 and second[1]["id"]=="Abc123_XyZ0"
    assert len(calls)==2


def test_http_308_resumable_status_probe_is_not_retried_or_auto_uploaded():
    seen=[]
    def opener(req,timeout):
        seen.append(req)
        raise HTTPError(req.full_url,308,"Resume Incomplete",
              {"Range":"bytes=0-3"},BytesIO(b""))
    req=BinaryUploadRequest("PUT",SESSION,{
       "Authorization":"Bearer "+TOKEN,"Content-Length":"0",
       "Content-Range":"bytes */5"},b"")
    status,body,headers=network_video_transport(req,opener=opener)
    assert status==308 and body=={} and headers["range"]=="bytes=0-3"
    assert len(seen)==1 and seen[0].get_method()=="PUT"


@pytest.mark.parametrize("url,method",[
    ("https://attacker.invalid/steal","POST"),
    ("http://graph.facebook.com/v26.0/123/media","POST"),
    ("https://graph.facebook.com/v26.0/123/feed","POST"),
    ("https://graph.facebook.com/v26.0/123/media?evil=1","POST"),
    ("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=evil","POST"),
    ("https://www.googleapis.com.evil.invalid/upload/youtube/v3/videos?upload_id=1","POST"),
    ("https://graph.facebook.com:8443/v26.0/123/media","POST"),
    ("https://graph.facebook.com@evil.invalid/v26.0/123/media","POST"),
])
def test_provider_endpoints_must_be_exact_and_no_network(url,method):
    calls=[]
    with pytest.raises(ProviderFailure,match="ENDPOINT_DENIED"):
        network_video_transport(ProviderRequest(
            method,url,{"Authorization":"Bearer "+TOKEN},{}),
            opener=lambda *a,**k:calls.append(1))
    assert calls==[]


def test_malformed_binary_metadata_blocked_before_any_provider_side_effect():
    calls=[]
    for headers,data in [
      ({"Authorization":"Bearer "+TOKEN,"Content-Length":"4",
        "Content-Type":"video/mp4"},b"video"),
      ({"Authorization":"Bearer "+TOKEN,"Content-Length":"5",
        "Content-Type":"application/json"},b"video"),
      ({"Authorization":"Bearer "+TOKEN,"Content-Length":"0"},b""),
      ({"Authorization":"Bearer "+TOKEN,"Content-Length":"0",
        "Content-Range":"bytes */0"},b""),
    ]:
        with pytest.raises(ProviderFailure,match="BINARY_INVALID"):
            network_video_transport(BinaryUploadRequest("PUT",SESSION,headers,data),
                opener=lambda *a,**k:calls.append(1))
    assert calls==[]


def test_redirect_timeout_bad_json_and_4xx_never_leak_tokens_or_retry():
    req=ig_create()
    scenarios=[
      lambda r,t: Response("https://attacker.invalid/steal",200,b"{}"),
      lambda r,t: Response(r.full_url,200,b"[]" ),
      lambda r,t: Response(r.full_url,200,b"x"*65537),
      lambda r,t: (_ for _ in ()).throw(TimeoutError("secret "+TOKEN)),
      lambda r,t: (_ for _ in ()).throw(
          HTTPError(r.full_url,429,"token="+TOKEN,{},BytesIO(b"{}"))),
    ]
    for open_req in scenarios:
        calls=[]
        def counted(r,timeout):
            calls.append(1)
            return open_req(r,timeout)
        with pytest.raises(ProviderFailure) as err:
            network_video_transport(req,opener=counted)
        assert len(calls)==1
        assert TOKEN not in str(err.value)


def test_no_invalid_get_body_or_missing_bearer_sent():
    calls=[]
    good=instagram_container_status_request(
        container_id="123456789",token=TOKEN,graph_version=GRAPH)
    for req in [
      ProviderRequest("GET",good.url,good.headers,{"injected":1}),
      ProviderRequest("GET",good.url,{"Authorization":"none"},{}),
    ]:
        with pytest.raises(ProviderFailure):
            network_video_transport(req,opener=lambda *a,**k:calls.append(1))
    assert calls==[]
