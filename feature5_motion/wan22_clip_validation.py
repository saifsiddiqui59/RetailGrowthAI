"""CPU-only Wan native video receipt preflight. Not a generated/approved clip.

The EXISTING claim-fenced Part3/Feature5 worker must invoke this AFTER real
licensed inference, private upload, measured billing and human visual review.
This module cannot claim success from a ComfyUI workflow or mocked media.
"""
from __future__ import annotations

import hashlib
import json
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
    size = candidate.stat().st_size
    if not 0 < size <= MAX_CLIP_BYTES:
        raise WanCompatibilityError("Generated MP4 missing/oversized")
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
        data = json.loads(result.stdout[:50000])
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
        n = int(v["nb_read_frames"])
        duration = float(data["format"]["duration"])
        if (data["format"].get("format_name","").split(",")[0] not in ("mov","mp4") or
            v["codec_name"] != "h264" or (v["width"],v["height"])!=(704,1280) or
            fps != "24/1" or n != 121 or not 4.9 <= duration <= 5.2):
            raise ValueError("Native Wan clip dimensions/codec/frames/duration mismatch")
        digest = hashlib.sha256()
        with target.open("rb") as h:
            for part in iter(lambda:h.read(1024*1024),b""):
                digest.update(part)
        if target.stat().st_size != size:
            raise ValueError("File changed during receipt hashing")
        return NativeClipInspection(digest.hexdigest(),size,704,1280,24,121,
                                    duration,"h264",shot.lineage_sha256)
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
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
