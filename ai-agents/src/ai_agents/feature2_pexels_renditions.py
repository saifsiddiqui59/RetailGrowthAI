"""Rendition picking adapted from real MIT MoneyPrinterTurbo app/services/material.py.

Upstream: harry0703/MoneyPrinterTurbo
Pinned commit: fd5127e81721f36f0a85aee21b298cc5f4452f42
Original file Git blob: 84431d1152a3e2adebfe83fdfe90ebd600ee51a3
License: MIT, copyright (c) 2024 Harry (see ai-agents/oss/MoneyPrinterTurbo/LICENSE)
Adaptations: no Pexels HTTP/API-key logic, no downloader, no video parser,
no unreviewed media accepted as licensed; bounded pure-data selection only.
The original prefers the *smallest rendition that can fill the canvas*, not
the largest expensive remote file, while rejecting incorrect orientations.
"""
from __future__ import annotations
import math


def _matches_video_aspect(width, height, aspect: str) -> bool:
    # Adapted from MoneyPrinterTurbo._matches_video_aspect().
    if aspect not in ("portrait", "landscape", "square"):
        raise ValueError("Unrecognized output aspect")
    try:
        w, h = int(float(width)), int(float(height))
    except (OverflowError, TypeError, ValueError):
        return False
    if w <= 0 or h <= 0 or w > 16384 or h > 16384:
        return False
    if aspect == "portrait":
        return h > w
    if aspect == "landscape":
        return w > h
    return w == h


def choose_pexels_rendition(video: dict, *, aspect: str = "portrait",
                           minimum_width: int = 1080,
                           minimum_height: int = 1920) -> dict | None:
    """Adapt MoneyPrinterTurbo.search_videos_pexels() rendition loop.

    Returns source metadata, never bytes, storage authorization or a license.
    Caller MUST validate CDN origin and verify original bytes before importing.
    """
    if (not isinstance(video, dict) or aspect not in
        ("portrait", "landscape", "square") or
        type(minimum_width) is not int or type(minimum_height) is not int or
        not 1 <= minimum_width <= 8192 or not 1 <= minimum_height <= 8192):
        raise ValueError("Invalid vetted Pexels dimensions")
    renditions = []
    for candidate in video.get("video_files", []):
        if not isinstance(candidate, dict):
            continue
        try:
            w = int(candidate.get("width"))
            h = int(candidate.get("height"))
        except (OverflowError, ValueError, TypeError):
            continue
        url = candidate.get("link")
        if (not isinstance(url, str) or not url or
            candidate.get("file_type") != "video/mp4" or
            not _matches_video_aspect(w, h, aspect) and aspect != "square" or
            w < minimum_width or h < minimum_height):
            continue
        # Prefer smallest adequate rendition exactly as the pinned project does.
        renditions.append((w * h, w, h, url))
    if not renditions:
        return None
    _, w, h, url = min(renditions, key=lambda item: item[0])
    return {
        "provider": "pexels", "asset_id": str(video.get("id", "")),
        "link": url, "width": w, "height": h,
        "original_bytes_verified": False, "commercial_use_approved": False,
        "can_publish": False,
    }


def select_materials_until_duration(materials: list[dict],
                                    *, max_clip_duration: int,
                                    audio_duration: float,
                                    current_duration: float = 0) -> list[dict]:
    """Adapt pinned MPT _select_materials_until_duration() prefix algorithm.

    Select only enough ordered cutaway candidates to cover a narration's
    length; uses metadata, not FFmpeg or proof of playable/licensed originals.
    """
    if (type(materials) is not list or len(materials) > 100 or
        type(max_clip_duration) is not int or not 1 <= max_clip_duration <= 30 or
        not isinstance(audio_duration, (int, float)) or
        not isinstance(current_duration, (int, float)) or
        not math.isfinite(audio_duration) or not math.isfinite(current_duration) or
        audio_duration <= 0 or current_duration < 0):
        raise ValueError("Invalid bounded cutaway plan")
    selected = []
    total = float(current_duration)
    for item in materials:
        if (not isinstance(item, dict) or
            type(item.get("duration_seconds")) not in (int, float) or
            not math.isfinite(item["duration_seconds"]) or
            item["duration_seconds"] <= 0):
            raise ValueError("Invalid stock duration")
        selected.append(item)
        total += min(max_clip_duration, item["duration_seconds"])
        if total > audio_duration:  # Original MIT algorithm: strict > threshold.
            break
    return selected
