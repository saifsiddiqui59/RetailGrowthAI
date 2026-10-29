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
import math
import os
import re
import sys
import wave

class VoiceQualityDenied(ValueError):
    pass

def _words(text):
    return [w.casefold() for w in re.findall(r"[\w']+",text,flags=re.UNICODE)]

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
                         original_audio_sha256,expected_script,transcript):
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
            len(_words(word))!=1 or type(start) not in (float,int) or
            type(end) not in (float,int) or type(conf) not in (float,int) or
            not all(math.isfinite(x) for x in (start,end,conf)) or
            not previous<=start<=end<=65 or not 0<=conf<=1):
            raise VoiceQualityDenied("Untrusted or reordered Feature7 timestamps")
        previous=end
        tokens.append({"word":_words(word)[0],"start":round(float(start),3),
                       "end":round(float(end),3),"confidence":float(conf)})
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
            "transcribed_words":heard,"expected_words":expected,
            "issues":issues,
            "transcript_matches_script":not issues,
            "pronunciation_verified":False,
            "publish_approved":False}

def run_openpronounce_lazy(*,original_wav,expected_script,lang="en",enabled=False):
    """Uses real upstream OpenPronounce.compare_audio_with_text directly.

    Heavy model worker must be preloaded separately. OFF by default, English
    only, network reference gTTS DISALLOWED; no backend downloads in CI.
    """
    if enabled is not True or os.getenv("RETAIL_F2_OPENPRONOUNCE_ENABLED")!="true":
        raise VoiceQualityDenied("Optional OpenPronounce quality worker OFF")
    if lang!="en" or os.getenv("OPENPRONOUNCE_TTS") not in ("piper","kokoro") or \
       os.getenv("HF_HUB_OFFLINE")!="1" or \
       os.getenv("RETAIL_F2_REFERENCE_AUDIO_PRELOADED")!="true":
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
    problems=[]
    for item in result["differences"].get("errors",[])[:80]:
        if not isinstance(item,dict):continue
        word=item.get("word")
        if not isinstance(word,str) or not word or len(word)>80:continue
        c=item.get("confidence")
        problems.append({"problem":"POSSIBLE_PRONUNCIATION_MISMATCH",
                         "word":word,"script_position":item.get("position"),
                         "expected_ipa":str(item.get("expected") or "")[:100],
                         "heard_ipa":str(item.get("actual") or "")[:100],
                         "confidence":c if isinstance(c,(float,int)) and 0<=c<=1 else None,
                         "manual_review_required":True,
                         "evidence":"OpenPronounce phoneme heuristic; false positives common"})
    return {"schema":"retailgrowth.feature2-openpronounce-review.v1",
            "audio_sha256":stats["sha256"],
            "provider":"Halleck45/OpenPronounce","version":"0.3.0",
            "lang":"en","heuristic_score":result.get("score"),
            "issues":problems,"review_required":True,
            "human_pronunciation_verified":False,"publish_approved":False}
