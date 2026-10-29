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


def reserve_budgeted_local_voice_job(*,shop_id,campaign_id,source_plan,
                                    voice_id,lang,speed,job_key,now_ms,
                                    authorize_current_editor,read_current_plan,
                                    read_authoritative_quota,
                                    reserve_atomic_once):
    """Fail-closed tenant CPU budget/idempotency/lease handoff.

    The server's reserve_atomic_once callback MUST lock a durable tenant
    budget row, check request digest uniqueness, cap concurrent CPU leases
    and commit both a quota reservation and fencing token atomically.
    This function validates the returned receipt, not database durability.
    """
    import json
    from .feature2_kokoro_local import SUPPORTED_VOICES,SPEEDS
    if (not all(_uuid(v) for v in (shop_id,campaign_id,job_key)) or
        type(now_ms) is not int or now_ms<1_700_000_000_000 or
        type(voice_id) is not str or SUPPORTED_VOICES.get(voice_id)!=lang or
        type(speed) is not str or speed not in SPEEDS or
        not all(callable(x) for x in (
            authorize_current_editor,read_current_plan,
            read_authoritative_quota,reserve_atomic_once))):
        raise LocalVoiceJobDenied("Trusted budgeted voice job scope required")
    try:
        creative,approval,script=_plan(
            source_plan,shop_id=shop_id,campaign_id=campaign_id)
    except SpeechRejected as exc:
        raise LocalVoiceJobDenied("Current reviewed plan missing") from exc
    plan_sha=approval["plan_sha256"]
    if (authorize_current_editor(shop_id,campaign_id) is not True or
        read_current_plan(shop_id,campaign_id)!=source_plan):
        raise LocalVoiceJobDenied("Voice editor or original source revoked")
    quota=read_authoritative_quota(shop_id,campaign_id)
    # The policy is trusted and signed by the backend, NEVER browser props.
    if (type(quota) is not dict or
        quota.get("shop_id")!=shop_id or
        quota.get("campaign_id")!=campaign_id or
        quota.get("provider")!="kokoro-onnx" or
        quota.get("paid_api_calls_allowed") is not False or
        type(quota.get("budget_revision")) is not int or
        quota["budget_revision"]<0 or
        type(quota.get("reserved_cpu_ms")) is not int or
        type(quota.get("used_cpu_ms")) is not int or
        type(quota.get("monthly_cpu_limit_ms")) is not int or
        type(quota.get("active_cpu_jobs")) is not int or
        type(quota.get("max_active_cpu_jobs")) is not int or
        not 0<=quota["reserved_cpu_ms"]<=86_400_000 or
        not 0<=quota["used_cpu_ms"]<=86_400_000 or
        not 1_000<=quota["monthly_cpu_limit_ms"]<=86_400_000 or
        not 0<=quota["active_cpu_jobs"]<=4 or
        not 1<=quota["max_active_cpu_jobs"]<=4 or
        type(quota.get("per_job_reserved_cpu_ms")) is not int or
        not 2_000<=quota["per_job_reserved_cpu_ms"]<=180_000 or
        type(quota.get("period_id")) is not str or
        not __import__("re").fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])",
                                       quota["period_id"]) or
        quota.get("policy_state")!="ACTIVE"):
        raise LocalVoiceJobDenied("Signed CPU budget policy invalid")
    reserved=quota["per_job_reserved_cpu_ms"]
    if (quota["active_cpu_jobs"]>=quota["max_active_cpu_jobs"] or
        quota["used_cpu_ms"]+quota["reserved_cpu_ms"]+reserved>
            quota["monthly_cpu_limit_ms"]):
        raise LocalVoiceJobDenied("CPU quota exhausted or too many active jobs")
    req={"shop_id":shop_id,"campaign_id":campaign_id,
         "creative_plan_sha256":plan_sha,
         "original_script_sha256":sha256(script.encode()).hexdigest(),
         "job_key":job_key,"voice_id":voice_id,"language":lang,
         "speed":speed,"provider":"kokoro-onnx",
         "period_id":quota["period_id"],
         "budget_revision":quota["budget_revision"],
         "reserved_cpu_ms":reserved,
         "paid_api_calls_allowed":False}
    request_sha=sha256(json.dumps(req,sort_keys=True,
                     separators=(",",":")).encode()).hexdigest()
    receipt=reserve_atomic_once(shop_id,campaign_id,job_key,request_sha,
                                quota["budget_revision"],reserved,dict(req))
    if (type(receipt) is not dict or
        receipt.get("schema")!="retailgrowth.feature2-local-cpu-reservation.v1" or
        receipt.get("shop_id")!=shop_id or
        receipt.get("campaign_id")!=campaign_id or
        receipt.get("creative_plan_sha256")!=plan_sha or
        receipt.get("job_key")!=job_key or
        receipt.get("request_sha256")!=request_sha or
        receipt.get("provider")!="kokoro-onnx" or
        receipt.get("reserved_cpu_ms")!=reserved or
        receipt.get("period_id")!=quota["period_id"] or
        type(receipt.get("lease_fence")) is not int or
        not 1<=receipt["lease_fence"]<2**63 or
        type(receipt.get("lease_expires_ms")) is not int or
        not now_ms<receipt["lease_expires_ms"]<=now_ms+300_000 or
        receipt.get("status")!="RESERVED" or
        receipt.get("private") is not True or
        receipt.get("paid_api_calls")!=0 or
        receipt.get("can_publish") is not False or
        receipt.get("atomic_unique_commit") is not True):
        raise LocalVoiceJobDenied("Durable private CPU reservation evidence invalid")
    if (authorize_current_editor(shop_id,campaign_id) is not True or
        read_current_plan(shop_id,campaign_id)!=source_plan):
        raise LocalVoiceJobDenied("Voice source revoked after CPU budget lease")
    return {"schema":receipt["schema"],"shop_id":shop_id,
            "campaign_id":campaign_id,"creative_plan_sha256":plan_sha,
            "job_key":job_key,"request_sha256":request_sha,
            "lease_fence":receipt["lease_fence"],
            "lease_expires_ms":receipt["lease_expires_ms"],
            "reserved_cpu_ms":reserved,"period_id":quota["period_id"],
            "provider":"kokoro-onnx","private":True,
            "can_publish":False,"paid_api_calls":0,
            "real_model_inference_observed":False,
            "reservation_is_not_worker_completion":True}


