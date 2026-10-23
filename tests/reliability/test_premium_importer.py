"""No external downloads: bounded premium media-import tests with injected fixtures."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from premium_importer import import_premium_video, PremiumImportRejected, _validated_provider_url, _check_video

SID = "223e4567-e89b-42d3-a456-426614174000"
JID = "123e4567-e89b-42d3-a456-426614174000"
LEASE = "323e4567-e89b-42d3-a456-426614174000"
HOST = "approved-video.example.net"
RESULT = "https://" + HOST + "/results/clip.mp4?token=short-lived-private-token"
MP4 = b"\x00\x00\x00\x18ftypisom" + b"synthetic-mocked-bytes" * 30


class Private:
    def __init__(self):
        self.uploads = []
    def upload(self, shop, job, path, *, lease_token):
        self.uploads.append((shop, job, lease_token, Path(path).read_bytes()))
        return shop + "/renders/" + job + "/" + lease_token + ".mp4"


def fake_probe(path):
    assert Path(path).exists()
    return {"streams": [{"codec_type": "video", "codec_name": "h264",
                         "width": 720, "height": 1280}],
            "format": {"duration": "5.000"}}


def test_success_imports_to_tenant_private_path_never_issues_provider_link():
    media = Private()
    response = import_premium_video(
        shop_id=SID, job_id=JID, lease_token=LEASE,
        source_url=RESULT, allowed_hosts=(HOST,), private_media=media,
        fetch=lambda url: MP4, probe=fake_probe)
    assert response["object_path"].startswith(SID + "/renders/" + JID)
    assert response["media"] == {"duration_seconds": 5, "width": 720, "height": 1280, "codec": "h264"}
    assert "token=" not in str(response) and "https://" not in str(response)
    assert media.uploads == [(SID, JID, LEASE, MP4)]


@pytest.mark.parametrize("url", [
    "http://" + HOST + "/video.mp4",
    "https://attacker.example/private/video.mp4",
    "https://" + HOST + ".evil.test/out.mp4",
    "https://user:secret@" + HOST + "/out.mp4",
    "https://" + HOST + ":444/out.mp4",
    "https://" + HOST + "/../out.mp4",
    "https://" + HOST + "/foo%2Fbar.mp4",
    "https://" + HOST + "/video.mp4#fragment",
    "https://localhost/metadata",
])
def test_source_urls_rejected_before_network_or_upload(url):
    calls, media = [], Private()
    with pytest.raises(PremiumImportRejected):
        import_premium_video(
            shop_id=SID, job_id=JID, lease_token=LEASE,
            source_url=url, allowed_hosts=(HOST,), private_media=media,
            fetch=lambda u: calls.append(u) or MP4, probe=fake_probe)
    assert not calls and not media.uploads


def test_default_output_host_is_never_implicitly_trusted():
    with pytest.raises(PremiumImportRejected):
        _validated_provider_url(RESULT, ())


def test_refuses_truncated_or_unrecognized_mp4():
    media = Private()
    for data in (b"", b"not MP4" * 100, MP4[:30]):
        with pytest.raises(PremiumImportRejected):
            import_premium_video(
                shop_id=SID, job_id=JID, lease_token=LEASE,
                source_url=RESULT, allowed_hosts=(HOST,), private_media=media,
                fetch=lambda url, d=data: d, probe=fake_probe)
    assert not media.uploads


def test_rejects_invalid_codec_or_duration_before_upload():
    media = Private()
    for fake in [
        {"streams": [{"codec_type":"video","codec_name":"vp9","width":720,"height":1280}],
         "format":{"duration":"5"}},
        {"streams": [{"codec_type":"video","codec_name":"h264","width":720,"height":1280}],
         "format":{"duration":"95"}},
        {"streams": [{"codec_type":"video","codec_name":"h264","width":720,"height":1280}],
         "format":{"duration":"5"}},
    ]:
        if fake["format"]["duration"] == "5" and fake["streams"][0]["codec_name"] == "h264":
            fake["streams"].append({"codec_type":"subtitle"})
        with pytest.raises(PremiumImportRejected):
            import_premium_video(shop_id=SID, job_id=JID, lease_token=LEASE,
                                 source_url=RESULT, allowed_hosts=(HOST,), private_media=media,
                                 fetch=lambda url: MP4, probe=lambda path, f=fake: f)
    assert media.uploads == []


def test_upload_failure_does_not_release_external_url():
    class Broken(Private):
        def upload(self, *args, **kwargs):
            raise RuntimeError("PRIVATE KEY DO NOT PRINT")
    with pytest.raises(PremiumImportRejected) as info:
        import_premium_video(shop_id=SID, job_id=JID, lease_token=LEASE,
                             source_url=RESULT, allowed_hosts=(HOST,), private_media=Broken(),
                             fetch=lambda _: MP4, probe=fake_probe)
    assert "PRIVATE KEY" not in str(info.value)
    assert "token=" not in str(info.value)
