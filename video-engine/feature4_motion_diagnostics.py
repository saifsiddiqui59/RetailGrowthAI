"""Bounded, offline motion diagnostics for privately staged video footage.

This rejects clearly frozen 'video' sources but NEVER certifies a real human,
garment identity, licensing, authenticity, visual art direction or customer QA.
No network, cloud model, GPU, customer content logging or billable inference.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

WIDTH, HEIGHT = 64, 112
FRAME_BYTES = WIDTH * HEIGHT
SAMPLES = 6


class MotionProbeError(ValueError):
    pass


def _run(args, timeout=18):
    try:
        return subprocess.run(args, capture_output=True, check=True, timeout=timeout).stdout
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise MotionProbeError("Unable to probe locally staged video") from exc


def inspect_staged_motion(filename):
    path = Path(filename)
    if not path.is_file() or path.is_symlink() or path.suffix.lower() not in (".mp4", ".mov", ".m4v"):
        raise MotionProbeError("Only an existing local staged video file may be inspected")
    try:
        stream = json.loads(_run([
            "ffprobe", "-v", "error", "-protocol_whitelist", "file",
            "-show_entries", "format=duration", "-of", "json", str(path)], 14))
        duration = float(stream["format"]["duration"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise MotionProbeError("Invalid verified media duration") from exc
    if not math.isfinite(duration) or not 2.0 <= duration <= 180:
        raise MotionProbeError("Video duration outside bounded visual inspection range")
    frames = []
    for i in range(SAMPLES):
        t = (i + .5) * duration / SAMPLES
        raw = _run(["ffmpeg","-nostdin","-v","error",
                    "-ss", f"{t:.3f}", "-protocol_whitelist","file",
                    "-i", str(path), "-vf", f"scale={WIDTH}:{HEIGHT}:flags=fast_bilinear,format=gray",
                    "-frames:v","1","-f","rawvideo","-pix_fmt","gray","-"], 15)
        if len(raw) != FRAME_BYTES:
            raise MotionProbeError("Source video frame is missing or cannot be safely decoded")
        frames.append(raw)
    deltas = [sum(abs(a-b) for a,b in zip(frames[i],frames[i+1]))/FRAME_BYTES
              for i in range(len(frames)-1)]
    mean = sum(deltas)/len(deltas)
    # A true actor is not implied by a positive score (camera panning cartoons
    # also move). Zero/near-zero means a frozen video cannot pass QA as motion.
    visible = sum(x >= 1.2 for x in deltas) >= 2 and mean >= 1.2
    return {
        "source_type": "local_private_media",
        "samples": SAMPLES,
        "duration_seconds": round(duration, 3),
        "mean_frame_delta": round(mean, 3),
        "max_frame_delta": round(max(deltas), 3),
        "visible_temporal_change": visible,
        "frame_freeze_check": "PASS" if visible else "FAILED_FROZEN_OR_LOW_MOTION",
        "photoreal_human_verified": False,
        "garment_identity_verified": False,
        "commercial_quality_approved": False,
    }
