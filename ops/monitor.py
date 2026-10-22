#!/usr/bin/env python3
"""Read-only, privacy-safe job reliability metrics from a supplied JSON snapshot.

Example: python -m ops.monitor < locally-exported-jobs.json
No network calls, tenant identifiers or personal content in the output.
"""
import json
import sys
from collections import Counter
from datetime import datetime, timezone

from .recovery import Job, decide, utc_time


def summarize(rows, now):
    now = utc_time(now)
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
            if now - job.created_at > __import__("datetime").timedelta(minutes=15):
                delayed[kind] += 1
    return {"total": sum(counts.values()), "statuses": dict(sorted(counts.items())),
            "recoverable": dict(sorted(actions.items())),
            "older_than_15m": dict(sorted(delayed.items())),
            "requires_operator": bool(actions or delayed)}


def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
            raise ValueError("expected {'jobs':[...]} snapshot")
        now = utc_time(payload.get("now") or datetime.now(timezone.utc))
        result = summarize(payload["jobs"], now)
        print(json.dumps(result, sort_keys=True))
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print("Invalid offline monitoring snapshot: " + type(exc).__name__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
