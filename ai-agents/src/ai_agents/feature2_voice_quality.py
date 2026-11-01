"""Feature2 independent audio/Feature7 STT evidence and optional OpenPronounce.

Feature7 owns Faster-Whisper inference. This consumer NEVER transcribes a file,
makes up word timestamps, or upgrades ASR match into good pronunciation.
OpenPronounce is actual third-party implementation, imported only after an
operator preloads its licensed offline reference models in a bounded worker.
"""
from __future__ import annotations
from array import array
from difflib import SequenceMatcher
from hashlib import sha256
from io import BytesIO
import hmac
import json
import math
import os
import re
import sys
import wave
import unicodedata

class VoiceQualityDenied(ValueError):
    pass


def _unsafe_audio_display(value):
    """Reject bidi/zero-width spoofing and active markup in review text.

    Preserve Indic vowel marks and U+200C/U+200D native joining. This
    source-only filter does not certify an ASR token as real spoken audio.
    """
    if type(value) is not str:
        return True
    for index,ch in enumerate(value):
        if ch in ("\u200c","\u200d"):
            # Preserve a legitimate Devanagari virama conjunct, but prevent
            # hidden text differences in an otherwise ordinary brand/word.
            following=value[index+1] if index+1<len(value) else ""
            if (index>0 and value[index-1]=="\u094d" and
                "\u0900"<=following<="\u097f" and
                unicodedata.category(following).startswith("L")):
                continue
            return True
        if ch in "<>" or unicodedata.category(ch) in ("Cc","Cf","Zl","Zp"):
            return True
    return False


def _words(text):
    """Unicode-grapheme-aware candidates; NEVER a pronunciation certificate.

    Python's default \\w drops some Devanagari vowel marks. Retain combining
    marks inside words; preserve apostrophes, not punctuation.
    """
    if not isinstance(text, str):
        return []
    tokens, chars = [], []
    for ch in unicodedata.normalize("NFC", text):
        category = unicodedata.category(ch)
        if (category[0] in ("L", "N") or
            (category[0] == "M" and chars) or
            (ch in ("\u200c","\u200d") and chars)):
            chars.append(ch)
        elif ch in ("'", "’") and chars:
            chars.append("'")
        else:
            if chars:
                word = "".join(chars).strip("'")
                if word:
                    tokens.append(word.casefold())
                chars = []
    if chars:
        word = "".join(chars).strip("'")
        if word:
            tokens.append(word.casefold())
    return tokens


