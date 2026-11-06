#!/usr/bin/env python3
"""Operator-only genuine local Kokoro CPU measurement. No customer data/network.

Use from repo root:
 RETAIL_FEATURE2_KOKORO_CPU_ENABLED=true \
   uv run --project ai-agents python \
   ai-agents/test-fixtures/retailer-voice/benchmark-pinned-kokoro-cpu.py \
   --cache-dir /absolute/operator-approved/kokoro

The two files must already be downloaded/verified by the pinned-source
provisioner. No automatic model download or Azure voice fallback occurs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ai_agents.feature2_kokoro_local import (
    LocalSpeechUnavailable, run_cpu_kokoro_benchmark,
)

def main(argv=None):
    parser=argparse.ArgumentParser(
        description="Measure pinned Kokoro-82M CPU only; no audio/scripts emitted")
    parser.add_argument("--cache-dir",type=Path,required=True)
    parser.add_argument("--voice",default="af_heart",
                        choices=("af_heart","af_sarah","am_adam","am_michael",
                                 "bf_emma","bf_isabella","bm_george","bm_lewis"))
    parser.add_argument("--repeats",type=int,default=2,choices=(1,2,3))
    args=parser.parse_args(argv)
    if not args.cache_dir.is_absolute():
        parser.error("--cache-dir must be an absolute, operator-approved local path")
    lang="en-gb" if args.voice.startswith(("bf_","bm_")) else "en-us"
    try:
        stats=run_cpu_kokoro_benchmark(
            cache_dir=args.cache_dir,voice_id=args.voice,lang=lang,
            repeats=args.repeats)
    except (LocalSpeechUnavailable,OSError) as exc:
        # No secrets, paths, transcript or potentially misleading partial
        # measurements enter stdout. Do not auto retry an uncertain job.
        print("Real pinned CPU benchmark unavailable; no positive proof produced",
              file=sys.stderr)
        return 2
    if stats["test_only"] or not stats["real_model_inference_verified"]:
        print("No genuine CPU inference proof",file=sys.stderr)
        return 3
    print(json.dumps(stats,sort_keys=True,separators=(",",":")))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
