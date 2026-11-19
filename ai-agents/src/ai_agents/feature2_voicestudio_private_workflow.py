"""Tenant-scoped VoiceStudio -> private-review WAV bridge (server-only).

Uses the unmodified VoiceStudio /v1/audio/speech upstream service. All supplied
reader/claim/writer callbacks MUST be authoritative server implementations;
this module does not implement an Auth API, SQL transaction or cloud storage.
"""
from __future__ import annotations

from hashlib import sha256
import re
from uuid import UUID

from .feature2_voicestudio_adapter import VoiceStudioUnavailable, synthesize_voice_wav
from .feature2_voicestudio_feature4 import fit_voiceover_to_reel

_SHA = re.compile(r"^[0-9a-f]{64}$")


def _uuid4(value):
    try:
        return type(value) is str and str(UUID(value)) == value and UUID(value).version == 4
    except (ValueError, TypeError, AttributeError):
        return False


def _current_plan(read_plan, shop_id, campaign_id, voice, reel_seconds):
    plan = read_plan(shop_id, campaign_id)
    if not isinstance(plan, dict) or plan.get("shop_id") != shop_id or plan.get("campaign_id") != campaign_id:
        raise VoiceStudioUnavailable("Current verified retailer voice source unavailable")
    script = plan.get("voiceover_script")
    digest = plan.get("plan_sha256")
    if (
        plan.get("active_editor") is not True
        or plan.get("script_review") != "APPROVED_FOR_NARRATION"
        or plan.get("can_publish") is not False
        or plan.get("voice") != voice
        or type(plan.get("duration_seconds")) is not int
        or plan["duration_seconds"] != reel_seconds
        or not isinstance(digest, str)
        or not _SHA.fullmatch(digest)
        or not isinstance(script, str)
        or not script.strip()
        or len(script) > 3000
    ):
        raise VoiceStudioUnavailable("Trusted reviewed voice source changed or was revoked")
    return {"shop_id": shop_id, "campaign_id": campaign_id,
            "voiceover_script": script, "plan_sha256": digest,
            "voice": voice, "duration_seconds": reel_seconds,
            "active_editor": True, "script_review": "APPROVED_FOR_NARRATION",
            "can_publish": False}


def create_private_voiceover(
    *, shop_id, campaign_id, request_id, voice, reel_seconds,
    base_url, api_key, read_current_plan, claim_once,
    write_private_audio, read_private_receipt,
    enabled=False, commercial_model_verified=False, transport=None,
):
    """Synthesize at most ONCE, then store private original and F4-ready WAV.

    A trusted original-key SQL claim must reject duplicate/uncertain requests
    *before* external inference. Private storage must be staged atomically,
    no-clobber and with authoritative shop/asset SHA; callbacks are not provided
    by HTTP clients. Never automatically retry after provider/store ambiguity.
    """
    if (
        not all(_uuid4(x) for x in (shop_id, campaign_id, request_id))
        or type(reel_seconds) is not int
        or reel_seconds not in (15, 30, 60)
        or not all(callable(x) for x in (read_current_plan, claim_once,
                                         write_private_audio, read_private_receipt))
    ):
        raise VoiceStudioUnavailable("Trusted tenant, job and private storage required")
    if enabled is not True or commercial_model_verified is not True:
        raise VoiceStudioUnavailable("VoiceStudio is not enabled with a verified commercial model")
    before = _current_plan(read_current_plan, shop_id, campaign_id, voice, reel_seconds)
    claim = claim_once(shop_id, campaign_id, request_id, before["plan_sha256"])
    if (
        not isinstance(claim, dict)
        or claim.get("shop_id") != shop_id
        or claim.get("campaign_id") != campaign_id
        or claim.get("request_id") != request_id
        or claim.get("plan_sha256") != before["plan_sha256"]
        or claim.get("status") != "CLAIMED_ONCE"
        or claim.get("paid_inference_calls") != 0
        or type(claim.get("paid_inference_calls")) is not int
    ):
        raise VoiceStudioUnavailable("Original-key voice job claim is missing or uncertain")
    if _current_plan(read_current_plan, shop_id, campaign_id, voice, reel_seconds) != before:
        raise VoiceStudioUnavailable("Voice source changed after job claim")

    original = synthesize_voice_wav(
        text=before["voiceover_script"], base_url=base_url, api_key=api_key,
        voice=voice, enabled=True, commercial_model_verified=True,
        transport=transport,
    )
    render_ready, proof = fit_voiceover_to_reel(original, reel_seconds=reel_seconds)
    if _current_plan(read_current_plan, shop_id, campaign_id, voice, reel_seconds) != before:
        raise VoiceStudioUnavailable("Editor/source revoked during voice generation")

    original_sha = sha256(original).hexdigest()
    render_sha = sha256(render_ready).hexdigest()
    # A failed or ambiguous write is never silently retried.
    write_private_audio(
        shop_id, campaign_id, request_id,
        original, render_ready, original_sha, render_sha,
        claim,
    )
    receipt = read_private_receipt(shop_id, campaign_id, request_id)
    if (
        not isinstance(receipt, dict)
        or not _uuid4(receipt.get("audio_asset_id"))
        or receipt.get("shop_id") != shop_id
        or receipt.get("campaign_id") != campaign_id
        or receipt.get("request_id") != request_id
        or receipt.get("plan_sha256") != before["plan_sha256"]
        or receipt.get("original_sha256") != original_sha
        or receipt.get("render_sha256") != render_sha
        or receipt.get("private") is not True
        or receipt.get("review_status") != "NEEDS_REVIEW"
        or receipt.get("commercial_rights_confirmed") is not True
        or receipt.get("publish_approved") is not False
    ):
        raise VoiceStudioUnavailable("Original private voice asset receipt mismatch")
    if _current_plan(read_current_plan, shop_id, campaign_id, voice, reel_seconds) != before:
        raise VoiceStudioUnavailable("Editor/source revoked after private registration")

    return {
        "schema": "retailgrowth.feature2-voicestudio-private-review.v1",
        "shop_id": shop_id, "campaign_id": campaign_id,
        "request_id": request_id, "plan_sha256": before["plan_sha256"],
        "audio_asset_id": receipt["audio_asset_id"],
        "original_audio_sha256": original_sha,
        "feature4_audio_sha256": render_sha,
        "feature4_duration_seconds": reel_seconds,
        "review_status": "NEEDS_REVIEW",
        "f4_source_hint": "retailer",
        "private_audio_url": None,
        "awaits_human_audio_review": True,
        "feature4_must_recheck_current_rights": True,
        "approved_to_render_or_publish": False,
        "paid_inference_calls": 0,
    }
