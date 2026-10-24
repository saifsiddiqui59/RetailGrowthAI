"""Pure offline checks; no storage, provider, Azure, or network credentials."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from social_media_evidence import inspect_staged_mp4, MediaEvidenceRejected

PROFILE = {
    "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "30.000000"},
    "streams": [
        {"codec_type": "video", "codec_name": "h264", "pix_fmt": "yuv420p",
         "width": 1080, "height": 1920},
        {"codec_type": "audio", "codec_name": "aac"},
    ],
}


def _run(payload):
    def runner(args, **kwargs):
        assert args[0] == "ffprobe" and args[-1].endswith("clip.mp4")
        assert kwargs["timeout"] == 20 and kwargs["check"] is False
        assert kwargs["capture_output"] and kwargs["text"]
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload))
    return runner


def _fixture(tmp_path):
    root = tmp_path / "private"
    root.mkdir()
    clip = root / "clip.mp4"
    clip.write_bytes(b"synthetic-private-mp4-for-offline-contract-test")
    digest = hashlib.sha256(clip.read_bytes()).hexdigest()
    return root, clip, digest


def test_valid_h264_aac_profile_is_derived_from_actual_private_bytes(tmp_path):
    root, clip, digest = _fixture(tmp_path)
    result = inspect_staged_mp4(
        source_path=clip, private_root=root, expected_sha256=digest,
        runner=_run(PROFILE))
    assert result["source_sha256"] == digest
    assert result["ffprobe"] == {
        "container": "mov,mp4,m4a,3gp,3g2,mj2",
        "video_codec": "h264", "audio_codec": "aac",
        "pixel_format": "yuv420p", "width": 1080, "height": 1920,
        "duration_seconds": "30.000",
    }


@pytest.mark.parametrize("mutation", [
    lambda x: x["streams"].pop(),
    lambda x: x["streams"][1].update(codec_name="mp3"),
    lambda x: x["streams"][0].update(codec_name="hevc"),
    lambda x: x["streams"][0].update(pix_fmt="yuv422p"),
    lambda x: x["streams"][0].update(width=720),
    lambda x: x["format"].update(duration="45.000000"),
    lambda x: x["format"].update(format_name="matroska,webm"),
    lambda x: x["streams"].append({"codec_type": "subtitle"}),
])
def test_rejects_ineligible_ffprobe_profiles(tmp_path, mutation):
    root, clip, digest = _fixture(tmp_path)
    profile = json.loads(json.dumps(PROFILE))
    mutation(profile)
    with pytest.raises(MediaEvidenceRejected, match="MEDIA_PROBE_REJECTED"):
        inspect_staged_mp4(source_path=clip, private_root=root,
                           expected_sha256=digest, runner=_run(profile))


def test_tenant_scratch_boundary_rejects_external_and_symlink_paths(tmp_path):
    root, clip, digest = _fixture(tmp_path)
    outside = tmp_path / "elsewhere.mp4"
    outside.write_bytes(clip.read_bytes())
    with pytest.raises(MediaEvidenceRejected, match="UNTRUSTED_MEDIA_PATH"):
        inspect_staged_mp4(source_path=outside, private_root=root,
                           expected_sha256=digest, runner=_run(PROFILE))
    link = root / "linked.mp4"
    link.symlink_to(clip)
    with pytest.raises(MediaEvidenceRejected, match="UNTRUSTED_MEDIA_PATH"):
        inspect_staged_mp4(source_path=link, private_root=root,
                           expected_sha256=digest, runner=_run(PROFILE))


def test_mismatch_and_mutation_never_reach_or_pass_ffprobe(tmp_path):
    root, clip, digest = _fixture(tmp_path)
    calls = []
    with pytest.raises(MediaEvidenceRejected, match="MEDIA_DIGEST_MISMATCH"):
        inspect_staged_mp4(source_path=clip, private_root=root,
            expected_sha256="0" * 64, runner=lambda *args, **kwargs: calls.append(1))
    assert calls == []

    def change_during_probe(*args, **kwargs):
        clip.write_bytes(b"changed")
        return SimpleNamespace(returncode=0, stdout=json.dumps(PROFILE))

    with pytest.raises(MediaEvidenceRejected, match="MEDIA_CHANGED_DURING_PROBE"):
        inspect_staged_mp4(source_path=clip, private_root=root,
                           expected_sha256=digest, runner=change_during_probe)


def test_empty_invalid_digest_and_broken_probe_fail_closed(tmp_path):
    root, clip, digest = _fixture(tmp_path)
    for invalid in ("not-a-digest", "", digest.upper()):
        with pytest.raises(MediaEvidenceRejected, match="MEDIA_DIGEST_REQUIRED"):
            inspect_staged_mp4(source_path=clip, private_root=root,
                               expected_sha256=invalid, runner=_run(PROFILE))
    with pytest.raises(MediaEvidenceRejected, match="MEDIA_PROBE_REJECTED"):
        inspect_staged_mp4(source_path=clip, private_root=root,
            expected_sha256=digest, runner=lambda *a, **k: SimpleNamespace(
                returncode=0, stdout="not-json"))
    with pytest.raises(MediaEvidenceRejected, match="MEDIA_PROBE_REJECTED"):
        inspect_staged_mp4(source_path=clip, private_root=root,
            expected_sha256=digest, runner=lambda *a, **k: SimpleNamespace(
                returncode=0, stdout="x" * 65537))
