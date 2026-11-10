"""Local-only, reviewable evidence from a successfully generated 5-second clip.

No model execution, tenant lookups, cloud uploads or automatic human approval.
The caller (manual operator) MUST use an already approved local private source
and select a protected disk location outside any public/server web root.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil

from .contracts import MotionError
from .visual_review_artifacts import prepare_visual_review
from .worker import validate_clip


def _copy_private(source: Path, destination: Path) -> str:
    if source.is_symlink() or not source.is_file():
        raise MotionError("Only local ordinary files may be exported")
    # Exclusive creation, not an unsafe overwrite of an earlier acceptance.
    with source.open("rb") as inp:
        fd = os.open(str(destination), os.O_WRONLY | os.O_EXCL | os.O_CREAT, 0o600)
        sha = hashlib.sha256()
        with os.fdopen(fd, "wb") as out:
            for chunk in iter(lambda: inp.read(1024 * 1024), b""):
                sha.update(chunk)
                out.write(chunk)
    return sha.hexdigest()


def export_pending_review(clip: Path, evidence_dir: Path, *,
                          mode: str, source_image: Path | None = None,
                          approved_model_manifest_sha256: str) -> dict:
    """Export a private MP4 + optional source image + human-review contact sheet.

    Both `mode` and model manifest digest are *operator assertions*, not
    proof of actual inference provenance. The clip must pass ffprobe's strict
    5-second H264 profile. All outputs remain PENDING_HUMAN_REVIEW.
    """
    if mode not in ("text", "image", "poster"):
        raise MotionError("Unsupported acceptance mode")
    if (mode == "text") != (source_image is None):
        raise MotionError("Source image must match text/image acceptance mode")
    if (not isinstance(approved_model_manifest_sha256, str) or
        len(approved_model_manifest_sha256) != 64 or
        any(x not in "0123456789abcdef" for x in approved_model_manifest_sha256)):
        raise MotionError("Reviewed model manifest digest required")
    candidate = Path(clip)
    if candidate.is_symlink() or not candidate.is_file():
        raise MotionError("Invalid private GPU clip for export")
    validate_clip(candidate)   # Never copy unvalidated MP4 bytes.
    if source_image is not None:
        source = Path(source_image)
        if (source.is_symlink() or not source.is_file() or
            source.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp") or
            not 0 < source.stat().st_size <= 20 * 1024 * 1024):
            raise MotionError("Invalid approved comparison source image")
    directory = Path(evidence_dir)
    if directory.is_symlink() or directory.exists():
        raise MotionError("Acceptance evidence output must be a new private directory")
    if not directory.parent.resolve(strict=True).is_dir():
        raise MotionError("Missing private evidence parent")
    directory.mkdir(mode=0o700, exist_ok=False)
    try:
        copied = directory / "clip.mp4"
        clip_hash = _copy_private(candidate, copied)
        evidence = prepare_visual_review(copied, directory / "review")
        if evidence["clip_sha256"] != clip_hash:
            raise MotionError("Review frames not bound to copied clip hash")
        source_hash = None
        if source_image is not None:
            original = Path(source_image)
            destination = directory / ("reference" + original.suffix.lower())
            source_hash = _copy_private(original, destination)
        record = {
            "status": "PENDING_HUMAN_REVIEW",
            "claimed_model": "hunyuanvideo-1.5-480p",
            "mode": mode,
            "clip_sha256": clip_hash,
            "reference_sha256": source_hash,
            "model_manifest_sha256": approved_model_manifest_sha256,
            "machine_profile": {
                "codec": evidence["codec"], "duration_seconds": evidence["duration_seconds"],
                "width": evidence["width"], "height": evidence["height"],
            },
            "visual_review": "review/review-manifest.json",
        }
        out = directory / "acceptance-pending.json"
        fd = os.open(str(out), os.O_WRONLY | os.O_EXCL | os.O_CREAT, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(record, stream, sort_keys=True)
        return record
    except Exception:
        shutil.rmtree(directory, ignore_errors=True)
        raise
