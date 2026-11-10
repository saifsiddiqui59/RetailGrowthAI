"""Private, ephemeral human-review contact sheet for real Hunyuan output.

CPU-only evidence gathering. It NEVER auto-approves quality, uploads files,
touches user-facing URLs, or changes the existing credit ledger. The trusted
caller authorizes/stages local tenant media and disposes of review scratch.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from .contracts import MotionError
from .worker import validate_clip

TIMESTAMPS = ("0.20", "1.00", "2.00", "3.00", "4.00", "4.80")


def _sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(part)
    return sha.hexdigest()


def prepare_visual_review(clip: Path, output_dir: Path, *, ffmpeg="ffmpeg") -> dict:
    """Extract representative PNG frames and a side-by-side local sheet.

    Input is already authorized tenant-private local storage. Output is a new
    empty 0700 private directory, owned/cleaned by the existing job service.
    Return immutable clip sha256 for *later* independent tenant review.
    """
    clip = Path(clip)
    if clip.is_symlink():
        raise MotionError("Review input must not be a symlink")
    clip = clip.resolve(strict=True)
    info = validate_clip(clip)
    out = Path(output_dir)
    if out.exists() or out.is_symlink() or not out.parent.resolve(strict=True).is_dir():
        raise MotionError("Review directory must be new and private")
    out.mkdir(mode=0o700, exist_ok=False)
    try:
        from PIL import Image, ImageDraw
        frames = []
        thumbs = []
        for i, timestamp in enumerate(TIMESTAMPS):
            name = f"frame-{i:02d}.png"
            target = out / name
            cmd = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error",
                   "-threads", "1", "-ss", timestamp, "-protocol_whitelist", "file",
                   "-i", str(clip), "-frames:v", "1", "-y", str(target)]
            completed = subprocess.run(cmd, capture_output=True, timeout=25)
            if completed.returncode or not target.is_file() or not 0 < target.stat().st_size <= 8_000_000:
                raise MotionError("Unable to prepare a local reviewer frame")
            with Image.open(target) as image:
                image.verify()
            with Image.open(target) as image:
                if image.size != (info["width"], info["height"]):
                    raise MotionError("Reviewer image dimensions mismatch validated clip")
                thumb = image.convert("RGB")
                thumb.thumbnail((240, 420))
                thumbs.append(thumb.copy())
            frames.append({"timestamp_seconds": timestamp, "file": name,
                           "sha256": _sha256(target)})
        width, height = 3 * 250, 2 * 455 + 44
        board = Image.new("RGB", (width, height), (18, 18, 24))
        draw = ImageDraw.Draw(board)
        draw.text((12, 9), "HUMAN REVIEW REQUIRED - no automatic approval",
                  fill=(230, 230, 230))
        for i, thumb in enumerate(thumbs):
            x, y = (i % 3) * 250 + 5, (i // 3) * 455 + 48
            board.paste(thumb, (x, y))
            draw.text((x + 5, y + thumb.height + 4),
                      "t=" + TIMESTAMPS[i] + "s", fill=(230, 230, 230))
        sheet_path = out / "contact-sheet.png"
        board.save(sheet_path, format="PNG")
        manifest = {
            "status": "PENDING_HUMAN_REVIEW",
            "clip_sha256": _sha256(clip),
            "codec": info["codec"], "duration_seconds": info["duration_seconds"],
            "width": info["width"], "height": info["height"],
            "frames": frames, "contact_sheet": "contact-sheet.png",
        }
        (out / "review-manifest.json").write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        return manifest
    except Exception as exc:
        shutil.rmtree(out, ignore_errors=True)
        if isinstance(exc, MotionError):
            raise
        raise MotionError("Unable to prepare offline visual-review materials") from exc
