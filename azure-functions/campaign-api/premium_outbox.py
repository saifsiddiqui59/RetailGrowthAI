"""Source-only premium outbox/poison/recovery boundary, disabled by default.

Requires unimplemented, audited service-role Postgres RPCs. No real timer,
queue trigger, cloud account or premium paid API is created here.

An at-least-once queue ACK can be ambiguous; underlying SQL job claim/lease
must fence *all* worker actions so replays NEVER duplicate provider POSTs.
"""
from __future__ import annotations

import hashlib
from tenant_store import StorageUnavailable, canonical_uuid


class PremiumRuntimeDisabled(RuntimeError):
    pass


def dispatch_premium_outbox(store, queue, *, enabled=False, limit=20):
    if not enabled:
        raise PremiumRuntimeDisabled("Premium publishing is disabled")
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError("Invalid premium outbox batch limit")
    events = store.claim_outbox(limit)
    if not isinstance(events, list):
        raise StorageUnavailable("Invalid premium outbox claim")
    count = 0
    for event in events:
        if not isinstance(event, dict) or event.get("kind") != "premium_video":
            raise StorageUnavailable("Invalid premium outbox type")
        try:
            event_id = canonical_uuid(event["id"])
            lease = canonical_uuid(event["lease_token"])
            jid = canonical_uuid(event["job_id"])
        except (ValueError, KeyError, TypeError) as exc:
            raise StorageUnavailable("Invalid premium outbox receipt") from None

        try:
            queue.enqueue(jid)
        except Exception:
            # A failed send does not prove the queue rejected the message.
            # SQL retains the event for CAS-fenced replay; do not claim
            # success or create any provider job here.
            store.confirm_outbox(event_id, lease, False)
        else:
            store.confirm_outbox(event_id, lease, True)
            count += 1
    return count


def record_premium_poison(store, raw_body, *, enabled=False):
    if not enabled:
        raise PremiumRuntimeDisabled("Premium poison recovery is disabled")
    if not isinstance(raw_body, bytes) or len(raw_body) > 65536:
        raise ValueError("Invalid premium poison body")
    fingerprint = hashlib.sha256(raw_body).hexdigest()
    try:
        candidate = raw_body.decode("ascii") if len(raw_body) == 36 else ""
        jid = canonical_uuid(candidate) if candidate else None
    except (UnicodeError, ValueError):
        jid = None
    # NEVER let a poison message directly set any customer/job status.
    # Durable receipt, then operator/reconciler reviews cost and provider.
    if store.record_poison("premium_video", fingerprint, jid) is not True:
        raise StorageUnavailable("Premium poison receipt was not durable")
    return jid


def reconcile_premium_and_dispatch(store, queue, *, enabled=False):
    if not enabled:
        raise PremiumRuntimeDisabled("Premium recovery is disabled")
    result = store.reconcile()
    if not isinstance(result, dict):
        raise StorageUnavailable("Invalid premium reconciliation receipt")
    # Implementing SQL must NEVER turn UNKNOWN/SUBMITTING into QUEUED:
    # an uncertain provider POST may have been charged.
    count = dispatch_premium_outbox(store, queue, enabled=True)
    return {"reconciliation": result, "dispatched": count}
