#!/usr/bin/env python3
"""Reproducible, offline 30s synthetic Reel benchmark; never measures Azure.

Generates original color cards and a sine tone, invokes the *real* renderer,
samples Linux /proc process-tree RSS/CPU and records a local FFmpeg binary
inventory. Default preset/fps reflect renderer defaults; CI overrides both.
"""
import argparse
import ast
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "frontend/src/features/campaigns/fixtures/sample-campaign.json"
RENDERER = ROOT / "video-engine/render.py"
GENERATOR = ROOT / "video-engine/generate_test_assets.py"
HOST_SECONDS = 20 * 60
LEASE_SECONDS = 25 * 60
FFMPEG_CAP_SECONDS = 780
NON_FFMPEG_RESERVE_SECONDS = HOST_SECONDS - FFMPEG_CAP_SECONDS
SAMPLE_SECONDS = 0.15


class BenchmarkError(ValueError):
    pass


def _command(binary, *args):
    try:
        return subprocess.run([binary, *args], check=True, text=True,
                              capture_output=True, timeout=20).stdout
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise BenchmarkError(f"Required local binary check failed ({Path(binary).name})") from exc


def audit_binary(name):
    resolved = shutil.which(name)
    if resolved is None:
        raise BenchmarkError(f"Required binary not found: {name}")
    path = Path(resolved).resolve(strict=True)
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    version_output = _command(str(path), "-version")
    version = version_output.splitlines()[0]
    header = path.open("rb").read(20)
    elf_linux_x64 = (header[:4] == b"\x7fELF" and header[4] == 2
                     and header[5] == 1 and header[18:20] == b"\x3e\x00")
    result = {
        "binary": name, "resolved_path": str(path), "sha256": digest.hexdigest(),
        "bytes": path.stat().st_size, "version": version,
        "linux_x86_64_elf": elf_linux_x64,
        "packaged_static_binary_verified": False,
        "third_party_notices_verified": False,
    }
    if name == "ffmpeg":
        license_text = _command(str(path), "-L").lower()
        config = version_output.lower()
        encoders = _command(str(path), "-encoders")
        filters = _command(str(path), "-filters")
        result.update({
            "gpl_enabled": "--enable-gpl" in config,
            "nonfree_enabled": "--enable-nonfree" in config,
            "declared_license_family": (
                "GPL" if "--enable-gpl" in config else
                "LGPL" if "lesser general public license" in license_text else "review required"
            ),
            "has_libx264_encoder": "libx264" in encoders,
            "has_aac_encoder": " aac " in encoders,
            "has_drawtext": "drawtext" in filters,
            "has_xfade": "xfade" in filters,
            "redistribution_cleared": False,
        })
        if result["nonfree_enabled"]:
            raise BenchmarkError("FFmpeg was built with --enable-nonfree; stop and obtain legal review")
        if not all(result[k] for k in ("has_libx264_encoder", "has_aac_encoder",
                                       "has_drawtext", "has_xfade")):
            raise BenchmarkError("FFmpeg lacks a required renderer codec/filter")
    return result


def assert_source_ffmpeg_cap():
    """Prevent the benchmark from silently auditing a stale timeout assumption."""
    tree = ast.parse(RENDERER.read_text(encoding="utf-8"))
    matching = [
        kw.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess" and node.func.attr == "run"
        for kw in node.keywords
        if kw.arg == "timeout" and isinstance(kw.value, ast.Constant)
    ]
    if matching != [FFMPEG_CAP_SECONDS]:
        raise BenchmarkError("Renderer subprocess timeout diverges from 780-second budget")
    return True


def budget_assessment(render_seconds, measured_peak_rss_bytes=None, memory_limit_mib=None):
    if not math.isfinite(render_seconds) or render_seconds < 0:
        raise BenchmarkError("Invalid elapsed time")
    return {
        "host_timeout_seconds": HOST_SECONDS,
        "claim_lease_seconds": LEASE_SECONDS,
        "ffmpeg_subprocess_cap_seconds": FFMPEG_CAP_SECONDS,
        "reserved_non_ffmpeg_seconds": NON_FFMPEG_RESERVE_SECONDS,
        "claim_lease_exceeds_host_by_seconds": LEASE_SECONDS - HOST_SECONDS,
        "observed_render_seconds": round(render_seconds, 3),
        "measured_render_within_ffmpeg_cap": render_seconds < FFMPEG_CAP_SECONDS,
        "host_time_remaining_after_render_seconds": round(HOST_SECONDS - render_seconds, 3),
        "preserves_full_420s_non_ffmpeg_reserve": render_seconds <= FFMPEG_CAP_SECONDS,
        "sampled_memory_within_specified_limit": (
            None if measured_peak_rss_bytes is None or memory_limit_mib is None
            else measured_peak_rss_bytes <= memory_limit_mib * 1024 * 1024
        ),
        "azure_runtime_verified": False,
    }


