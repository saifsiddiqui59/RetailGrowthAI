"""Bounded, offline preflight of server-staged images/audio before invoking FFmpeg.

This is defense in depth, not provenance verification or a malware scanner.
Call only AFTER load_job has checked tenant IDs, rights metadata and confined paths.
"""
import json
import math
import subprocess
from pathlib import Path

IMAGE_CODECS = {".jpg": "mjpeg", ".jpeg": "mjpeg", ".png": "png", ".webp": "webp"}
AUDIO_CODECS = {
    ".wav": {"pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_f32le", "pcm_f64le"},
    ".mp3": {"mp3"}, ".aac": {"aac"}, ".m4a": {"aac", "alac"}, ".flac": {"flac"},
}
MAX_IMAGE_BYTES = 25 * 1024 * 1024
MAX_AUDIO_BYTES = 50 * 1024 * 1024
MAX_PIXELS = 24_000_000
MAX_SIDE = 8192
PROBE_TIMEOUT = 15


class AssetPreflightError(ValueError):
    pass


def _probe(path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-protocol_whitelist", "file",
             "-show_streams", "-show_format", "-of", "json", str(path)],
            capture_output=True, text=True, check=True, timeout=PROBE_TIMEOUT,
        )
        return json.loads(result.stdout)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired,
            ValueError) as exc:
        raise AssetPreflightError("Invalid or unprobeable staged media") from exc


def _image_signature(path):
    with Path(path).open("rb") as f:
        head = f.read(16)
    suffix = Path(path).suffix.lower()
    return {
        ".jpg": head.startswith(b"\xff\xd8\xff"),
        ".jpeg": head.startswith(b"\xff\xd8\xff"),
        ".png": head.startswith(b"\x89PNG\r\n\x1a\n"),
        ".webp": head.startswith(b"RIFF") and head[8:12] == b"WEBP",
    }.get(suffix, False)


def inspect_staged_image(path):
    path = Path(path)
    if path.suffix.lower() not in IMAGE_CODECS:
        raise AssetPreflightError("Unsupported image extension")
    size = path.stat().st_size
    if not 0 < size <= MAX_IMAGE_BYTES or not _image_signature(path):
        raise AssetPreflightError("Image signature or byte-size limit failed")
    data = _probe(path)
    streams = data.get("streams", [])
    if len(streams) != 1 or streams[0].get("codec_type") != "video":
        raise AssetPreflightError("Staged image must contain exactly one video/image stream")
    video = streams[0]
    try:
        width, height = int(video.get("width") or 0), int(video.get("height") or 0)
    except (TypeError, ValueError, OverflowError) as exc:
        raise AssetPreflightError("Invalid image dimensions") from exc
    if (video.get("codec_name") != IMAGE_CODECS[path.suffix.lower()]
            or width <= 0 or height <= 0 or width > MAX_SIDE or height > MAX_SIDE
            or width * height > MAX_PIXELS):
        raise AssetPreflightError("Image dimensions or codec not permitted")
    return {"width": width, "height": height, "bytes": size}


def inspect_staged_audio(path):
    path = Path(path)
    if path.suffix.lower() not in AUDIO_CODECS:
        raise AssetPreflightError("Unsupported audio extension")
    size = path.stat().st_size
    if not 0 < size <= MAX_AUDIO_BYTES:
        raise AssetPreflightError("Audio byte-size limit failed")
    data = _probe(path)
    streams = data.get("streams", [])
    if len(streams) != 1 or streams[0].get("codec_type") != "audio":
        raise AssetPreflightError("Staged music must contain exactly one audio stream")
    stream = streams[0]
    if stream.get("codec_name") not in AUDIO_CODECS[path.suffix.lower()]:
        raise AssetPreflightError("Audio extension/codec mismatch")
    try:
        rate = int(stream.get("sample_rate") or 0)
        channels = int(stream.get("channels") or 0)
        raw_duration = data.get("format", {}).get("duration")
        duration = float(raw_duration) if raw_duration is not None else None
    except (TypeError, ValueError, OverflowError) as exc:
        raise AssetPreflightError("Invalid audio stream metadata") from exc
    if not 0 < rate <= 192000 or not 0 < channels <= 8:
        raise AssetPreflightError("Audio channel/sample-rate limit failed")
    if duration is not None and (not math.isfinite(duration) or not 0 < duration <= 3600):
        raise AssetPreflightError("Music length limit failed")
    return {"bytes": size, "sample_rate": rate, "channels": channels, "duration_seconds": duration}


def preflight_assets(images, music):
    """Deduplicate re-used image IDs to avoid repeated probes."""
    seen = set()
    for path in images.values():
        path = Path(path).resolve(strict=True)
        if path not in seen:
            inspect_staged_image(path)
            seen.add(path)
    if music is not None:
        inspect_staged_audio(Path(music).resolve(strict=True))
