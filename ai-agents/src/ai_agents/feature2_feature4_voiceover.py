"""Trusted F2 review-only private WAV -> F4 editable soundtrack selector input.

No actual MP4 mixing or approval of transcript fidelity: F4 independently
checks signed tenant/lease/current media before using this immutable receipt.
"""
from __future__ import annotations

from uuid import UUID
from copy import deepcopy
import re
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


def prepare_feature4_speech_review_candidate(*,shop_id,campaign_id,audio_asset_id,
                                              active_editor_reader,
                                              read_current_audio,
                                              read_current_quality):
    """F2 original-Kokoro WAV + real F7 words -> F4 *review-only* draft.

    This source contract does NOT create a publishable or executable F4 edit;
    F4 must use separately persisted human approval, current lease and rights.
    """
    if (not all(_uuid(v) for v in (shop_id,campaign_id,audio_asset_id)) or
        not all(callable(x) for x in (
            active_editor_reader,read_current_audio,read_current_quality))):
        raise Feature4VoiceoverDenied("Trusted Feature4 speech reviewer required")
    def current():
        if active_editor_reader(shop_id,campaign_id) is not True:
            raise Feature4VoiceoverDenied("Current editor denied")
        audio=read_current_audio(shop_id,campaign_id,audio_asset_id)
        quality=read_current_quality(shop_id,campaign_id,audio_asset_id)
        if (type(audio) is not dict or type(quality) is not dict or
            audio.get("shop_id")!=shop_id or audio.get("campaign_id")!=campaign_id or
            audio.get("audio_asset_id")!=audio_asset_id or
            audio.get("schema")!="retailgrowth.feature2-to-feature4-original-voice.v1" or
            audio.get("provider")!="kokoro-onnx" or
            audio.get("private") is not True or audio.get("revoked_at") is not None or
            audio.get("review_state")!="PENDING_HUMAN_LISTEN_AND_RIGHTS" or
            audio.get("can_publish") is not False or
            quality.get("schema")!="retailgrowth.feature2-verified-audio-qa.v1" or
            quality.get("shop_id")!=shop_id or
            quality.get("campaign_id")!=campaign_id or
            quality.get("audio_asset_id")!=audio_asset_id or
            quality.get("review_state")!="PENDING_HUMAN_LISTEN_AND_RIGHTS" or
            quality.get("can_publish") is not False or
            quality.get("approved_for_editing") is not False or
            quality.get("pronunciation_verified") is not False or
            quality.get("source_rechecked") is not True or
            not re.fullmatch("[a-f0-9]{64}",
                             str(audio.get("original_audio_sha256") or "")) or
            quality.get("original_audio_sha256")!=audio["original_audio_sha256"] or
            audio.get("creative_plan_sha256")!=quality.get("creative_plan_sha256") or
            audio.get("original_script_sha256")!=quality.get("original_script_sha256") or
            audio.get("duration_seconds")!=quality.get("audio_duration_seconds")):
            raise Feature4VoiceoverDenied("Original audio/ASR quality review changed")
        words=quality.get("asr_word_timing")
        duration=quality["audio_duration_seconds"]
        if (not isinstance(words,list) or not 1<=len(words)<=600 or
            type(duration) not in (float,int) or not 0.2<=duration<=65):
            raise Feature4VoiceoverDenied("F7 actual word timing unavailable")
        prev=0
        for w in words:
            if (type(w) is not dict or set(w)!={"word","startMs","endMs"} or
                not isinstance(w.get("word"),str) or
                not re.fullmatch(r"[A-Za-z0-9'-]{1,80}",w["word"]) or
                type(w.get("startMs")) is not int or
                type(w.get("endMs")) is not int or
                not prev<=w["startMs"]<w["endMs"]<=round(duration*1000)+1):
                raise Feature4VoiceoverDenied("Untrusted candidate F4 captions")
            prev=w["endMs"]
        return deepcopy(audio),deepcopy(quality)
    original_a,original_q=current()
    same_a,same_q=current()
    if original_a!=same_a or original_q!=same_q:
        raise Feature4VoiceoverDenied("Source/audio/quality changed mid-handoff")
    return {
        "schema":"retailgrowth.feature2-feature4-speech-review.v1",
        "shop_id":shop_id,"campaign_id":campaign_id,
        "creative_plan_sha256":original_q["creative_plan_sha256"],
        "original_script_sha256":original_q["original_script_sha256"],
        "voiceover_asset_id":audio_asset_id,
        "original_audio_sha256":original_a["original_audio_sha256"],
        "original_wav_duration_seconds":original_a["duration_seconds"],
        "provider":"kokoro-onnx",
        "model_version":original_a.get("model_version"),
        "voice_id":original_a.get("voice_id"),
        "language":original_a.get("language"),
        "source_feature7_job_id":original_q["feature7_job_id"],
        "candidate_caption_words":[dict(x) for x in original_q["asr_word_timing"]],
        "quality_issues":[*original_q.get("asr_issues",[]),
                          *original_q.get("pcm_quality_warnings",[])],
        "word_confidence_available":False,
        "actual_phoneme_approval":False,
        "review_status":"NEEDS_HUMAN_LISTEN_AND_CAPTION_REVIEW",
        "approved":False,"renderable":False,"can_publish":False,
        "f4_must_recheck_media_rights_lease_and_editor":True,
        "f4_owns_final_audio_mix_and_caption_timing":True,
        "raw_audio_exposed":False,"public_audio_url":None,
    }