def estimate_compute_cost(seconds, count, vcpus, memory_gib, vcpu_usd_per_second,
                          gib_usd_per_second):
    """Illustrative *user-supplied rates* only; never assume current Azure prices."""
    params = (seconds, count, vcpus, memory_gib, vcpu_usd_per_second,
              gib_usd_per_second)
    if any(not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0 for x in params):
        raise BenchmarkError("Invalid billing parameter")
    if count < 1 or vcpus <= 0 or memory_gib <= 0:
        raise BenchmarkError("Positive count/vCPU/memory required")
    unit = seconds * (vcpus * vcpu_usd_per_second + memory_gib * gib_usd_per_second)
    return {
        "unit_estimate_usd": round(unit, 8), "batch_estimate_usd": round(unit * count, 6),
        "assumed_vcpus": vcpus, "assumed_memory_gib": memory_gib,
        "assumed_vcpu_usd_per_second": vcpu_usd_per_second,
        "assumed_gib_usd_per_second": gib_usd_per_second, "renders": count,
        "excludes": ["storage", "queue", "network_egress", "AI", "retries",
                     "cold_start", "other_worker_overhead", "provider_billing_rules"],
        "rate_source": "caller-supplied, NOT fetched or validated Azure price",
    }


def _process_tree(pid):
    """Best-effort Linux sampling only; no claims about missed subinterval spikes."""
    pending, seen = [pid], set()
    while pending:
        child = pending.pop()
        if child in seen:
            continue
        seen.add(child)
        try:
            children = Path(f"/proc/{child}/task/{child}/children").read_text().split()
            pending.extend(int(c) for c in children)
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass
    return seen


def _sample_tree(pid):
    rss, cpu = 0, {}
    ticks = os.sysconf("SC_CLK_TCK")
    for member in _process_tree(pid):
        try:
            status = Path(f"/proc/{member}/status").read_text()
            for line in status.splitlines():
                if line.startswith("VmRSS:"):
                    rss += int(line.split()[1]) * 1024
                    break
            stat = Path(f"/proc/{member}/stat").read_text()
            # Strip comm (it may contain spaces), then index from original field 3.
            parts = stat.rsplit(") ", 1)[1].split()
            cpu[member] = (int(parts[11]) + int(parts[12])) / ticks
        except (FileNotFoundError, PermissionError, ProcessLookupError, IndexError, ValueError):
            pass
    return rss, cpu


def run_render(command, timeout=HOST_SECONDS):
    start = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True)
    peak_rss, cpu_seen, samples = 0, {}, 0
    try:
        while process.poll() is None:
            if sys.platform.startswith("linux") and Path("/proc").exists():
                rss, cpu = _sample_tree(process.pid)
                peak_rss = max(peak_rss, rss)
                cpu_seen.update(cpu)
                samples += 1
            if time.monotonic() - start >= timeout:
                process.kill()
                process.communicate()
                raise BenchmarkError("Renderer exceeded host timeout")
            time.sleep(SAMPLE_SECONDS)
        out, err = process.communicate(timeout=30)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()
    elapsed = time.monotonic() - start
    if process.returncode != 0:
        raise BenchmarkError("Renderer failed: " + err[-1800:])
    try:
        metadata = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise BenchmarkError("Renderer returned no JSON probe result") from exc
    return {
        "wall_seconds": round(elapsed, 3),
        "sampled_peak_process_tree_rss_bytes": peak_rss if samples else None,
        "sampled_process_tree_cpu_seconds_lower_bound": (
            round(sum(cpu_seen.values()), 3) if samples else None
        ),
        "samples": samples, "sampling_interval_seconds": SAMPLE_SECONDS,
        "sampling_limitations": (
            "Linux /proc point samples only; short-lived peaks/processes may be missed."
            if samples else "Memory/CPU tree metrics unavailable on this runner."
        ),
        "output": {k: metadata.get(k) for k in
                   ("duration_seconds", "width", "height", "size_bytes",
                    "video_codec", "audio_codec", "video_pix_fmt")},
    }


