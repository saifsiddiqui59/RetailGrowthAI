#!/usr/bin/env python3
"""Offline F4-14 aggregate: immutable actual 15/30/60 MP4s + CPU receipts.

NO render, GPU, Azure, upload, credentials or customer approval is performed.
A claimed Git checkout SHA is NOT authenticated GitHub Actions provenance.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess

from feature4_export_matrix import MatrixEvidenceError, verify_export_matrix

HEAD_RX = re.compile(r"^[0-9a-f]{40}$")
KINDS = (15, 30, 60)
MAX_REPORT_BYTES = 64 * 1024


class CpuMatrixError(ValueError):
    pass


def _read_report(path):
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or not 20 <= before.st_size <= MAX_REPORT_BYTES:
                raise CpuMatrixError("Missing or unsafe bounded CPU receipt")
            data = stream.read(MAX_REPORT_BYTES + 1)
            after = os.fstat(stream.fileno())
            current = os.lstat(path)
            if (len(data) != before.st_size or
                    (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) !=
                    (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) or
                    not stat.S_ISREG(current.st_mode) or
                    (current.st_dev, current.st_ino, current.st_size) !=
                    (after.st_dev, after.st_ino, after.st_size)):
                raise CpuMatrixError("CPU receipt changed or was replaced")
            obj = json.loads(data.decode("utf-8"))
            if type(obj) is not dict:
                raise CpuMatrixError("CPU receipt must be one JSON object")
            return obj
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CpuMatrixError("CPU receipt unavailable, unsafe or malformed") from exc


def _positive_number(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def aggregate_cpu_matrix(manifest, root, *, expected_head):
    """Review three recorded local benchmarks; do not synthesize media or rates."""
    if type(expected_head) is not str or not HEAD_RX.fullmatch(expected_head):
        raise CpuMatrixError("Expected one exact git checkout SHA")
    if (type(manifest) is not dict or set(manifest) != {"schema", "source_commit", "renders"}
            or manifest["schema"] != "feature4_cpu_matrix_inputs_v1"
            or manifest["source_commit"] != expected_head):
        raise CpuMatrixError("Unexpected or cross-commit CPU matrix inputs")
    rows = manifest["renders"]
    if type(rows) is not list or len(rows) != 3:
        raise CpuMatrixError("Three source-linked 15/30/60 receipts required")
    media_rows = []
    receipts = {}
    occupied = set()
    for row in rows:
        if type(row) is not dict or set(row) != {"seconds", "path", "sha256", "benchmark"}:
            raise CpuMatrixError("Invalid CPU matrix input row")
        duration = row["seconds"]
        if type(duration) is not int or duration not in KINDS or duration in receipts:
            raise CpuMatrixError("Missing or repeated duration")
        report_name = row["benchmark"]
        if (type(report_name) is not str or len(report_name) > 120 or
                not report_name.endswith(".json") or report_name in ("", ".", "..")
                or "/" in report_name or "\\" in report_name or
                report_name == row["path"] or report_name in occupied):
            raise CpuMatrixError("CPU receipts must be distinct local JSON basenames")
        occupied.add(report_name)
        media_rows.append({key: row[key] for key in ("seconds", "path", "sha256")})
        receipts[duration] = report_name

    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise CpuMatrixError("Expected private existing media/benchmark directory")
    try:
        media = verify_export_matrix(
            {"schema": "feature4_export_matrix_inputs_v1",
             "source_commit": expected_head, "renders": media_rows},
            root, expected_head=expected_head)
    except MatrixEvidenceError as exc:
        raise CpuMatrixError("Actual encoded MP4 profile / immutable SHA verification failed") from exc

    results = []
    for item in media["renders"]:
        duration = item["seconds"]
        receipt = _read_report(root / receipts[duration])
        if (receipt.get("kind") != "OFFLINE_SYNTHETIC_HYPERFRAMES_CPU_BENCHMARK_NOT_AZURE"
                or receipt.get("source_commit_claim") != expected_head
                or receipt.get("output_sha256") != item["sha256"]
                or receipt.get("output_bytes") != item["bytes"]
                or receipt.get("output_hash_type") != "SHA256_STABLE_LOCAL_REGULAR_FILE_ONLY"
                or receipt.get("duration_seconds") != duration
                or (receipt.get("width"), receipt.get("height"), receipt.get("fps")) !=
                   (1080, 1920, 24)
                or receipt.get("cloud_or_gpu_inference") is not False
                or receipt.get("measured_on_azure_functions") is not False
                or receipt.get("commercial_visual_quality_accepted") is not False
                or receipt.get("azure_runtime_memory_verified") is not False
                or receipt.get("azure_cost_inr") is not None
                or not _positive_number(receipt.get("wall_seconds"))
                or not _positive_number(receipt.get("max_sampled_process_tree_rss_bytes"))
                or not _positive_number(receipt.get("max_sampled_cpu_seconds_lower_bound"))
                or not _positive_number(receipt.get("sampling_interval_seconds"))
                or type(receipt.get("samples")) is not int or receipt["samples"] < 1
                or type(receipt.get("max_observed_process_count")) is not int
                or receipt["max_observed_process_count"] < 1):
            raise CpuMatrixError("Benchmark receipt does not match exact encoded profile, source or safe cost scope")
        results.append({
            "seconds": duration, "original_mp4_sha256": item["sha256"],
            "original_mp4_bytes": item["bytes"],
            "wall_seconds": receipt["wall_seconds"],
            "sampled_peak_rss_bytes_lower_bound": receipt["max_sampled_process_tree_rss_bytes"],
            "sampled_cpu_seconds_lower_bound": receipt["max_sampled_cpu_seconds_lower_bound"],
            "sample_count": receipt["samples"],
        })
    results.sort(key=lambda item: item["seconds"])
    return {
        "schema": "feature4_cpu_15_30_60_offline_observations_v1",
        "status": "THREE_ENCODED_LENGTHS_CPU_OBSERVED_NOT_CLOUD_QUALIFIED",
        "source_commit_claim": expected_head,
        "code_commit_attested_by_ci": False,
        "renders": results,
        "max_measured_wall_seconds": max(x["wall_seconds"] for x in results),
        "max_sampled_rss_bytes_lower_bound": max(
            x["sampled_peak_rss_bytes_lower_bound"] for x in results),
        "cloud_budget_accepted": False,
        "actual_azure_memory_verified": False,
        "commercial_release_eligible": False,
        "human_visual_approval": False,
        "missing_short_peak_and_child_memory_risk": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    manifest_path, output = Path(args.manifest), Path(args.report)
    if (output.exists() or output.is_symlink() or output.suffix.lower() != ".json"
            or not output.parent.is_dir() or output.parent.is_symlink()):
        raise CpuMatrixError("CPU matrix output must be fresh, private and local")
    inputs = _read_report(manifest_path)
    head = subprocess.check_output(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=Path(__file__).resolve().parents[1], text=True, timeout=5).strip()
    result = aggregate_cpu_matrix(inputs, args.source_root, expected_head=head)
    with output.open("x", encoding="utf-8") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print(result["status"] + " — NOT cloud or retailer approval")


if __name__ == "__main__":
    main()
