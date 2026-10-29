"""Bounded signed source-only local pronunciation retake for one affected scene.

A reviewer chooses the candidate sentence; one charged/CPU effort is
reserved against current shop/plan/voice and capped to ONE re-synthesis
attempt. F4 must assemble the approved corrected scene; do not mutate
the immutable original creative script or invent new F7 word timestamps.
"""
from __future__ import annotations
from hashlib import sha256
from uuid import UUID
import re
from .feature2_kokoro_local import synthesize_local
from .feature2_voice_quality import pcm_stats
from .feature2_pronunciation_dictionary import apply_approved_local_corrections
from .feature2_azure_speech import _plan, SpeechRejected

class RetakeDenied(ValueError):pass

def _uuid(x):
    try:return type(x) is str and str(UUID(x))==x and UUID(x).version==4
    except (ValueError,TypeError,AttributeError):return False

def local_sentence_retake(*,shop_id,campaign_id,source_plan,sentence_index,
                         flagged_audio_sha256,voice_id,language,speed,job_key,
                         current_editor,read_plan,read_approved_words,
                         claim_one_retake,write_pending_private,
                         model_cache_dir=None,synthesizer=synthesize_local):
    if (not _uuid(shop_id) or not _uuid(campaign_id) or not _uuid(job_key) or
        type(sentence_index) is not int or not 0<=sentence_index<=12 or
        type(flagged_audio_sha256) is not str or
        not re.fullmatch("[a-f0-9]{64}",flagged_audio_sha256) or
        not all(callable(x) for x in (current_editor,read_plan,read_approved_words,
                                     claim_one_retake,write_pending_private))):
        raise RetakeDenied("Trusted single-sentence retake required")
    try:creative,review,script=_plan(source_plan,shop_id=shop_id,campaign_id=campaign_id)
    except SpeechRejected as exc:raise RetakeDenied("Reviewed source script unavailable") from exc
    # Keep actual approved sentence boundaries; punctuation remains in source.
    sentences=[x.strip() for x in re.findall(r"[^.!?]+[.!?]?",script) if x.strip()]
    if len(sentences)>13 or sentence_index>=len(sentences):
        raise RetakeDenied("Requested sentence is outside original script")
    original=sentences[sentence_index]
    if current_editor(shop_id,campaign_id) is not True or read_plan(shop_id,campaign_id)!=source_plan:
        raise RetakeDenied("Active editor or current original script not verified")
    corrected=apply_approved_local_corrections(
        script=original,shop_id=shop_id,lang=language,
        read_current_entries=read_approved_words)
    if not corrected["corrections"]:
        raise RetakeDenied("No approved pronunciation correction for this sentence")
    # Callback implements durable unique (shop, campaign, plan, prior audio,
    # sentence_idx, job) CAS. Any duplicate or later retry must fail CLOSED.
    claim=claim_one_retake(shop_id,campaign_id,review["plan_sha256"],
                           flagged_audio_sha256,sentence_index,job_key)
    if type(claim) is not str or len(claim)<8:
        raise RetakeDenied("One local correction attempt already used or unauthorized")
    try:
        result=synthesizer(text=corrected["corrected_text_for_tts"],
                           voice_id=voice_id,lang=language,
                           speed=speed,cache_dir=model_cache_dir)
    except Exception as exc:
        raise RetakeDenied("Local retake failed; no automatic Azure") from exc
    if type(result) is not dict or result.get("provider")!="kokoro-onnx" or \
       result.get("actual_inference_verified") is not True or result.get("test_only") is not False:
        raise RetakeDenied("Real Kokoro sentence audio not verified")
    wav=result.get("audio_wav")
    summary=pcm_stats(wav)
    if summary["sha256"]!=result.get("audio_sha256") or \
       summary["duration_seconds"]>creative["duration_seconds"]:
        raise RetakeDenied("Retake produced invalid original audio")
    if current_editor(shop_id,campaign_id) is not True or read_plan(shop_id,campaign_id)!=source_plan:
        raise RetakeDenied("Source revoked after retake")
    data={"schema":"retailgrowth.feature2-sentence-retake.v1",
          "shop_id":shop_id,"campaign_id":campaign_id,
          "creative_plan_sha256":review["plan_sha256"],
          "job_key":job_key,
          "original_full_script_sha256":sha256(script.encode()).hexdigest(),
          "original_sentence_sha256":sha256(original.encode()).hexdigest(),
          "correction_input_sha256":sha256(corrected["corrected_text_for_tts"].encode()).hexdigest(),
          "prior_audio_sha256":flagged_audio_sha256,
          "new_audio_sha256":summary["sha256"],
          "duration_seconds":summary["duration_seconds"],
          "sentence_index":sentence_index,"voice_id":voice_id,
          "language":language,"speed":speed,
          "corrections":corrected["corrections"],
          "review_status":"PENDING_NEW_STT_AND_HUMAN_LISTEN",
          "actual_pronunciation_success_verified":False,
          "word_timestamps":None,"private":True,
          "can_publish":False,"azure_fallback_used":False,
          "attempts_reserved":1}
    saved=write_pending_private(shop_id,campaign_id,claim,wav,dict(data))
    # This is a *trusted backend writer* receipt, not a browser-supplied flag.
    # Bind it to the exact reserved one-shot job, original private bytes,
    # requested voice/locale and pending review, not merely a matching SHA.
    if (type(saved) is not dict or not _uuid(saved.get("asset_id")) or
        saved.get("shop_id")!=shop_id or saved.get("campaign_id")!=campaign_id or
        saved.get("creative_plan_sha256")!=review["plan_sha256"] or
        saved.get("job_key")!=job_key or
        saved.get("prior_audio_sha256")!=flagged_audio_sha256 or
        saved.get("new_audio_sha256")!=summary["sha256"] or
        saved.get("voice_id")!=voice_id or saved.get("language")!=language or
        saved.get("speed")!=speed or
        saved.get("review_status")!="PENDING_NEW_STT_AND_HUMAN_LISTEN" or
        saved.get("private") is not True or
        any(saved.get(k) is True for k in
            ("can_publish","commercial_use_approved","azure_fallback_used"))):
        raise RetakeDenied("Exact private one-shot retake receipt not registered")
    # A successful storage callback does not confer current editor authority.
    # Real coordinator writes MUST fence their own atomic commit; this
    # post-write check prevents stale/foreign successes from reaching the UI.
    if (current_editor(shop_id,campaign_id) is not True or
        read_plan(shop_id,campaign_id)!=source_plan):
        raise RetakeDenied("Source revoked after private retake registration")
    return {**data,"private_sentence_audio_asset_id":saved["asset_id"],
            "requires_feature4_scene_assembly":True,
            "requires_new_feature7_transcription":True}
