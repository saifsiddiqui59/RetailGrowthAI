"""Real-speech CPU model word-error benchmark, NOT a quality self-attestation.

Input is a trusted WAV plus independently human-authored transcript. This
runner calls real Faster-Whisper inference; reference text is NEVER provided
as a model prompt. Does not decide whether media can be published, and a
single sample cannot qualify Indian accents or customer word alignment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unicodedata
from faster_whisper_cpu import infer_audio, LocalFasterWhisperError

def tokens(text: str) -> list[str]:
    if not isinstance(text,str) or not text.strip():
        raise LocalFasterWhisperError("Independent human reference required")
    # Hindi/Marathi combining vowel signs are part of words (\\w splits
    # several Devanagari clusters); preserve Unicode letter/mark/number runs.
    result, current = [], []
    for char in unicodedata.normalize("NFKC", text).casefold():
        if unicodedata.category(char)[0] in ("L", "M", "N"):
            current.append(char)
        elif current:
            result.append("".join(current))
            current = []
    if current:
        result.append("".join(current))
    return result

def word_error_rate(reference: str, hypothesis: str) -> dict:
    ref=tokens(reference); hypo=tokens(hypothesis)
    if not ref:
        raise LocalFasterWhisperError("Empty human reference words")
    # Standard Levenshtein word substitutions/deletions/insertions.
    earlier=list(range(len(hypo)+1))
    for i, expected in enumerate(ref,1):
        row=[i]
        for j, found in enumerate(hypo,1):
            row.append(min(earlier[j]+1,row[-1]+1,
                           earlier[j-1]+(expected!=found)))
        earlier=row
    return {
        "reference_word_count":len(ref),
        "recognized_word_count":len(hypo),
        "word_edit_distance":earlier[-1],
        "word_error_rate":round(earlier[-1]/len(ref),5)
    }

def benchmark(*,wav_path: str,expected_sha256: str,
              model_dir: str,manifest_path: str,
              reference_path: str,reference_sha256: str,
              audio_duration: float,language: str="en") -> dict:
    source=Path(wav_path);reference=Path(reference_path)
    if not source.is_file() or source.is_symlink() or \
       not reference.is_file() or reference.is_symlink():
        raise LocalFasterWhisperError("Missing real private WAV or human transcript")
    if reference.stat().st_size>64*1024 or reference.stat().st_size==0:
        raise LocalFasterWhisperError("Unbounded or missing human reference")
    if hashlib.sha256(source.read_bytes()).hexdigest()!=expected_sha256 or \
       hashlib.sha256(reference.read_bytes()).hexdigest()!=reference_sha256:
        raise LocalFasterWhisperError("Private audio/human-reference hash mismatch")
    with tempfile.TemporaryDirectory(prefix="f7-faster-wer-") as folder:
        out=Path(folder)/"model_words.json"
        generated=infer_audio(wav_path=wav_path,model_dir=model_dir,
            manifest_path=manifest_path,output_path=str(out),
            audio_duration=audio_duration,language=language)
    reference_text=reference.read_text(encoding="utf-8")
    recognized=" ".join(w["word"] for w in generated["segments"][0]["words"])
    scores=word_error_rate(reference_text,recognized)
    return {
        "version":"feature7_faster_whisper_cpu_human_reference_wer_v1",
        "model_revision":generated["model_revision"],
        "model_bin_sha256":generated["model_bin_sha256"],
        "audio_sha256":expected_sha256,
        "human_reference_sha256":reference_sha256,
        **scores,
        "engineering_target_wer_at_most_0_20_met":
            len(tokens(reference_text))>=10 and
            scores["word_error_rate"]<=.20,
        "actual_cpu_model_inference_executed":True,
        "human_reference_independent":True,
        "multi_speaker_accent_benchmark_completed":False,
        "brand_name_pronunciation_verified":False,
        "word_timing_accuracy_independently_measured":False,
        "customer_quality_accepted":False,
        "approved":False
    }

def main() -> int:
    parser=argparse.ArgumentParser()
    for key in ("wav","expected-sha256","model-dir","model-manifest",
                "reference-text-file","reference-sha256","duration"):
        parser.add_argument("--"+key,required=True)
    parser.add_argument("--language",default="en",choices=("en","hi","mr"))
    args=parser.parse_args()
    try:
        result=benchmark(wav_path=args.wav,expected_sha256=args.expected_sha256,
            model_dir=args.model_dir,manifest_path=args.model_manifest,
            reference_path=args.reference_text_file,
            reference_sha256=args.reference_sha256,
            audio_duration=float(args.duration),language=args.language)
        print(json.dumps(result,sort_keys=True))
        return 0
    except (ValueError,OSError) as error:
        print("Feature7 WER benchmark not accepted: "+str(error),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
