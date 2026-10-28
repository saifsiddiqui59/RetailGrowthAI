"""Feature #2 audio discovery ranking for DRAFT reels.

Source-only recommendation engine; no scraper, streaming music, paid AI or
copyright grant is inferred from a trending sound. An optional SERVER-SIDE
approved-model ranker may reorder a validated shortlist, but cannot authorize
audio use. Kuble-Lab/open-creative-director's pinned MIT upstream music-video
plan remains the beat-aware scene planner downstream of this selection step.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
import re

_ALLOWED_SOURCES = {
    "instagram_reels": ("www.instagram.com", "instagram.com"),
    "youtube_shorts": ("www.youtube.com", "youtube.com", "youtu.be"),
    "meta_sound_collection": ("www.facebook.com", "facebook.com"),
    "pixabay_music": ("pixabay.com", "www.pixabay.com"),
    "tenant_upload": (),
}
_ALLOWED_MOODS = {"festive", "energetic", "elegant", "calm", "playful",
                  "cinematic", "romantic", "modern", "traditional"}
_WORDS = re.compile(r"[a-z0-9]+", re.I)
_CONTEXT = {
    "clothing": {"fashion", "outfit", "dress", "kurti", "kurta", "saree",
                 "boutique", "style", "ethnic", "garment"},
    "restaurant": {"food", "restaurant", "dish", "cafe", "dining"},
    "technology": {"software", "tech", "ai", "coding", "innovation"},
}
_SHA = re.compile(r"^[0-9a-f]{64}$")


class MusicRecommendationRejected(ValueError):
    pass


def _bounded(value: object, label: str, max_len: int = 180) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_len:
        raise MusicRecommendationRejected("Invalid " + label)
    if any(ord(char) < 32 for char in value) or "<" in value or ">" in value:
        raise MusicRecommendationRejected("Unsafe " + label)
    return value.strip()


def _observed(value: object, now: datetime) -> tuple[str, bool]:
    if not isinstance(value, str):
        raise MusicRecommendationRejected("Missing observation timestamp")
    try:
        observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MusicRecommendationRejected("Invalid observation timestamp") from exc
    if observed.tzinfo is None:
        raise MusicRecommendationRejected("Timezone required")
    observed = observed.astimezone(timezone.utc)
    if observed > now + timedelta(minutes=5):
        raise MusicRecommendationRejected("Future observation")
    return observed.isoformat(), observed >= now - timedelta(days=7)


def _safe_source(source: str, url: object) -> str | None:
    if source == "tenant_upload":
        if url is not None:
            raise MusicRecommendationRejected("Private media has no public URL")
        return None
    url = _bounded(url, "evidence URL", 500)
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in _ALLOWED_SOURCES[source]
            or parsed.username or parsed.password or parsed.port is not None):
        raise MusicRecommendationRejected("Untrusted audio evidence URL")
    return url


def recommend_audio(
    *, shop_id: str, creative_brief: str, duration_seconds: int,
    candidates: list[dict], observed_now: datetime, category: str = "clothing",
    ai_ranker=None,
) -> dict:
    """Select up to three review-only sounds from server-supplied candidates.

    ai_ranker is an optional trusted server adapter, not a client JSON field.
    Return IDs only; no streamed bytes or publishing grant is ever generated.
    The runtime must obtain original audio + a tenant-private rights proof
    before any Feature #4 mixer or Part 2 platform submission.
    """
    shop_id = _bounded(shop_id, "shop ID", 90)
    brief = _bounded(creative_brief, "creative brief", 1500)
    if (type(duration_seconds) is not int or duration_seconds not in (15, 30, 60)
            or not isinstance(observed_now, datetime)
            or observed_now.tzinfo is None or type(candidates) is not list
            or len(candidates) > 100 or category not in _CONTEXT):
        raise MusicRecommendationRejected("Invalid audio request")
    now = observed_now.astimezone(timezone.utc)
    brief_words = set(_WORDS.findall(brief.casefold())) | _CONTEXT[category]
    scored = []
    seen = set()
    for row in candidates:
        if type(row) is not dict:
            raise MusicRecommendationRejected("Invalid catalog entry")
        audio_id = _bounded(row.get("audio_id"), "audio ID", 100)
        if audio_id in seen:
            raise MusicRecommendationRejected("Duplicate audio ID")
        seen.add(audio_id)
        source = row.get("source")
        if source not in _ALLOWED_SOURCES:
            raise MusicRecommendationRejected("Unknown audio source")
        title = _bounded(row.get("title"), "track title")
        source_url = _safe_source(source, row.get("evidence_url"))
        timestamp, fresh = _observed(row.get("observed_at"), now)
        # Popularity is an observation only, not proof that sound is viral.
        popularity = row.get("popularity_score", 0)
        if type(popularity) not in (int, float) or not 0 <= popularity <= 100:
            raise MusicRecommendationRejected("Invalid popularity observation")
        tags = row.get("tags", [])
        if (type(tags) is not list or len(tags) > 12
                or any(not isinstance(tag, str) or
                       tag not in _ALLOWED_MOODS for tag in tags)):
            raise MusicRecommendationRejected("Invalid mood tags")
        if source == "tenant_upload" and row.get("shop_id") != shop_id:
            raise MusicRecommendationRejected("Cross-shop uploaded audio reference")
        rights = row.get("rights_status", "UNVERIFIED")
        if rights not in ("UNVERIFIED", "PLATFORM_NATIVE_ONLY",
                          "COMMERCIAL_LICENSE_REVIEW_REQUIRED",
                          "OWNER_RIGHTS_REVIEW_REQUIRED"):
            raise MusicRecommendationRejected("Untrusted music rights assertion")
        description = _bounded(row.get("description", title), "description", 500)
        matching = len(brief_words & set(_WORDS.findall((title + " " + description).casefold())))
        mood = len(set(tags) & ({"festive", "elegant", "traditional"}
                                  if category == "clothing" else
                                  {"energetic", "modern"}))
        score = round(10 * matching + 5 * mood +
                      (min(popularity, 100) / 10 if fresh else 0), 2)
        scored.append({
            "audio_id": audio_id, "source": source, "title": title,
            "evidence_url": source_url, "observed_at": timestamp,
            "fresh_observation": fresh, "relevance_score": score,
            "rights_status": rights,
            "can_attach_to_export": False,
            "can_publish": False,
            "rights_gate": "CURRENT_PRIVATE_LICENSE_AND_PLATFORM_REVIEW_REQUIRED",
            "suggested_use": "BACKGROUND_MUSIC_REVIEW_ONLY",
        })
    scored.sort(key=lambda track: (-track["relevance_score"], track["audio_id"]))
    ranked = scored
    ai_status = "NO_LIVE_AI_RANKER_USED"
    if ai_ranker is not None and scored:
        # Trusted server code can call an approved LLM with sanitized metadata.
        # Verify its response, so a hallucinated track cannot be selected.
        shortlist = tuple({k: item[k] for k in
                           ("audio_id", "source", "title", "relevance_score")}
                          for item in scored[:20])
        response = ai_ranker(brief, shortlist)
        if (type(response) not in (list, tuple) or
                len(response) != len(shortlist) or
                any(type(item) is not str for item in response) or
                set(response) != {item["audio_id"] for item in shortlist}):
            raise MusicRecommendationRejected("Invalid AI audio ranking")
        lookup = {item["audio_id"]: item for item in scored}
        ranked = [lookup[identifier] for identifier in response] + scored[20:]
        ai_status = "TRUSTED_MODEL_RANKER_RETURNED_IDS_OFFLINE_ONLY"
    return {
        "shop_id": shop_id, "duration_seconds": duration_seconds,
        "mode": "DRAFT_AUDIO_RECOMMENDATIONS",
        "ai_ranker_status": ai_status,
        "recommendations": ranked[:3],
        "selected_audio_id": None,
        "can_mix_audio": False, "can_publish": False,
        "gpu_enabled": False, "paid_calls_performed_by_this_module": 0,
        "notes": "Popularity is not a license or proof of virality. Review track, platform and commercial rights before use.",
    }
