"""Kokoro-first trusted Feature2 narration workflow; NEVER automatic paid Azure.

Azure requires its own explicit authorization and reserved once-only job.
No public route or database schema introduced. F4 gets metadata, not raw WAV.
"""
from __future__ import annotations
from hashlib import sha256
from uuid import UUID
from .feature2_azure_speech import _plan, SpeechRejected
from .feature2_kokoro_local import synthesize_local
from .feature2_voice_quality import pcm_stats, consume_feature7_stt, VoiceQualityDenied
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
    status="F7_NOT_CONNECTED";words=None
    if f7_transcript is not None:
        try: tested=consume_feature7_stt(
            shop_id=shop_id,campaign_id=campaign_id,
            source_sha256=review["plan_sha256"],
            original_audio_sha256=metrics["sha256"],
            expected_script=script,transcript=f7_transcript)
        except VoiceQualityDenied as exc:
            raise LocalVoiceJobDenied("External Feature7 evidence invalid") from exc
        issues.extend(tested["issues"])
        status="F7_VERSIONED_RECEIPT_REVIEWED"
        words=f7_transcript["words"]
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
        "music_ducking_recommended":True}
    result=store_original_private(shop_id,campaign_id,held,original,dict(envelope))
    if (type(result) is not dict or not _uuid(result.get("audio_asset_id")) or
        result.get("shop_id")!=shop_id or result.get("campaign_id")!=campaign_id or
        result.get("original_audio_sha256")!=metrics["sha256"] or
        result.get("private") is not True):
        raise LocalVoiceJobDenied("Original audio was not registered in private storage")
    return {**envelope,"private_audio_asset_id":result["audio_asset_id"],
            "audio_bytes":None,"signed_url":None,
            "f4_must_recheck_private_rights":True}
