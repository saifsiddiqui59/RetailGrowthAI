"""Part 3: source-only, fail-closed cancellation of *unsubmitted* premium jobs.

No HTTP route, migration or worker is activated by importing this module.
Only a future reviewed service-role DB transaction may actually cancel a job.
"""
from __future__ import annotations

from tenant_store import canonical_uuid, StorageUnavailable


class PremiumCancelBoundary:
    """JWT-scoped request guard before ONE authoritative DB cancellation RPC.

    Required store.cancel_unsubmitted_atomic(job_id, shop_id, user_id):
      - A SINGLE database transaction serializes against QUEUED -> SUBMITTING.
      - Rechecks active OWNER/EDITOR membership, exact shop and job, and a
        reservation in the EXISTING shop_usage_reservations ledger.
      - Requires status QUEUED, provider_task_id NULL, attempt_token NULL.
      - Sets CANCELED, releases the premium reservation and records a durable
        audit/credit release receipt atomically.
      - Returns an exact receipt, or None if any precondition has changed.
      - NEVER touches SUBMITTING/PENDING/RUNNING/UNKNOWN/IMPORTING jobs.
    Until that RPC and its concurrency tests exist this boundary must remain OFF.
    """

    def __init__(self, users, store, *, enabled=False):
        self.users, self.store, self.enabled = users, store, enabled

    def cancel(self, token, user_id, job_id):
        if not self.enabled:
            return 503, {"error": "PREMIUM_VIDEO_DISABLED"}
        try:
            uid, jid = canonical_uuid(user_id), canonical_uuid(job_id)
        except (TypeError, ValueError):
            return 400, {"error": "INVALID_REQUEST"}
        try:
            job = self.store.get_authenticated(token, jid)
            if not isinstance(job, dict) or job.get("id") != jid:
                return 404, {"error": "NOT_FOUND"}
            sid = canonical_uuid(job["shop_id"])
            if not self.users.member(token, uid, sid, write=True):
                return 404, {"error": "NOT_FOUND"}
            if job.get("status") == "CANCELED":
                # Require persisted proof; CANCELED alone is not proof of a
                # provider-free cancellation or refundable credit release.
                if (job.get("credit_released") is True and
                    job.get("provider_submission_not_started") is True and
                    job.get("provider_task_id") is None):
                    return 200, {"job_id": jid, "status": "CANCELED"}
                return 409, {"error": "CANCELLATION_REQUIRES_RECONCILIATION"}
            if (job.get("status") != "QUEUED" or
                job.get("provider_task_id") is not None or
                job.get("attempt_token") is not None):
                return 409, {"error": "CANCELLATION_REQUIRES_RECONCILIATION"}

            receipt = self.store.cancel_unsubmitted_atomic(jid, sid, uid)
            if receipt is None:
                # Race with another worker: no refund or state assertion.
                return 409, {"error": "CANCELLATION_REQUIRES_RECONCILIATION"}
            if (not isinstance(receipt, dict) or
                receipt.get("id") != jid or
                receipt.get("shop_id") != sid or
                receipt.get("status") != "CANCELED" or
                receipt.get("credit_released") is not True or
                receipt.get("provider_submission_not_started") is not True or
                receipt.get("provider_task_id") is not None):
                # Fail closed if DB RPC cannot prove a transactional refund.
                return 503, {"error": "CANCELLATION_RECEIPT_UNVERIFIED"}
            return 200, {"job_id": jid, "status": "CANCELED"}
        except (StorageUnavailable, ValueError, TypeError, KeyError):
            return 503, {"error": "SERVICE_UNAVAILABLE"}
