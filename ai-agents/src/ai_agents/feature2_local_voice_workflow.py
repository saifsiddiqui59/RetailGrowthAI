"""Kokoro-first trusted Feature2 narration workflow; NEVER automatic paid Azure.

Azure requires its own explicit authorization and reserved once-only job.
No public route or database schema introduced. F4 gets metadata, not raw WAV.
"""
from __future__ import annotations
from hashlib import sha256
from uuid import UUID
from .feature2_azure_speech import _plan, SpeechRejected
from .feature2_kokoro_local import synthesize_local
from .feature2_voice_quality import (pcm_stats, review_signed_audio_transcript,
                                     Feature7AudioEvidenceDenied, VoiceQualityDenied)
from .feature2_pronunciation_dictionary import apply_approved_local_corrections

class LocalVoiceJobDenied(ValueError): pass

def _uuid(s):
    try: return type(s) is str and UUID(s).version==4 and str(UUID(s))==s
    except (ValueError,TypeError,AttributeError):return False

def synthesize_and_stage(*,shop_id,campaign_id,source_plan,voice_id,lang,speed,
                         job_key,authorize_editor,read_current_plan,
                         reserve_job_once,store_original_private,
                         operator_cache_dir=None,pronunciation_reader=None,
                         f7_transcript=None,synthesizer=synthesize_local):
    """One bounded CPU synthesis with current tenant, original sha and rights.

    Backend callbacks must come from real trusted server / RLS; client JSON
    never implements authorize_editor/reserve_job_once/store_original_private.
    """
    if (not _uuid(shop_id) or not _uuid(campaign_id) or not _uuid(job_key) or
        not all(callable(f) for f in (authorize_editor,read_current_plan,
                                    reserve_job_once,store_original_private))):
        raise LocalVoiceJobDenied("Trusted same-shop worker callbacks required")
    try: creative,review,script=_plan(source_plan,shop_id=shop_id,campaign_id=campaign_id)
    except SpeechRejected as exc: raise LocalVoiceJobDenied("Reviewed source plan missing") from exc
    if (authorize_editor(shop_id,campaign_id) is not True or
        read_current_plan(shop_id,campaign_id)!=source_plan):
        raise LocalVoiceJobDenied("Current editor or source plan revoked")
    held=reserve_job_once(shop_id,campaign_id,review["plan_sha256"],job_key)
    if type(held) is not str or len(held)<8:
        raise LocalVoiceJobDenied("No durable once-only local job")
    changed=None
    if pronunciation_reader:
        if not callable(pronunciation_reader):
            raise LocalVoiceJobDenied("Untrusted pronunciation dictionary")
        changed=apply_approved_local_corrections(
            script=script,shop_id=shop_id,lang=lang,
            read_current_entries=pronunciation_reader)
    text=changed["corrected_text_for_tts"] if changed else script
    # This is a real upstream Kokoro.create call in production, not our own
    # inference engine. No TTS provider is called if Kokoro fails.
    try: generated=synthesizer(text=text,voice_id=voice_id,lang=lang,
                                speed=speed,cache_dir=operator_cache_dir)
    except Exception as exc:
        raise LocalVoiceJobDenied("Kokoro job failed, Azure fallback not started") from exc
    if (type(generated) is not dict or generated.get("provider")!="kokoro-onnx" or
        generated.get("actual_inference_verified") is not True or
        generated.get("test_only") is not False):
        raise LocalVoiceJobDenied("No real verified Kokoro synthesis result")
    original=generated.get("audio_wav")
    metrics=pcm_stats(original)
    if (generated.get("audio_sha256")!=metrics["sha256"] or
        metrics["duration_seconds"]>creative["duration_seconds"]):
        raise LocalVoiceJobDenied("Wrong original WAV SHA or Reel duration")
    issues=[{"problem":v,"manual_review_required":True}
            for v in ("audio_clipped","too_quiet","too_loud","excessive_silence")
            if metrics[v]]
    # A Feature7 transcript must be signed against the *registered* private
    # original WAV asset ID. F7 currently signs uploaded MP4 source hashes.
    # Never trust an injected boolean worker_verified (or pre-registration ASR).
    # Review via feature2_feature7_signed_audio only AFTER private registration.
    if f7_transcript is not None:
        raise LocalVoiceJobDenied(
            "Feature7 audio review requires registered WAV and signed receipt")
    status="F7_PENDING_SIGNED_AUDIO_ADAPTER";words=None
    if (authorize_editor(shop_id,campaign_id) is not True or
        read_current_plan(shop_id,campaign_id)!=source_plan):
        raise LocalVoiceJobDenied("Source tenant/plan revoked after synthesis")
    envelope={
        "schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
        "shop_id":shop_id,"campaign_id":campaign_id,
        "creative_plan_sha256":review["plan_sha256"],
        "original_script_sha256":sha256(script.encode()).hexdigest(),
        "provider":"kokoro-onnx","upstream_commit":generated["upstream_revision"],
        "model_version":generated["model"],"voice_id":voice_id,
        "language":lang,"speed":speed,
        "original_audio_sha256":metrics["sha256"],
        "duration_seconds":metrics["duration_seconds"],
        "mime_type":"audio/wav","private":True,
        "quality_issues":issues,"stt_status":status,"actual_word_timestamps":words,
        "dictionary_changes":changed["corrections"] if changed else [],
        "pronunciation_verified":False,
        "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
        "can_publish":False,"can_dispatch_motion":False,
        "azure_fallback_used":False,"paid_calls":0,
        "music_ducking_recommended":True,
        "local_inference_evidence":True}
    result=store_original_private(shop_id,campaign_id,held,original,dict(envelope))
    if (type(result) is not dict or not _uuid(result.get("audio_asset_id")) or
        result.get("shop_id")!=shop_id or result.get("campaign_id")!=campaign_id or
        result.get("original_audio_sha256")!=metrics["sha256"] or
        result.get("private") is not True):
        raise LocalVoiceJobDenied("Original audio was not registered in private storage")
    return {**envelope,"private_audio_asset_id":result["audio_asset_id"],
            "audio_bytes":None,"signed_url":None,
            "f4_must_recheck_private_rights":True}


