"""Feature #2: evidence-first, shared trend collection and tenant-aware ranking.

Provider calls are read-only, bounded and off by default until approved configuration.
RSS chart and YouTube mostPopular are *observations*, never proof of virality.
No external text is treated as a prompt or trusted executable instruction.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

UTC = timezone.utc
GOOGLE_RSS = "https://trends.google.com/trending/rss?geo=IN"
YOUTUBE_API = "https://www.googleapis.com/youtube/v3/videos"
REGIONS = {"IN"}
CATEGORY_TERMS = {
    "clothing": ("clothing", "outfit", "fashion", "saree", "kurta", "dress", "style", "festival", "वस्त्र", "फॅशन"),
    "restaurant": ("restaurant", "cafe", "food", "recipe", "dining", "thali", "biryani", "खाद्य", "जेवण"),
    "technology": ("technology", "ai", "software", "coding", "developer", "tech", "विज्ञान"),
    "general": (),
}
INJECTION = re.compile(
    r"(?i)(ignore (all |previous |prior )?(instructions|rules)|system prompt|developer message|"
    r"you are (now |an? )|execute (this|code|command)|<script|javascript:|"
    r"secret key|api[_ -]?key|prompt injection|act as an ai)"
)
TAG = re.compile(r"<[^>]*>")
SPACE = re.compile(r"\s+")


def _clean(value: object, *, limit: int = 160) -> str:
    if not isinstance(value, str):
        return ""
    if "<" in value or ">" in value:
        return ""
    value = SPACE.sub(" ", TAG.sub(" ", unicodedata.normalize("NFKC", value))).strip()
    # Untrusted RSS/YouTube titles must not carry hidden format/bidi, C1,
    # surrogate or paragraph-separator characters into retailer-facing drafts.
    # Keep ordinary Indic combining marks (Mn/Mc), which are not controls.
    if (len(value) > limit or INJECTION.search(value) or
        any(ord(c) < 32 or 0x7f <= ord(c) <= 0x9f or
            unicodedata.category(c) in {"Cf", "Cs", "Zl", "Zp"}
            for c in value)):
        return ""
    return value


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("UTC-aware clock required")
    return value.astimezone(UTC)


def _stamp(value: datetime) -> str:
    return _utc(value).isoformat(timespec="seconds")


def _evidence_url(url: str, source: str) -> str:
    try:
        parsed = urlparse(url)
        hosts = {"google_rss": {"trends.google.com", "www.google.com"},
                 "youtube": {"www.youtube.com"}}[source] if source != "festival_calendar" else None
        valid_host = ((parsed.hostname in hosts) if hosts is not None
                      else (parsed.hostname == "gov.in" or
                            (parsed.hostname or "").endswith(".gov.in")))
        if (parsed.scheme != "https" or not valid_host or
                parsed.username or parsed.password or parsed.port or
                len(url) > 600 or any(ord(c) < 32 for c in url)):
            return ""
        return url
    except (ValueError, KeyError, TypeError):
        return ""


@dataclass(frozen=True)
class Trend:
    trend_id: str
    source: str
    title: str
    category: str
    region: str
    language: str
    observed_at: str
    expires_at: str
    evidence_url: str
    popularity_value: int | None = None
    popularity_kind: str | None = None
    source_published_at: str | None = None
    event_date: str | None = None

    def public(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SourceState:
    source: str
    status: str  # ok / disabled / unavailable / quota_limited / incomplete
    observed_at: str | None
    count: int
    message: str


def _trend(source: str, title: str, category: str, language: str, url: str,
           now: datetime, *, popularity: int | None = None,
           popularity_kind: str | None = None, ttl_hours: int = 30,
           source_published_at: datetime | None = None,
           event_date: str | None = None) -> Trend | None:
    cleaned = _clean(title, limit=140)
    evidence = _evidence_url(url, source)
    if not cleaned or not evidence or category not in CATEGORY_TERMS:
        return None
    trend_id = hashlib.sha256(f"{source}|IN|{cleaned.casefold()}".encode()).hexdigest()[:32]
    return Trend(trend_id, source, cleaned, category, "IN", language,
                 _stamp(now), _stamp(now + timedelta(hours=ttl_hours)), evidence,
                 popularity, popularity_kind,
                 _stamp(source_published_at) if source_published_at else None,
                 event_date)


class _NoRedirect(HTTPRedirectHandler):
    """Do not follow redirects (especially when URL contains a server-side key)."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _default_get(url: str, *, headers: dict | None = None, timeout: int = 8) -> bytes:
    # Fixed allowlisted endpoints only; reject redirects BEFORE making a second
    # network request, so a YouTube API key cannot leak to a redirect target.
    parsed = urlparse(url)
    if url != GOOGLE_RSS:
        values = parse_qs(parsed.query, strict_parsing=True)
        if (parsed.scheme != "https" or parsed.netloc != "www.googleapis.com" or
                parsed.path != "/youtube/v3/videos" or parsed.params or parsed.fragment or
                set(values) != {"part", "chart", "regionCode", "maxResults", "key"} or
                values.get("part") != ["snippet,statistics"] or
                values.get("chart") != ["mostPopular"] or
                values.get("regionCode") != ["IN"] or
                values.get("maxResults") != ["25"] or not values.get("key", [""])[0]):
            raise ValueError("unexpected provider endpoint")
    with build_opener(_NoRedirect()).open(
        Request(url, headers=headers or {"User-Agent": "RetailGrowthAI-Trends/1.0"}),
        timeout=timeout,
    ) as response:
        if response.status != 200 or response.url != url:
            raise ValueError("unexpected provider response/redirect")
        data = response.read(262145)
        if len(data) > 262144:
            raise ValueError("response exceeds size budget")
        return data


