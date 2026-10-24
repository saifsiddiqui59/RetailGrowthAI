"""Offline mocked transport for tenant-safe Part 1 generated MP4 reads."""
import hashlib
from io import BytesIO
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from social_private_render_reader import SocialPrivateRenderReader, SocialVideoDownloadDenied

SHOP = "31000000-0000-4000-8000-000000000001"
JOB = "91000000-0000-4000-8000-000000000001"
KEY = SHOP + "/renders/" + JOB + ".mp4"
LEASE = "91000000-0000-4000-8000-000000000002"
SECRET = "sb_secret_test-only"
ORIGIN = "https://retail.test.supabase.co"
DATA = b"private-render-bytes"


class Response:
    def __init__(self, url, payload=DATA, *, status=200, headers=None):
        self.url, self.stream, self.status = url, BytesIO(payload), status
        self.headers = headers or {}
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def geturl(self): return self.url
    def read(self, size): return self.stream.read(size)


def digest(data=DATA):
    return hashlib.sha256(data).hexdigest()


def test_authorized_private_render_streams_only_expected_bytes(tmp_path):
    requests = []
    def opener(request, timeout):
        requests.append(request)
        assert timeout == 45 and request.get_method() == "GET"
        return Response(request.full_url)
    reader = SocialPrivateRenderReader(ORIGIN, SECRET, transport=opener)
    result = reader.download(shop_id=SHOP, object_path=KEY,
             destination=tmp_path / "result.mp4", private_root=tmp_path,
             expected_sha256=digest())
    assert result["source_sha256"] == digest()
    assert result["size_bytes"] == len(DATA)
    assert result["path"].read_bytes() == DATA
    assert "/storage/v1/object/retailgrowth-media/" in requests[0].full_url
    assert requests[0].get_header("Apikey") == SECRET
    assert requests[0].get_header("Accept-encoding") == "identity"
    assert len(requests) == 1


@pytest.mark.parametrize("key", [
    "other-shop/renders/" + JOB + ".mp4",
    SHOP + "/uploads/" + JOB + ".mp4",
    SHOP + "/renders/../../private.mp4",
    SHOP + "/renders/" + JOB + ".mp4?token=bad",
    SHOP + "/renders/" + JOB + ".mp4/extra",
    SHOP + "/renders/not-a-uuid.mp4",
    SHOP + "/renders/" + JOB.upper() + ".mp4",
])
def test_non_authoritative_media_path_refused_before_credentialed_request(tmp_path, key):
    calls = []
    reader = SocialPrivateRenderReader(ORIGIN, SECRET, transport=lambda *a, **k: calls.append(1))
    with pytest.raises(SocialVideoDownloadDenied, match="VIDEO_PATH_INVALID"):
        reader.download(shop_id=SHOP, object_path=key,
            destination=tmp_path / "result.mp4", private_root=tmp_path,
            expected_sha256=digest())
    assert calls == []


def test_exact_lease_path_and_bound_sha_enforced(tmp_path):
    path = SHOP + "/renders/" + JOB + "/" + LEASE + ".mp4"
    reader = SocialPrivateRenderReader(ORIGIN, SECRET,
       transport=lambda req, timeout: Response(req.full_url))
    with pytest.raises(SocialVideoDownloadDenied, match="VIDEO_DIGEST_MISMATCH"):
        reader.download(shop_id=SHOP, object_path=path,
            destination=tmp_path / "result.mp4", private_root=tmp_path,
            expected_sha256="0" * 64)
    assert not (tmp_path / "result.mp4").exists()
    assert reader.download(shop_id=SHOP, object_path=path,
        destination=tmp_path / "result.mp4", private_root=tmp_path,
        expected_sha256=digest())["size_bytes"] == len(DATA)


def test_cross_scratch_root_symlink_and_existing_file_denied(tmp_path):
    home = tmp_path / "private"
    home.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    reader = SocialPrivateRenderReader(ORIGIN, SECRET,
        transport=lambda req, timeout: Response(req.full_url))
    with pytest.raises(SocialVideoDownloadDenied, match="VIDEO_SCRATCH_PATH_INVALID"):
        reader.download(shop_id=SHOP,object_path=KEY,destination=other/"result.mp4",
            private_root=home,expected_sha256=digest())
    target = home/"linked.mp4"
    target.symlink_to(other/"elsewhere.mp4")
    with pytest.raises(SocialVideoDownloadDenied, match="VIDEO_SCRATCH_PATH_INVALID"):
        reader.download(shop_id=SHOP,object_path=KEY,destination=target,
            private_root=home,expected_sha256=digest())
    target.unlink()
    target.write_bytes(b"existing")
    with pytest.raises(SocialVideoDownloadDenied, match="VIDEO_PRIVATE_FETCH_UNAVAILABLE"):
        reader.download(shop_id=SHOP,object_path=KEY,destination=target,
            private_root=home,expected_sha256=digest())
    assert target.read_bytes() == b"existing"


def test_redirect_or_unexpected_response_never_leaks_media(tmp_path):
    for status, url, headers in [
        (302, "https://attacker.invalid/private", {}),
        (200, "https://attacker.invalid/private", {}),
        (200, None, {"Content-Encoding": "gzip"}),
    ]:
        reader = SocialPrivateRenderReader(ORIGIN, SECRET,
            transport=lambda req, timeout: Response(
                url or req.full_url, status=status, headers=headers))
        with pytest.raises(SocialVideoDownloadDenied, match="VIDEO_PRIVATE_FETCH_REJECTED"):
            reader.download(shop_id=SHOP,object_path=KEY,
                destination=tmp_path/"result.mp4",private_root=tmp_path,
                expected_sha256=digest())
        assert not (tmp_path/"result.mp4").exists()


def test_origin_and_missing_digest_fail_closed_without_request(tmp_path):
    for origin in ["http://retail.test.supabase.co",
                   "https://attacker.invalid",
                   "https://retail.test.supabase.co:444",
                   "https://retail.test.supabase.co@attacker.invalid"]:
        with pytest.raises(SocialVideoDownloadDenied, match="VIDEO_ORIGIN_INVALID"):
            SocialPrivateRenderReader(origin, SECRET)
    reader = SocialPrivateRenderReader(ORIGIN, SECRET,
        transport=lambda *a, **k: pytest.fail("must not request media"))
    with pytest.raises(SocialVideoDownloadDenied, match="VIDEO_DIGEST_REQUIRED"):
        reader.download(shop_id=SHOP,object_path=KEY,
            destination=tmp_path/"result.mp4",private_root=tmp_path,
            expected_sha256="not-a-digest")
