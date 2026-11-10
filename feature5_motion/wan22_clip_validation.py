"""CPU-only Wan native video receipt preflight. Not a generated/approved clip.

The EXISTING claim-fenced Part3/Feature5 worker must invoke this AFTER real
licensed inference, private upload, measured billing and human visual review.
This module cannot claim success from a ComfyUI workflow or mocked media.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .wan22_motion_adapter import WanShotPackage, WanCompatibilityError

MAX_CLIP_BYTES = 80 * 1024 * 1024


@dataclass(frozen=True)
class NativeClipInspection:
    sha256: str
    size_bytes: int
    width: int
    height: int
    fps: int
    frames: int
    duration_seconds: float
    codec: str
    lineage_sha256: str
    status: str = "PENDING_PRIVATE_IMPORT_AND_VISUAL_REVIEW"


def inspect_native_mp4(shot: WanShotPackage, *, staged_file: Path, ffprobe="ffprobe"):
    """Read only a private local file via ffprobe with no external protocols.

    Source-video audio, upscaling and Fashion/garment visual fidelity are NOT
    verified by ffprobe. Feature4 handles final 1080x1920 / captions and audio.
    """
    if not isinstance(shot, WanShotPackage) or shot.task != "image_to_video":
        raise WanCompatibilityError("Unrecognized Wan approved-lineage clip")
    candidate = Path(staged_file)
    if candidate.is_symlink() or candidate.suffix.lower() != ".mp4" or not candidate.is_file():
        raise WanCompatibilityError("Expected local private .mp4, no symlinks/URLs")
    initial = candidate.stat(follow_symlinks=False)
    size = initial.st_size
    if not 0 < size <= MAX_CLIP_BYTES or initial.st_nlink != 1:
        raise WanCompatibilityError("Generated MP4 missing/oversized or linked")
    # Canonical private worker paths are independently scoped by the caller.
    target = candidate.resolve(strict=True)
    try:
        result = subprocess.run(
            [ffprobe, "-v","error", "-protocol_whitelist","file",
             "-count_frames", "-show_entries",
             "format=duration,format_name:stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames",
             "-of","json",str(target)],
            check=True, capture_output=True, text=True, timeout=30,
        )
        # Never parse only a prefix: a forged/oversized ffprobe response
        # could hide a second audio/video stream after the accepted JSON.
        if type(result.stdout) is not str or len(result.stdout) > 50000:
            raise ValueError("Oversized or invalid ffprobe JSON output")
        def unique_json_keys(pairs):
            values = {}
            for key, value in pairs:
                if key in values:
                    raise ValueError("Ambiguous ffprobe JSON duplicate key")
                values[key] = value
            return values
        data = json.loads(
            result.stdout, object_pairs_hook=unique_json_keys,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ValueError("Nonfinite ffprobe number")),
        )
        if type(data) is not dict or type(data.get("format")) is not dict:
            raise ValueError("Malformed ffprobe root or format")
        # Native Wan SaveVideo output is exactly one silent H264 video.
        # Extra audio, subtitles, attachments or second video streams can
        # smuggle unreviewed content into the downstream editor/publisher.
        # Final Feature4 music/voice is separately licensed and reviewed.
        streams = data["streams"]
        if (type(streams) is not list or len(streams) != 1 or
            type(streams[0]) is not dict or
            streams[0].get("codec_type") != "video"):
            raise ValueError("Native silent Wan MP4 must have one video stream only")
        v = streams[0]
        fps = v["r_frame_rate"]
        frame_count = v.get("nb_read_frames")
        duration_raw = data["format"].get("duration")
        # ffprobe's JSON fields are decimal ASCII strings. Never silently
        # truncate fractional frame counts or accept nonfinite/spoofed values.
        if (type(frame_count) is not str or not frame_count.isascii() or
            not frame_count.isdigit() or len(frame_count) > 6 or
            type(duration_raw) is not str or len(duration_raw) > 24 or
            not re.fullmatch(r"[0-9]{1,4}(?:\.[0-9]{1,12})?", duration_raw) or
            type(v.get("width")) is not int or type(v.get("height")) is not int):
            raise ValueError("Invalid native frame count, size or duration types")
        n = int(frame_count)
        duration = float(duration_raw)
        if (data["format"].get("format_name","").split(",")[0] not in ("mov","mp4") or
            v["codec_name"] != "h264" or (v["width"],v["height"])!=(704,1280) or
            fps != "24/1" or n != 121 or not 4.9 <= duration <= 5.2):
            raise ValueError("Native Wan clip dimensions/codec/frames/duration mismatch")
        digest = hashlib.sha256()
        with target.open("rb") as h:
            for part in iter(lambda:h.read(1024*1024),b""):
                digest.update(part)
        final = target.stat(follow_symlinks=False)
        if (final.st_dev, final.st_ino, final.st_size, final.st_mtime_ns) != (
            initial.st_dev, initial.st_ino, initial.st_size, initial.st_mtime_ns
        ):
            raise ValueError("File changed during ffprobe or receipt hashing")
        return NativeClipInspection(digest.hexdigest(),size,704,1280,24,121,
                                    duration,"h264",shot.lineage_sha256)
    except (OSError,ValueError,KeyError,TypeError,RecursionError,subprocess.SubprocessError) as exc:
        raise WanCompatibilityError("Native video not accepted; no Feature4 approval") from exc


def pending_private_receipt(shot: WanShotPackage, inspection: NativeClipInspection):
    """Immutable measured metadata, not a forged reviewed Feature4 clip."""
    if not isinstance(shot,WanShotPackage) or not isinstance(inspection,NativeClipInspection):
        raise WanCompatibilityError("Unknown Wan result")
    if inspection.lineage_sha256 != shot.lineage_sha256:
        raise WanCompatibilityError("Private output lineage mismatch")
    return {
        "schema":"wan22_clip_inspection_v1",
        "provider":shot.provider,
        "shop_id":shot.lineage["shop_id"],"shot_id":shot.lineage["shot_id"],
        "source_asset_id":shot.lineage["source_asset_id"],
        "source_sha256":shot.lineage["source_sha256"],
        "prompt_sha256":shot.prompt_sha256,
        "lineage_sha256":shot.lineage_sha256,
        "media_sha256":inspection.sha256,
        "bytes":inspection.size_bytes,
        "codec":inspection.codec,
        "frames":inspection.frames,"fps":inspection.fps,
        "width":inspection.width,"height":inspection.height,
        "duration_seconds":inspection.duration_seconds,
        "quality_state":"PENDING_HUMAN_VISUAL_REVIEW",
        "private_import_required":True,
        "approved_for_feature4":False,
    }
