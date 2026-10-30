#!/usr/bin/env python3
"""Private, bounded 540p MP4 reviewer proxy for an already-authorized H264/AAC reel.

This is NOT a public endpoint, rights grant, JWT checker or signed URL creator.
Call only inside trusted/authorized tenant render flow, preserve original MP4.
Never derive caller paths from HTTP/browser input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

MAX_SOURCE_BYTES = 80 * 1024 * 1024
MAX_PREVIEW_BYTES = 8 * 1024 * 1024
SUPPORTED_DURATIONS = (15, 30, 60)


class PreviewExportError(ValueError):
    pass


def inspect_mp4(path: Path, *, max_size: int):
    path = Path(path)
    if (path.is_symlink() or not path.is_file()
            or not 1_000 < path.stat().st_size <= max_size
            or path.suffix.lower() != ".mp4"):
        raise PreviewExportError("Missing, unsafe or oversized local MP4")
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-protocol_whitelist", "file",
             "-show_format", "-show_streams", "-of", "json", str(path)],
            capture_output=True, text=True, check=True, timeout=25,
        )
        record = json.loads(result.stdout)
        streams = record["streams"]
        video = [v for v in streams if v.get("codec_type") == "video"]
        audio = [a for a in streams if a.get("codec_type") == "audio"]
        if (len(video) != 1 or len(audio) != 1 or len(streams) != 2
                or video[0].get("codec_name") != "h264"
                or audio[0].get("codec_name") != "aac"):
            raise PreviewExportError("Preview source must have one H264 video and AAC audio")
        width = int(video[0]["width"])
        height = int(video[0]["height"])
        seconds = float(record["format"]["duration"])
        if (width < 540 or height < 960 or width > 2160 or height > 3840
                or width * 16 != height * 9
                or not 1.0 <= seconds <= 60.6):
            raise PreviewExportError("Preview source aspect/resolution/duration invalid")
        return {"width": width, "height": height,
                "seconds": round(seconds, 3), "bytes": path.stat().st_size}
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as exc:
        if isinstance(exc, PreviewExportError):
            raise
        raise PreviewExportError("Could not verify local MP4") from exc


def export_private_preview(source: Path, target: Path, *, expected_seconds: int):
    """Encode a small full-duration private reviewer copy, atomically.

    Source is already authorized and claimed by trusted worker. This module
    checks media integrity but does not perform authorization or persist data.
    Never overwrite either source or an existing preview; never publish here.
    """
    if type(expected_seconds) is not int or expected_seconds not in SUPPORTED_DURATIONS:
        raise PreviewExportError("Only 15/30/60-second reviewed output supported")
    source, target = Path(source), Path(target)
    if target.suffix.lower() != ".mp4" or target.is_symlink() or target.exists():
        raise PreviewExportError("Preview target must be a fresh local MP4")
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise PreviewExportError("Preview output directory must already be private and local")
    if source.resolve() == target.resolve():
        raise PreviewExportError("Preview source cannot be overwritten")
    original = inspect_mp4(source, max_size=MAX_SOURCE_BYTES)
    # Pin the actual input bytes before encoding. A changed private source must
    # never receive a SHA/provenance receipt for an older rendered preview.
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if abs(original["seconds"] - expected_seconds) > 0.45:
        raise PreviewExportError("Source is not expected approved render duration")
    # tempfile in the same private directory guarantees atomic rename. Never
    # grant this temp file a public ACL or invent a downloadable media URL.
    partial = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".preview-", suffix=".mp4",
                                         dir=str(target.parent), delete=False) as out:
            partial = Path(out.name)
        cmd = [
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-protocol_whitelist", "file", "-i", str(source),
            "-map", "0:v:0", "-map", "0:a:0",
            "-vf", "fps=24,scale=540:960:flags=lanczos,setsar=1",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "29",
            "-maxrate", "700k", "-bufsize", "1400k", "-pix_fmt", "yuv420p",
            "-g", "48", "-keyint_min", "48", "-sc_threshold", "0",
            "-c:a", "aac", "-b:a", "64k", "-ar", "32000", "-ac", "2",
            "-movflags", "+faststart", "-map_metadata", "-1",
            "-map_chapters", "-1", "-threads", "2", "-y", str(partial),
        ]
        subprocess.run(cmd, check=True, capture_output=True,
                       timeout=240)
        preview = inspect_mp4(partial, max_size=MAX_PREVIEW_BYTES)
        if ((preview["width"], preview["height"]) != (540, 960)
                or abs(preview["seconds"] - expected_seconds) > 0.45
                or preview["bytes"] >= original["bytes"]):
            raise PreviewExportError("Preview failed bounded size/codec/duration checks")
        if hashlib.sha256(source.read_bytes()).hexdigest() != source_sha:
            raise PreviewExportError("Authorized source bytes changed during preview rendering")
        # Re-check concurrent target creation. Prevent normal accidental overwrite.
        if target.exists() or target.is_symlink():
            raise PreviewExportError("Preview destination appeared while rendering")
        # Atomic no-clobber: os.link fails if another worker created target
        # during encoding. Path.replace would silently overwrite that file.
        os.link(partial, target)
        partial.unlink()
        partial = None
        return {
            "status": "PRIVATE_PREVIEW_ENCODED_NOT_PUBLISHED",
            "source_sha256": source_sha,
            "preview_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "source_bytes": original["bytes"],
            "preview_bytes": preview["bytes"],
            "duration_seconds": expected_seconds,
            "width": 540, "height": 960, "fps": 24,
            "video_codec": "h264", "audio_codec": "aac",
            "signed_download_ready": False,
            "retailer_media_authorization_checked_here": False,
            "commercial_release_eligible": False,
        }
    except (OSError, subprocess.SubprocessError) as exc:
        raise PreviewExportError("Unable to encode bounded private MP4 preview") from exc
    finally:
        if partial is not None:
            partial.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--duration", required=True, type=int, choices=SUPPORTED_DURATIONS)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()
    try:
        report = export_private_preview(Path(args.source), Path(args.output),
                                        expected_seconds=args.duration)
        dest = Path(args.report)
        if dest.exists() or dest.is_symlink() or not dest.parent.is_dir():
            raise PreviewExportError("Report path must be new in a pre-existing directory")
        dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "bytes": report["preview_bytes"]}))
    except PreviewExportError as exc:
        print("PRIVATE REVIEW PREVIEW REJECTED: " + str(exc), file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
