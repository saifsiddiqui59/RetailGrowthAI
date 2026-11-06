"""REAL offline Faster-Whisper/CTranslate2 CPU inference for Feature #7.

Uses the actual upstream SYSTRAN/faster-whisper WhisperModel API (MIT).
Does not implement an ASR model. No download, provider call, GPU or generated
transcript fixture is allowed in this program. Worker must provision an approved
local CTranslate2 checkpoint and dependency wheels separately; release needs
independent human-reference WER and word alignment tests.

Run only by trusted private-media worker after verifying tenant rights, media
SHA, and FFmpeg audio extraction. Outputs bounded WhisperX-shaped JSON for the
EXISTING transcript_adapter.mjs; empty/no-word audio fails closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import time
try:
    import resource  # Unix process RSS; unavailable on Windows local development
except ImportError:
    resource = None

_MODEL_FILES = ("config.json", "model.bin", "tokenizer.json")
_APPROVED_MODEL_REVISION = "536b0662742c02347bc0e980a01041f333bce120"
_SHA = re.compile(r"^[a-f0-9]{64}$")
_LANG = re.compile(r"^[a-z]{2,3}$")
_MAX_WORDS = 3000
_MAX_FILE_BYTES = 2 * 1024 * 1024


class LocalFasterWhisperError(ValueError):
    pass


def _check(ok: bool, reason: str) -> None:
    if not ok:
        raise LocalFasterWhisperError(reason)


def _regular_file(path: Path, *, max_size: int | None = None) -> None:
    st = path.lstat()
    _check(stat.S_ISREG(st.st_mode) and not path.is_symlink()
           and st.st_size > 0 and
           (max_size is None or st.st_size <= max_size),
           "Untrusted, empty or excessive ASR file")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while part := source.read(1024 * 1024):
            digest.update(part)
    return digest.hexdigest()


def validate_local_model(model_dir: str, manifest_path: str) -> dict:
    """Require operator-reviewed exact file hashes; never resolve HF model IDs."""
    model = Path(model_dir)
    manifest = Path(manifest_path)
    _check(model.is_absolute() and manifest.is_absolute(),
           "Absolute local model and manifest required")
    _check(model.is_dir() and not model.is_symlink(),
           "Preapproved local model directory unavailable")
    _regular_file(manifest, max_size=64 * 1024)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    _check(isinstance(data, dict) and
           data.get("version") == "feature7_faster_whisper_model_manifest_v1" and
           data.get("commercial_rights_reviewed") is True and
           data.get("model_project") == "Systran/faster-whisper-small" and
           isinstance(data.get("model_revision"), str) and
           data["model_revision"] == _APPROVED_MODEL_REVISION and
           isinstance(data.get("files"), dict),
           "Operator-reviewed pinned model provenance required")
    hashes = data["files"]
    _check(set(hashes) >= set(_MODEL_FILES) and len(hashes) <= 8,
           "Incomplete or excessive approved model file inventory")
    for name, expected in hashes.items():
        _check(re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", name) is not None and
               isinstance(expected, str) and _SHA.fullmatch(expected) is not None,
               "Malformed local model file/hash")
        file_path = model / name
        _regular_file(file_path, max_size=1024 * 1024 * 1024)
        _check(_sha256_file(file_path) == expected,
               "Pinned local model weights/tokenizer integrity mismatch")
    return {"model_project": data["model_project"],
            "model_revision": data["model_revision"],
            "model_bin_sha256": hashes["model.bin"]}


def normalize_actual_words(segments, *, audio_duration: float) -> list[dict]:
    """Validate ACTUAL decoder word output; never interpolate missing timing."""
    _check(math.isfinite(audio_duration) and 0.5 <= audio_duration <= 600,
           "Invalid independently probed audio duration")
    normalized: list[dict] = []
    prior_end = 0.0
    for segment in segments:
        words = getattr(segment, "words", None)
        _check(words is not None, "Decoder omitted actual word timestamps")
        for word in words:
            text = getattr(word, "word", None)
            start = getattr(word, "start", None)
            end = getattr(word, "end", None)
            _check(isinstance(text, str) and 0 < len(text.strip()) <= 80 and
                   isinstance(start, (float, int)) and
                   isinstance(end, (float, int)) and
                   math.isfinite(start) and math.isfinite(end) and
                   start >= 0 and end > start and
                   start >= prior_end - 0.05 and
                   end <= audio_duration + 0.001,
                   "ASR produced invalid/overlapping/missing word timing")
            start_ms, end_ms = round(start * 1000), round(end * 1000)
            _check(end_ms > start_ms, "Word timestamp precision invalid")
            normalized.append({"word": text.strip(),
                               "start": start_ms / 1000,
                               "end": end_ms / 1000})
            _check(len(normalized) <= _MAX_WORDS,
                   "Unbounded generated word transcript")
            prior_end = end
    _check(len(normalized) > 0, "No verified model words: do not invent speech")
    return normalized


def infer_audio(*, wav_path: str, model_dir: str, manifest_path: str,
                output_path: str, audio_duration: float,
                language: str | None = None,
                threads: int = 2) -> dict:
    _check(os.environ.get("HF_HUB_OFFLINE") == "1" and
           os.environ.get("TRANSFORMERS_OFFLINE") == "1" and
           os.environ.get("CUDA_VISIBLE_DEVICES") == "",
           "Offline/CPU-only worker policy missing")
    _check(isinstance(threads, int) and 1 <= threads <= 4,
           "Invalid CPU worker concurrency")
    _check(language is None or
           (_LANG.fullmatch(language) is not None and
            language in ("en", "hi", "mr")),
           "Only reviewed ASR language codes are accepted")
    source, output = Path(wav_path), Path(output_path)
    _check(source.is_absolute() and output.is_absolute() and
           source.resolve() != output.resolve(),
           "Trusted source WAV and separate output required")
    _regular_file(source, max_size=32 * 1024 * 1024)
    _check(source.suffix.lower() == ".wav", "Only private 16 kHz WAV input")
    # Actual SHA-256 of original private, locally staged audio. No transcript
    # produced by a replaced source may be counted in real CPU benchmarks.
    input_sha = _sha256_file(source)
    provenance = validate_local_model(model_dir, manifest_path)
    # This is actual upstream code, not a simulated transcription engine.
    # Local *absolute* model path + local_files_only=True prevents downloads.
    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise LocalFasterWhisperError(
            "Install pinned reviewed faster-whisper and CTranslate2 wheels") from error
    started = time.perf_counter()
    initial_rss = (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                   if resource is not None else None)
    model = WhisperModel(str(Path(model_dir).resolve()),
                         device="cpu", compute_type="int8",
                         cpu_threads=threads, num_workers=1,
                         local_files_only=True)
    stream, info = model.transcribe(str(source), task="transcribe",
                                   language=language, beam_size=5,
                                   word_timestamps=True, vad_filter=False,
                                   condition_on_previous_text=False)
    words = normalize_actual_words(stream, audio_duration=audio_duration)
    decode_seconds = max(0.0, time.perf_counter() - started)
    peak_rss = (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                if resource is not None else None)
    # Linux reports KiB; macOS bytes. On Windows return null, not a guess.
    rss_unit = 1 if sys.platform == 'darwin' else 1024
    peak_rss_bytes = int(peak_rss * rss_unit) if peak_rss is not None else None
    memory_baseline_bytes = (int(initial_rss * rss_unit)
                             if initial_rss is not None else None)
    _check(_sha256_file(source) == input_sha,
           "Original staged WAV mutated during CPU inference")
    _check(validate_local_model(model_dir, manifest_path) == provenance,
           "ASR checkpoint changed during inference")
    reported_language = getattr(info, "language", None)
    _check(isinstance(reported_language, str) and
           _LANG.fullmatch(reported_language) is not None,
           "ASR returned an invalid language")
    _check(reported_language in ("en", "hi", "mr"),
           "Auto-detected language is not approved for this worker")
    _check(language is None or reported_language == language,
           "Detected language differs from approved source language")
    result = {
        "version": "feature7_faster_whisper_cpu_transcript_v1",
        "engine": "SYSTRAN/faster-whisper",
        "model_project": provenance["model_project"],
        "model_revision": provenance["model_revision"],
        "model_bin_sha256": provenance["model_bin_sha256"],
        "language": reported_language,
        "source_audio_duration_seconds": audio_duration,
        "verified_input_sha256": input_sha,
        "actual_decode_wall_seconds": round(decode_seconds, 3),
        "actual_decode_realtime_factor": round(decode_seconds/audio_duration, 4),
        "process_peak_rss_bytes": peak_rss_bytes,
        "process_baseline_peak_rss_bytes": memory_baseline_bytes,
        "peak_rss_is_process_high_watermark": True,
        "word_timestamps_from_actual_model": True,
        "word_accuracy_benchmarked": False,
        "speech_rights_checked_by_this_process": False,
        "commercial_quality_approved": False,
        "approved": False, "renderable": False,
        "segments": [{"words": words}]
    }
    encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    _check(len(encoded.encode("utf-8")) <= _MAX_FILE_BYTES,
           "Excessive speech recognition output")
    _check(output.parent.is_dir() and not output.exists(),
           "ASR output must be a new private file")
    with output.open("x", encoding="utf-8") as file:
        os.chmod(output, 0o600)
        file.write(encoded)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Feature7 offline real Faster-Whisper CPU")
    parser.add_argument("--wav", required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--model-manifest", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--duration", required=True, type=float)
    parser.add_argument("--language", choices=("auto", "en", "hi", "mr"), default="auto")
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    try:
        report = infer_audio(
            wav_path=args.wav, model_dir=args.model_dir,
            manifest_path=args.model_manifest, output_path=args.output_json,
            audio_duration=args.duration,
            language=None if args.language == "auto" else args.language,
            threads=args.threads)
        # Safe metadata only: do not log private retailer transcript.
        print(json.dumps({"status": "decoded_real_cpu_model",
                          "word_count": len(report["segments"][0]["words"]),
                          "approved": False}))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print("Feature7 real ASR not accepted: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
