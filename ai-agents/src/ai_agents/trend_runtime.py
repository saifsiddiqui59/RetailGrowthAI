"""Shared daily collection orchestration; external store must implement atomic claim.

A coordinator may bind run_daily_collection to ONE Azure timer and an RLS-backed
Supabase private shared snapshot table. This module performs no provisioning or
unreviewed network calls, and never holds tenant identifiers or AI credentials.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol

from .trend_intelligence import collect


class SnapshotStore(Protocol):
    def load(self, region: str) -> dict | None: ...
    def claim_day(self, region: str, day: str) -> bool: ...
    def save(self, region: str, snapshot: dict) -> None: ...


def run_daily_collection(now: datetime, store: SnapshotStore, *, environ=None, get=None) -> dict:
    """Atomic per-region UTC day claim; retries must not multiply provider calls."""
    if now.tzinfo is None:
        raise ValueError("aware clock required")
    now = now.astimezone(timezone.utc)
    region = "IN"
    day = now.date().isoformat()
    old = store.load(region)
    if not store.claim_day(region, day):
        return {"state": "cached" if old else "incomplete", "snapshot": old,
                "reason": "Collector already claimed this UTC date"}
    result = collect(now, environ=environ, get=get)
    # Include honest failed/disabled source states; don't backfill from unknown
    # older data and label it live.
    store.save(region, result)
    return {"state": "collected" if result["complete"] else "incomplete",
            "snapshot": result, "reason": None}
