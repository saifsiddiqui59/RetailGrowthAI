"""Offline negative tests: no provider connection or real media upload."""
import sys
from pathlib import Path
from urllib.error import HTTPError

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from social_dispatch import ProviderFailure
from social_media_transport import MediaNetworkTransport
from social_media_uploads import BinaryUploadRequest
from social_providers import (facebook_page_request, instagram_reel_container_request,
    instagram_container_status_request, youtube_resumable_init_request,
    youtube_upload_location, ProviderRejected, ProviderRequest)


SESSION = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&upload_id=opaque"
MEDIA = "https://demo.supabase.co/storage/v1/object/sign/retailgrowth-media/31000000-0000-4000-8000-000000000001/social-exports/62000000-0000-4000-8000-000000000001/1/abababababababababababababababababababababababababababababababab.mp4?token=signed-secret-long-token-123456"


class Response:
    def __init__(self, target, status, body, headers=None):
        self.target, self.status, self.body, self.headers = target, status, body, headers or {}
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def geturl(self): return self.target
    def read(self, size): return self.body[:size]


def instagram_req():
    return instagram_reel_container_request(ig_user_id="123", token="SENSITIVE-TOKEN",
        video_url=MEDIA, caption="Reviewed text",
        supabase_origin="https://demo.supabase.co", graph_version="v26.0")


def test_disabled_transport_never_opens_a_socket():
    calls = []
    transport = MediaNetworkTransport(opener=lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ProviderFailure, match="MEDIA_TRANSPORT_DISABLED") as exc:
        transport(instagram_req())
    assert exc.value.definitely_not_sent is True and calls == []


def test_ig_form_encoded_and_status_get_with_bounded_body():
    seen = []
    def opener(req, timeout):
        seen.append((req.get_method(), req.data, req.full_url, timeout))
        return Response(req.full_url, 200, b'{"id":"987654321"}')
    transport = MediaNetworkTransport(enabled=True, opener=opener)
    assert transport(instagram_req())[1]["id"] == "987654321"
    assert b"media_type=REELS" in seen[0][1] and b"caption=Reviewed+text" in seen[0][1]
    assert b"token%3Dsigned-secret" in seen[0][1]
    assert b"share_to_feed=true" in seen[0][1]
    status = instagram_container_status_request(container_id="987654321",
        token="SENSITIVE-TOKEN", graph_version="v26.0")
    assert transport(status)[0] == 200
    assert seen[1][0] == "GET" and seen[1][1] is None


def test_youtube_private_init_and_308_status_range_without_reupload():
    seen = []
    def opener(req, timeout):
        seen.append(req)
        if req.get_method() == "POST":
            return Response(req.full_url, 200, b'{}', {"Location": SESSION})
        raise HTTPError(req.full_url, 308, "Resume Incomplete", {"Range":"bytes=0-9"}, None)
    transport = MediaNetworkTransport(enabled=True, opener=opener)
    init = youtube_resumable_init_request(token="SENSITIVE-TOKEN",
        title="A boutique sample", description="Private video", size_bytes=10)
    assert transport(init)[2]["location"] == SESSION
    probe = BinaryUploadRequest(method="PUT", url=SESSION,
        headers={"Authorization":"Bearer SENSITIVE-TOKEN",
                 "Content-Length":"0", "Content-Range":"bytes */10"}, data=b"")
    code, body, headers = transport(probe)
    assert code == 308 and body == {} and headers == {"range":"bytes=0-9"}
    assert seen[1].data == b"" and seen[1].get_method() == "PUT"


@pytest.mark.parametrize("url", [
    "https://www.googleapis.com:444/upload/youtube/v3/videos?upload_id=xyz",
    "https://www.googleapis.com/upload/../sensitive?upload_id=xyz",
    "https://www.googleapis.com/upload/youtube/v3/videos#secret",
    "https://www.googleapis.com/upload/youtube/v3/videos",
    "https://youtube.googleapis.com.attacker.invalid/upload/youtube/v3/videos?upload_id=x",
    "https://www.googleapis.com@attacker.invalid/upload/youtube/v3/videos?upload_id=x",
    "https://www.googleapis.com/upload/youtube/v3/videos?upload_id=x\r\nAuthorization:bad",
])
def test_youtube_session_origin_and_path_are_never_relaxed(url):
    with pytest.raises(ProviderRejected):
        youtube_upload_location(url)


