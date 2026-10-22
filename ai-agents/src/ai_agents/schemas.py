"""Dependency-free strict v1 request and response validation.

Asset UUIDs here are references, NOT proof of ownership or permission to render.
The authenticated API layer must authorize them against a tenant-aware asset store.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo


class ContractError(ValueError):
    """A v1 campaign contract violation."""


def _object(value: Any, name: str) -> dict:
    if not isinstance(value, dict):
        raise ContractError(f"{name} must be an object")
    return value


def _text(value: Any, name: str, maximum: int = 1000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ContractError(f"{name} must be nonempty text (max {maximum})")
    return value.strip()


def _date(value: Any, name: str) -> date:
    try:
        return date.fromisoformat(_text(value, name, 10))
    except ValueError as exc:
        raise ContractError(f"{name} must be ISO YYYY-MM-DD") from exc


def _uuid(value: Any, name: str) -> str:
    try:
        raw = _text(value, name, 36)
        parsed = UUID(raw)
        if str(parsed) != raw.lower():
            raise ValueError("noncanonical UUID")
        return str(parsed)
    except (ValueError, AttributeError) as exc:
        raise ContractError(f"{name} must be a canonical UUID") from exc


def _keys(obj: dict, expected: set[str], label: str) -> None:
    if set(obj) != expected:
        raise ContractError(f"{label} keys mismatch: {sorted(set(obj) ^ expected)}")


def _positive_int(value: Any, name: str) -> int:
    if type(value) is not int or value < 1:
        raise ContractError(f"{name} must be a positive integer")
    return value


@dataclass(frozen=True)
class Offer:
    description: str
    valid_until: date


@dataclass(frozen=True)
class CampaignBrief:
    shop_id: str
    brief: str
    duration_days: int
    start_date: date
    timezone: str
    language: str
    platforms: tuple[str, ...]
    media_asset_ids: tuple[str, ...]
    offer: Offer | None = None

    @classmethod
    def from_dict(cls, value: Any) -> "CampaignBrief":
        obj = _object(value, "brief")
        if set(obj) - {"shop_id", "brief", "duration_days", "start_date",
                       "timezone", "language", "platforms", "media_asset_ids", "offer"}:
            raise ContractError("unknown brief fields")
        shop_id = _uuid(obj.get("shop_id"), "shop_id")
        brief = _text(obj.get("brief"), "brief", 1500)
        days = _positive_int(obj.get("duration_days"), "duration_days")
        if days > 7:
            raise ContractError("duration_days maximum is 7")
        start = _date(obj.get("start_date"), "start_date")
        timezone = _text(obj.get("timezone"), "timezone", 80)
        try:
            ZoneInfo(timezone)
        except (ValueError, KeyError) as exc:
            raise ContractError("timezone must be a valid IANA timezone") from exc
        language = _text(obj.get("language"), "language", 20)
        if language != "en-IN":
            raise ContractError("only en-IN mock copy is currently supported")
        platforms = obj.get("platforms")
        if not isinstance(platforms, list) or len(platforms) != 2 or set(platforms) != {"linkedin", "instagram"}:
            raise ContractError("v1 must request linkedin and instagram")
        raw_ids = obj.get("media_asset_ids")
        if not isinstance(raw_ids, list) or not (1 <= len(raw_ids) <= 21):
            raise ContractError("media_asset_ids must contain 1-21 authorized asset UUIDs")
        ids = tuple(_uuid(item, "media_asset_id") for item in raw_ids)
        if len(set(ids)) != len(ids):
            raise ContractError("duplicate media_asset_id")
        raw_offer = obj.get("offer")
        offer = None
        if raw_offer is not None:
            details = _object(raw_offer, "offer")
            _keys(details, {"description", "valid_until"}, "offer")
            desc = _text(details["description"], "offer.description", 180)
            expires = _date(details["valid_until"], "offer.valid_until")
            if expires < start:
                raise ContractError("offer cannot expire before campaign start")
            offer = Offer(desc, expires)
        return cls(shop_id, brief, days, start, timezone, language,
                   tuple(platforms), ids, offer)


DAY_KEYS = {"id", "campaign_id", "shop_id", "day_index", "scheduled_date",
            "topic", "linkedin", "instagram", "review_status"}


def validate_campaign(data: Any, *, expected_count: int | None = None) -> dict:
    """Validate the complete GET /api/campaigns/{id} response shape."""
    campaign = _object(data, "campaign")
    _keys(campaign, {"id", "shop_id", "status", "days"}, "campaign")
    cid = _uuid(campaign["id"], "campaign.id")
    sid = _uuid(campaign["shop_id"], "campaign.shop_id")
    if campaign["status"] not in {"DRAFT", "PLANNING", "FAILED"}:
        raise ContractError("invalid campaign status")
    items = campaign["days"]
    if not isinstance(items, list) or not 1 <= len(items) <= 7:
        raise ContractError("campaign.days must contain 1-7 days")
    if expected_count is not None and len(items) != expected_count:
        raise ContractError("incorrect number of days")
    dates = []
    ids = set()
    topics = set()
    for index, day in enumerate(items, start=1):
        d = _object(day, f"day {index}")
        _keys(d, DAY_KEYS, f"day {index}")
        did = _uuid(d["id"], "day.id")
        if did in ids:
            raise ContractError("duplicate day ID")
        ids.add(did)
        if _uuid(d["campaign_id"], "day.campaign_id") != cid or _uuid(d["shop_id"], "day.shop_id") != sid:
            raise ContractError("cross-campaign or cross-shop day")
        if type(d["day_index"]) is not int or d["day_index"] != index:
            raise ContractError("day_index out of sequence")
        dates.append(_date(d["scheduled_date"], "scheduled_date"))
        topic = _text(d["topic"], "topic", 140)
        if topic.casefold() in topics:
            raise ContractError("duplicate topic")
        topics.add(topic.casefold())
        if d["review_status"] != "DRAFT":
            raise ContractError("generated work must remain in DRAFT status")
        linkedin = _object(d["linkedin"], "linkedin")
        _keys(linkedin, {"post_text", "hashtags"}, "linkedin")
        _text(linkedin["post_text"], "linkedin.post_text", 3000)
        if not isinstance(linkedin["hashtags"], list) or not linkedin["hashtags"] or any(
            not isinstance(h, str) or not h.startswith("#") or len(h) > 60 for h in linkedin["hashtags"]
        ):
            raise ContractError("invalid LinkedIn hashtags")
        instagram = _object(d["instagram"], "instagram")
        _keys(instagram, {"caption", "banner_asset_id", "reel"}, "instagram")
        _text(instagram["caption"], "instagram.caption", 2200)
        if instagram["banner_asset_id"] is not None:
            _uuid(instagram["banner_asset_id"], "banner_asset_id")
        reel = _object(instagram["reel"], "reel")
        _keys(reel, {"duration_seconds", "aspect_ratio", "storyboard", "music_asset_id", "cta"}, "reel")
        if type(reel["duration_seconds"]) is not int or reel["duration_seconds"] != 30 or reel["aspect_ratio"] != "9:16":
            raise ContractError("reel must be 30s and 9:16")
        if reel["music_asset_id"] is not None:
            _uuid(reel["music_asset_id"], "music_asset_id")
        _text(reel["cta"], "reel.cta", 100)
        shots = reel["storyboard"]
        if not isinstance(shots, list) or not shots:
            raise ContractError("empty storyboard")
        current = 0
        for shot in shots:
            s = _object(shot, "storyboard segment")
            _keys(s, {"start_seconds", "duration_seconds", "asset_id", "overlay_text"}, "storyboard segment")
            if type(s["start_seconds"]) is not int or s["start_seconds"] != current:
                raise ContractError("storyboard gap or overlap")
            current += _positive_int(s["duration_seconds"], "duration_seconds")
            _uuid(s["asset_id"], "asset_id")
            _text(s["overlay_text"], "overlay_text", 100)
        if current != 30:
            raise ContractError("storyboard must total exactly 30 seconds")
    if any(d != dates[0] + timedelta(days=i) for i, d in enumerate(dates)):
        raise ContractError("campaign dates must be consecutive")
    return campaign
