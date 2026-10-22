#!/usr/bin/env python3
"""Reproducible offline FFmpeg wall-time, output and *estimated* compute cost.

Uses synthetic assets through the actual RetailGrowthAI render.py CLI. No cloud
access, customer data, external stock media or built-in Azure pricing guesses.
Run: python -m ops.benchmark --profile worker --repeats 3
Supply both per-second USD prices for a hypothetical estimate.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "frontend/src/features/campaigns/fixtures/sample-campaign.json"
GENERATOR = ROOT / "video-engine/generate_test_assets.py"
RENDER = ROOT / "video-engine/render.py"


def compute_cost(seconds, *, vcpus, memory_gb, cpu_second_usd, gb_second_usd):
    values = (seconds, vcpus, memory_gb, cpu_second_usd, gb_second_usd)
    if any(not isinstance(n, (float, int)) or isinstance(n, bool) or not math.isfinite(n)
           or n < 0 for n in values) or vcpus <= 0 or memory_gb <= 0:
        raise ValueError("cost inputs must be finite, nonnegative, positive resources")
    return seconds * (vcpus * cpu_second_usd + memory_gb * gb_second_usd)


def inspect_mp4(path, width, height):
    raw = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        text=True, timeout=30)
    data = json.loads(raw)
    streams = data["streams"]
    video = [stream for stream in streams if stream["codec_type"] == "video"]
    audio = [stream for stream in streams if stream["codec_type"] == "audio"]
    duration = float(data["format"]["duration"])
    if (len(video) != 1 or len(audio) != 1 or video[0]["codec_name"] != "h264"
            or audio[0]["codec_name"] != "aac"
            or (video[0]["width"], video[0]["height"]) != (width, height)
            or not 29.88 <= duration <= 30.12):
        raise ValueError("output failed 30s H.264/AAC portrait validation")
    return {"seconds": round(duration, 3), "bytes": path.stat().st_size}


def run_benchmark(*, profile, repeats, vcpus, memory_gb, cpu_second_usd=None,
                  gb_second_usd=None):
    if profile not in ("ci", "worker") or type(repeats) is not int or not 1 <= repeats <= 10:
        raise ValueError("expected profile ci/worker and 1-10 repeats")
    if (cpu_second_usd is None) != (gb_second_usd is None):
        raise ValueError("specify both CPU and memory rates, or neither")
    if not 0 < vcpus <= 64 or not 0 < memory_gb <= 256:
        raise ValueError("invalid modeled worker resources")
    if cpu_second_usd is not None:
        compute_cost(0, vcpus=vcpus, memory_gb=memory_gb,
                     cpu_second_usd=cpu_second_usd, gb_second_usd=gb_second_usd)
    width, height, fps, preset = (360, 640, 15, "ultrafast") if profile == "ci" else (
        1080, 1920, 24, "veryfast")
    measurements = []
    with tempfile.TemporaryDirectory(prefix="retailgrowth-benchmark-") as tmp:
        assets = Path(tmp) / "assets"
        subprocess.run([sys.executable, str(GENERATOR), "--campaign", str(CAMPAIGN),
                        "--out-dir", str(assets)],
                       check=True, capture_output=True, text=True, timeout=120)
        for index in range(repeats):
            mp4 = Path(tmp) / f"reel-{index}.mp4"
            cmd = [sys.executable, str(RENDER),
                   "--campaign", str(assets / "campaign-with-ci-audio.json"),
                   "--manifest", str(assets / "manifest.json"),
                   "--asset-root", str(assets), "--day-index", "1",
                   "--output", str(mp4), "--width", str(width), "--height", str(height),
                   "--fps", str(fps), "--preset", preset, "--allow-test-media"]
            start = time.perf_counter()
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=900)
            elapsed = time.perf_counter() - start
            probe = inspect_mp4(mp4, width, height)
            measurements.append({"wall_seconds": round(elapsed, 3), **probe})
    wall = sorted(item["wall_seconds"] for item in measurements)
    p95 = wall[math.ceil(0.95 * len(wall)) - 1]
    result = {
        "profile": profile, "synthetic_only": True, "cloud_measured": False,
        "resolution": f"{width}x{height}", "fps": fps, "preset": preset,
        "repeats": repeats, "median_wall_seconds": round(statistics.median(wall), 3),
        "p95_wall_seconds": round(p95, 3), "results": measurements,
        "modeled_vcpus": vcpus, "modeled_memory_gb": memory_gb,
        "estimated_usd_per_1000": None,
        "exclusions": ["storage", "network", "queue", "requests", "idle/startup",
                       "AI inference", "retry overhead", "free grants", "taxes"],
    }
    if cpu_second_usd is not None:
        result["estimated_usd_per_1000"] = round(
            1000 * compute_cost(result["median_wall_seconds"], vcpus=vcpus,
                                memory_gb=memory_gb,
                                cpu_second_usd=cpu_second_usd,
                                gb_second_usd=gb_second_usd), 4)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("ci", "worker"), default="ci")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--vcpus", type=float, default=2)
    parser.add_argument("--memory-gb", type=float, default=4)
    parser.add_argument("--cpu-second-usd", type=float)
    parser.add_argument("--gb-second-usd", type=float)
    args = parser.parse_args()
    try:
        report = run_benchmark(profile=args.profile, repeats=args.repeats,
                               vcpus=args.vcpus, memory_gb=args.memory_gb,
                               cpu_second_usd=args.cpu_second_usd,
                               gb_second_usd=args.gb_second_usd)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print("FFmpeg benchmark failed: " + type(exc).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