def read_registered_private_original_wav(*,shop_id,campaign_id,source_plan,
        audio_asset_id,requested_audio_sha256,
        authorize_current_editor,read_current_plan,
        read_registered_private_asset,read_private_blob):
    """Return verified *original* WAV bytes only to a trusted JWT/RLS endpoint.

    The endpoint authenticates before calling, sends HTTP no-store and checks
    current shop/editor rights; this function validates callbacks/bytes twice.
    Never use a public storage URL or browser-provided file path.
    """
    import re
    if (not all(_uuid(x) for x in (shop_id,campaign_id,audio_asset_id)) or
        type(requested_audio_sha256) is not str or
        not re.fullmatch(r"[a-f0-9]{64}",requested_audio_sha256) or
        not all(callable(x) for x in
                (authorize_current_editor,read_current_plan,
                 read_registered_private_asset,read_private_blob))):
        raise LocalVoiceJobDenied("Trusted original private WAV reader required")
    try:
        _,review,script=_plan(source_plan,shop_id=shop_id,campaign_id=campaign_id)
    except SpeechRejected as exc:
        raise LocalVoiceJobDenied("Authoritative current narration plan denied") from exc
    original_script_sha256=sha256(script.encode()).hexdigest()
    def current():
        return (authorize_current_editor(shop_id,campaign_id) is True and
                read_current_plan(shop_id,campaign_id)==source_plan)
    def registered():
        media=read_registered_private_asset(shop_id,campaign_id,audio_asset_id)
        if (type(media) is not dict or
            media.get("schema")!="retailgrowth.feature2-to-feature4-original-voice.v1" or
            media.get("shop_id")!=shop_id or
            media.get("campaign_id")!=campaign_id or
            media.get("audio_asset_id")!=audio_asset_id or
            media.get("creative_plan_sha256")!=review["plan_sha256"] or
            media.get("original_script_sha256")!=original_script_sha256 or
            media.get("original_audio_sha256")!=requested_audio_sha256 or
            media.get("provider")!="kokoro-onnx" or
            media.get("mime_type")!="audio/wav" or
            media.get("private") is not True or
            media.get("can_publish") is not False or
            media.get("review_state")!="PENDING_HUMAN_LISTEN_AND_RIGHTS" or
            media.get("revoked_at") is not None or
            media.get("local_inference_evidence") is not True):
            raise LocalVoiceJobDenied("Private original WAV registration or rights changed")
        return media
    if not current():
        raise LocalVoiceJobDenied("Editor revoked before original WAV download")
    prior=registered()
    # Reader is server-selected by the registered asset; no client bucket or
    # object path. Blob bytes must not be logged or cached in shared state.
    raw=read_private_blob(shop_id,campaign_id,audio_asset_id)
    if (type(raw) is not bytes or not 128<=len(raw)<=20_000_000):
        raise LocalVoiceJobDenied("Original private WAV bytes invalid")
    try:
        metrics=pcm_stats(raw)
    except (VoiceQualityDenied,ValueError,TypeError) as exc:
        raise LocalVoiceJobDenied("Original private WAV format denied") from exc
    if (metrics["sha256"]!=requested_audio_sha256 or
        type(prior.get("duration_seconds")) not in (float,int) or
        prior["duration_seconds"]!=metrics["duration_seconds"]):
        raise LocalVoiceJobDenied("Private WAV bytes or duration changed")
    if not current() or registered()!=prior:
        raise LocalVoiceJobDenied("Private original WAV rights or shop revoked during read")
    return {"schema":"retailgrowth.feature2-private-original-wav-read.v1",
            "shop_id":shop_id,"campaign_id":campaign_id,
            "asset_id":audio_asset_id,
            "original_audio_sha256":metrics["sha256"],
            "mime_type":"audio/wav","audio_bytes":raw,
            "private":True,"can_publish":False,
            "can_dispatch_motion":False,
            "human_listen_required":True,
            "commercial_rights_not_certified":True}
