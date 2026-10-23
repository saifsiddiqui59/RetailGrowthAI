"""Part 2: timezone-safe schedule and no-duplicate dispatch decision rules."""
from __future__ import annotations
from datetime import date, datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ScheduleDenied(ValueError):
    pass


def schedule_utc(*, day, clock, zone, now_utc, fold=None):
    """Reject DST gaps/ambiguous wall times unless the customer chose the fold."""
    try:
        wall = datetime.combine(date.fromisoformat(day), time.fromisoformat(clock))
        tz = ZoneInfo(zone)
    except (ValueError, TypeError, ZoneInfoNotFoundError) as exc:
        raise ScheduleDenied("invalid date, local time or IANA timezone") from exc
    if now_utc.tzinfo is None:
        raise ScheduleDenied("UTC clock must be aware")
    options = []
    for candidate_fold in (0, 1):
        aware = wall.replace(tzinfo=tz, fold=candidate_fold)
        when = aware.astimezone(timezone.utc)
        if when.astimezone(tz).replace(tzinfo=None) == wall:
            options.append(when)
    unique = sorted(set(options))
    if not unique:
        raise ScheduleDenied("nonexistent local time due to daylight saving")
    if len(unique) > 1 and fold not in (0, 1):
        raise ScheduleDenied("ambiguous local time: select earlier or later offset")
    chosen = (wall.replace(tzinfo=tz, fold=fold).astimezone(timezone.utc)
              if len(unique) > 1 else unique[0])
    if not now_utc + timedelta(minutes=1) <= chosen <= now_utc + timedelta(days=365):
        raise ScheduleDenied("schedule must be 1 minute to 365 days in the future")
    return chosen


def dispatch_eligibility(*, job_status, scheduled_at, now_utc, approved_digest_matches,
                         account_connected, membership_active, render_approved,
                         quota_reserved, provider_access_approved):
    """Inputs MUST come from server-verified rows, never from a browser payload."""
    if scheduled_at.tzinfo is None or now_utc.tzinfo is None:
        raise ScheduleDenied("aware timestamps required")
    return bool(
        job_status in {"APPROVED", "QUEUED", "RETRYABLE"}
        and scheduled_at <= now_utc
        and approved_digest_matches and account_connected and membership_active
        and render_approved and quota_reserved and provider_access_approved
    )


def failure_transition(*, attempts, ambiguous, retryable, retry_after_seconds=None):
    """Never re-POST a possibly successful provider write without reconciliation."""
    if ambiguous:
        return "RECONCILE", None
    if not isinstance(attempts, int) or attempts < 1 or attempts > 5:
        raise ScheduleDenied("invalid attempt counter")
    if retryable and attempts < 5:
        default_backoff = (60, 300, 900, 1800)[attempts - 1]
        if retry_after_seconds is None:
            delay = default_backoff
        else:
            if not isinstance(retry_after_seconds, int) or not 0 <= retry_after_seconds <= 86400:
                raise ScheduleDenied("invalid retry-after")
            delay = max(default_backoff, retry_after_seconds)
        return "RETRYABLE", delay
    return "FAILED", None
