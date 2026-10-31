"""Offline, fail-closed CPU ASR operator preflight (NO inference, no download).

Use on the isolated worker AFTER legal/licensing and model provisioning.
Measures local manifest integrity, runtime version and CTranslate2 CPU int8
support. A successful preflight is NOT a passed WER/phoneme benchmark, tenant
authorization, or proof of SaaS distribution rights.
"""
from __future__ import annotations

import argparse
from importlib import metadata
import json
import os
from pathlib import Path
import sys

from faster_whisper_cpu import validate_local_model, LocalFasterWhisperError

_APPROVED_PACKAGE = "1.2.1"


def assert_offline_cpu_worker():
    if any((
        os.environ.get("HF_HUB_OFFLINE") != "1",
        os.environ.get("TRANSFORMERS_OFFLINE") != "1",
        os.environ.get("CUDA_VISIBLE_DEVICES") != "",
        os.environ.get("FEATURE7_GPU_ENABLED", "0") != "0",
        os.environ.get("FEATURE7_ALLOW_PAID_INFERENCE", "0") != "0",
        os.environ.get("FEATURE7_NETWORK_MODELS", "0") != "0"
    )):
        raise LocalFasterWhisperError("Unapproved offline CPU inference environment")


def preflight_real_cpu_model(model_dir: str, manifest_path: str) -> dict:
    """Inspect real local approved weights, versions and CPU INT8 capability."""
    assert_offline_cpu_worker()
    provenance = validate_local_model(model_dir, manifest_path)
    try:
        faster_version = metadata.version("faster-whisper")
        ct_version = metadata.version("ctranslate2")
    except metadata.PackageNotFoundError as exc:
        raise LocalFasterWhisperError("Pinned real Python AI dependencies absent") from exc
    if faster_version != _APPROVED_PACKAGE:
        raise LocalFasterWhisperError("Unapproved Faster-Whisper package version")
    try:
        import ctranslate2
        supported = ctranslate2.get_supported_compute_types("cpu")
    except (ImportError, RuntimeError, OSError) as exc:
        raise LocalFasterWhisperError("Local CTranslate2 CPU runtime unavailable") from exc
    if not isinstance(supported, (set, list, tuple)) or "int8" not in supported:
        raise LocalFasterWhisperError("Worker CPU lacks approved int8 support")
    # Refuse to call this benchmarked until actual human-reference recordings
    # run through the real decoder and the human-verified WER/word clock test.
    return {
        "schema": "feature7_offline_cpu_asr_preflight_v1",
        "faster_whisper": faster_version,
        "ctranslate2": ct_version,
        "model_project": provenance["model_project"],
        "model_revision": provenance["model_revision"],
        "model_bin_sha256": provenance["model_bin_sha256"],
        "local_manifest_sha256_verified": True,
        "offline_cpu_int8_supported": True,
        "model_weights_actual_inference_executed": False,
        "human_reference_wer_passed": False,
        "word_timing_quality_verified": False,
        "commercial_rights_independently_verified": False,
        "customer_publishable": False
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Feature7 local CPU model preflight")
    p.add_argument("--model-dir", required=True)
    p.add_argument("--model-manifest", required=True)
    args = p.parse_args()
    try:
        report = preflight_real_cpu_model(args.model_dir, args.model_manifest)
    except (LocalFasterWhisperError, ValueError, OSError) as exc:
        print("Feature7 CPU preflight denied: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
