"""Durable at-least-once outbox dispatcher and poison receipts (server-only).

The database INSERT trigger is the source of truth; queue sends can duplicate when
Azure accepted a message but the PostgREST confirmation failed. Worker attempt/token
fencing makes those deliveries safe. Never ACK poison before the receipt commits.
"""
from __future__ import annotations

from hashlib import sha256
from uuid import UUID

from tenant_store import StorageUnavailable, canonical_uuid


def dispatch_outbox(admin, planning_queue, render_queue, *, limit=20):
    """Claim DB events first; send UUIDs only; confirm with a CAS dispatch token.

    Queue failure is recorded as a retryable DB state. A failed confirmation is
    propagated: the lease expires for replay, even if send actually succeeded.
    """
    if not 1 <= limit <= 50:
        raise ValueError("unsafe outbox batch")
    count = 0
    for event in admin.claim_outbox(limit):
        if not isinstance(event, dict):
            raise StorageUnavailable("malformed outbox event")
        kind = event.get("kind")
        if kind not in ("planning", "render"):
            raise StorageUnavailable("unknown outbox job kind")
        canonical_uuid(event["id"])
        canonical_uuid(event["lease_token"])
        job_id = canonical_uuid(event["job_id"])
        queue = planning_queue if kind == "planning" else render_queue
        try:
            queue.enqueue(job_id)
        except Exception:
            # False confirmation preserves the row and schedules bounded backoff.
            admin.confirm_outbox(event, False)
        else:
            admin.confirm_outbox(event, True)
            count += 1
    return count


def record_poison(admin, kind, raw_body):
    """Persist deduplicated poison evidence before returning/ACKing the message.

    Even malformed/unknown job IDs are durably fingerprinted; they cannot be used
    to update another tenant's job. The timer reconciler performs safe replay.
    """
    if kind not in ("planning", "render"):
        raise ValueError("unrecognized poison queue")
    if not isinstance(raw_body, bytes):
        raise ValueError("poison payload must be bytes")
    digest = sha256(raw_body).hexdigest()
    job_id = None
    if len(raw_body) == 36:
        try:
            candidate = raw_body.decode("ascii", "strict")
            job_id = canonical_uuid(candidate)
        except (UnicodeError, ValueError):
            pass
    admin.record_poison(kind, digest, job_id)
    return job_id


def reconcile_and_dispatch(admin, planning_queue, render_queue):
    """Scheduled reconciler: CAS terminal/replay in PG, then dispatch ready rows."""
    result = admin.reconcile()
    if not isinstance(result, dict):
        raise StorageUnavailable("invalid reconciliation result")
    dispatched = dispatch_outbox(admin, planning_queue, render_queue)
    return {"reconciliation": result, "dispatched": dispatched}
