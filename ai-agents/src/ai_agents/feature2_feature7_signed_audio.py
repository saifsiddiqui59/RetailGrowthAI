"""Feature #2 consumer for Feature #7's exact signed Faster-Whisper evidence.

This does NOT run ASR or make a video transcript into a narration transcript.
Feature7 currently signs original VIDEO hashes; the Kokoro-to-ASR audio route
must be implemented by Feature7 before this adapter accepts a real receipt.
The signing key and this adapter belong exclusively inside a trusted backend.
"""
from __future__ import annotations

from hashlib import sha256
import hmac
import json
import math
import re
from .feature2_voice_quality import consume_feature7_stt, VoiceQualityDenied

SHA = re.compile(r"^[a-f0-9]{64}$")
ID = re.compile(r"^[A-Za-z0-9_-]{1,120}$")
_EVIDENCE_FIELDS = ("version", "shop_id", "asset_id", "job_id", "source_sha256",
                    "transcript_sha256", "model_id", "issued_at_ms", "expires_at_ms")
_DOMAIN = b"retailgrowth.feature7.asr.v1\n"

class Feature7AudioEvidenceDenied(ValueError):
    pass

def _deny_if(condition, reason):
    if condition:
        raise Feature7AudioEvidenceDenied(reason)

def review_signed_audio_transcript(*, receipt, shop_id, campaign_id,
                                   audio_asset_id, creative_plan_sha256,
                                   original_audio_sha256, audio_duration_seconds,
                                   expected_script, evidence_key, now_ms):
    """Verify F7 HMAC AND original WAV byte identity before reviewing words.

    Returns review-only word evidence. Current F7 MP4/video receipts are refused,
    not silently repurposed as a synthesized narration's WAV transcript.
    """
    _deny_if(not isinstance(receipt, dict) or type(evidence_key) is not bytes or
             len(evidence_key) < 32 or type(now_ms) is not int or now_ms < 0 or
             not all(isinstance(s, str) and SHA.fullmatch(s) for s in
                     (creative_plan_sha256, original_audio_sha256)) or
             not isinstance(audio_duration_seconds, (float, int)) or
             isinstance(audio_duration_seconds, bool) or
             not math.isfinite(audio_duration_seconds) or
             not 0.2 <= audio_duration_seconds <= 65,
             "Trusted server evidence and original WAV required")
    _deny_if(receipt.get("version") != "feature7_signed_faster_whisper_asr_v1" or
             receipt.get("source_media_kind") != "audio/wav" or
             receipt.get("shop_id") != shop_id or
             receipt.get("campaign_id") != campaign_id or
             receipt.get("creative_plan_sha256") != creative_plan_sha256 or
             receipt.get("asset_id") != audio_asset_id or
             receipt.get("source_sha256") != original_audio_sha256 or
             receipt.get("original_media_sha256") != original_audio_sha256 or
             receipt.get("source_duration_seconds") != audio_duration_seconds or
             receipt.get("model_id") != "faster_whisper_small_cpu_int8" or
             receipt.get("local_cpu_inference_invoked") is not True or
             receipt.get("no_remote_model_calls") is not True or
             receipt.get("transcription_status") != "real_local_cpu_decoder_output" or
             receipt.get("approved") is not False or
             receipt.get("renderable") is not False or
             receipt.get("customer_publishable") is not False,
             "F7 original-audio binding or real CPU provenance missing")
    evidence = receipt.get("evidence")
    _deny_if(not isinstance(evidence, dict) or
             set(evidence) != set(_EVIDENCE_FIELDS) | {"mac"} or
             evidence.get("version") != "feature7_asr_evidence_v1" or
             not all(isinstance(evidence.get(k), str) and ID.fullmatch(evidence[k])
                     for k in ("shop_id", "asset_id", "job_id", "model_id")) or
             not all(isinstance(evidence.get(k), str) and SHA.fullmatch(evidence[k])
                     for k in ("source_sha256", "transcript_sha256", "mac")) or
             type(evidence.get("issued_at_ms")) is not int or
             type(evidence.get("expires_at_ms")) is not int or
             evidence["issued_at_ms"] < 0 or
             not 0 < evidence["expires_at_ms"]-evidence["issued_at_ms"] <= 600000 or
             not evidence["issued_at_ms"]-30000 <= now_ms <= evidence["expires_at_ms"],
             "Invalid/expired Feature7 signed evidence")
    _deny_if(any(evidence[k] != receipt[k] for k in
                 ("shop_id", "asset_id", "source_sha256", "transcript_sha256", "model_id")),
             "Feature7 evidence scope mismatch")
    words = receipt.get("words")
    _deny_if(not isinstance(words, list) or not 1 <= len(words) <= 600,
             "No bounded actual Feature7 word data")
    canonical = []
    previous_end = 0
    for item in words:
        _deny_if(not isinstance(item, dict) or
                 set(item) != {"word", "startMs", "endMs"} or
                 type(item.get("word")) is not str or
                 not 1 <= len(item["word"].strip()) <= 80 or
                 type(item.get("startMs")) is not int or
                 type(item.get("endMs")) is not int or
                 not previous_end <= item["startMs"] < item["endMs"] <=
                 round(audio_duration_seconds * 1000) + 1,
                 "Invalid or invented F7 word alignment")
        canonical.append({"word": item["word"], "startMs": item["startMs"],
                          "endMs": item["endMs"]})
        previous_end = item["endMs"]
    digest = sha256(json.dumps(canonical, ensure_ascii=False,
                                separators=(",", ":")).encode("utf-8")).hexdigest()
    _deny_if(receipt.get("transcript_sha256") != digest or
             evidence["transcript_sha256"] != digest,
             "F7 transcript changed after signing")
    payload = {k: evidence[k] for k in _EVIDENCE_FIELDS}
    expected_mac = hmac.digest(evidence_key, _DOMAIN + json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), "sha256")
    _deny_if(not hmac.compare_digest(expected_mac.hex(), evidence["mac"]),
             "F7 signature mismatch")
    # F7 currently has no actual token confidence field. NEVER fabricate it.
    normalized = [{"word": x["word"], "start": x["startMs"]/1000,
                   "end": x["endMs"]/1000, "confidence": None} for x in canonical]
    transcript = {"schema": "retailgrowth.feature7-stt-words.v1",
                  "shop_id": shop_id, "campaign_id": campaign_id,
                  "creative_plan_sha256": creative_plan_sha256,
                  "original_audio_sha256": original_audio_sha256,
                  "provider": "faster-whisper",
                  "model_version": receipt.get("model_revision"),
                  "worker_verified": True, "words": normalized}
    try:
        quality = consume_feature7_stt(
            shop_id=shop_id, campaign_id=campaign_id,
            source_sha256=creative_plan_sha256,
            original_audio_sha256=original_audio_sha256,
            expected_script=expected_script, transcript=transcript,
            audio_duration_seconds=audio_duration_seconds)
    except VoiceQualityDenied as exc:
        raise Feature7AudioEvidenceDenied("Signed STT content invalid") from exc
    return {**quality, "evidence_mac_verified": True,
            "audio_asset_id": audio_asset_id,
            "source_media_kind": "audio/wav",
            "confidence_available": False,
            "phoneme_accuracy_verified": False,
            "independent_word_alignment_accepted": False,
            "human_listen_required": True, "publish_approved": False}