def test_invalid_endpoint_port_redirect_and_oversized_response_fail_closed():
    calls = []
    transport = MediaNetworkTransport(enabled=True, opener=lambda req, timeout:
        calls.append(req) or Response("https://evil.invalid/redirect",200,b'{}'))
    for url in ["https://graph.facebook.com:777/v26.0/123/media",
                "https://attacker.invalid/v26.0/123/media"]:
        request = ProviderRequest("POST", url, {"Authorization":"Bearer SENSITIVE-TOKEN"},
                                  {"caption":"abc"})
        with pytest.raises(ProviderFailure, match="UNAPPROVED_MEDIA_ENDPOINT"):
            transport(request)
    assert not calls
    with pytest.raises(ProviderFailure,match="MEDIA_PROVIDER_RESULT_UNCERTAIN") as exc:
        transport(instagram_req())
    assert "SENSITIVE-TOKEN" not in str(exc.value)
    assert "signed-secret" not in str(exc.value)
    assert len(calls) == 1

    huge = MediaNetworkTransport(enabled=True,
        opener=lambda req, timeout: Response(req.full_url, 200, b"x" * 32769))
    with pytest.raises(ProviderFailure,match="MEDIA_PROVIDER_RESULT_UNCERTAIN"):
        huge(instagram_req())


def test_binary_payload_length_and_range_are_checked_before_network():
    calls = []
    transport=MediaNetworkTransport(enabled=True, opener=lambda req,timeout:
                                    calls.append(req))
    for body,headers in [
        (b"abc",{"Authorization":"Bearer token","Content-Length":"4","Content-Type":"video/mp4"}),
        (b"abc",{"Authorization":"Bearer token","Content-Length":"3","Content-Range":"bytes */3"}),
        (b"",{"Authorization":"Bearer token","Content-Length":"0","Content-Type":"video/mp4"}),
    ]:
        with pytest.raises(ProviderFailure,match="UNAPPROVED_MEDIA_REQUEST") as exc:
            transport(BinaryUploadRequest("PUT",SESSION,headers,body))
        assert exc.value.definitely_not_sent
    assert calls == []


def test_guarded_youtube_partial_binary_put_keeps_exact_content_range():
    """The current approved worker may send only final contiguous bytes."""
    seen=[]
    def opener(req,timeout):
        seen.append(req)
        assert req.get_method()=="PUT" and req.data==b"second"
        assert timeout==30
        assert req.full_url==SESSION
        assert req.get_header("Content-range")=="bytes 5-10/11"
        assert req.get_header("Content-length")=="6"
        assert req.get_header("Content-type")=="video/mp4"
        return Response(req.full_url,201,b'{"id":"Abc123_XyZ0"}')
    transport=MediaNetworkTransport(enabled=True,opener=opener)
    request=BinaryUploadRequest(method="PUT",url=SESSION,
        headers={"Authorization":"Bearer SENSITIVE-TOKEN",
                 "Content-Length":"6","Content-Type":"video/mp4",
                 "Content-Range":"bytes 5-10/11"},data=b"second")
    code,body,headers=transport(request)
    assert code==201 and body["id"]=="Abc123_XyZ0"
    assert len(seen)==1 and headers["range"] is None


@pytest.mark.parametrize("data,headers",[
    (b"second",{"Content-Length":"6","Content-Type":"video/mp4",
                "Content-Range":"bytes 5-10/12"}), # end not last
    (b"second",{"Content-Length":"6","Content-Type":"video/mp4",
                "Content-Range":"bytes 6-10/11"}), # body too long
    (b"second",{"Content-Length":"6","Content-Type":"video/mp4",
                "Content-Range":"bytes 10-5/11"}), # decreasing range
    (b"second",{"Content-Length":"6","Content-Type":"video/mp4",
                "Content-Range":"bytes 05-10/11"}), # noncanonical
    (b"second",{"Content-Length":"6","Content-Type":"video/mp4",
                "Content-Range":"bytes 5-10/83886081"}), # >80 MB
    (b"second",{"Content-Length":"6","Content-Type":"text/plain",
                "Content-Range":"bytes 5-10/11"}), # unsafe codec
    (b"second",{"Content-Length":"6",
                "Content-Range":"bytes 5-10/11"}), # missing media type
    (b"second",{"Content-Length":"6","Content-Type":"video/mp4",
                "Content-Range":"bytes */11"}), # probe not a payload
    (b"second",{"Content-Length":"7","Content-Type":"video/mp4",
                "Content-Range":"bytes 5-10/11"}), # declared size wrong
    (b"",{"Content-Length":"0","Content-Type":"video/mp4",
          "Content-Range":"bytes 5-10/11"}), # empty partial
])
def test_partial_resumption_bad_range_never_reaches_provider(data,headers):
    calls=[]
    transport=MediaNetworkTransport(enabled=True,opener=lambda req,timeout:
                                    calls.append(req))
    with pytest.raises(ProviderFailure,match="UNAPPROVED_MEDIA_REQUEST") as error:
        transport(BinaryUploadRequest("PUT",SESSION,
            {"Authorization":"Bearer SENSITIVE-TOKEN",**headers},data))
    assert error.value.definitely_not_sent is True
    assert calls==[]
