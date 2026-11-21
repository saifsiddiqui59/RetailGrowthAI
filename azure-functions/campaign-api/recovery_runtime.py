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


def dispatch_feature4_cpu_outbox(admin, cpu_queue, *, limit=10):
    """Service-only F4 v2 outbox: UUID-only messages and CAS acknowledge.

    A lost queue ACK can lead to duplicate delivery. The SQL job lease token
    fences every render; never auto-retry a blind billable HTTP submission.
    """
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("invalid CPU outbox limit")
    sent = 0
    for event in admin.feature4_outbox_claim(limit):
        if type(event) is not dict or set(event) != {
            "id", "job_id", "lease_token"}:
            raise StorageUnavailable("untrusted CPU outbox event")
        canonical_uuid(event["id"])
        canonical_uuid(event["lease_token"])
        job_id = canonical_uuid(event["job_id"])
        try:
            cpu_queue.enqueue(job_id)
        except Exception:
            admin.feature4_outbox_confirm(event, False)
        else:
            admin.feature4_outbox_confirm(event, True)
            sent += 1
    return sent


def reconcile_feature4_cpu(admin, cpu_queue):
    """Recover bounded stale leases, then dispatch the distinct F4 v2 outbox."""
    recovered = admin.feature4_reconcile()
    if type(recovered) is not int or recovered < 0:
        raise StorageUnavailable("invalid F4 CPU reconciliation result")
    return {
        "recovered": recovered,
        "dispatched": dispatch_feature4_cpu_outbox(admin, cpu_queue),
    }


def record_feature4_cpu_poison(admin, raw_body):
    """Persist v2 poison fingerprint before Azure poison queue ACK."""
    if type(raw_body) is not bytes:
        raise ValueError("CPU poison body must be bytes")
    fingerprint = sha256(raw_body).hexdigest()
    job_id = None
    if len(raw_body) == 36:
        try:
            job_id = canonical_uuid(raw_body.decode("ascii", "strict"))
        except (UnicodeError, ValueError, TypeError):
            pass
    admin.feature4_record_poison(fingerprint, job_id)
    return job_id
