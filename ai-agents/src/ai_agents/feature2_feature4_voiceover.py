"""Trusted F2 review-only private WAV -> F4 editable soundtrack selector input.

No actual MP4 mixing or approval of transcript fidelity: F4 independently
checks signed tenant/lease/current media before using this immutable receipt.
"""
from __future__ import annotations

from uuid import UUID
from .feature2_audio_evidence import inspect_private_narration_wav, AudioEvidenceRejected

class Feature4VoiceoverDenied(ValueError):
    pass

def _uuid(value):
    try:
        return type(value) is str and str(UUID(value))==value and UUID(value).version==4
    except (TypeError,ValueError,AttributeError):
        return False

def prepare_feature4_voiceover(*,creative_bundle, original_wav,
                               signed_audio_record,audio_asset_id,
                               active_editor_reader):
    if not _uuid(audio_asset_id) or not callable(active_editor_reader):
        raise Feature4VoiceoverDenied("Trusted private editor required")
    if (not isinstance(signed_audio_record,dict) or
        signed_audio_record.get("audio_asset_id")!=audio_asset_id or
        signed_audio_record.get("approval_state")!="APPROVED_FOR_EDITING" or
        signed_audio_record.get("preview") is True or
        signed_audio_record.get("revoked_at") is not None):
        raise Feature4VoiceoverDenied("Private reviewed narration is not available")
    try:
        # The established F2 verifier checks all original audio SHA, retailer
        # shop/plan, commercial rights, duration, and membership twice.
        proof=inspect_private_narration_wav(
            bundle=creative_bundle, audio_original=original_wav,
            signed_audio_record={k:v for k,v in signed_audio_record.items()
                if k in ("shop_id","campaign_id","creative_plan_sha256",
                         "original_audio_sha256","private","commercial_use_allowed",
                         "revoked_at","mime","rights_reviewed")},
            active_owner_or_editor_check=active_editor_reader,
        )
    except AudioEvidenceRejected as exc:
        raise Feature4VoiceoverDenied("No current approved private original WAV") from exc
    return {"schema":"retailgrowth.feature2-f4-voiceover-source.v1",
            "shop_id":proof.shop_id,"campaign_id":proof.campaign_id,
            "creative_plan_sha256":proof.plan_sha256,"voiceover_asset_id":audio_asset_id,
            "original_audio_sha256":proof.audio_sha256,"mime_type":"audio/wav",
            "duration_seconds":proof.duration_seconds,
            "source_state":"PRIVATE_REVIEWED_SOURCE_REVALIDATE_IN_F4",
            "audio_bytes_passed_to_browser":False,
            "f4_must_check_rights_and_lease":True,
            "actual_word_alignment_verified":False,
            "actual_speech_match_verified":False,
            "publish_approved":False,
            "paid_motion_permitted":False}
