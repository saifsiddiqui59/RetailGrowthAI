#!/usr/bin/env python3
"""Build a separate, source-reviewed Feature4 CPU Azure Functions artifact.

This script does NOT deploy, create Azure queues, change flags, call any cloud
provider or include secrets. Existing v1 Functions package.py is unchanged.
Use --check for fast PR CI; --build requires locally present, independently
verified Python 3.11, Node22, FFmpeg, and pinned Puppeteer shell dependencies.

Python dependencies must be installed into a private directory with:
  python3.11 -m pip install --requirement azure-functions/campaign-api/requirements.txt \
      --target <isolated-python-packages>
Node dependencies require npm ci in video-engine/hyperframes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "azure-functions" / "campaign-api"
ISOLATED = ROOT / "azure-functions" / "feature4-cpu-worker"
VIDEO = ROOT / "video-engine"
MAX_ARCHIVE = 1024 * 1024 * 1024
MAX_FILES = 100_000

# Keep this deliberately narrower than the general v1 backend source.
SERVICE_MODULES = (
    "admin_store.py", "tenant_store.py", "queue_adapter.py",
    "private_media.py", "recovery_runtime.py",
)
ISOLATED_MODULES = ("function_app.py", "cpu_backend.py")
STATIC_FILES = ("render.mjs", "package.json", "package-lock.json")


def sources():
    """Return flattened importable Python + reviewed Node sources; no v1 ZIP."""
    mapping = {
        "host.json": SERVICE / "host.json",
        "requirements.txt": SERVICE / "requirements.txt",
    }
    for name in SERVICE_MODULES:
        mapping[name] = SERVICE / name
    for name in ISOLATED_MODULES:
        mapping[name] = ISOLATED / name
    # The native engine contains pure approved assembly, not the v1 renderer.
    for path in sorted(VIDEO.glob("*.py")):
        if path.name.startswith("test_"):
            continue
        if path.name in mapping:
            raise ValueError("Duplicate Python module name in separate F4 worker: " + path.name)
        mapping[path.name] = path
    for name in STATIC_FILES:
        mapping["hyperframes/" + name] = VIDEO / "hyperframes" / name
    for rel, file in mapping.items():
        if not file.is_file() or file.is_symlink():
            raise ValueError("Missing/unsafe Feature4 package source: " + rel)
        # A source directory link can redirect a reviewed path to mutable code.
        # Check every ancestor inside the checkout before reading or packaging.
        if any(parent.is_symlink() for parent in file.parents):
            raise ValueError("Linked Feature4 package source directory: " + rel)
        if not rel or rel.startswith("/") or ".." in Path(rel).parts:
            raise ValueError("Unsafe archive member: " + rel)
    host = json.loads(mapping["host.json"].read_text(encoding="utf-8"))
    if host.get("functionTimeout") != "00:20:00":
        raise ValueError("Unreviewed Functions timeout")
    if host.get("extensions", {}).get("queues", {}).get("messageEncoding") != "none":
        raise ValueError("Queue encoding must match UUID-only messages")
    app = mapping["function_app.py"].read_text(encoding="utf-8")
    if "retail-feature4-cpu-render" not in app or "RETAIL_FEATURE4_CPU_WORKER_ENABLED" not in app:
        raise ValueError("Worker queue name/activation gate missing")
    if "retail-reel-render" in app:
        raise ValueError("F4 worker must not consume legacy v1 render queue")
    return mapping


def _assert_native_binary(binary):
    # Verify the original path before resolve(), even when the test runner
    # uses a different Python minor than the Azure 3.11 build image.
    if (not binary.is_file() or binary.is_symlink()
            or any(parent.is_symlink() for parent in binary.parents)):
        raise ValueError("Missing or linked native dependency: " + binary.name)


def _version(binary, argv, expected):
    _assert_native_binary(binary)
    try:
        message = subprocess.check_output([str(binary), *argv],
                                          text=True, stderr=subprocess.STDOUT, timeout=20)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("Native executable cannot run: " + binary.name) from exc
    if not re.search(expected, message):
        raise ValueError("Unreviewed native dependency version: " + binary.name)


def _collect_tree(root, prefix, *, omit_bin_shims=False):
    if (root.is_symlink() or any(parent.is_symlink() for parent in root.parents)
            or not root.is_dir()):
        raise ValueError("Missing or linked offline build dependency directory: " + prefix)
    listing = {}
    for file in sorted(root.rglob("*")):
        # npm ci creates node_modules/.bin symlink shims. They are never
        # executed or shipped: skip them before symlink rejection, while
        # retaining strict rejection for all included runtime dependencies.
        if omit_bin_shims and ".bin" in file.relative_to(root).parts:
            continue
        if file.is_symlink():
            raise ValueError("Symlink in F4 package: " + str(file.relative_to(root)))
        if file.is_dir():
            continue
        # FIFOs/devices/sockets can block read_bytes or inject non-file data.
        if not stat.S_ISREG(file.lstat().st_mode):
            raise ValueError("Non-regular F4 package dependency: " + str(file.relative_to(root)))
        if omit_bin_shims and ".bin" in file.relative_to(root).parts:
            continue
        rel = file.relative_to(root)
        # Reject links before resolution: internal links can otherwise hide
        # duplicate or mutable payloads inside a supposedly reviewed ZIP.
        if file.is_symlink() or any(parent.is_symlink() for parent in file.parents if parent != root and root in parent.parents):
            raise ValueError("Symlink in F4 package: " + str(rel))
        target = file.resolve(strict=True)
        if not target.is_file() or not target.is_relative_to(root.resolve(strict=True)):
            raise ValueError("External path / non-file in F4 package: " + str(rel))
        name = prefix + "/" + rel.as_posix()
        if name in listing:
            raise ValueError("Duplicate F4 runtime member: " + name)
        listing[name] = target
    return listing


def _write_member(z, archive_path, origin):
    # Reject archive traversal and Windows separators even if a caller supplies
    # a member outside the reviewed source mapping. ZIP names are POSIX paths.
    parts = archive_path.split("/")
    if (not archive_path or archive_path.startswith("/") or chr(92) in archive_path
            or any(part in ("", ".", "..") for part in parts)):
        raise ValueError("Unsafe F4 archive member: " + archive_path)
    if archive_path in z.namelist():
        raise ValueError("Duplicate F4 archive member: " + archive_path)
    # Zip deploy does not require source-tree symlink semantics. Copy a
    # regular, locally verified file and retain executable permissions.
    if not stat.S_ISREG(origin.lstat().st_mode) or origin.is_symlink():
        raise ValueError("Unsafe non-regular F4 archive source: " + archive_path)
    # Bound each input before allocating its bytes; a single oversized file
    # must not exhaust CI/worker memory before the ZIP-size guard runs.
    if origin.stat().st_size > MAX_ARCHIVE:
        raise ValueError("F4 archive source exceeds 1GB limit: " + archive_path)
    # Stream bounded chunks instead of allocating a whole native binary in RAM.
    # Re-check the count while copying to catch growth after the initial stat.
    perms = stat.S_IMODE(origin.stat().st_mode)
    info = ZipInfo(archive_path, date_time=(2026, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | (perms or 0o644)) << 16
    info.compress_type = ZIP_DEFLATED
    digest = hashlib.sha256()
    count = 0
    with origin.open("rb") as source, z.open(info, "w", force_zip64=True) as target:
        while chunk := source.read(1024 * 1024):
            count += len(chunk)
            if count > MAX_ARCHIVE:
                raise ValueError("F4 archive source exceeds 1GB limit: " + archive_path)
            digest.update(chunk)
            target.write(chunk)
    return digest.hexdigest()


def build(args):
    mapping = sources()
    # Link/source integrity is platform-independent and must fail closed
    # BEFORE the Python-minor guard, including in the Python 3.13 test suite.
    node, ffmpeg, ffprobe = (Path(x) for x in
                           (args.node, args.ffmpeg, args.ffprobe))
    for binary in (node, ffmpeg, ffprobe):
        _assert_native_binary(binary)
    if sys.version_info[:2] != (3, 11):
        raise ValueError("Only Python 3.11 supports this pinned isolated runtime build")
    _version(node, ["--version"], r"^v22\.")
    _version(ffmpeg, ["-version"], r"^ffmpeg version")
    _version(ffprobe, ["-version"], r"^ffprobe version")
    # Both formats are needed for private consumer MP4 exports.
    encoders = subprocess.check_output([str(ffmpeg), "-hide_banner", "-encoders"],
                                       text=True, timeout=20)
    if "libx264" not in encoders or not re.search(r"\baac\b", encoders):
        raise ValueError("Native worker FFmpeg codecs missing")
    filters = subprocess.check_output([str(ffmpeg), "-hide_banner", "-filters"],
                                      text=True, timeout=20)
    if "drawtext" not in filters:
        raise ValueError("Native FFmpeg has no caption renderer")
    installed = VIDEO / "hyperframes" / "node_modules"
    if not (installed / "@hyperframes" / "producer").is_dir():
        raise ValueError("Pinned HyperFrames npm ci dependencies are missing")
    if not (Path(args.python_site_packages) / "azure" / "functions").is_dir():
        raise ValueError("Python Azure Functions dependencies missing")
    cache = Path(args.puppeteer_cache)
    browsers = list(cache.glob(
        "chrome-headless-shell/*/chrome-headless-shell-linux64/chrome-headless-shell"))
    if len(browsers) != 1 or not browsers[0].is_file():
        raise ValueError("Expected one locally installed Puppeteer shell build")
    mapping.update({
        "bin/node": node, "bin/ffmpeg": ffmpeg, "bin/ffprobe": ffprobe
    })
    mapping.update(_collect_tree(installed, "hyperframes/node_modules",
                                 omit_bin_shims=True))
    mapping.update(_collect_tree(cache / "chrome-headless-shell",
                                 "puppeteer-cache/chrome-headless-shell"))
    mapping.update(_collect_tree(Path(args.python_site_packages),
                                 ".python_packages/lib/site-packages"))
    if len(mapping) > MAX_FILES:
        raise ValueError("Unbounded worker package member count")
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    checksums = {}
    if out.exists():
        raise FileExistsError("Refusing to replace existing release artifact")
    try:
        with ZipFile(out, "x") as z:
            for name, file in sorted(mapping.items()):
                checksums[name] = _write_member(z, name, file)
                if out.stat().st_size > MAX_ARCHIVE:
                    raise ValueError("F4 worker ZIP exceeds Azure 1GB package limit")
            manifest = json.dumps({
                "schema": "retailgrowth-f4-native-worker-zip-v1",
                "cpu_only": True, "gpu_allowed": False,
                "contains_secrets": False, "file_sha256": checksums,
            }, sort_keys=True, separators=(",", ":")).encode()
            z.writestr("package_manifest.json", manifest)
    except BaseException:
        # A failed package must never be mistaken for a deployable release ZIP.
        out.unlink(missing_ok=True)
        raise
    if out.stat().st_size > MAX_ARCHIVE:
        out.unlink(missing_ok=True)
        raise ValueError("F4 worker ZIP exceeds Azure 1GB package limit")
    # Close the release artifact before a later deploy/cleanup step can access it.
    with out.open("rb") as artifact:
        artifact_sha256 = hashlib.file_digest(artifact, "sha256").hexdigest()
    print(json.dumps({"artifact": str(out), "files": len(checksums),
                      "bytes": out.stat().st_size, "sha256": artifact_sha256}))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check", action="store_true")
    actions.add_argument("--build", action="store_true")
    parser.add_argument("--node")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    parser.add_argument("--python-site-packages")
    parser.add_argument("--puppeteer-cache")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    if args.check:
        listing = sources()
        print("PASS Feature4 isolated worker sources:", len(listing))
        return 0
    if any(not x for x in (
            args.node, args.ffmpeg, args.ffprobe,
            args.python_site_packages, args.puppeteer_cache, args.output)):
        parser.error("--build requires all pinned runtime locations and output")
    build(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
