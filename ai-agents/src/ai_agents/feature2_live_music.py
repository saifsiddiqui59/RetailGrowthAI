"""Opt-in live, read-only music VIDEO popularity discovery from official YouTube.

YouTube Data API videos.list(chart=mostPopular,videoCategoryId=10,regionCode=IN)
is an official music-category video chart, NOT evidence of trending songs on
Instagram/Shorts or a grant to use copyrighted soundtrack audio. Only links,
titles and bounded metadata are returned. Source is disabled by default.
Reuses feature2_music_recommender.recommend_audio for review-only ranking.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .feature2_music_recommender import recommend_audio

ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"
_KEY = re.compile(r"^[a-zA-Z0-9_-]{12,160}$")
_VIDEO_ID = re.compile(r"^[a-zA-Z0-9_-]{11}$")
_BAD_TEXT = re.compile(r"(?i)<|>|ignore previous|system prompt|developer message|javascript:|execute code")
MAX_RESPONSE_BYTES = 262144


class AudioDiscoveryUnavailable(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _get(url: str, *, timeout: int = 8) -> bytes:
    """Allowlist exact request shape; redirect and oversized replies fail closed."""
    parsed = urlsplit(url)
    values = parse_qs(parsed.query, strict_parsing=True)
    if (parsed.scheme != "https" or parsed.netloc != "www.googleapis.com" or
            parsed.path != "/youtube/v3/videos" or parsed.fragment or
            set(values) != {"part", "chart", "regionCode", "videoCategoryId",
                            "maxResults", "key"} or
            values["part"] != ["snippet,statistics"] or
            values["chart"] != ["mostPopular"] or
            values["regionCode"] != ["IN"] or
            values["videoCategoryId"] != ["10"] or
            values["maxResults"] != ["25"] or
            not _KEY.fullmatch(values["key"][0])):
        raise AudioDiscoveryUnavailable("Unapproved music discovery endpoint")
    with build_opener(_NoRedirect()).open(
        Request(url, headers={"User-Agent": "RetailGrowthAI-Feature2-Music/1.0"}),
        timeout=timeout,
    ) as response:
        if response.status != 200 or response.url != url:
            raise AudioDiscoveryUnavailable("Unexpected YouTube response")
        content = response.read(MAX_RESPONSE_BYTES + 1)
        if len(content) > MAX_RESPONSE_BYTES:
            raise AudioDiscoveryUnavailable("Music response exceeds budget")
        return content


def parse_music_popular(payload: bytes, *, now: datetime) -> list[dict]:
    """Convert public video observations into conservative, *unlicensed* choices."""
    if (not isinstance(payload, bytes) or len(payload) > MAX_RESPONSE_BYTES or
            not isinstance(now, datetime) or now.tzinfo is None):
        raise AudioDiscoveryUnavailable("Invalid music observation context")
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, ValueError) as exc:
        raise AudioDiscoveryUnavailable("Invalid YouTube music JSON") from exc
    if (type(document) is not dict or type(document.get("items")) is not list or
            len(document["items"]) > 50):
        raise AudioDiscoveryUnavailable("Invalid music chart shape")
    now = now.astimezone(timezone.utc)
    selected = []
    seen = set()
    for rank, item in enumerate(document["items"][:25], 1):
        if type(item) is not dict:
            continue
        video_id, snippet = item.get("id"), item.get("snippet")
        if (not isinstance(video_id, str) or not _VIDEO_ID.fullmatch(video_id)
                or video_id in seen or type(snippet) is not dict):
            continue
        if snippet.get("categoryId") != "10":
            continue  # We requested music; never accept out-of-category content.
        title, channel = snippet.get("title"), snippet.get("channelTitle")
        if (not isinstance(title, str) or not 1 <= len(title.strip()) <= 150 or
                _BAD_TEXT.search(title) or not isinstance(channel, str) or
                not 1 <= len(channel.strip()) <= 100 or _BAD_TEXT.search(channel)):
            continue
        published = snippet.get("publishedAt")
        if not isinstance(published, str):
            continue
        try:
            published_dt = datetime.fromisoformat(
                published.replace("Z", "+00:00"))
        except ValueError:
            continue
        if (published_dt.tzinfo is None or
                published_dt > now + timedelta(minutes=5)):
            continue
        seen.add(video_id)
        selected.append({
            "audio_id": "youtube-music-video-" + video_id,
            "source": "youtube_music_video",
            "evidence_url": "https://www.youtube.com/watch?v=" + video_id,
            "title": title.strip(),
            "description": channel.strip(),
            "observed_at": now.isoformat(),
            "tags": [], "popularity_score": round(100 * (26-rank) / 25, 2),
            "rights_status": "UNVERIFIED",
        })
    return selected


def discover_music(*, now: datetime, environ=None, get=None) -> dict:
    """One opted-in provider call; never use browser secrets or fake live data."""
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("Timezone-aware clock required")
    env = os.environ if environ is None else environ
    if env.get("RETAIL_FEATURE2_MUSIC_YT_ENABLED", "").lower() != "true":
        return {"status": "DISABLED", "observed_at": None, "candidates": [],
                "provider": "YOUTUBE_MUSIC_CATEGORY_MOST_POPULAR",
                "can_use_audio": False}
    key = env.get("RETAIL_FEATURE2_MUSIC_YT_API_KEY", "")
    if not isinstance(key, str) or not _KEY.fullmatch(key):
        return {"status": "NO_SERVER_API_KEY", "observed_at": None,
                "candidates": [], "provider": "YOUTUBE_MUSIC_CATEGORY_MOST_POPULAR",
                "can_use_audio": False}
    url = ENDPOINT + "?" + urlencode({
        "part": "snippet,statistics", "chart": "mostPopular",
        "regionCode": "IN", "videoCategoryId": "10", "maxResults": "25",
        "key": key,
    })
    try:
        payload = (get or _get)(url, timeout=8)
        candidates = parse_music_popular(payload, now=now)
        return {"status": "OK" if candidates else "EMPTY", "candidates": candidates,
                "observed_at": now.astimezone(timezone.utc).isoformat(),
                "provider": "YOUTUBE_MUSIC_CATEGORY_MOST_POPULAR",
                "can_use_audio": False}
    except Exception:
        # Provider/API key details must not leak; never backfill fictional tracks.
        return {"status": "UNAVAILABLE", "observed_at": None, "candidates": [],
                "provider": "YOUTUBE_MUSIC_CATEGORY_MOST_POPULAR",
                "can_use_audio": False}


def discover_retailer_music(*, shop_id: str, creative_brief: str,
                            duration_seconds: int, now: datetime,
                            authorized_shop_reader, environ=None, get=None):
    """Server caller supplies current signed shop membership reader, not a bool."""
    if (not callable(authorized_shop_reader) or
            not authorized_shop_reader(shop_id)):
        raise PermissionError("Current authenticated retailer membership required")
    collected = discover_music(now=now, environ=environ, get=get)
    if collected["status"] != "OK":
        return {"discovery_status": collected["status"], "shop_id": shop_id,
                "recommendations": [], "can_publish": False,
                "can_mix_audio": False}
    # Re-check after remote call: a revocation during discovery must deny.
    if not authorized_shop_reader(shop_id):
        raise PermissionError("Shop membership revoked during provider call")
    ranked = recommend_audio(
        shop_id=shop_id, creative_brief=creative_brief,
        duration_seconds=duration_seconds, candidates=collected["candidates"],
        observed_now=now)
    return {"discovery_status": "OK", **ranked}
