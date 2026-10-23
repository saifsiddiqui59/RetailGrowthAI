#!/usr/bin/env python3
"""Optional, offline FFmpeg assembly of already-imported licensed Wan clips.

This NEVER sends a Wan API request or reserves/charges usage. A trusted worker
must derive receipts from a tenant-scoped DB query, not from browser JSON.
FFmpeg standard image renderer is unchanged and remains the free default.
"""
from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path

from render import checked_path, validate_rights, RenderError
from probe import verify_reel
from asset_preflight import inspect_staged_audio, AssetPreflightError

MP4 = {".mp4"}
AUDIO = {".mp3", ".wav", ".m4a", ".aac", ".flac"}
MAX_CLIP_BYTES = 80 * 1024 * 1024


class PremiumComposeError(RuntimeError):
    """No raw FFmpeg error output, provider URL or private paths in response."""


def _check_input_clip(path, seconds):
    """Each input was previously imported privately; re-probe local bytes."""
    try:
        if path.stat().st_size < 1024 or path.stat().st_size > MAX_CLIP_BYTES:
            raise ValueError("invalid clip size")
        result = subprocess.check_output([
            "ffprobe", "-v", "error", "-protocol_whitelist", "file",
            "-show_streams", "-show_format",
            "-of", "json", str(path)
        ], text=True, timeout=30)
        info = json.loads(result)
        videos = [v for v in info["streams"] if v.get("codec_type") == "video"]
        actual = float(info["format"]["duration"])
        if (len(videos) != 1 or videos[0].get("codec_name") != "h264" or
            int(videos[0]["width"]) not in (720, 1080) or
            int(videos[0]["height"]) not in (1280, 1920) or
            int(videos[0]["width"]) * 16 != int(videos[0]["height"]) * 9 or
            not math.isfinite(actual) or abs(actual - seconds) > 0.5):
            raise ValueError("unsupported clip")
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        raise PremiumComposeError("Imported clip preflight failed") from None


def select_render_mode(*, premium_enabled=False, authorized=False,
                       all_clips_ready=False):
    """Free FFmpeg is ALWAYS the default; selection does not incur usage."""
    if premium_enabled is True and authorized is True and all_clips_ready is True:
        return "premium"
    return "ffmpeg"


def compose_approved_clips(*, shop_id, clips, asset_root, output,
                           licensed_music=None, width=1080, height=1920,
                           fps=24, preset="veryfast"):
    """Join private clips to exactly 30s H.264/AAC; no customer-provided URLs.

    clips are DB-origin receipt maps: shop_id, asset_id, path, status,
    provider, duration_seconds and reviewed rights. Source rights, account
    access, job ownership and billing must ALSO be enforced in the database.
    licensed_music, if given, is another server-owned rights-bearing asset.
    """
    if (not isinstance(shop_id, str) or not shop_id or not isinstance(clips, list)
        or not 2 <= len(clips) <= 8):
        raise PremiumComposeError("Invalid premium clip manifest")
    if ((width, height) not in ((1080, 1920), (720, 1280))
        or fps not in (12, 15, 24, 25, 30)
        or preset not in ("ultrafast", "superfast", "veryfast", "faster", "fast")):
        raise PremiumComposeError("Unsupported premium output preset")

    try:
        root = Path(asset_root).resolve(strict=True)
        target = Path(output)
        if not target.is_absolute():
            raise ValueError("Output must be a worker-owned absolute path")
        target = target.resolve()
        if target.is_relative_to(root):
            raise ValueError("Never overwrite staged input assets")
        inputs, intervals = [], []
        for record in clips:
            if not isinstance(record, dict):
                raise ValueError("Invalid clip record")
            seconds = record.get("duration_seconds")
            if (record.get("shop_id") != shop_id or
                record.get("status") != "SUCCEEDED" or
                record.get("provider") != "alibaba-wan" or
                not isinstance(record.get("asset_id"), str) or
                type(seconds) is not int or not 2 <= seconds <= 15):
                raise ValueError("Untrusted premium clip receipt")
            validate_rights(record.get("rights"), record["asset_id"])
            path = checked_path(root, record.get("path"), record["asset_id"], MP4)
            _check_input_clip(path, seconds)
            inputs.append(path)
            intervals.append(seconds)
        if sum(intervals) != 30:
            raise ValueError("Premium clips must fill precisely thirty seconds")
        music_path = None
        if licensed_music is not None:
            if not isinstance(licensed_music, dict) or licensed_music.get("shop_id") != shop_id:
                raise ValueError("Foreign music asset")
            validate_rights(licensed_music.get("rights"), licensed_music.get("asset_id"))
            music_path = checked_path(root, licensed_music.get("path"),
                                      licensed_music.get("asset_id"), AUDIO)
            inspect_staged_audio(music_path)
    except (OSError, ValueError, TypeError, RenderError, AssetPreflightError,
            PremiumComposeError):
        raise PremiumComposeError("Tenant media, rights or duration preflight failed") from None

    with tempfile.TemporaryDirectory(prefix="retail-premium-compose-") as scratch:
        temporary = Path(scratch) / "composed.mp4"
        ff = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y"]
        for path in inputs:
            ff += ["-i", str(path)]
        if music_path is None:
            ff += ["-f", "lavfi", "-t", "30", "-i",
                   "anullsrc=channel_layout=stereo:sample_rate=44100"]
        else:
            ff += ["-stream_loop", "-1", "-i", str(music_path)]
        filters = []
        for i, seconds in enumerate(intervals):
            filters.append(
                f"[{i}:v]fps={fps},scale={width}:{height}:"
                f"force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                f"setsar=1,format=yuv420p,trim=duration={seconds},"
                f"setpts=PTS-STARTPTS[v{i}]"
            )
        joined = "".join(f"[v{i}]" for i in range(len(inputs)))
        filters.append(f"{joined}concat=n={len(inputs)}:v=1:a=0,"
                       "fps=" + str(fps) + ",trim=duration=30,"
                       "setpts=PTS-STARTPTS,format=yuv420p[vout]")
        ff += ["-filter_complex", ";".join(filters),
               "-map", "[vout]", "-map", f"{len(inputs)}:a:0",
               "-af", "atrim=duration=30,asetpts=PTS-STARTPTS,"
                      "afade=t=out:st=29:d=1",
               "-t", "30", "-threads", "2", "-c:v", "libx264",
               "-preset", preset, "-crf", "24", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
               "-movflags", "+faststart", str(temporary)]
        try:
            subprocess.run(ff, check=True, capture_output=True, text=True,
                           timeout=780)
            info = verify_reel(temporary, width, height)
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary.replace(target)
            return info
        except (OSError, ValueError, subprocess.SubprocessError):
            raise PremiumComposeError("Premium FFmpeg assembly failed") from None
