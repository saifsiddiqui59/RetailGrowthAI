"""Offline, server-side verification of a previously authorized private MP4.

This is a source-only building block, NOT an Azure worker registration or
provider publishing approval. The caller must obtain media from the existing
tenant-authorized Part 1 private storage path, establish the server-owned
expected SHA-256 independently, and review commercial rights separately.
Never pass a browser-provided path, hash or ffprobe document as authority.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from hashlib import sha256
import hmac
import json
from pathlib import Path
import re
import subprocess

_MAX_BYTES = 512 * 1024 * 1024
_MAX_PROBE_BYTES = 65536
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_CONTAINER = {"mp4", "mov,mp4,m4a,3gp,3g2,mj2"}


class MediaEvidenceRejected(ValueError):
    """Safe denial: never includes local path, content or probe stderr."""


def _normalize_probe(document):
    if not isinstance(document, dict):
        raise MediaEvidenceRejected("MEDIA_PROBE_REJECTED")
    tracks = document.get("streams")
    fmt = document.get("format")
    if not isinstance(tracks, list) or not isinstance(fmt, dict):
        raise MediaEvidenceRejected("MEDIA_PROBE_REJECTED")
    if fmt.get("format_name") not in _CONTAINER:
        raise MediaEvidenceRejected("MEDIA_PROBE_REJECTED")
    videos = [s for s in tracks if isinstance(s, dict) and s.get("codec_type") == "video"]
    audios = [s for s in tracks if isinstance(s, dict) and s.get("codec_type") == "audio"]
    if (len(videos) != 1 or len(audios) != 1 or len(tracks) != 2
            or videos[0].get("codec_name") != "h264"
            or videos[0].get("pix_fmt") != "yuv420p"
            or type(videos[0].get("width")) is not int or videos[0]["width"] != 1080
            or type(videos[0].get("height")) is not int or videos[0]["height"] != 1920
            or audios[0].get("codec_name") != "aac"):
        raise MediaEvidenceRejected("MEDIA_PROBE_REJECTED")
    try:
        duration = Decimal(str(fmt.get("duration")))
        if not duration.is_finite() or duration < 29 or duration > 31:
            raise MediaEvidenceRejected("MEDIA_PROBE_REJECTED")
        rounded = duration.quantize(Decimal("0.001"))
    except (InvalidOperation, TypeError, ValueError):
        raise MediaEvidenceRejected("MEDIA_PROBE_REJECTED") from None
    return {
        "container": fmt["format_name"],
        "video_codec": "h264",
        "audio_codec": "aac",
        "pixel_format": "yuv420p",
        "width": 1080,
        "height": 1920,
        "duration_seconds": str(rounded),
    }


def _digest_file(source):
    digest = sha256()
    count = 0
    with source.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            count += len(block)
            if count > _MAX_BYTES:
                raise MediaEvidenceRejected("MEDIA_SIZE_REJECTED")
            digest.update(block)
    if count == 0:
        raise MediaEvidenceRejected("MEDIA_SIZE_REJECTED")
    return digest.hexdigest()


def inspect_staged_mp4(*, source_path, private_root, expected_sha256,
                       ffprobe_binary="ffprobe", runner=None):
    """Compute byte-bound FFprobe profile inside an operator-owned scratch root.

    `expected_sha256` must come from a server-trusted asset/source receipt;
    it is **not** inferred from the caller's request. A mismatch is denied.
    This does not certify licenses, ownership, or permission to publish.
    """
    if not isinstance(expected_sha256, str) or not _SHA.fullmatch(expected_sha256):
        raise MediaEvidenceRejected("MEDIA_DIGEST_REQUIRED")
    if not isinstance(ffprobe_binary, str) or not ffprobe_binary:
        raise MediaEvidenceRejected("MEDIA_PROBE_UNAVAILABLE")
    try:
        root = Path(private_root).resolve(strict=True)
        original = Path(source_path)
        if original.is_symlink():
            raise MediaEvidenceRejected("UNTRUSTED_MEDIA_PATH")
        source = original.resolve(strict=True)
        if source == root or root not in source.parents or not source.is_file():
            raise MediaEvidenceRejected("UNTRUSTED_MEDIA_PATH")
        start = source.stat()
        if not 0 < start.st_size <= _MAX_BYTES:
            raise MediaEvidenceRejected("MEDIA_SIZE_REJECTED")
        before = _digest_file(source)
        if not hmac.compare_digest(before, expected_sha256):
            raise MediaEvidenceRejected("MEDIA_DIGEST_MISMATCH")
        probe = runner or subprocess.run
        result = probe([
            ffprobe_binary, "-v", "error", "-show_entries",
            "format=format_name,duration:stream=codec_type,codec_name,pix_fmt,width,height",
            "-of", "json", str(source),
        ], capture_output=True, text=True, timeout=20, check=False)
        if (result.returncode != 0 or not isinstance(result.stdout, str)
                or len(result.stdout.encode("utf-8")) > _MAX_PROBE_BYTES):
            raise MediaEvidenceRejected("MEDIA_PROBE_REJECTED")
        profile = _normalize_probe(json.loads(result.stdout))
        finish = source.stat()
        if (start.st_dev, start.st_ino, start.st_size, start.st_mtime_ns) != (
                finish.st_dev, finish.st_ino, finish.st_size, finish.st_mtime_ns):
            raise MediaEvidenceRejected("MEDIA_CHANGED_DURING_PROBE")
        if not hmac.compare_digest(_digest_file(source), expected_sha256):
            raise MediaEvidenceRejected("MEDIA_CHANGED_DURING_PROBE")
        return {"source_sha256": before, "ffprobe": profile}
    except MediaEvidenceRejected:
        raise
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired):
        raise MediaEvidenceRejected("MEDIA_PROBE_REJECTED") from None
