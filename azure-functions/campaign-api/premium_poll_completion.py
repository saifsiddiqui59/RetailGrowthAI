"""Source-only, fail-closed Wan poll -> verified private clip completion.

No Azure trigger is registered here. A future protected service-role store must
claim IMPORTING jobs atomically and issue a fenced lease. Never send provider
URLs into HTTP responses, job queues, customer-visible DB rows or logs.
"""
from __future__ import annotations

import re

from premium_private_import import (
    PremiumImportError, import_to_private_storage, validate_vendor_video_url,
)
from tenant_store import canonical_uuid

TASK_ID = re.compile(r"^[A-Za-z0-9_-]{8,128}$")


class PremiumCompletionError(RuntimeError):
    """Safe error with no provider URL, token, tenant prompt or raw payload."""


class PremiumPollCompletion:
    """Only the already-reserved, claim-fenced IMPORTING job can import video.

    store.claim_import(job_id) MUST be an atomic service-role DB RPC that
    returns id, shop_id, attempt_token, provider_task_id, status, seconds,
    reservation_confirmed and holds the active lease. The returned claim
    must come exclusively from the database, not from an HTTP/queue payload.
    store.finalize(job, shop, lease, private_path) MUST atomically verify this
    same active lease, tenant membership, and existing reservation.
    """

    def __init__(self, store, provider, media, *, enabled=False, opener=None,
                 probe=None):
        self.store, self.provider, self.media = store, provider, media
        self.enabled, self.opener, self.probe = enabled, opener, probe

    def run_once(self, job_id):
        jid = canonical_uuid(job_id)
        if not self.enabled:
            raise PremiumCompletionError("Premium private completion is disabled")

        claim = self.store.claim_import(jid)
        if claim is None:
            return {"job_id": jid, "status": "NOT_CLAIMED"}
        try:
            sid = canonical_uuid(claim["shop_id"])
            token = canonical_uuid(claim["attempt_token"])
            assert canonical_uuid(claim["id"]) == jid
            assert claim["status"] == "IMPORTING"
            assert claim["reservation_confirmed"] is True
            seconds = claim["seconds"]
            assert type(seconds) is int and 2 <= seconds <= 15
            task_id = claim["provider_task_id"]
            assert isinstance(task_id, str) and TASK_ID.fullmatch(task_id)
        except (AssertionError, AttributeError, KeyError, TypeError, ValueError) as exc:
            raise PremiumCompletionError("Premium import claim is invalid") from None

        # One task GET, not another billable create POST. Provider itself
        # requires its independent owner-approved enabled/key/cost gates.
        try:
            result = self.provider.poll_private(task_id)
            if not isinstance(result, dict) or result.get("task_id") != task_id:
                raise PremiumCompletionError("Provider task identity mismatch")
            status = result.get("status")
            if status in ("PENDING", "RUNNING"):
                return {"job_id": jid, "status": "AWAITING_PROVIDER"}
            if status in ("FAILED", "CANCELED", "UNKNOWN"):
                # UNKNOWN can be expiry; neither refund nor paid retry is safe.
                # Operator must reconcile provider billing and state.
                return {"job_id": jid, "status": "RECONCILE"}
            if status != "SUCCEEDED":
                raise PremiumCompletionError("Unsupported provider task state")
            url = result.get("video_url")
            validate_vendor_video_url(url)
            params = {
                "provider_url": url,
                "shop_id": sid,
                "job_id": jid,
                "lease_token": token,
                "expected_seconds": seconds,
                "media": self.media,
                "store": self.store,
                "opener": self.opener,
            }
            if self.probe is not None:
                params["probe"] = self.probe
            complete = import_to_private_storage(**params)
            return {"job_id": jid, "status": "SUCCEEDED",
                    "output_asset_id": canonical_uuid(complete["output_asset_id"])}
        except (PremiumImportError, PremiumCompletionError):
            raise PremiumCompletionError("Premium import needs safe reconciliation") from None
        except Exception:
            # Unexpected provider/store errors also must not leak signed URLs.
            # No silent retry, credit refund, duplicate POST or success flag.
            raise PremiumCompletionError("Premium private completion unavailable") from None
