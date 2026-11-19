"""Original-key VoiceStudio private WAV registration orchestration.

Connects the existing F2 one-shot speech client to the *actual* private WAV
storage writer and its readback, then an injected authoritative SQL CAS
registration. This is worker-only: never call from a browser or public route.
Does not implement tenant JWT/RLS, a schema migration, or rights approval.
"""
from __future__ import annotations

from .feature2_voicestudio_private_workflow import (
    VoiceStudioUnavailable, create_private_voiceover,
)

def run_verified_private_voice_job(
    *,
    shop_id: str,
    campaign_id: str,
    request_id: str,
    voice: str,
    reel_seconds: int,
    base_url: str,
    api_key: str,
    storage,
    read_current_plan,
    claim_once,
    register_verified_private_pair,
    read_private_receipt,
    enabled: bool = False,
    commercial_model_verified: bool = False,
    transport=None,
):
    """Produce only NEEDS_REVIEW private audio, never render/publish rights.

    Trusted SQL callbacks must enforce active JWT/RLS membership and role,
    one exact original request ID and never allocate a second paid job after
    uncertain provider or storage acknowledgements. The registration callback
    must commit job+two media asset receipts atomically, scoped to claim and
    SHA-verified object bytes; it must refuse role/source/rights revocations.
    """
    if (
        not all(callable(x) for x in (
            read_current_plan, claim_once, register_verified_private_pair,
            read_private_receipt,
        ))
        or storage is None
        or not all(callable(getattr(storage, n, None)) for n in (
            "paths", "write_private_audio", "verify_pair",
        ))
    ):
        raise VoiceStudioUnavailable("Trusted SQL and private WAV storage dependencies required")
    if enabled is not True or commercial_model_verified is not True:
        raise VoiceStudioUnavailable("VoiceStudio model and private job are not authorized")

    def write_verified(shop, campaign, request, original, render, original_sha, render_sha, claim):
        # The original producer already verified the current reviewed plan,
        # tenant and original-key claim before reaching this callback.
        original_path, render_path = storage.paths(shop, campaign, request)
        if (
            original_path != f"{shop}/voicestudio/{campaign}/{request}/original.wav"
            or render_path != f"{shop}/voicestudio/{campaign}/{request}/render.wav"
            or not isinstance(claim, dict)
            or claim.get("status") != "CLAIMED_ONCE"
            or claim.get("shop_id") != shop
            or claim.get("campaign_id") != campaign
            or claim.get("request_id") != request
            or type(claim.get("paid_inference_calls")) is not int
            or claim["paid_inference_calls"] != 0
        ):
            raise VoiceStudioUnavailable("Untrusted original private job or object path")
        written = storage.write_private_audio(
            shop, campaign, request, original, render, original_sha, render_sha, claim
        )
        if (
            not isinstance(written, dict)
            or written.get("status") != "PRIVATE_WAV_BYTES_WRITTEN_NOT_REGISTERED"
            or written.get("shop_id") != shop
            or written.get("campaign_id") != campaign
            or written.get("request_id") != request
            or written.get("original_object_key") != original_path
            or written.get("render_object_key") != render_path
            or written.get("original_sha256") != original_sha
            or written.get("render_sha256") != render_sha
            or written.get("publish_approved") is not False
        ):
            raise VoiceStudioUnavailable("Private WAV writer did not attest exact objects")
        # Read bytes back from private Supabase Storage before any SQL
        # registration. A lost ACK/tamper remains unresolved; never retry.
        verified = storage.verify_pair(shop, campaign, request, original_sha, render_sha)
        if (
            not isinstance(verified, dict)
            or verified.get("status") != "PRIVATE_WAV_READBACK_VERIFIED_NOT_REGISTERED"
            or verified.get("shop_id") != shop
            or verified.get("campaign_id") != campaign
            or verified.get("request_id") != request
            or verified.get("original_sha256") != original_sha
            or verified.get("render_sha256") != render_sha
            or verified.get("publish_approved") is not False
            or type(verified.get("original_bytes")) is not int
            or verified["original_bytes"] != len(original)
            or type(verified.get("render_bytes")) is not int
            or verified["render_bytes"] != len(render)
        ):
            raise VoiceStudioUnavailable("Exact private WAV readback missing")
        registration = register_verified_private_pair(
            shop, campaign, request,
            claim, {
                "original_object_key": original_path,
                "render_object_key": render_path,
                "original_sha256": original_sha,
                "render_sha256": render_sha,
                "original_bytes": verified["original_bytes"],
                "render_bytes": verified["render_bytes"],
                "requires_human_review": True,
                "publish_approved": False,
            },
        )
        if (
            not isinstance(registration, dict)
            or registration.get("status") != "REGISTERED_PRIVATE_NEEDS_REVIEW"
            or registration.get("shop_id") != shop
            or registration.get("campaign_id") != campaign
            or registration.get("request_id") != request
            or registration.get("original_sha256") != original_sha
            or registration.get("render_sha256") != render_sha
            or registration.get("publish_approved") is not False
        ):
            raise VoiceStudioUnavailable("Original-key SQL registration was not confirmed")
        # Caller will independently re-fetch the registered asset in
        # create_private_voiceover; never trust this writer's claim alone.

    return create_private_voiceover(
        shop_id=shop_id,
        campaign_id=campaign_id,
        request_id=request_id,
        voice=voice,
        reel_seconds=reel_seconds,
        base_url=base_url,
        api_key=api_key,
        read_current_plan=read_current_plan,
        claim_once=claim_once,
        write_private_audio=write_verified,
        read_private_receipt=read_private_receipt,
        enabled=True,
        commercial_model_verified=True,
        transport=transport,
    )
