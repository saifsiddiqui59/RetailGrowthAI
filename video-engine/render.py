#!/usr/bin/env python3
"""Local FFmpeg renderer for the frozen RetailGrowthAI campaign-day v1 contract.

Requires server-authorized, locally staged asset IDs and explicit rights metadata.
Never accepts client URLs or arbitrary FFmpeg filter expressions.
"""
import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from probe import verify_reel

DURATION = 30.0
TRANSITION = 0.5
ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".flac"}
COMMERCIAL_LICENSES = {"owned", "cc0", "royalty_free", "commercial"}


class RenderError(ValueError):
    pass


def check_text(value, name, limit=100):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise RenderError(f"{name} must contain 1-{limit} characters")
    if any(ord(c) < 32 and c != "\n" for c in value):
        raise RenderError(f"{name} contains invalid control characters")
    return value.strip()


def validate_rights(rights, asset_id, allow_test_media=False):
    if not isinstance(rights, dict) or rights.get("commercial_use") is not True:
        raise RenderError(f"Asset {asset_id}: commercial-use rights must be confirmed")
    license_type = rights.get("license")
    allowed = COMMERCIAL_LICENSES | ({"synthetic_test"} if allow_test_media else set())
    if license_type not in allowed:
        raise RenderError(f"Asset {asset_id}: unsupported or unverified license")
    check_text(rights.get("evidence"), f"Asset {asset_id} rights evidence", 500)
    check_text(rights.get("source"), f"Asset {asset_id} rights source", 300)


def checked_path(asset_root, relative, asset_id, suffixes):
    if not isinstance(relative, str) or not relative or "://" in relative or "\\" in relative:
        raise RenderError(f"Asset {asset_id}: expected a server-staged relative path")
    if Path(relative).is_absolute():
        raise RenderError(f"Asset {asset_id}: absolute paths are forbidden")
    root = Path(asset_root).resolve(strict=True)
    candidate = (root / relative).resolve(strict=True)
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise RenderError(f"Asset {asset_id}: path escapes asset root or is not a file")
    if candidate.suffix.lower() not in suffixes:
        raise RenderError(f"Asset {asset_id}: unsupported file type")
    return candidate


def load_job(campaign_path, manifest_path, asset_root, day_index, allow_test_media=False):
    campaign = json.loads(Path(campaign_path).read_text(encoding="utf-8"))
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if not isinstance(campaign, dict) or not isinstance(manifest, dict):
        raise RenderError("Campaign and asset manifest must be objects")
    days = campaign.get("days")
    if not isinstance(days, list) or not days:
        raise RenderError("Missing campaign days")
    matched = [d for d in days if isinstance(d, dict) and d.get("day_index") == day_index]
    if len(matched) != 1:
        raise RenderError("Exactly one matching day_index is required")
    day = matched[0]
    shop_id = campaign.get("shop_id")
    if not shop_id or shop_id != day.get("shop_id") or shop_id != manifest.get("shop_id"):
        raise RenderError("Cross-tenant shop_id mismatch")
    if not campaign.get("id") or day.get("campaign_id") != campaign["id"]:
        raise RenderError("Campaign ownership mismatch")
    reel = day.get("instagram", {}).get("reel", {})
    if reel.get("aspect_ratio") != "9:16" or reel.get("duration_seconds") != 30:
        raise RenderError("Only the v1 9:16, 30-second Reel preset is supported")
    storyboard = reel.get("storyboard")
    if not isinstance(storyboard, list) or not 2 <= len(storyboard) <= 8:
        raise RenderError("Storyboards must contain 2-8 segments")
    assets = manifest.get("assets")
    if not isinstance(assets, dict):
        raise RenderError("Missing asset-ID manifest")
    resolved = {}
    current = 0.0
    for segment in storyboard:
        if not isinstance(segment, dict):
            raise RenderError("Invalid storyboard segment")
        start, length = segment.get("start_seconds"), segment.get("duration_seconds")
        if (not isinstance(start, (int, float)) or isinstance(start, bool)
                or not isinstance(length, (int, float)) or isinstance(length, bool)
                or not math.isfinite(start) or not math.isfinite(length)
                or length <= TRANSITION or abs(start - current) > 0.00001):
            raise RenderError("Storyboard must be contiguous, ordered and longer than transitions")
        current += length
        asset_id = segment.get("asset_id")
        if not isinstance(asset_id, str) or not ID_PATTERN.fullmatch(asset_id):
            raise RenderError("Invalid storyboard asset ID")
        check_text(segment.get("overlay_text"), "overlay_text", 110)
        if asset_id not in assets:
            raise RenderError(f"Unknown asset_id {asset_id}")
        entry = assets[asset_id]
        if not isinstance(entry, dict) or entry.get("kind") != "image":
            raise RenderError(f"Asset {asset_id}: image required")
        validate_rights(entry.get("rights"), asset_id, allow_test_media)
        resolved[asset_id] = checked_path(asset_root, entry.get("path"), asset_id, IMAGE_SUFFIXES)
    if abs(current - DURATION) > 0.00001:
        raise RenderError("Storyboard must total exactly 30 seconds")
    music_id = reel.get("music_asset_id")
    music = None
    if music_id is not None:
        if not isinstance(music_id, str) or not ID_PATTERN.fullmatch(music_id) or music_id not in assets:
            raise RenderError("Unknown music_asset_id")
        entry = assets[music_id]
        if not isinstance(entry, dict) or entry.get("kind") != "audio":
            raise RenderError("Audio asset required for music_asset_id")
        validate_rights(entry.get("rights"), music_id, allow_test_media)
        music = checked_path(asset_root, entry.get("path"), music_id, AUDIO_SUFFIXES)
    cta = check_text(reel.get("cta"), "CTA", 110)
    return storyboard, resolved, music, cta