def benchmark(args):
    assert_source_ffmpeg_cap()
    binaries = [audit_binary("ffmpeg"), audit_binary("ffprobe")]
    with tempfile.TemporaryDirectory(prefix="retailgrowth-bench-") as directory:
        work = Path(directory)
        assets = work / "assets"
        asset_start = time.monotonic()
        subprocess.run([sys.executable, str(GENERATOR), "--campaign", str(CAMPAIGN),
                        "--out-dir", str(assets)], check=True, capture_output=True,
                       text=True, timeout=120)
        asset_elapsed = time.monotonic() - asset_start
        command = [
            sys.executable, str(RENDERER), "--campaign",
            str(assets / "campaign-with-ci-audio.json"),
            "--manifest", str(assets / "manifest.json"),
            "--asset-root", str(assets), "--day-index", "1",
            "--output", str(work / "reel.mp4"),
            "--width", str(args.width), "--height", str(args.height),
            "--fps", str(args.fps), "--preset", args.preset,
            "--allow-test-media",
        ]
        render = run_render(command)
    elapsed = render["wall_seconds"]
    result = {
        "kind": "OFFLINE_SYNTHETIC_RENDER_BENCHMARK_NOT_AZURE",
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count_reported": os.cpu_count(),
        "profile": {"width": args.width, "height": args.height, "fps": args.fps,
                    "preset": args.preset, "duration_seconds": 30},
        "binary_inventory": binaries,
        "asset_generation_seconds_excluded_from_render": round(asset_elapsed, 3),
        "render_measurement": render,
        "safety_budget": budget_assessment(
            elapsed, render["sampled_peak_process_tree_rss_bytes"],
            args.memory_limit_mib,
        ),
        "measured_on_azure": False,
        "provenance": "Three original synthetic FFmpeg color cards and an original 440Hz test tone",
        "commercial_media_rights_verified": False,
        "packaged_binary_licenses_verified": False,
    }
    if args.vcpu_rate is not None:
        if None in (args.memory_rate, args.allocated_vcpus, args.allocated_memory_gib):
            raise BenchmarkError("Provide BOTH rates and BOTH resource allocations for cost modeling")
        result["cost_model"] = estimate_compute_cost(
            elapsed, args.renders, args.allocated_vcpus, args.allocated_memory_gib,
            args.vcpu_rate, args.memory_rate)
    if not result["safety_budget"]["preserves_full_420s_non_ffmpeg_reserve"]:
        raise BenchmarkError("Observed synthetic render consumed the reserved host overhead margin")
    if result["safety_budget"]["sampled_memory_within_specified_limit"] is False:
        raise BenchmarkError("Sampled RSS exceeds configured memory limit")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", help="Write JSON evidence (no media files persisted)")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--preset", default="veryfast")
    parser.add_argument("--memory-limit-mib", type=int)
    parser.add_argument("--vcpu-rate", type=float, help="Caller-provided USD per vCPU-second")
    parser.add_argument("--memory-rate", type=float, help="Caller-provided USD per GiB-second")
    parser.add_argument("--allocated-vcpus", type=float)
    parser.add_argument("--allocated-memory-gib", type=float)
    parser.add_argument("--renders", type=int, default=1000)
    args = parser.parse_args()
    if args.width <= 0 or args.height <= 0 or args.width * 16 != args.height * 9:
        parser.error("Expected a positive 9:16 render profile")
    if args.memory_limit_mib is not None and args.memory_limit_mib <= 0:
        parser.error("memory-limit-mib must be positive")
    try:
        report = benchmark(args)
    except (BenchmarkError, OSError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, ValueError) as exc:
        print("BENCHMARK FAILED: " + str(exc), file=sys.stderr)
        return 2
    serial = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        file = Path(args.report)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(serial + "\n", encoding="utf-8")
    print(serial)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