def review_registered_kokoro_audio(*, shop_id, campaign_id, source_plan,
                                   audio_asset_id, f7_job_id, evidence_key,
                                   now_ms, authorize_editor, read_current_plan,
                                   read_original_private, read_feature7_job,
                                   save_pending_review):
    """Post-registration trusted WAV -> Feature7 ASR -> review-only F4 candidate.

    Feature7 currently has an MP4-only producer, so this awaits an F7-owned
    AUDIO worker. All callbacks MUST be trusted backend/RLS and the F7 job
    reader MUST reassert it ran against the original registered WAV bytes.
    A browser cannot inject a signed receipt, source check or saved review.
    """
    if (not _uuid(shop_id) or not _uuid(campaign_id) or
        not _uuid(audio_asset_id) or type(f7_job_id) is not str or
        not 1 <= len(f7_job_id) <= 120 or
        not all(c.isalnum() or c in "_-" for c in f7_job_id) or
        type(now_ms) is not int or now_ms < 0 or
        type(evidence_key) is not bytes or len(evidence_key) < 32 or
        not all(callable(x) for x in (
            authorize_editor,read_current_plan,read_original_private,
            read_feature7_job,save_pending_review))):
        raise LocalVoiceJobDenied("Trusted post-registration audio review required")
    try:
        _, approval, script = _plan(source_plan,
                                   shop_id=shop_id,campaign_id=campaign_id)
    except SpeechRejected as exc:
        raise LocalVoiceJobDenied("Authoritative reviewed creative unavailable") from exc
    plan_sha=approval["plan_sha256"]
    script_sha=sha256(script.encode()).hexdigest()
    def current():
        return (authorize_editor(shop_id,campaign_id) is True and
                read_current_plan(shop_id,campaign_id)==source_plan)
    if not current():
        raise LocalVoiceJobDenied("Current creative plan/editor denied")
    def read_valid_original():
        original=read_original_private(shop_id,campaign_id,audio_asset_id)
        if (type(original) is not dict or
            original.get("schema")!="retailgrowth.feature2-to-feature4-original-voice.v1" or
            original.get("shop_id")!=shop_id or
            original.get("campaign_id")!=campaign_id or
            original.get("creative_plan_sha256")!=plan_sha or
            original.get("original_script_sha256")!=script_sha or
            original.get("audio_asset_id")!=audio_asset_id or
            original.get("mime_type")!="audio/wav" or
            original.get("provider")!="kokoro-onnx" or
            original.get("private") is not True or
            original.get("can_publish") is not False or
            original.get("review_state")!="PENDING_HUMAN_LISTEN_AND_RIGHTS" or
            original.get("revoked_at") is not None or
            original.get("feature7_audio_job_id")!=f7_job_id or
            original.get("local_inference_evidence") is not True):
            raise LocalVoiceJobDenied("Original private audio identity/review job denied")
        try:
            metrics=pcm_stats(original.get("audio_wav"))
        except (VoiceQualityDenied,TypeError) as exc:
            raise LocalVoiceJobDenied("Private registered original WAV invalid") from exc
        if (original.get("original_audio_sha256")!=metrics["sha256"] or
            original.get("duration_seconds")!=metrics["duration_seconds"]):
            raise LocalVoiceJobDenied("Stored audio hash or duration changed")
        return metrics
    metrics=read_valid_original()
    f7=read_feature7_job(shop_id,campaign_id,audio_asset_id,f7_job_id)
    if (type(f7) is not dict or
        f7.get("job_id")!=f7_job_id or
        f7.get("shop_id")!=shop_id or
        f7.get("campaign_id")!=campaign_id or
        f7.get("audio_asset_id")!=audio_asset_id or
        f7.get("source_media_kind")!="audio/wav" or
        f7.get("original_audio_sha256")!=metrics["sha256"] or
        f7.get("origin")!="trusted_feature7_original_audio_worker" or
        f7.get("revoked_at") is not None):
        raise LocalVoiceJobDenied("No authoritative Feature7 original-WAV worker job")
    def check_current_source(*scope):
        if scope!=(shop_id,campaign_id,audio_asset_id,plan_sha,
                   metrics["sha256"],f7_job_id) or not current():
            return False
        try:
            fresh=read_valid_original()
            job=read_feature7_job(shop_id,campaign_id,audio_asset_id,f7_job_id)
            return (fresh==metrics and type(job) is dict and
                    job.get("job_id")==f7_job_id and
                    job.get("origin")=="trusted_feature7_original_audio_worker" and
                    job.get("source_media_kind")=="audio/wav" and
                    job.get("original_audio_sha256")==metrics["sha256"] and
                    job.get("revoked_at") is None)
        except (LocalVoiceJobDenied,TypeError,KeyError,ValueError):
            return False
    try:
        reviewed=review_signed_audio_transcript(
            receipt=f7.get("receipt"),shop_id=shop_id,campaign_id=campaign_id,
            audio_asset_id=audio_asset_id,creative_plan_sha256=plan_sha,
            original_audio_sha256=metrics["sha256"],
            audio_duration_seconds=metrics["duration_seconds"],
            expected_script=script,evidence_key=evidence_key,now_ms=now_ms,
            expected_job_id=f7_job_id,
            assert_current_source=check_current_source)
    except Feature7AudioEvidenceDenied as exc:
        raise LocalVoiceJobDenied("Feature7 signed original-WAV review rejected") from exc
    if not current() or not check_current_source(shop_id,campaign_id,
                audio_asset_id,plan_sha,metrics["sha256"],f7_job_id):
        raise LocalVoiceJobDenied("Source revoked before pending review persistence")
    # No customer voice, scripts, raw audio, HMAC or bearer token in result.
    summary={
        "schema":"retailgrowth.feature2-verified-audio-qa.v1",
        "shop_id":shop_id,"campaign_id":campaign_id,
        "creative_plan_sha256":plan_sha,
        "original_script_sha256":script_sha,
        "audio_asset_id":audio_asset_id,
        "original_audio_sha256":metrics["sha256"],
        "audio_duration_seconds":metrics["duration_seconds"],
        "feature7_job_id":f7_job_id,
        "asr_model_version":reviewed["model_version"],
        "asr_transcript_matched_script":reviewed["transcript_matches_script"],
        "asr_word_timing":f7["receipt"]["words"],
        "asr_word_confidence_available":False,
        "asr_issues":reviewed["issues"],
        "pcm_quality_warnings":[key for key in
          ("audio_clipped","too_quiet","too_loud","excessive_silence")
          if metrics[key]],
        "pronunciation_verified":False,
        "source_rechecked":True,
        "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
        "can_publish":False,"can_dispatch_motion":False,
        "approved_for_editing":False,
    }
    saved=save_pending_review(shop_id,campaign_id,audio_asset_id,
                              f7_job_id,dict(summary))
    if (type(saved) is not dict or
        saved.get("shop_id")!=shop_id or
        saved.get("campaign_id")!=campaign_id or
        saved.get("audio_asset_id")!=audio_asset_id or
        saved.get("original_audio_sha256")!=metrics["sha256"] or
        saved.get("review_state")!="PENDING_HUMAN_LISTEN_AND_RIGHTS" or
        saved.get("private") is not True):
        raise LocalVoiceJobDenied("Trusted pending reviewer record unavailable")
    return summary
