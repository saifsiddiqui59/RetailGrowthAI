#!/usr/bin/env python3
"""Read-only operator runbook for retry/poison and orphan inventory.

Usage:
  python -m ops.runbook recovery < snapshots.json
  python -m ops.runbook poison < poison.json
  python -m ops.runbook orphans < storage-inventory.json

No network, requeue, DB mutation, queue acknowledgement or deletion performed.
Never pass raw JWTs/secrets or customer-generated content in input.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone

from .orphan_cleanup import StorageObject, find_orphans
from .recovery import Job, decide, poison_decision, utc_time


def load_job(data):
    if not isinstance(data, dict):
        raise ValueError("invalid job")
    return Job(
        kind=data["kind"], job_id=data["id"], status=data["status"],
        attempts=data["attempts"], created_at=data["created_at"],
        lease_until=data.get("lease_until"))


def plan(mode, payload):
    if mode not in ("recovery", "poison", "orphans") or not isinstance(payload, dict):
        raise ValueError("unsupported mode or input")
    now = utc_time(payload.get("now") or datetime.now(timezone.utc))
    if mode == "recovery":
        jobs = payload["jobs"]
        if not isinstance(jobs, list) or len(jobs) > 10000:
            raise ValueError("invalid job inventory")
        decisions = []
        for data in jobs:
            job = load_job(data)
            decision = decide(job, now)
            if decision.action != "ack_final":
                decisions.append({
                    "kind": job.kind, "job_id": job.job_id,
                    "action": decision.action, "code": decision.code,
                    "fingerprint": decision.fingerprint,
                })
        return {"dry_run": True, "actions": decisions}
    if mode == "poison":
        kind = payload["kind"]
        body = payload["message"]
        if not isinstance(body, str) or len(body) > 256:
            raise ValueError("invalid poison message")
        raw = body.encode("utf-8")
        job = load_job(payload["job"]) if payload.get("job") is not None else None
        decision = poison_decision(kind, raw, job, now)
        # Do not echo malformed message text in operator logs.
        return {"dry_run": True, "action": decision.action, "code": decision.code,
                "fingerprint": decision.fingerprint,
                "message_digest": hashlib.sha256(raw).hexdigest()[:16]}
    items = payload["objects"]
    paths = payload["referenced_paths"]
    if not isinstance(items, list) or not isinstance(paths, list):
        raise ValueError("invalid storage inventory")
    if len(items) > 100000 or len(paths) > 100000:
        raise ValueError("inventory exceeds safe batch size")
    objects = [StorageObject(path=item["path"], etag=item["etag"],
                             updated_at=item["updated_at"]) for item in items]
    candidates = find_orphans(objects, set(paths), now)
    return {"dry_run": True, "eligible": [
        {"path": candidate.item.path, "etag": candidate.item.etag,
         "reason": candidate.reason} for candidate in candidates]}


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m ops.runbook {recovery|poison|orphans} < snapshot.json",
              file=sys.stderr)
        return 2
    try:
        raw = sys.stdin.read(10_000_001)
        if len(raw) > 10_000_000:
            raise ValueError("inventory too large")
        result = plan(sys.argv[1], json.loads(raw))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print("Invalid offline runbook snapshot: " + type(exc).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