def escape_filter_path(path):
    # Inputs are paths to our own temporary text files; never interpolate user text.
    return str(path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")


def overlay_filter(text_file, y, fontsize):
    return (
        "drawtext=font='DejaVu Sans':textfile='"
        + escape_filter_path(text_file)
        + f"':fontsize={fontsize}:fontcolor=white:line_spacing=12:"
        "borderw=2:bordercolor=black@0.8:box=1:boxcolor=black@0.6:"
        f"boxborderw=18:x=(w-text_w)/2:y={y}"
    )


def create_textfile(directory, name, value, wrap_width):
    path = directory / name
    path.write_text(textwrap.fill(value, width=wrap_width, break_long_words=True), encoding="utf-8")
    return path


def render(storyboard, images, music, cta, output, width=1080, height=1920,
           fps=24, preset="veryfast", offer_text=None):
    if width <= 0 or height <= 0 or width * 16 != height * 9:
        raise RenderError("Resolution must be 9:16 portrait")
    if fps not in (12, 15, 24, 25, 30):
        raise RenderError("Unsupported FPS")
    if preset not in ("ultrafast", "superfast", "veryfast", "faster", "fast", "medium"):
        raise RenderError("Unsupported encoder preset")
    if offer_text is not None:
        offer_text = check_text(offer_text, "Explicit approved offer", 110)
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="retail-reel-") as scratch:
        working = Path(scratch)
        ff = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y"]
        chains = []
        for i, segment in enumerate(storyboard):
            duration = float(segment["duration_seconds"]) + (TRANSITION if i < len(storyboard) - 1 else 0)
            ff.extend(["-loop", "1", "-framerate", str(fps), "-t", f"{duration:.6f}",
                       "-i", str(images[segment["asset_id"]])])
            label = f"v{i}"
            title_file = create_textfile(working, f"title{i}.txt", segment["overlay_text"], 24)
            steps = [
                f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease",
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black",
                "setsar=1", "format=yuv420p",
                f"trim=duration={duration:.6f}", "setpts=PTS-STARTPTS",
                overlay_filter(title_file, "h*0.72", max(26, width // 20)),
            ]
            if offer_text and i == 0:
                offer_file = create_textfile(working, "offer.txt", offer_text, 23)
                steps.append(overlay_filter(offer_file, "h*0.12", max(27, width // 20)))
            if i == len(storyboard) - 1:
                cta_file = create_textfile(working, "cta.txt", cta, 26)
                steps.append(overlay_filter(cta_file, "h*0.88", max(25, width // 22)))
            chains.append(",".join(steps) + f"[{label}]")
        for i in range(1, len(storyboard)):
            prev = f"v0" if i == 1 else f"x{i-1}"
            dst = f"x{i}"
            offset = sum(float(s["duration_seconds"]) for s in storyboard[:i])
            chains.append(
                f"[{prev}][v{i}]xfade=transition=fade:duration={TRANSITION}:"
                f"offset={offset:.6f}[{dst}]"
            )
        chains.append(f"[x{len(storyboard)-1}]fps={fps},trim=duration=30,"
                      "setpts=PTS-STARTPTS,format=yuv420p[vout]")
        if music:
            ff.extend(["-stream_loop", "-1", "-i", str(music)])
            audio_input = f"{len(storyboard)}:a:0"
        else:
            ff.extend(["-f", "lavfi", "-t", "30", "-i",
                       "anullsrc=channel_layout=stereo:sample_rate=44100"])
            audio_input = f"{len(storyboard)}:a:0"
        ff.extend([
            "-filter_complex", ";".join(chains),
            "-map", "[vout]", "-map", audio_input,
            "-af", "atrim=duration=30,asetpts=PTS-STARTPTS,afade=t=out:st=29:d=1",
            "-t", "30", "-r", str(fps), "-threads", "2",
            "-c:v", "libx264", "-preset", preset, "-crf", "24",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
            "-ar", "44100", "-ac", "2", "-movflags", "+faststart",
            str(working / "render.mp4"),
        ])
        try:
            subprocess.run(ff, check=True, capture_output=True, text=True, timeout=780)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            detail = getattr(exc, "stderr", "") or str(exc)
            raise RenderError(f"FFmpeg failed: {detail[-2500:]}") from exc
        summary = verify_reel(working / "render.mp4", width, height)
        (working / "render.mp4").replace(output)
        return summary


def main():
    p = argparse.ArgumentParser(description="Offline, licensed, tenant-bound 30s Instagram Reel renderer")
    p.add_argument("--campaign", required=True, help="Frozen v1 campaign JSON")
    p.add_argument("--manifest", required=True, help="Server-created asset ID + rights map")
    p.add_argument("--asset-root", required=True, help="Server-controlled local media staging directory")
    p.add_argument("--day-index", type=int, required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--width", type=int, default=1080)
    p.add_argument("--height", type=int, default=1920)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--preset", default="veryfast")
    p.add_argument("--offer-text", help="ONLY a human-approved offer from the campaign brief")
    p.add_argument("--allow-test-media", action="store_true",
                   help="Allow synthetic_test rights; NEVER use in production")
    args = p.parse_args()
    try:
        storyboard, images, music, cta = load_job(
            args.campaign, args.manifest, args.asset_root, args.day_index, args.allow_test_media
        )
        result = render(storyboard, images, music, cta, args.output,
                        args.width, args.height, args.fps, args.preset, args.offer_text)
        print(json.dumps({"result": "PASS", "path": str(Path(args.output).resolve()), **result}))
    except (RenderError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"RENDER FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
