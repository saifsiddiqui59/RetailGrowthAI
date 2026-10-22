#!/usr/bin/env python3
"""Read-only, privacy-safe job reliability metrics from a supplied JSON snapshot.

Example: python -m ops.monitor < locally-exported-jobs.json
No network calls, tenant identifiers or personal content in the output.
"""
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

from .recovery import Job, decide, utc_time


def summarize(rows, now, *, poison_depths=None):
    now = utc_time(now)
    poison_depths = poison_depths or {}
    if (not isinstance(poison_depths, dict)
            or any(k not in ("planning", "render") or type(v) is not int or v < 0
                   for k, v in poison_depths.items())):
        raise ValueError("invalid poison queue depths")
    counts = Counter()
    actions = Counter()
    delayed = Counter()
    for record in rows:
        kind = record["kind"]
        job = Job(kind=kind, job_id=record["id"], status=record["status"],
                  attempts=record["attempts"], created_at=record["created_at"],
                  lease_until=record.get("lease_until"))
        counts[kind + "." + job.status] += 1
        decision = decide(job, now)
        if decision.action in ("requeue", "mark_failed"):
            actions[kind + "." + decision.action] += 1
        if job.status not in ("DRAFT", "READY", "SUCCEEDED", "FAILED"):
            if now - job.created_at > timedelta(minutes=15):
                delayed[kind] += 1
    return {"total": sum(counts.values()), "statuses": dict(sorted(counts.items())),
            "recoverable": dict(sorted(actions.items())),
            "older_than_15m": dict(sorted(delayed.items())),
            "poison_queue_depths": dict(sorted(poison_depths.items())),
            "requires_operator": bool(actions or delayed or any(poison_depths.values()))}


def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
            raise ValueError("expected {'jobs':[...]} snapshot")
        now = utc_time(payload.get("now") or datetime.now(timezone.utc))
        result = summarize(payload["jobs"], now,
                           poison_depths=payload.get("poison_depths", {}))
        print(json.dumps(result, sort_keys=True))
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print("Invalid offline monitoring snapshot: " + type(exc).__name__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