def parse_google_rss(payload: bytes, now: datetime) -> list[Trend]:
    if len(payload) > 262144 or b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
        raise ValueError("invalid RSS")
    root = ET.fromstring(payload)
    ns = "{https://trends.google.com/trending/rss}"
    found: list[Trend] = []
    for item in root.findall(".//item")[:40]:
        title = item.findtext("title", "")
        link = item.findtext("link", "").strip()
        raw_traffic = item.findtext(ns + "approx_traffic", "")
        published = None
        pub_date = item.findtext("pubDate")
        if pub_date:
            try:
                published = _utc(parsedate_to_datetime(pub_date))
            except (TypeError, ValueError, IndexError):
                pass
        if published and (published > now + timedelta(minutes=5) or
                          published < now - timedelta(days=2)):
            continue  # stale/future-dated RSS item cannot be promoted as fresh
        # Approximate lower-bound bucket, not an exact observed search count.
        m = re.fullmatch(r"(\d{1,9})([KM])?\+", raw_traffic.replace(",", "").strip())
        approx = int(m.group(1)) * {"K": 1000, "M": 1000000, None: 1}[m.group(2)] if m else None
        category = classify(title)
        trend = _trend("google_rss", title, category, "und", link, now,
                       popularity=approx, popularity_kind="approx_searches_lower_bound" if approx else None,
                       source_published_at=published)
        if trend:
            found.append(trend)
    return found


def classify(value: str) -> str:
    content = _clean(value, limit=500).casefold()
    tokens = set(re.findall(r"[\w]+", content, flags=re.UNICODE))
    for category in ("clothing", "restaurant", "technology"):
        if any(term in tokens for term in CATEGORY_TERMS[category]):
            return category
    return "general"


def parse_youtube(payload: bytes, now: datetime) -> list[Trend]:
    if len(payload) > 262144:
        raise ValueError("response too large")
    data = json.loads(payload)
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise ValueError("unexpected YouTube response")
    found = []
    for item in data["items"][:40]:
        if not isinstance(item, dict):
            continue
        video_id = item.get("id")
        snippet = item.get("snippet") or {}
        if not isinstance(video_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id) or not isinstance(snippet, dict):
            continue
        stat = item.get("statistics") or {}
        views = stat.get("viewCount") if isinstance(stat, dict) else None
        views_int = int(views) if isinstance(views, str) and views.isdecimal() and len(views) <= 18 else None
        title = snippet.get("title", "")
        language = _clean(snippet.get("defaultLanguage") or "und", limit=20) or "und"
        published = None
        raw_date = snippet.get("publishedAt")
        if isinstance(raw_date, str):
            try:
                published = _utc(datetime.fromisoformat(raw_date.replace("Z", "+00:00")))
            except ValueError:
                pass
        if published and published > now + timedelta(minutes=5):
            continue
        trend = _trend("youtube", title, classify(title), language,
                       "https://www.youtube.com/watch?v=" + video_id, now,
                       popularity=views_int, popularity_kind="lifetime_video_views" if views_int is not None else None,
                       source_published_at=published)
        if trend:
            found.append(trend)
    return found


def _enabled(name: str, environ: dict) -> bool:
    return environ.get(name, "").lower() in ("1", "true", "yes")


