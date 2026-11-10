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
from studio_v2 import (DesignError, _prepare_authorized_images,
                       _render_prepared, validate_design)

FORMATS = frozenset({"gif", "mp4"})


EFFECTS = frozenset({"flash", "pulse", "fade", "slide", "zoom", "sparkle", "reveal"})


def _frame_document(base, index, count, effects):
    """Use deterministic normalized layer transforms; never mutate saved drafts."""
    import copy
    import math
    doc = copy.deepcopy(base)
    progress = index / max(count - 1, 1)
    for layer in doc["layers"]:
        if layer["type"] == "image":
            if "zoom" in effects:
                scale = 1 + .035 * (1 - math.cos(progress * math.pi))
                x, y, w, h = (layer[key] for key in ("x", "y", "w", "h"))
                nw, nh = min(1.0, w * scale), min(1.0, h * scale)
                layer.update({
                    "x": max(0, min(1 - nw, x + (w - nw) / 2)),
                    "y": max(0, min(1 - nh, y + (h - nh) / 2)),
                    "w": nw, "h": nh,
                })
            if "reveal" in effects and progress < .2:
                # The missing photo shows the original layout background.
                # This is a hard cut, never generated image interpolation.
                layer.clear()
                layer.update({"id": "reveal-placeholder", "type": "rect",
                              "x": .07, "y": .19, "w": .86, "h": .43,
                              "color": doc["background"]})
        elif layer["id"] == "headline" and "slide" in effects:
            shift = min(.06, (1 - layer["x"] - layer["w"]))
            layer["x"] += shift * (1 - progress) ** 2
        elif layer["id"] == "offer" and layer["type"] == "text":
            if "flash" in effects:
                layer["color"] = "#171921" if index % max(2, count // 4) == 0 else layer["color"]
            if "pulse" in effects:
                layer["font_size"] = min(150, round(
                    layer["font_size"] * (1 + .08 * abs(math.sin(progress * math.pi * 3)))
                ))
    return validate_design(doc)


def _finish_frame(path, design, index, count, effects, scale):
    """Apply pixel-only overlays after exact deterministic type raster."""
    if not ({"sparkle", "fade"} & effects):
        return
    from PIL import ImageDraw
    import math
    with Image.open(path) as source:
        frame = source.convert("RGB")
    if "sparkle" in effects:
        painter = ImageDraw.Draw(frame)
        w, h = frame.size
        points = ((.12, .2), (.88, .19), (.09, .62), (.92, .60), (.83, .78))
        for n, (fx, fy) in enumerate(points):
            phase = ((index + n * 2) / count) * math.pi * 4
            r = max(1, round(3 * scale * (1 + abs(math.sin(phase)))))
            px, py = round(fx * w), round(fy * h)
            painter.ellipse((px - r, py - r, px + r, py + r), fill="#F7CD70")
    if "fade" in effects:
        phase = index / max(count - 1, 1)
        opacity = min(1.0, phase / .25, (1 - phase) / .25)
        # End frame should retain all exact campaign text for review/export.
        if index == count - 1:
            opacity = 1.0
        back = Image.new("RGB", frame.size, design["background"])
        frame = Image.blend(back, frame, opacity)
    frame.save(path, format="PNG")


def export_animation(design, manifest, staged_root, output_path, *, duration=2,
                     fps=8, scale=1, effects=("flash", "pulse"),
                     ffmpeg="ffmpeg"):
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
    if (not isinstance(effects, (list, tuple)) or not 1 <= len(effects) <= 3
        or any(not isinstance(effect, str) or effect not in EFFECTS for effect in effects)
        or len(set(effects)) != len(effects)):
        raise DesignError("Animation effects must be approved templates (max three)")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Validate every source only once for this bounded render job, including
    # a reveal frame that may initially hide a product. Never cache images
    # across tenants/jobs or after rights might have been revoked.
    prepared = _prepare_authorized_images(design, manifest, staged_root)
    resized_cache = {}  # bounded to four entries, one render job only
    frames = []
    with tempfile.TemporaryDirectory(prefix="retailgrowth-animation-") as work:
        root = Path(work)
        count = round(duration * fps)
        for index in range(count):
            path = root / ("frame-%04d.png" % index)
            frame_doc = _frame_document(design, index, count, set(effects))
            _render_prepared(frame_doc, prepared, path, scale=scale,
                             image_transform_cache=resized_cache)
            _finish_frame(path, design, index, count, set(effects), scale)
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
            "duration_seconds": duration, "effects": list(effects), "inference": False}
