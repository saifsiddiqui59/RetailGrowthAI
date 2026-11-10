"""Synthetic-only tests: VoiceStudio private WAV writer, no Supabase connection."""
import io
from hashlib import sha256
from pathlib import Path
import sys
from uuid import uuid4
import wave

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
from feature2_voicestudio_storage import (  # noqa: E402
    PrivateVoiceStorageDenied, VoiceStudioPrivateStorage,
)

SHOP, CAMPAIGN, JOB = (str(uuid4()) for _ in range(3))
SECRET = "sb_secret_" + "unit-only-" * 5


def wav():
    out = io.BytesIO()
    with wave.open(out, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(b"\x01\x02" * 16000)
    return out.getvalue()


class Success:
    status = 201
    def __init__(self, url): self.url = url
    def geturl(self): return self.url
    def __enter__(self): return self
    def __exit__(self, *_): pass


def harness(*, transport=None):
    calls = []
    def sender(request, timeout):
        calls.append((request, timeout))
        return Success(request.full_url)
    return VoiceStudioPrivateStorage(
        "https://test-project.supabase.co", SECRET,
        transport=transport or sender), calls


def write(store, **changes):
    data = wav()
    options = dict(shop_id=SHOP, campaign_id=CAMPAIGN, request_id=JOB,
                   original=data, render_wav=data,
                   original_sha=sha256(data).hexdigest(),
                   render_sha=sha256(data).hexdigest(),
                   claim={"status":"CLAIMED_ONCE", "shop_id":SHOP,
                          "campaign_id":CAMPAIGN, "request_id":JOB})
    options.update(changes)
    return store.write_private_audio(**options)


def test_private_wav_objects_written_only_after_claim():
    store, calls = harness()
    report = write(store)
    assert report["status"] == "PRIVATE_WAV_BYTES_WRITTEN_NOT_REGISTERED"
    assert report["readback_and_sql_registration_required"] is True
    assert report["publish_approved"] is False
    assert len(calls) == 2
    for req, timeout in calls:
        assert req.get_method() == "POST"
        assert "/storage/v1/object/retailgrowth-media/" + SHOP in req.full_url
        assert req.get_header("X-upsert") == "false"
        assert req.get_header("Content-type") == "audio/wav"
        assert req.get_header("Apikey") == SECRET
        assert timeout == 30
    assert calls[0][0].full_url.endswith("/original.wav")
    assert calls[1][0].full_url.endswith("/render.wav")


@pytest.mark.parametrize("change", [
    {"shop_id": "not-uuid"},
    {"request_id": str(uuid4()), "claim": {"status":"CLAIMED_ONCE"}},
    {"claim": {"status":"CLAIMED_ONCE", "shop_id":str(uuid4()), "campaign_id":CAMPAIGN, "request_id":JOB}},
    {"claim": {"status":"REPLAY", "shop_id":SHOP, "campaign_id":CAMPAIGN, "request_id":JOB}},
    {"original_sha": "0"*64},
    {"render_sha": "f"*64},
    {"original": b"garbage"},
])
def test_no_network_on_bad_tenant_claim_or_media(change):
    store, calls = harness()
    with pytest.raises(PrivateVoiceStorageDenied):
        write(store, **change)
    assert calls == []


def test_second_object_upload_failure_is_not_retried():
    count = []
    from urllib.error import URLError
    def sender(req, timeout):
        count.append(req)
        if len(count) == 2:
            raise URLError("connection lost after possibly committing storage")
        return Success(req.full_url)
    store, _ = harness(transport=sender)
    with pytest.raises(PrivateVoiceStorageDenied, match="uncertain"):
        write(store)
    assert len(count) == 2


def test_redirected_or_wrong_status_upload_denied():
    for status, url in [(302, "https://other.example/"), (200, "https://other.example/"), (500, "")]:
        def sender(req, timeout):
            class Reply(Success):
                pass
            result = Reply(url or req.full_url)
            result.status = status
            return result
        store, _ = harness(transport=sender)
        with pytest.raises(PrivateVoiceStorageDenied):
            write(store)


@pytest.mark.parametrize("origin", ["http://example.com", "https://", "https://x/y", "https://x@evil.com", "https://x?token=secret"])
def test_invalid_origin_denied(origin):
    with pytest.raises(PrivateVoiceStorageDenied):
        VoiceStudioPrivateStorage(origin, SECRET)


def test_invalid_service_role_credential_denied():
    with pytest.raises(ValueError):
        VoiceStudioPrivateStorage("https://test-project.supabase.co", "not-a-key")


def test_readback_verifies_original_and_render_from_private_bucket():
    payload = wav()
    events = []
    class ReadResult(io.BytesIO):
        status = 200
        def __init__(self, url):
            super().__init__(payload)
            self.url = url
        def geturl(self): return self.url
    def sender(req, timeout):
        events.append(req.get_method())
        if req.get_method() == "POST":
            return Success(req.full_url)
        return ReadResult(req.full_url)
    store, _ = harness(transport=sender)
    write(store)
    sha = sha256(payload).hexdigest()
    result = store.verify_pair(SHOP, CAMPAIGN, JOB, sha, sha)
    assert result["status"] == "PRIVATE_WAV_READBACK_VERIFIED_NOT_REGISTERED"
    assert result["original_bytes"] == len(payload)
    assert result["render_bytes"] == len(payload)
    assert result["publish_approved"] is False
    assert events == ["POST", "POST", "GET", "GET"]


def test_private_wav_readback_denies_tamper_without_retry():
    payload = wav()
    calls = []
    class ReadResult(io.BytesIO):
        status = 200
        def __init__(self, url):
            super().__init__(payload[:-5] + b"abcde")
            self.url = url
        def geturl(self): return self.url
    def sender(req, timeout):
        calls.append(req)
        return ReadResult(req.full_url)
    store, _ = harness(transport=sender)
    sha = sha256(payload).hexdigest()
    with pytest.raises(PrivateVoiceStorageDenied):
        store.verify_pair(SHOP, CAMPAIGN, JOB, sha, sha)
    assert len(calls) == 1