def collect(now: datetime, *, environ: dict | None = None, get=None, regions=("IN",),
            festival_records: list[dict] | None = None) -> dict:
    """Once-per-day shared collector; storage/scheduling are separate reviewed adapters.

    Never caches API credentials or tenant profile. Every source has an explicit status,
    so empty, disabled and failing sources are not misrepresented as 'no trends'.
    """
    now = _utc(now)
    environ = dict(os.environ if environ is None else environ)
    get = get or _default_get
    signals: list[Trend] = []
    statuses: list[SourceState] = []
    if tuple(regions) != ("IN",):
        raise ValueError("only verified IN regional coverage is supported")
    for source, flag in (("google_rss", "RETAIL_TRENDS_GOOGLE_RSS_ENABLED"),
                         ("youtube", "RETAIL_TRENDS_YOUTUBE_ENABLED")):
        if not _enabled(flag, environ):
            statuses.append(SourceState(source, "disabled", None, 0, "Explicit feature flag off"))
            continue
        key = environ.get("RETAIL_YOUTUBE_DATA_API_KEY", "") if source == "youtube" else ""
        if source == "youtube" and not key:
            statuses.append(SourceState(source, "disabled", None, 0, "Official API credential unavailable"))
            continue
        try:
            if source == "google_rss":
                rows = parse_google_rss(get(GOOGLE_RSS, timeout=8), now)
            else:
                url = YOUTUBE_API + "?" + urlencode({
                    "part": "snippet,statistics", "chart": "mostPopular",
                    "regionCode": "IN", "maxResults": "25", "key": key,
                })
                rows = parse_youtube(get(url, timeout=8), now)
            signals.extend(rows)
            statuses.append(SourceState(source, "ok" if rows else "incomplete",
                                        _stamp(now), len(rows),
                                        "Public RSS observed" if source == "google_rss" else "Official mostPopular chart observed"))
        except Exception as exc:
            # Exceptions, API payload and URL may include credentials; never include details.
            status = "quota_limited" if getattr(exc, "code", None) == 403 and source == "youtube" else "unavailable"
            statuses.append(SourceState(source, status, None, 0, "Provider fetch/parse failed; no results inferred"))
    if festival_records is None:
        statuses.append(SourceState("festival_calendar", "disabled", None, 0,
                                    "Verified-date registry not configured; no event dates inferred"))
    else:
        from .seasonal_calendar import verified_event_rows
        events = verified_event_rows(festival_records, now)
        event_trends = [
            _trend("festival_calendar", row["event"], row["category"],
                   row["language"], row["source"], now, event_date=row["date"])
            for row in events
        ]
        accepted = [event for event in event_trends if event is not None]
        signals.extend(accepted)
        statuses.append(SourceState(
            "festival_calendar", "ok" if accepted else "incomplete",
            _stamp(now), len(accepted), "Source-reviewed government events only"))
    by_key: dict[tuple[str, str], Trend] = {}
    for item in signals:
        key = (item.region, item.title.casefold())
        if key not in by_key or (item.source == "google_rss" and by_key[key].source != "google_rss"):
            by_key[key] = item
    return {"observed_at": _stamp(now), "sources": [asdict(s) for s in statuses],
            "trends": [v.public() for v in sorted(by_key.values(), key=lambda x: x.trend_id)][:60],
            "complete": all(s.status == "ok" for s in statuses)}


def recommendations(snapshot: dict, profile: dict, now: datetime, *, limit: int = 12) -> list[dict]:
    """Personalize a trusted shared snapshot; tenant authorization occurs before invocation."""
    now = _utc(now)
    if not 1 <= limit <= 25:
        raise ValueError("invalid limit")
    if profile.get("category") not in CATEGORY_TERMS or not isinstance(profile.get("city"), str):
        raise ValueError("verified retailer category and city required")
    category = profile["category"]
    language = profile.get("language", "en-IN")
    words = {_clean(p, limit=70).casefold() for p in profile.get("products", [])[:20] if isinstance(p, str)}
    ranked = []
    for value in snapshot.get("trends", [])[:60]:
        try:
            trend = Trend(**value)
            observed = datetime.fromisoformat(trend.observed_at)
            expiry = datetime.fromisoformat(trend.expires_at)
            if observed > now + timedelta(minutes=5) or expiry <= now or (now - observed) > timedelta(days=2):
                continue
            if (trend.region != "IN" or not _evidence_url(trend.evidence_url, trend.source) or
                    not _clean(trend.title, limit=140)):
                continue
        except (ValueError, TypeError, KeyError):
            continue
        # Broad/general chart noise is excluded; do not inject unrelated viral topics.
        product_match = any(p and p in trend.title.casefold() for p in words)
        category_match = trend.category == category
        if not category_match and not product_match:
            continue
        match_language = trend.language in ("und", language, language.split("-")[0])
        age_hours = (now - observed).total_seconds() / 3600
        freshness = max(0, round(25 - age_hours * 0.75))
        score = (55 if category_match else 0) + (20 if product_match else 0) + freshness + (5 if match_language else 0)
        ranked.append({
            "trend_id": trend.trend_id, "title": trend.title, "category": trend.category,
            "city": profile["city"][:80], "language": language,
            "source": trend.source, "observed_at": trend.observed_at,
            "source_published_at": trend.source_published_at,
            "event_date": trend.event_date,
            "expires_at": trend.expires_at, "evidence_url": trend.evidence_url,
            "popularity_value": trend.popularity_value, "popularity_kind": trend.popularity_kind,
            "score": score, "confidence": "medium" if category_match else "low",
            "why_relevant": "Category match" if category_match else "Retailer product keyword match",
            "approval_status": "DRAFT",
        })
    return sorted(ranked, key=lambda x: (-x["score"], x["trend_id"]))[:limit]
