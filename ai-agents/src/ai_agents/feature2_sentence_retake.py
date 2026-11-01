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
from .feature2_kokoro_local import synthesize_local, SUPPORTED_VOICES, SPEEDS
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
        type(voice_id) is not str or type(language) is not str or
        SUPPORTED_VOICES.get(voice_id)!=language or
        type(speed) is not str or speed not in SPEEDS or
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
    if (type(saved) is not dict or not _uuid(saved.get("asset_id")) or
        saved.get("shop_id")!=shop_id or
        saved.get("new_audio_sha256")!=summary["sha256"] or
        saved.get("private") is not True or
        ("campaign_id" in saved and saved["campaign_id"]!=campaign_id) or
        ("creative_plan_sha256" in saved and
         saved["creative_plan_sha256"]!=review["plan_sha256"]) or
        ("prior_audio_sha256" in saved and
         saved["prior_audio_sha256"]!=flagged_audio_sha256) or
        ("sentence_index" in saved and
         (type(saved["sentence_index"]) is not int or
          saved["sentence_index"]!=sentence_index))):
        raise RetakeDenied("Private sentence retake not registered")
    # Tenant-private registered bytes are still pending fresh STT and
    # human listening. The writer cannot grant publication, media rights,
    # billed provider work, or return a signed/public URL in its receipt.
    if (any(key in saved and saved[key] is not False for key in
            ("can_publish","can_dispatch_paid_motion","commercial_use_approved",
             "audio_rights_approved","actual_pronunciation_success_verified",
             "azure_fallback_used","paid_inference_authorized",
             "may_auto_invoke_azure")) or
        ("review_status" in saved and
         saved["review_status"]!="PENDING_NEW_STT_AND_HUMAN_LISTEN") or
        ("requires_new_feature7_transcription" in saved and
         saved["requires_new_feature7_transcription"] is not True) or
        ("requires_feature4_scene_assembly" in saved and
         saved["requires_feature4_scene_assembly"] is not True) or
        ("paid_calls" in saved and
         (type(saved["paid_calls"]) is not int or saved["paid_calls"]!=0)) or
        ("billing" in saved and saved["billing"]!="NONE") or
        ("signed_url" in saved and saved["signed_url"] is not None) or
        ("private_download_url" in saved and
         saved["private_download_url"] is not None)):
        raise RetakeDenied("Private writer attempted to bypass retake review")
    # A private writer may run after editor access or the original plan was
    # revoked. Do not return a successful retake receipt in that race.
    # The real storage adapter MUST make its commit conditional on current
    # tenant authorization and clean up orphaned pending bytes atomically;
    # this source-only recheck does not prove such a transaction exists.
    if (current_editor(shop_id,campaign_id) is not True or
        read_plan(shop_id,campaign_id)!=source_plan):
        raise RetakeDenied("Retake source revoked during private registration")
    return {**data,"private_sentence_audio_asset_id":saved["asset_id"],
            "requires_feature4_scene_assembly":True,
            "requires_new_feature7_transcription":True}
