"""Offline tenant/failure tests for private VoiceStudio job -> F4 audio handoff."""
from hashlib import sha256
import io
from uuid import uuid4
import wave

import pytest

from ai_agents.feature2_voicestudio_adapter import VoiceStudioUnavailable
from ai_agents.feature2_voicestudio_private_workflow import create_private_voiceover


SHOP, CAMPAIGN, JOB, ASSET = (str(uuid4()) for _ in range(4))
PLAN_SHA = sha256(b"reviewed source plan").hexdigest()


def make_wav():
    out = io.BytesIO()
    with wave.open(out, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(b"\x01\x02" * 16000)
    return out.getvalue()


class Response(io.BytesIO):
    status = 200
    headers = {"Content-Type": "audio/wav"}

    def geturl(self):
        return "http://127.0.0.1:3900/v1/audio/speech"


class PrivateHarness:
    def __init__(self):
        self.plan = {
            "shop_id": SHOP, "campaign_id": CAMPAIGN,
            "voiceover_script": "Original approved sample for a fictional boutique.",
            "plan_sha256": PLAN_SHA,
            "voice": "alloy", "duration_seconds": 30,
            "active_editor": True,
            "script_review": "APPROVED_FOR_NARRATION",
            "can_publish": False,
        }
        self.claimed = False
        self.provider_calls = 0
        self.write_calls = 0
        self.record = None

    def current(self, shop, campaign):
        return dict(self.plan)

    def claim(self, shop, campaign, job, plan_sha):
        if self.claimed:
            return None
        self.claimed = True
        return {"shop_id": shop, "campaign_id": campaign,
                "request_id": job, "plan_sha256": plan_sha,
                "status": "CLAIMED_ONCE", "paid_inference_calls": 0}

    def transport(self, request, timeout):
        self.provider_calls += 1
        assert request.full_url.endswith("/v1/audio/speech")
        assert timeout == 45
        return Response(make_wav())

    def write(self, shop, campaign, job, original, render_ready, original_sha, render_sha, claim):
        self.write_calls += 1
        assert original_sha == sha256(original).hexdigest()
        assert render_sha == sha256(render_ready).hexdigest()
        assert claim["request_id"] == job
        with wave.open(io.BytesIO(render_ready), "rb") as wav:
            assert wav.getnframes() / wav.getframerate() == 30
        self.record = {
            "audio_asset_id": ASSET, "shop_id": shop, "campaign_id": campaign,
            "request_id": job, "plan_sha256": PLAN_SHA,
            "original_sha256": original_sha, "render_sha256": render_sha,
            "private": True, "review_status": "NEEDS_REVIEW",
            "commercial_rights_confirmed": True, "publish_approved": False,
        }

    def read(self, shop, campaign, job):
        return dict(self.record or {})

    def execute(self, **kw):
        args = dict(
            shop_id=SHOP, campaign_id=CAMPAIGN, request_id=JOB,
            voice="alloy", reel_seconds=30, base_url="http://127.0.0.1:3900",
            api_key="private-test-key-12345678", enabled=True,
            commercial_model_verified=True,
            read_current_plan=self.current, claim_once=self.claim,
            write_private_audio=self.write, read_private_receipt=self.read,
            transport=self.transport,
        )
        args.update(kw)
        return create_private_voiceover(**args)


def test_upstream_wav_is_stored_privately_and_handed_to_f4_without_publishing():
    h = PrivateHarness()
    result = h.execute()
    assert result["audio_asset_id"] == ASSET
    assert result["review_status"] == "NEEDS_REVIEW"
    assert result["approved_to_render_or_publish"] is False
    assert result["private_audio_url"] is None
    assert result["feature4_duration_seconds"] == 30
    assert result["f4_source_hint"] == "retailer"
    assert h.provider_calls == h.write_calls == 1
    with pytest.raises(VoiceStudioUnavailable):
        h.execute()  # one original request ID must not generate again
    assert h.provider_calls == 1


@pytest.mark.parametrize("edited", [
    {"active_editor": False},
    {"shop_id": str(uuid4())},
    {"campaign_id": str(uuid4())},
    {"voice": "another"},
    {"duration_seconds": 60},
    {"script_review": "DRAFT"},
    {"can_publish": True},
    {"plan_sha256": "not-a-digest"},
    {"voiceover_script": ""},
])
def test_unapproved_or_foreign_source_never_claims_or_calls_provider(edited):
    h = PrivateHarness()
    h.plan.update(edited)
    with pytest.raises(VoiceStudioUnavailable):
        h.execute()
    assert not h.claimed and h.provider_calls == h.write_calls == 0


def test_stale_source_after_claim_denies_before_provider():
    h = PrivateHarness()
    original_claim = h.claim
    def claim_then_revoke(*args):
        result = original_claim(*args)
        h.plan["active_editor"] = False
        return result
    with pytest.raises(VoiceStudioUnavailable):
        h.execute(claim_once=claim_then_revoke)
    assert h.provider_calls == h.write_calls == 0


def test_revocation_during_provider_prevents_private_write():
    h = PrivateHarness()
    def generate_then_revoke(req, timeout):
        result = h.transport(req, timeout)
        h.plan["active_editor"] = False
        return result
    with pytest.raises(VoiceStudioUnavailable):
        h.execute(transport=generate_then_revoke)
    assert h.provider_calls == 1 and h.write_calls == 0


def test_original_receipt_has_to_match_private_storage_evidence():
    h = PrivateHarness()
    def forged_receipt(shop, campaign, job):
        result = h.read(shop, campaign, job)
        result["shop_id"] = str(uuid4())
        return result
    with pytest.raises(VoiceStudioUnavailable, match="receipt"):
        h.execute(read_private_receipt=forged_receipt)
    assert h.provider_calls == h.write_calls == 1


def test_writer_ambiguity_is_not_retried_and_no_success_is_claimed():
    h = PrivateHarness()
    def failed_write(*args):
        h.write_calls += 1
        raise TimeoutError("uncertain remote ACK")
    with pytest.raises(TimeoutError):
        h.execute(write_private_audio=failed_write)
    assert h.provider_calls == h.write_calls == 1
    with pytest.raises(VoiceStudioUnavailable):
        h.execute(write_private_audio=failed_write)
    assert h.provider_calls == h.write_calls == 1


@pytest.mark.parametrize("bad_claim", [
    None, {}, {"status": "CLAIMED_ONCE", "paid_inference_calls": True},
    {"status": "PAID_FALLBACK", "paid_inference_calls": 1},
])
def test_no_provider_if_job_claim_missing_or_untrusted(bad_claim):
    h = PrivateHarness()
    with pytest.raises(VoiceStudioUnavailable):
        h.execute(claim_once=lambda *args: bad_claim)
    assert h.provider_calls == h.write_calls == 0


def test_post_write_editor_revocation_denies_success_without_deleting_unknown_bytes():
    h = PrivateHarness()
    def write_and_revoke(*args):
        h.write(*args)
        h.plan["active_editor"] = False
    with pytest.raises(VoiceStudioUnavailable, match="revoked"):
        h.execute(write_private_audio=write_and_revoke)
    assert h.provider_calls == h.write_calls == 1


def test_no_upstream_call_without_explicit_server_side_activation():
    h = PrivateHarness()
    for arg in ({"enabled": False}, {"commercial_model_verified": False}):
        with pytest.raises(VoiceStudioUnavailable):
            h.execute(**arg)
    assert h.provider_calls == h.write_calls == 0
