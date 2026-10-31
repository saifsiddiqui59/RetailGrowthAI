#!/usr/bin/env python3
"""Burn an already reviewed subtitle track into a PRIVATE reviewer MP4.

This does not transcribe speech, confer music/image rights, authorize a tenant,
publish, or change the immutable Full-HD master. Call inside an authorized,
leased Feature4 worker with reviewed Feature2 cue timings and private scratch.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile

from feature4_private_preview import PreviewExportError, inspect_mp4
from feature4_subtitles import SubtitleExportError, compose_approved_subtitles


class SubtitleBurnError(ValueError):
    pass


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ffmpeg(args, *, timeout=240):
    try:
        subprocess.run(args, check=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        raise SubtitleBurnError("Subtitle burn-in or local codec verification failed") from exc


def burn_reviewed_subtitles(source: Path, srt_path: Path, target: Path, *,
                           cues, expected_seconds: int):
    """Encode a distinct H264/AAC private captioned MP4; never overwrite.

    Paths are trusted worker generated, not browser values. Restrict the SRT
    filter's filename alphabet to avoid FFmpeg filter-graph option injection.
    """
    source, srt_path, target = (Path(p) for p in (source, srt_path, target))
    if type(expected_seconds) is not int or expected_seconds not in (15, 30, 60):
        raise SubtitleBurnError("Only reviewed 15/30/60-second Reels supported")
    if (source.suffix.lower() != ".mp4" or target.suffix.lower() != ".mp4"
            or srt_path.suffix.lower() != ".srt"
            or source.is_symlink() or srt_path.is_symlink() or target.is_symlink()
            or not source.is_file() or not srt_path.is_file()
            or target.exists()):
        raise SubtitleBurnError("Sources must be files and output must be fresh")
    parent = source.parent
    if (parent.is_symlink() or not parent.is_dir()
            or srt_path.parent != parent or target.parent != parent
            or parent.stat().st_mode & 0o077
            or srt_path.stat().st_mode & 0o077
            or not re.fullmatch(r"/[A-Za-z0-9_./-]+", str(srt_path.resolve()))):
        raise SubtitleBurnError("Unsafe FFmpeg subtitle path or nonprivate staging")
    try:
        srt, _ = compose_approved_subtitles(cues, duration_seconds=expected_seconds)
        if srt_path.stat().st_size > 20_000 or srt_path.read_bytes() != srt.encode("utf-8"):
            raise SubtitleBurnError("Subtitle bytes differ from immutable reviewed cues")
        original = inspect_mp4(source, max_size=80 * 1024 * 1024)
    except (SubtitleExportError, PreviewExportError) as exc:
        raise SubtitleBurnError("Unreviewed subtitles or invalid H264/AAC source") from exc
    if abs(original["seconds"] - expected_seconds) > .45:
        raise SubtitleBurnError("Source duration differs from reviewed cue Reel")
    source_sha, cues_sha = _sha(source), _sha(srt_path)
    partial = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".subtitle-burn-",
                                         suffix=".mp4", dir=parent,
                                         delete=False) as tmp:
            partial = Path(tmp.name)
        os.chmod(partial, 0o600)
        _ffmpeg([
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-protocol_whitelist", "file", "-i", str(source),
            "-map", "0:v:0", "-map", "0:a:0",
            "-vf", f"subtitles=filename={srt_path.resolve()}:charenc=UTF-8",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", "24",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
            "-movflags", "+faststart", "-map_metadata", "-1",
            "-map_chapters", "-1", "-threads", "2", "-y", str(partial),
        ])
        result = inspect_mp4(partial, max_size=80 * 1024 * 1024)
        if ((result["width"], result["height"]) !=
                (original["width"], original["height"])
                or abs(result["seconds"] - expected_seconds) > .45):
            raise SubtitleBurnError("Subtitle encode changed duration or frame profile")
        if _sha(source) != source_sha or _sha(srt_path) != cues_sha:
            raise SubtitleBurnError("Source or approved subtitles changed during encode")
        if target.exists() or target.is_symlink():
            raise SubtitleBurnError("Another worker created the preview destination")
        os.link(partial, target)  # Atomic no-clobber, not an overwrite.
        partial.unlink()
        partial = None
        return {
            "status": "PRIVATE_ENCODED_SUBTITLES_NOT_PUBLISHED",
            "source_sha256": source_sha,
            "reviewed_srt_sha256": cues_sha,
            "captioned_mp4_sha256": _sha(target),
            "cue_count": len(cues),
            "duration_seconds": expected_seconds,
            "width": result["width"], "height": result["height"],
            "video_codec": "h264", "audio_codec": "aac",
            "actual_encoded_subtitle_filter_executed": True,
            "spoken_word_alignment_verified": False,
            "human_visual_approval": False,
            "commercial_release_eligible": False,
            "signed_download_ready": False,
            "tenant_rights_checked_here": False,
        }
    except (OSError, subprocess.SubprocessError) as exc:
        raise SubtitleBurnError("Could not safely finish private subtitle encoding") from exc
    finally:
        if partial is not None:
            partial.unlink(missing_ok=True)
