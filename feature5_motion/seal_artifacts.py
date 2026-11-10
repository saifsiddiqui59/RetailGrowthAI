"""Offline operator helper to create (NOT approve) a model artifact candidate.

Example:
  python -m feature5_motion.seal_artifacts \
    --checkout /sealed/hunyuan-code --weights /licensed/hunyuan-weights \
    --out /restricted/feature5-v1.lock.json

Review source commit, Tencent license, exact code/files, dependency lock and
weight provenance. Store the printed manifest SHA256 in independently reviewed
DEV deployment configuration, not inside the downloadable model directory.
This script does not fetch code/weights, run CUDA, or grant commercial rights.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

from .artifact_lock import construct_manifest
from .contracts import MotionError


def create_candidate(*, checkout: Path, weights: Path, destination: Path) -> str:
    raw = construct_manifest(checkout, weights)
    output = Path(destination)
    if output.is_symlink() or not output.parent.resolve(strict=True).is_dir():
        raise MotionError("Lock output parent must already be a safe directory")
    # Exclusive create; must not overwrite any already reviewed manifest.
    fd = os.open(str(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as target:
            target.write(raw)
            target.flush()
            os.fsync(target.fileno())
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create offline, UNAPPROVED Hunyuan file lock")
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    digest = create_candidate(
        checkout=options.checkout, weights=options.weights, destination=options.out)
    print("CANDIDATE ONLY — independent model license, supplier and hash review required")
    print("Reviewed artifact manifest SHA256 (after independent approval):", digest)


if __name__ == "__main__":
    main()