def pcm_stats(wav_original):
    """Actual PCM16 mono evidence, not fake speech/pronunciation diagnosis."""
    if type(wav_original) is not bytes or not 128<=len(wav_original)<=20_000_000:
        raise VoiceQualityDenied("Bounded original WAV required")
    try:
        with wave.open(BytesIO(wav_original),"rb") as w:
            if (w.getnchannels()!=1 or w.getsampwidth()!=2 or
                w.getcomptype()!="NONE" or not 16000<=w.getframerate()<=48000):
                raise VoiceQualityDenied("Only mono PCM16 WAV analysis")
            n=w.getnframes();hz=w.getframerate()
            if not 0.2<=n/hz<=65:raise VoiceQualityDenied("Audio length invalid")
            raw=w.readframes(n)
            if len(raw)!=n*2:raise VoiceQualityDenied("Truncated audio")
    except (EOFError, OSError,ValueError,wave.Error) as exc:
        raise VoiceQualityDenied("Invalid speech WAV") from exc
    pcm=array("h")
    pcm.frombytes(raw)
    if sys.byteorder!="little":pcm.byteswap()
    peak=max(abs(v) for v in pcm)
    rms=math.sqrt(sum((v/32768)**2 for v in pcm)/len(pcm))
    clipping=sum(1 for s in pcm if abs(s)>=32760)/len(pcm)
    # Non-overlapping windows of 100 ms RMS, NO claimed sentence alignment.
    window=max(1,hz//10)
    quiet=[]
    for i in range(0,len(pcm),window):
        chunk=pcm[i:i+window]
        if len(chunk)==0:continue
        level=math.sqrt(sum((v/32768)**2 for v in chunk)/len(chunk))
        quiet.append(level<0.008)
    max_quiet=0;current=0
    for q in quiet:
        current=current+1 if q else 0
        max_quiet=max(max_quiet,current)
    return {"sha256":sha256(wav_original).hexdigest(),
            "duration_seconds":round(n/hz,3),"sample_rate_hz":hz,
            "peak_amplitude":round(peak/32768,6),
            "rms":round(rms,6),"clip_fraction":round(clipping,6),
            "max_quiet_seconds":round(max_quiet*0.1,2),
            "audio_clipped":clipping>0.001,
            "too_quiet":rms<0.015,
            "too_loud":rms>0.4,
            "excessive_silence":max_quiet>=12,
            "words_heard_verified":False}

def consume_feature7_stt(*,shop_id,campaign_id,source_sha256,
                         original_audio_sha256,expected_script,transcript,
                         audio_duration_seconds=None):
    """Fail closed unless F7 signed-worker output binds original same-shop bytes.

    Contract proposed to Feature7; this alone is NOT an F7 implementation.
    An untrusted browser could forge the transcript, so backend must provide
    current signed/F7 worker output and authoritative plan and media readers.
    """
    if (not isinstance(transcript,dict) or
        transcript.get("schema")!="retailgrowth.feature7-stt-words.v1" or
        transcript.get("shop_id")!=shop_id or
        transcript.get("campaign_id")!=campaign_id or
        transcript.get("creative_plan_sha256")!=source_sha256 or
        transcript.get("original_audio_sha256")!=original_audio_sha256 or
        transcript.get("provider")!="faster-whisper" or
        transcript.get("model_version") in (None,"") or
        transcript.get("worker_verified") is not True or
        type(expected_script) is not str or not 1<=len(expected_script)<=1800):
        raise VoiceQualityDenied("No trusted Feature7 transcription evidence")
    if audio_duration_seconds is not None and (
        type(audio_duration_seconds) not in (int,float) or
        not math.isfinite(audio_duration_seconds) or
        not 0.2 <= audio_duration_seconds <= 65):
        raise VoiceQualityDenied("Independent original WAV duration missing")
    rows=transcript.get("words")
    if not isinstance(rows,list) or not 1<=len(rows)<=600:
        raise VoiceQualityDenied("No bounded word timestamps from Feature7")
    tokens=[]
    previous=0.
    for row in rows:
        if not isinstance(row,dict) or set(row)!={"word","start","end","confidence"}:
            raise VoiceQualityDenied("Invalid Feature7 word record")
        word=row["word"];start=row["start"];end=row["end"];conf=row["confidence"]
        if (type(word) is not str or not 1<=len(word)<=80 or
            _unsafe_audio_display(word) or
            len(_words(word))!=1 or type(start) not in (float,int) or
            type(end) not in (float,int) or
            (conf is not None and type(conf) not in (float,int)) or
            not all(math.isfinite(x) for x in (start,end)) or
            (conf is not None and (not math.isfinite(conf) or not 0<=conf<=1)) or
            not previous<=start<end<=65 or
            (audio_duration_seconds is not None and
             end>audio_duration_seconds+0.001)):
            raise VoiceQualityDenied("Untrusted or reordered Feature7 timestamps")
        previous=end
        tokens.append({"word":_words(word)[0],"start":round(float(start),3),
                       "end":round(float(end),3),"confidence":float(conf) if conf is not None else None})
    expected=_words(expected_script)
    heard=[x["word"] for x in tokens]
    issues=[]
    for action,i,j,k,l in SequenceMatcher(a=expected,b=heard,autojunk=False).get_opcodes():
        if action=="equal":continue
        for idx in range(i,j):
            evidence=tokens[k] if k<len(tokens) else None
            issues.append({"problem":"MISSING_OR_SUBSTITUTED_WORD" if action=="replace" else "MISSING_WORD",
                           "word":expected[idx],"script_word_index":idx,
                           "audio_start_seconds":evidence["start"] if evidence else None,
                           "confidence":evidence["confidence"] if evidence else None,
                           "evidence":"Feature7 ASR text mismatch; may be ASR error",
                           "manual_review_required":True})
        if action in ("replace","insert"):
            for h in tokens[k:l]:
                issues.append({"problem":"UNEXPECTED_OR_SUBSTITUTED_WORD",
                               "word":h["word"],"script_word_index":i,
                               "audio_start_seconds":h["start"],
                               "confidence":h["confidence"],
                               "evidence":"Feature7 ASR extra/substituted candidate",
                               "manual_review_required":True})
    return {"schema":"retailgrowth.feature2-stt-review.v1",
            "model_version":transcript["model_version"],
            "audio_sha256":original_audio_sha256,
            "word_timing_verified_by_external_worker":True,
            "token_confidence_available":all(x["confidence"] is not None for x in tokens),
            "human_listen_required":True,
            "transcribed_words":heard,"expected_words":expected,
            "issues":issues,
            "transcript_matches_script":not issues,
            "pronunciation_verified":False,
            "publish_approved":False}

def project_offline_openpronounce_review(*,audio_sha256,result):
    """Validate genuine worker schema into safe, *non-authoritative* hints.

    Must only be called with model evidence under a trusted operator boundary.
    The existence of this projection alone proves NO checkpoint was loaded.
    """
    if (type(audio_sha256) is not str or not re.fullmatch(r"[a-f0-9]{64}",audio_sha256)
        or type(result) is not dict or
        type(result.get("score")) not in (int,float) or
        not math.isfinite(result["score"]) or
        not 0<=result["score"]<=100 or
        type(result.get("differences")) is not dict):
        raise VoiceQualityDenied("Untrusted phoneme scoring")
    errors=result["differences"].get("errors")
    if type(errors) is not list or len(errors)>80:
        raise VoiceQualityDenied("Unbounded pronunciation differences")
    problems=[]
    for item in errors:
        if type(item) is not dict:
            raise VoiceQualityDenied("Invalid phoneme difference")
        word=item.get("word")
        index=item.get("position")
        ipa_expected=item.get("expected")
        ipa_actual="" if item.get("actual") is None else item.get("actual")
        confidence=item.get("confidence")
        if (type(word) is not str or not 1<=len(word)<=80 or
            _unsafe_audio_display(word) or
            type(index) is not int or not 0<=index<=600 or
            type(ipa_expected) is not str or len(ipa_expected)>100 or
            type(ipa_actual) is not str or len(ipa_actual)>100 or
            _unsafe_audio_display(ipa_expected+ipa_actual) or
            (confidence is not None and
             (type(confidence) not in (int,float) or
              not math.isfinite(confidence) or
              not 0<=confidence<=1))):
            raise VoiceQualityDenied("Invalid unapproved phoneme confidence")
        problems.append({
            "problem":"POSSIBLE_PRONUNCIATION_MISMATCH",
            "word":word,"script_position":index,
            "expected_ipa":ipa_expected,"heard_ipa":ipa_actual,
            "confidence":confidence,
            "manual_review_required":True,
            "evidence":"OpenPronounce heuristic; possible false positives",
        })
    return {"schema":"retailgrowth.feature2-openpronounce-review.v1",
            "audio_sha256":audio_sha256,
            "provider":"Halleck45/OpenPronounce","version":"0.3.0",
            "lang":"en","heuristic_score":result["score"],
            "issues":problems,"review_required":True,
            "human_pronunciation_verified":False,"publish_approved":False}


def run_openpronounce_lazy(*,original_wav,expected_script,lang="en",enabled=False):
    """Uses real upstream OpenPronounce.compare_audio_with_text directly.

    Heavy model worker must be preloaded separately. OFF by default, English
    only, network reference gTTS DISALLOWED; no backend downloads in CI.
    """
    if enabled is not True or os.getenv("RETAIL_F2_OPENPRONOUNCE_ENABLED")!="true":
        raise VoiceQualityDenied("Optional OpenPronounce quality worker OFF")
    if (lang!="en" or os.getenv("OPENPRONOUNCE_TTS") not in ("piper","kokoro") or
        os.getenv("HF_HUB_OFFLINE")!="1" or
        os.getenv("TRANSFORMERS_OFFLINE")!="1" or
        os.getenv("OPENPRONOUNCE_DEVICE")!="cpu" or
        os.getenv("OPENPRONOUNCE_PHONEME_MODEL")=="off" or
        os.getenv("RETAIL_F2_REFERENCE_AUDIO_PRELOADED")!="true"):
        raise VoiceQualityDenied("Offline calibrated English reference model not approved")
    if type(expected_script) is not str or not 1<=len(expected_script)<=1800:
        raise VoiceQualityDenied("Actual reference script required")
    stats=pcm_stats(original_wav)
    try:
        import soundfile as sf
        import librosa
        from openpronounce import compare_audio_with_text  # genuine upstream scoring
        audio,sr=sf.read(BytesIO(original_wav),dtype="float32")
        mono=audio if sr==16000 else librosa.resample(audio,orig_sr=sr,target_sr=16000)
        result=compare_audio_with_text(mono,expected_script,lang="en")
        if not isinstance(result,dict) or not isinstance(result.get("differences"),dict):
            raise VoiceQualityDenied("Untrusted phoneme scoring")
    except (ImportError, OSError,ValueError) as exc:
        raise VoiceQualityDenied("Offline OpenPronounce model unavailable") from exc
    return project_offline_openpronounce_review(
        audio_sha256=stats["sha256"],result=result)


# Security-sensitive Feature7 HMAC/WAV adapter kept alongside the existing
# Feature2 reviewer to stay within the coordinator-owned Functions ZIP limit.
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
                                   expected_script, evidence_key, now_ms,
                                   expected_job_id=None, assert_current_source=None):
    """Verify F7 HMAC AND original WAV byte identity before reviewing words.

    Returns review-only word evidence. Current F7 MP4/video receipts are refused,
    not silently repurposed as a synthesized narration's WAV transcript.
    """
    _deny_if(not isinstance(receipt, dict) or type(evidence_key) is not bytes or
             len(evidence_key) < 32 or type(now_ms) is not int or now_ms < 0 or
             type(expected_job_id) is not str or not ID.fullmatch(expected_job_id) or
             not callable(assert_current_source) or
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
             not isinstance(receipt.get("model_revision"),str) or
             not re.fullmatch("[a-f0-9]{40}",receipt["model_revision"]) or
             not isinstance(receipt.get("model_bin_sha256"),str) or
             not SHA.fullmatch(receipt["model_bin_sha256"]) or
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
    _deny_if(evidence["job_id"] != expected_job_id,
             "F7 transcript job does not match authoritative audio job")
    # F7's current signed payload omits campaign, creative revision and MIME.
    # Require an *independently trusted backend* read binding these values to
    # original private media and the F7 source job before trusting the MAC.
    scope=(shop_id,campaign_id,audio_asset_id,creative_plan_sha256,
           original_audio_sha256,expected_job_id)
    _deny_if(assert_current_source(*scope) is not True,
             "Current private audio source/creative/job provenance denied")
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
                 _unsafe_audio_display(item["word"]) or
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
    _deny_if(assert_current_source(*scope) is not True,
             "Registered private source changed during F7 review")
    return {**quality, "evidence_mac_verified": True,
            "trusted_current_source_verified": True,
            "source_job_id":expected_job_id,
            "audio_asset_id": audio_asset_id,
            "source_media_kind": "audio/wav",
            "confidence_available": False,
            "phoneme_accuracy_verified": False,
            "independent_word_alignment_accepted": False,
            "human_listen_required": True, "publish_approved": False}


def _word_edit_totals(expected,heard):
    """Exact word-level Levenshtein counts (not SequenceMatcher heuristics).

    Tie-breaking is deterministic: diagonal substitution, deletion, insertion.
    Time bounded at 600x600 tokens, independent of audio and model loading.
    """
    if (type(expected) is not list or type(heard) is not list or
        not 1<=len(expected)<=600 or not 1<=len(heard)<=600 or
        any(type(w) is not str or not 1<=len(w)<=80 for w in expected+heard)):
        raise VoiceQualityDenied("Bounded word sequences required for WER")
    prev=[(j,0,0,j) for j in range(len(heard)+1)]
    for i,reference in enumerate(expected,1):
        curr=[(i,0,i,0)]
        for j,actual in enumerate(heard,1):
            unchanged=reference==actual
            diag=prev[j-1]
            substitutions=(diag[0]+(0 if unchanged else 1),
                           diag[1]+(0 if unchanged else 1),diag[2],diag[3])
            dele=prev[j]
            deletion=(dele[0]+1,dele[1],dele[2]+1,dele[3])
            ins=curr[-1]
            insertion=(ins[0]+1,ins[1],ins[2],ins[3]+1)
            # tuple costs incorporate fixed tie priorities; the cost alone
            # determines WER (not the arbitrary S/D/I operation split).
            curr.append(min((substitutions,deletion,insertion),
                            key=lambda x:(x[0],0 if x is substitutions else
                                          1 if x is deletion else 2)))
        prev=curr
    errors,subs,deletes,inserts=prev[-1]
    return {"substitutions":subs,"deletions":deletes,"insertions":inserts,
            "edit_distance":errors,
            "reference_word_count":len(expected),
            "heard_word_count":len(heard),
            "word_error_rate":round(errors/len(expected),5),
            "word_accuracy_is_not_pronunciation":True}


def compare_signed_feature7_word_error_rate(*,receipt,shop_id,campaign_id,
        audio_asset_id,creative_plan_sha256,original_audio_sha256,
        audio_duration_seconds,expected_script,evidence_key,now_ms,
        expected_job_id,assert_current_source,
        human_transcript=None,verify_signed_human_transcript=None):
    """Signed original-WAV ASR WER; optional independent signed human WER.

    Human reference must be cryptographically bound by a trusted backend to
    current shop/campaign/asset/plan/WAV/job + exact UTF-8 digest. No browser
    checkbox, self-proclaimed speaker or ASR receipt can impersonate a human
    reviewer. It never certifies audio inference, voice quality or publishing.
    """
    quality=review_signed_audio_transcript(
        receipt=receipt,shop_id=shop_id,campaign_id=campaign_id,
        audio_asset_id=audio_asset_id,
        creative_plan_sha256=creative_plan_sha256,
        original_audio_sha256=original_audio_sha256,
        audio_duration_seconds=audio_duration_seconds,
        expected_script=expected_script,evidence_key=evidence_key,
        now_ms=now_ms,expected_job_id=expected_job_id,
        assert_current_source=assert_current_source)
    expected=quality["expected_words"]
    actual=quality["transcribed_words"]
    asr=_word_edit_totals(expected,actual)
    human=None;manual_agreement=None
    if human_transcript is not None:
        if (type(human_transcript) is not str or
            not 1<=len(human_transcript)<=1800 or
            _unsafe_audio_display(human_transcript) or
            not callable(verify_signed_human_transcript)):
            raise VoiceQualityDenied("Independently signed human transcript required")
        human_words=_words(human_transcript)
        if not 1<=len(human_words)<=600:
            raise VoiceQualityDenied("Human transcript must contain bounded speech words")
        digest=sha256(human_transcript.encode("utf-8")).hexdigest()
        binding=(shop_id,campaign_id,audio_asset_id,creative_plan_sha256,
                 original_audio_sha256,expected_job_id,digest)
        if verify_signed_human_transcript(*binding) is not True or \
           assert_current_source(*binding[:-1]) is not True:
            raise VoiceQualityDenied("Human reference revoked or not independently signed")
        human=_word_edit_totals(expected,human_words)
        manual_agreement=_word_edit_totals(human_words,actual)
        if verify_signed_human_transcript(*binding) is not True or \
           assert_current_source(*binding[:-1]) is not True:
            raise VoiceQualityDenied("Signed human reference changed during comparison")
    elif verify_signed_human_transcript is not None:
        raise VoiceQualityDenied("Human evidence callback without transcript")
    return {"schema":"retailgrowth.feature2-verified-word-error-review.v1",
            "shop_id":shop_id,"campaign_id":campaign_id,
            "audio_asset_id":audio_asset_id,
            "original_audio_sha256":original_audio_sha256,
            "creative_plan_sha256":creative_plan_sha256,
            "source_job_id":expected_job_id,
            "feature7_hmac_and_current_source_verified":True,
            "feature7_asr_word_error":asr,
            "human_signed_transcript_available":human is not None,
            "human_transcript_vs_script_error":human,
            "feature7_asr_vs_human_error":manual_agreement,
            "human_accuracy_not_assumed":True,
            "real_worker_execution_independently_observed":False,
            "source_only_metric_not_acoustic_certification":True,
            "pronunciation_verified":False,"can_publish":False}
