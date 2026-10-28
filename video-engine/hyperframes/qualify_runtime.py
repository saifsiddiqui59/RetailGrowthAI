#!/usr/bin/env python3
"""F4-08 no-network, source-only HyperFrames/Chromium runtime preflight.

Qualifies a *local* Linux runner; this cannot certify Azure Functions package
contents, HTTP ingress, licensed media, billing, cold start or a GPU.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
NODE_MINIMUM = (22, 12, 0)
PRODUCER_VERSION = "0.8.185"


def node_version(raw):
    if type(raw) is not str:
        raise ValueError("Node version must be textual")
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:\+.*)?", raw.strip())
    if match is None:
        raise ValueError("Invalid Node version")
    version = tuple(map(int, match.groups()))
    if version < NODE_MINIMUM:
        raise ValueError("Puppeteer and HyperFrames require Node >=22.12.0")
    return version


def chromium_binary(cache_root):
    root = Path(cache_root)
    if not root.is_dir():
        return None
    candidates = sorted(root.glob(
        "chrome-headless-shell/linux-*/chrome-headless-shell-linux64/chrome-headless-shell"
    ))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def local_runtime_report(*, root=ROOT, cache_root=None):
    """Fail closed when local renderer dependencies are unavailable."""
    root = Path(root)
    node = shutil.which("node")
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not node or not ffmpeg or not ffprobe:
        raise ValueError("Node, FFmpeg and FFprobe must exist on PATH")
    version_raw = subprocess.run(
        [node, "--version"], capture_output=True, text=True, timeout=5,
        check=True,
    ).stdout.strip()
    version = node_version(version_raw)
    package = root / "node_modules/@hyperframes/producer/package.json"
    if not package.is_file() or json.loads(package.read_text()).get("version") != PRODUCER_VERSION:
        raise ValueError("Pinned HyperFrames producer package must be installed")
    if cache_root is None:
        cache_root = os.environ.get("PUPPETEER_CACHE_DIR") or (
            Path.home() / ".cache/puppeteer"
        )
    chrome = chromium_binary(cache_root)
    if chrome is None:
        raise ValueError("Offline Chrome Headless Shell binary not installed")
    cgroup_bytes = None
    limit = Path("/sys/fs/cgroup/memory.max")
    if limit.is_file():
        try:
            raw = limit.read_text().strip()
            if raw != "max":
                cgroup_bytes = int(raw)
        except (ValueError, OSError):
            pass
    return {
        "kind": "SOURCE_ONLY_GITHUB_OR_LOCAL_BROWSER_RUNTIME_NOT_AZURE",
        "node_version": ".".join(map(str, version)),
        "node_minimum": ".".join(map(str, NODE_MINIMUM)),
        "hyperframes_producer_version": PRODUCER_VERSION,
        "chromium_headless_shell_present": True,
        "ffmpeg_present": True,
        "ffprobe_present": True,
        "platform": platform.platform(),
        "cgroup_memory_limit_bytes_if_reported": cgroup_bytes,
        "azure_functions_packaging_verified": False,
        "azure_cold_start_verified": False,
        "azure_billing_verified": False,
        "commercial_media_rights_verified": False,
        "transitive_license_notices_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Feature4 local render dependency gate")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    report = Path(args.report)
    if report.suffix != ".json":
        parser.error("Report must be JSON")
    try:
        record = local_runtime_report()
    except (ValueError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        parser.exit(2, "Feature4 runtime preflight rejected: " + str(exc) + "\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print("PASS: local Node/Chromium/FFmpeg source-runtime preflight; Azure unverified")


if __name__ == "__main__":
    main()
