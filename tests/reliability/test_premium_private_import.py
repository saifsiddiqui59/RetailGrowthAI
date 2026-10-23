"""Part 3 private media delivery tests; no provider network or real cloud writes."""
from io import BytesIO
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "azure-functions" / "campaign-api"))
from premium_private_import import (
    NoRedirect, PremiumImportError, validate_vendor_video_url,
    fetch_signed_video, verify_video, import_to_private_storage, MAX_BYTES,
)

SID = "123e4567-e89b-42d3-a456-426614174001"
JID = "123e4567-e89b-42d3-a456-426614174002"
LEASE = "123e4567-e89b-42d3-a456-426614174003"
ASSET = "123e4567-e89b-42d3-a456-426614174004"
URL = "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/some/clip.mp4?Expires=9999999999"
MP4 = bytes.fromhex("00000018667479706d703432") + (b"0" * 2100)

class Response:
    def __init__(self, data=MP4, *, content_type="video/mp4", status=200, length=None):
        self.stream = BytesIO(data)
        self.headers = {"Content-Type": content_type,
                        "Content-Length": str(len(data) if length is None else length)}
        self.status = status
    def read(self, n=-1): return self.stream.read(n)
    def __enter__(self): return self
    def __exit__(self, *args): pass

class Transport:
    def __init__(self, response=None):
        self.calls = []
        self.response = response or Response()
    def open(self, req, timeout):
        self.calls.append((req.full_url, timeout))
        return self.response

class Media:
    def __init__(self): self.calls = []
    def upload(self, shop, job, file, *, lease_token):
        self.calls.append((shop, job, lease_token, Path(file).stat().st_size))
        return f"{shop}/renders/{job}/{lease_token}.mp4"

class Store:
    def __init__(self, success=True): self.calls = []; self.success = success
    def finalize(self, job, shop, token, path):
        self.calls.append((job, shop, token, path))
        return {"status":"SUCCEEDED","output_asset_id":ASSET} if self.success else {"status":"FAILED"}

def probe(_):
    return {"format":{"duration":"5.02"},
            "streams":[{"codec_type":"video","codec_name":"h264",
                        "width":720,"height":1280}]}

def test_approved_signed_vendor_origin_is_not_client_storage_url():
    assert validate_vendor_video_url(URL) == URL
    assert NoRedirect().redirect_request(None, None, 302, "", {}, "http://169.254.169.254") is None

@pytest.mark.parametrize("bad", [
    "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/video.mp4?Expires=99",
    "https://169.254.169.254/meta.mp4?Expires=99",
    "https://127.0.0.1/video.mp4?Expires=99",
    "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com.evil.invalid/x.mp4?Expires=99",
    "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com:8443/x.mp4?Expires=99",
    "https://evil@dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/x.mp4?Expires=99",
    "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/x.mp4",
    "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/../x.mp4?Expires=99",
    "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/x.html?Expires=99",
    "https://jeearzffnjbvghwjjjrf.supabase.co/storage/v1/object/public/b/x.mp4?Expires=99",
])
def test_output_origin_rejects_redirects_and_ssrf(bad):
    with pytest.raises(PremiumImportError):
        validate_vendor_video_url(bad)

def test_private_clip_is_downloaded_in_bounded_chunks(tmp_path):
    target = tmp_path / "media.mp4"
    transport = Transport()
    assert fetch_signed_video(URL, target, opener=transport) == len(MP4)
    assert target.read_bytes() == MP4
    assert len(transport.calls) == 1

def test_failed_size_or_content_type_never_creates_media(tmp_path):
    cases = [Response(content_type="text/html"), Response(length=MAX_BYTES+1),
             Response(data=b"hi"), Response(data=b"X"*2100)]
    for response in cases:
        with pytest.raises(PremiumImportError):
            fetch_signed_video(URL, tmp_path / "media.mp4",
                               opener=Transport(response))

def test_codec_duration_and_dimensions_must_match_reserved_job():
    verify_video(probe(None), expected_seconds=5)
    invalid = [
        ({"format":{"duration":5},"streams":[{"codec_type":"video","codec_name":"hevc",
          "width":720,"height":1280}]},5),
        (probe(None),10),
        ({"format":{"duration":5},"streams":[{"codec_type":"video","codec_name":"h264",
          "width":1919,"height":1080}]},5),
    ]
    for metadata, seconds in invalid:
        with pytest.raises(PremiumImportError):
            verify_video(metadata, expected_seconds=seconds)

def test_private_output_and_db_fenced_completion_are_required():
    transport, media, store = Transport(), Media(), Store()
    result = import_to_private_storage(
        provider_url=URL, shop_id=SID, job_id=JID, lease_token=LEASE,
        expected_seconds=5, media=media, store=store, opener=transport,
        probe=probe
    )
    assert result == {"job_id":JID, "status":"SUCCEEDED","output_asset_id":ASSET}
    assert media.calls[0][:3] == (SID, JID, LEASE)
    assert store.calls[0][3] == f"{SID}/renders/{JID}/{LEASE}.mp4"
    assert "url" not in result

def test_failed_db_finalization_is_not_misrepresented_as_video_ready():
    media, store = Media(), Store(success=False)
    with pytest.raises(PremiumImportError):
        import_to_private_storage(
            provider_url=URL, shop_id=SID, job_id=JID, lease_token=LEASE,
            expected_seconds=5, media=media, store=store,
            opener=Transport(), probe=probe)
    assert len(media.calls)==1 and len(store.calls)==1
