#!/usr/bin/env python3
"""Feature4 F4-03: bind 15/30/60 ACTUAL local MP4 evidence on a single code head.

No renderer/model/hosting runs here. This checks codec/shape/duration and exact
file bytes; a self-declared source SHA is NOT an Actions attestation, rights
grant, human visual acceptance, or proof that footage is customer-approved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from render_adapter import CreativeRenderError, verify_mp4

SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
SECONDS = (15, 30, 60)
MAX_BYTES = 80 * 1024 * 1024


class MatrixEvidenceError(ValueError):
    pass


def _stable_sha(path):
    """Before/after stat and content check of bounded regular, non-symlink file."""
    if path.is_symlink() or not path.is_file():
        raise MatrixEvidenceError("Missing or unsafe encoded MP4")
    before = path.stat()
    if not 1024 < before.st_size <= MAX_BYTES:
        raise MatrixEvidenceError("Output is empty or beyond private reviewer cap")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(part)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise MatrixEvidenceError("Encoded source mutated during hashing")
    if path.is_symlink():
        raise MatrixEvidenceError("Encoded source switched to symlink")
    return before.st_size, digest.hexdigest()


def verify_export_matrix(manifest, source_root, *, expected_head):
    if type(expected_head) is not str or not SHA.fullmatch(expected_head):
        raise MatrixEvidenceError("Expected exact checkout commit SHA")
    if type(manifest) is not dict or set(manifest) != {"schema", "source_commit", "renders"}:
        raise MatrixEvidenceError("Unexpected export matrix manifest")
    if (manifest["schema"] != "feature4_export_matrix_inputs_v1" or
            manifest["source_commit"] != expected_head):
        raise MatrixEvidenceError("Reels must claim this same exact checkout SHA")
    rows = manifest["renders"]
    if type(rows) is not list or len(rows) != 3:
        raise MatrixEvidenceError("Exactly three actual 15/30/60 exports required")
    root = Path(source_root)
    if not root.is_dir() or root.is_symlink():
        raise MatrixEvidenceError("Expected one existing private source directory")
    verified = []
    found = set()
    seen_paths = set()
    for row in rows:
        if type(row) is not dict or set(row) != {"seconds", "path", "sha256"}:
            raise MatrixEvidenceError("Unexpected export-row fields")
        seconds, name, claimed_digest = row["seconds"], row["path"], row["sha256"]
        if type(seconds) is not int or seconds not in SECONDS or seconds in found:
            raise MatrixEvidenceError("Missing or duplicated export duration")
        if (type(name) is not str or not name or len(name) > 120 or
                name in (".", "..") or "/" in name or "\\" in name or
                not name.endswith(".mp4") or name in seen_paths):
            raise MatrixEvidenceError("Only distinct local MP4 basenames supported")
        if type(claimed_digest) is not str or not DIGEST.fullmatch(claimed_digest):
            raise MatrixEvidenceError("Missing immutable original media SHA")
        path = root / name
        size, actual = _stable_sha(path)
        if actual != claimed_digest:
            raise MatrixEvidenceError("Manifest original-byte SHA mismatch")
        try:
            probe = verify_mp4(path, duration=seconds, width=1080, height=1920, fps=24)
        except CreativeRenderError as exc:
            raise MatrixEvidenceError("Actual encoded 1080x1920 H264/AAC/24fps proof failed") from exc
        if (type(probe) is not dict or type(probe.get("bytes")) is not int or
                probe["bytes"] != size or _stable_sha(path) != (size, actual)):
            raise MatrixEvidenceError("Encoded MP4 changed during verification")
        found.add(seconds)
        seen_paths.add(name)
        verified.append({"seconds": seconds, "file_name": name,
                         "bytes": size, "sha256": actual,
                         "code_sha_claim": expected_head,
                         "encoded_codec_check": "H264_AAC_YUV420P_1080X1920_24FPS"})
    if found != set(SECONDS):
        raise MatrixEvidenceError("15/30/60 profile coverage is incomplete")
    return {
        "schema": "feature4_15_30_60_local_export_matrix_v1",
        "status": "ALL_THREE_LOCAL_ENCODED_PROFILES_TECHNICALLY_CHECKED",
        "source_commit_claim": expected_head,
        "code_commit_attested_by_ci": False,
        "renders": sorted(verified, key=lambda r: r["seconds"]),
        "scope": "PRIVATE_OFFLINE_SOURCE_VERIFICATION_ONLY",
        "commercial_release_eligible": False,
        "retailer_media_rights_verified": False,
        "human_visual_approval": False,
        "speech_alignment_verified": False,
        "hosted_dev_e2e_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    manifest_path = Path(args.manifest)
    report = Path(args.report)
    if (manifest_path.is_symlink() or not manifest_path.is_file() or
            manifest_path.stat().st_size > 32_768):
        raise MatrixEvidenceError("Only bounded private manifest files accepted")
    if (report.exists() or report.is_symlink() or report.suffix != ".json" or
            not report.parent.is_dir() or report.parent.is_symlink()):
        raise MatrixEvidenceError("Report must be a new private JSON file")
    expected_head = subprocess.check_output(
        ["git", "rev-parse", "--verify", "HEAD"], text=True,
        timeout=5, cwd=Path(__file__).resolve().parents[1]).strip()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    evidence = verify_export_matrix(manifest, args.source_root, expected_head=expected_head)
    with report.open("x", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2)
        handle.write("\n")
    print(evidence["status"] + " — NOT customer/hosted quality approval")


if __name__ == "__main__":
    main()
