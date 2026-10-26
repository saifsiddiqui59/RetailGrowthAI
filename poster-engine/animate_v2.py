"""Bounded CPU animation of deterministic poster layers (no generative video GPU).

Input uses studio_v2's tenant-scoped, licensed image manifest and schema.
No arbitrary ffmpeg flags, media URLs, scripts, shell, or uploaded audio.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
from studio_v2 import DesignError, render_design, validate_design

FORMATS = frozenset({"gif", "mp4"})


def export_animation(design, manifest, staged_root, output_path, *, duration=2,
                     fps=8, scale=1, ffmpeg="ffmpeg"):
    design = validate_design(design)
    output = Path(output_path)
    kind = output.suffix.lower().lstrip(".")
    if kind not in FORMATS:
        raise DesignError("Animated poster output must be GIF or MP4")
    if type(duration) not in (int, float) or not .5 <= duration <= 4:
        raise DesignError("Animation duration out of range")
    if type(fps) is not int or not 2 <= fps <= 15 or fps * duration > 60:
        raise DesignError("Animation frame budget exceeded")
    if type(scale) not in (int, float) or not .2 <= scale <= 1:
        raise DesignError("Unsafe animation resolution")
    # Constant metadata and private output are managed by the calling worker;
    # this offline module never uploads, signs, schedules, or retries jobs.
    output.parent.mkdir(parents=True, exist_ok=True)
    frames = []
    with tempfile.TemporaryDirectory(prefix="retailgrowth-animation-") as work:
        root = Path(work)
        count = round(duration * fps)
        for index in range(count):
            path = root / ("frame-%04d.png" % index)
            pulse = ("flash" if index % max(2, round(fps / 2)) == 0
                     else "pulse" if index % 3 == 0 else False)
            render_design(design, manifest, staged_root, path, scale=scale,
                          pulse_offer=pulse)
            if kind == "gif":
                with Image.open(path) as frame:
                    frames.append(frame.convert("P", palette=Image.Palette.ADAPTIVE))
        if kind == "gif":
            frames[0].save(output, format="GIF", save_all=True,
                           append_images=frames[1:], duration=round(1000 / fps),
                           loop=0, optimize=False, disposal=2)
        else:
            if shutil.which(ffmpeg) is None:
                raise DesignError("FFmpeg executable unavailable")
            cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                   "-framerate", str(fps), "-i", str(root / "frame-%04d.png"),
                   "-c:v", "libx264", "-pix_fmt", "yuv420p",
                   "-movflags", "+faststart", "-t", str(duration), str(output)]
            try:
                subprocess.run(cmd, timeout=90, check=True, capture_output=True)
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                output.unlink(missing_ok=True)
                raise DesignError("Bounded FFmpeg animation render failed") from exc
    if not output.is_file() or output.stat().st_size < 100:
        raise DesignError("Animation output incomplete")
    return {"path": str(output), "format": kind, "frames": round(duration * fps),
            "duration_seconds": duration, "inference": False}
