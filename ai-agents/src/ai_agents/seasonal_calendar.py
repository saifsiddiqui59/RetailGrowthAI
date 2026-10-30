"""Conservative, source-verified Indian seasonal event ingestion.

No evergreen guessed dates. Calendar rows must be explicitly curated with
an official dated government source and a review status before use.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse

from .trend_intelligence import _clean

def verified_event_rows(records: list[dict], now: datetime) -> list[dict]:
    if now.tzinfo is None or not isinstance(records, list) or len(records) > 120:
        raise ValueError("bounded event rows and aware clock required")
    out = []
    today = now.date()
    for row in records:
        if not isinstance(row, dict) or row.get("verification") != "reviewed":
            continue
        title = _clean(row.get("event", ""), limit=100)
        raw_date = row.get("date")
        official = row.get("official_source_url", "")
        try:
            holiday = date.fromisoformat(raw_date)
            parsed = urlparse(official)
            if (parsed.scheme != "https" or not parsed.hostname or
                not (parsed.hostname == "gov.in" or parsed.hostname.endswith(".gov.in")) or
                parsed.username or parsed.password or parsed.port or
                holiday < today or holiday > today + timedelta(days=90)):
                continue
        except (ValueError, TypeError):
            continue
        try:
            reviewed = date.fromisoformat(row["source_reviewed_at"])
            if reviewed > today or reviewed < today - timedelta(days=120):
                continue
        except (KeyError, TypeError, ValueError):
            continue
        if not title:
            continue
        category = row.get("category", "general")
        if category not in ("clothing", "restaurant", "technology", "general"):
            continue
        out.append({
            "event_id": _clean(row.get("event_id", ""), limit=80),
            "event": title, "date": holiday.isoformat(), "source": official,
            "category": category, "source_reviewed_at": row["source_reviewed_at"],
            "region": "IN", "language": row.get("language", "und"),
        })
    return out
