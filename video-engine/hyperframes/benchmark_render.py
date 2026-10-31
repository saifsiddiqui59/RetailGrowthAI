#!/usr/bin/env python3
"""Low-cost, source-only HyperFrames CPU benchmark for synthetic CI assets.

Measures the actual render.mjs invocation on a Linux runner. Sampled RSS/CPU
are lower-bound observations, not guaranteed peaks, Azure prices or capacity
claims. Never accepts arbitrary commands or tenant HTML.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import stat
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent
NODE_SCRIPT = ROOT / "render.mjs"


def parse_proc_stat(raw):
    """Parse Linux /proc/PID/stat including process names with parentheses."""
    try:
        cut = raw.rfind(") ")
        if cut < 0:
            return None
        pid = int(raw[:raw.find(" (")])
        fields = raw[cut + 2:].split()
        if len(fields) < 22:
            return None
        return (pid, int(fields[1]), int(fields[2]),
                int(fields[11]) + int(fields[12]), max(0, int(fields[21])))
    except (ValueError, IndexError):
        return None


def sample_process_group(pgid, *, proc_root=Path("/proc")):
    """Sum sampled RSS/CPU for a new private session and descendants."""
    if not proc_root.is_dir():
        return (0, 0, 0)
    records = {}
    for child in proc_root.iterdir():
        if not child.name.isdecimal():
            continue
        try:
            stat = parse_proc_stat((child / "stat").read_text())
            if stat is not None:
                records[stat[0]] = stat
        except (OSError, UnicodeError):
            continue
    active = {pid for pid, stat in records.items() if stat[2] == pgid}
    active.add(pgid)
    for _ in range(len(records)):
        extra = {pid for pid, stat in records.items() if stat[1] in active}
        if extra <= active:
            break
        active.update(extra)
    page = os.sysconf("SC_PAGE_SIZE")
    rss = sum(stat[4] * page for pid, stat in records.items() if pid in active)
    ticks = sum(stat[3] for pid, stat in records.items() if pid in active)
    return rss, ticks, len(active & records.keys())


def verified_output_sha256(path):
    """Hash exactly one stable regular render file, rejecting symlink swaps.

    The hash binds a *local synthetic benchmark receipt* to the encoded bytes
    actually left on disk; not cloud artifact custody or a rights approval.
    """
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size < 1024:
                raise ValueError("Expected nonempty regular encoded benchmark output")
            digest = hashlib.sha256()
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
            after = os.fstat(source.fileno())
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                raise ValueError("Benchmark output changed while hashing")
            # The path itself must still refer to that file, not a late swap.
            current = os.lstat(path)
            if (not stat.S_ISREG(current.st_mode) or
                    current.st_dev != after.st_dev or
                    current.st_ino != after.st_ino or
                    current.st_size != after.st_size):
                raise ValueError("Benchmark output path changed")
            return after.st_size, digest.hexdigest()
    except OSError as exc:
        raise ValueError("Benchmark output could not be safely hashed") from exc


def benchmark(project, output, report, *, timeout_seconds=420, use_npm_node22=False,
              sampling_interval=0.2):
    if type(timeout_seconds) is not int or not 20 <= timeout_seconds <= 780:
        raise ValueError("Bounded render timeout must be 20..780 seconds")
    project, output, report = Path(project), Path(output), Path(report)
    config = json.loads((project / "render-config.json").read_text())
    if (config.get("contract_version") != "rg_video_v2" or
            config.get("renderer") != "hyperframes" or
            config.get("duration_seconds") not in (15, 30, 60) or
            (config.get("width"), config.get("height")) not in ((540, 960), (1080, 1920)) or
            config.get("fps") not in (24, 30) or output.suffix != ".mp4"):
        raise ValueError("Expected an existing approved local HyperFrames composition")
    if report.suffix != ".json" or report == output:
        raise ValueError("Expected separate JSON performance evidence file")
    if output.exists() or output.is_symlink() or report.exists() or report.is_symlink():
        raise ValueError("Benchmark output and report destinations must be new")
    command = (["npm", "exec", "--yes", "--package=node@22", "--", "node"] if use_npm_node22
               else ["node"]) + [str(NODE_SCRIPT), str(project), str(output)]
    started = time.monotonic()
    samples = 0
    max_rss, max_ticks, max_processes = 0, 0, 0
    timed_out = False
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen(
            command, stdout=stdout, stderr=stderr, start_new_session=True,
            cwd=ROOT,
        )
        try:
            while process.poll() is None:
                rss, ticks, count = sample_process_group(process.pid)
                samples += 1
                max_rss = max(max_rss, rss)
                max_ticks = max(max_ticks, ticks)
                max_processes = max(max_processes, count)
                if time.monotonic() - started > timeout_seconds:
                    timed_out = True
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    break
                time.sleep(sampling_interval)
            process.wait(timeout=15)
        finally:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=15)
    if timed_out:
        raise RuntimeError("Bounded local HyperFrames render exceeded timeout")
    if process.returncode != 0 or not output.is_file():
        raise RuntimeError("Local HyperFrames render failed; inspect restricted CI job output")
    output_bytes, output_sha256 = verified_output_sha256(output)
    ticks_per_second = os.sysconf("SC_CLK_TCK")
    report_data = {
        "kind": "OFFLINE_SYNTHETIC_HYPERFRAMES_CPU_BENCHMARK_NOT_AZURE",
        "cloud_or_gpu_inference": False,
        "measured_on_azure_functions": False,
        "commercial_visual_quality_accepted": False,
        "duration_seconds": config["duration_seconds"],
        "width": config["width"],
        "height": config["height"],
        "fps": config["fps"],
        "output_bytes": output_bytes,
        "output_sha256": output_sha256,
        # Declared current Git checkout, not a signed CI provenance attestation.
        "source_commit_claim": subprocess.check_output(
            ["git", "-C", str(ROOT.parents[1]), "rev-parse", "--verify", "HEAD"],
            text=True, timeout=5).strip(),
        "output_hash_type": "SHA256_STABLE_LOCAL_REGULAR_FILE_ONLY",
        "runtime_platform": platform.platform(),
        "cpu_count_visible": os.cpu_count(),
        "wall_seconds": round(time.monotonic() - started, 3),
        "max_sampled_process_tree_rss_bytes": max_rss,
        "max_sampled_cpu_seconds_lower_bound": round(max_ticks / ticks_per_second, 3),
        "max_observed_process_count": max_processes,
        "samples": samples,
        "sampling_interval_seconds": sampling_interval,
        "sampling_limitations": (
            "Linux /proc periodic samples: short peaks, exited processes and "
            "detached Chromium/FFmpeg helpers may be missed. CPU is a sampled lower bound."
        ),
        "host_timeout_seconds_reference_only": 1200,
        "render_cap_seconds_reference_only": 780,
        "azure_cost_inr": None,
        "azure_runtime_memory_verified": False,
        "package_lock_present_in_workspace": (ROOT / "package-lock.json").is_file(),
        "package_lock_tracked_in_git": subprocess.run(
            ["git", "-C", str(ROOT.parents[1]), "ls-files", "--error-unmatch",
             "video-engine/hyperframes/package-lock.json"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
            check=False,
        ).returncode == 0,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    # Keep the benchmark receipt from overwriting another job's proof.
    with report.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report_data, indent=2, sort_keys=True) + "\n")
    print("PASS: source-only HyperFrames sampled benchmark", json.dumps({
        k: report_data[k] for k in (
            "duration_seconds", "width", "height", "wall_seconds",
            "max_sampled_process_tree_rss_bytes", "samples", "output_bytes",
        )
    }), flush=True)
    return report_data


def main():
    parser = argparse.ArgumentParser(description="Feature4 CPU benchmark; no cloud actions")
    parser.add_argument("project")
    parser.add_argument("output")
    parser.add_argument("report")
    parser.add_argument("--timeout", type=int, default=420)
    parser.add_argument("--use-npm-node22", action="store_true")
    args = parser.parse_args()
    benchmark(args.project, args.output, args.report,
              timeout_seconds=args.timeout, use_npm_node22=args.use_npm_node22)


if __name__ == "__main__":
    main()
