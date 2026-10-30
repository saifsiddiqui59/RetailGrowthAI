"""Service-only PostgREST transport for Feature3's *existing* GPU ledger.

This does not dispatch a Queue message, authorize the caller's JWT, start CUDA,
approve a model, or deploy a GPU. The SQL reserve RPC checks actual active
OWNER/EDITOR membership, subscription, source revision and default-off budget.
Only trusted server code may instantiate this class with a backend secret.
There is deliberately no automatic retry after an uncertain HTTP outcome.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re

from admin_store import AdminStore
from tenant_store import StorageUnavailable, canonical_uuid

_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_MONEY_MAX = Decimal("2.5")


def _money(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("trusted GPU dollar amount required")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid GPU dollar amount") from exc
    if not amount.is_finite() or amount > _MONEY_MAX or (
        amount <= 0 if positive else amount < 0
    ) or amount.as_tuple().exponent < -6:
        raise ValueError("GPU amount outside six-decimal USD bounds")
    return str(amount)


def _one(rows, description):
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise StorageUnavailable(description)
    return rows[0]


class Feature3GPUServiceStore:
    """Backend-secret RPC calls; no user-facing HTTP route or GPU activation."""

    def __init__(self, origin, service_role_key, *, transport=None):
        self.db = AdminStore(origin, service_role_key, transport=transport)

    def reserve(self, *, shop_id, actor_id, design_id, revision,
                design_sha256, request_id, upper_cost_usd):
        sid, actor, did, rid = map(
            canonical_uuid, (shop_id, actor_id, design_id, request_id)
        )
        if type(revision) is not int or not 1 <= revision <= 1_000_000 or (
            not isinstance(design_sha256, str) or
            not _SHA256.fullmatch(design_sha256)
        ):
            raise ValueError("invalid versioned design receipt")
        amount = _money(upper_cost_usd, positive=True)
        receipt = self.db.request("rpc/feature3_reserve_gpu_job", method="POST", data={
            "p_shop_id": sid, "p_actor_id": actor, "p_design_id": did,
            "p_expected_revision": revision, "p_expected_sha256": design_sha256,
            "p_request_id": rid, "p_upper_cost_usd": amount,
        })
        # The SQL has already committed an authoritative reservation+outbox.
        # A missing/ambiguous acknowledgment is NOT permission to reserve again.
        if (type(receipt) is not dict or set(receipt) != {
                "shop_id", "job_id", "reservation_id", "reserved_usd",
                "status", "gpu_started"} or
                receipt.get("shop_id") != sid or receipt.get("status") != "QUEUED" or
                receipt.get("gpu_started") is not False):
            raise StorageUnavailable("unconfirmed GPU reservation; inspect DB before retry")
        try:
            jid = canonical_uuid(receipt["job_id"])
            reservation = canonical_uuid(receipt["reservation_id"])
            confirmed = _money(receipt["reserved_usd"], positive=True)
        except (ValueError, TypeError, KeyError, AttributeError):
            # SQL may already have committed the reservation. An invalid
            # receipt never authorizes an identical second paid request.
            raise StorageUnavailable(
                "GPU reservation ACK invalid; reconcile before retry") from None
        if Decimal(confirmed) < Decimal(amount):
            raise StorageUnavailable("GPU reservation below requested bound")
        return {
            "shop_id": sid, "job_id": jid, "reservation_id": reservation,
            "reserved_usd": confirmed, "status": "QUEUED", "gpu_started": False,
        }

    def claim(self, job_id, claim_token):
        jid, token = canonical_uuid(job_id), canonical_uuid(claim_token)
        receipt = self.db.request("rpc/feature3_claim_gpu_job", method="POST",
                                  data={"p_job_id": jid, "p_claim_token": token})
        if receipt is None:
            # Already claimed, outbox not SENT, or canceled. Do not requeue.
            return None
        if (type(receipt) is not dict or set(receipt) != {
                "shop_id", "job_id", "attempt", "claim_token"} or
                receipt.get("job_id") != jid or
                receipt.get("claim_token") != token or
                type(receipt.get("attempt")) is not int or
                receipt["attempt"] != 1):
            raise StorageUnavailable("untrusted GPU claim response")
        try:
            shop = canonical_uuid(receipt["shop_id"])
        except (ValueError, TypeError, AttributeError):
            raise StorageUnavailable("Untrusted GPU claim shop ID") from None
        return {"shop_id": shop, "job_id": jid, "attempt": 1, "claim_token": token}

    def read_prepaid_reservation(self, shop_id, job_id, attempt, claim_token):
        """Read the existing reservation; never insert a second charge.

        This is called only AFTER the one-shot claim succeeds. It validates
        the CURRENT claim/lease and matching reservation under service scope.
        The worker still must separately reauthorize media and the actor.
        """
        sid, jid, token = map(canonical_uuid, (shop_id, job_id, claim_token))
        if type(attempt) is not int or attempt != 1:
            raise ValueError("only first GPU attempt permitted")
        row = _one(self.db.request("feature3_gpu_jobs", query={
            "select": "id,shop_id,reservation_id,status,attempts,claim_token,lease_until",
            "id": "eq." + jid, "shop_id": "eq." + sid, "limit": "2",
        }), "GPU claim unavailable")
        if (row.get("id") != jid or row.get("shop_id") != sid or
            row.get("status") != "RUNNING" or
            type(row.get("attempts")) is not int or row["attempts"] != 1 or
            row.get("claim_token") != token):
            raise StorageUnavailable("stale GPU claim")
        lease = row.get("lease_until")
        try:
            deadline = datetime.fromisoformat(lease.replace("Z", "+00:00"))
        except (AttributeError, TypeError, ValueError) as exc:
            raise StorageUnavailable("missing GPU claim lease") from exc
        if deadline.tzinfo is None or deadline <= datetime.now(timezone.utc):
            raise StorageUnavailable("expired GPU claim lease")
        rid = canonical_uuid(row.get("reservation_id"))
        reservation = _one(self.db.request("shop_ai_spend_reservations", query={
            "select": "id,shop_id,operation,state,reserved_usd",
            "id": "eq." + rid, "shop_id": "eq." + sid, "limit": "2",
        }), "prepaid GPU reservation missing")
        if (reservation.get("id") != rid or reservation.get("shop_id") != sid or
            reservation.get("state") != "RESERVED" or
            reservation.get("operation") != "image_generation"):
            raise StorageUnavailable("prepaid GPU reservation not active")
        try:
            amount = _money(reservation.get("reserved_usd"), positive=True)
        except ValueError as exc:
            raise StorageUnavailable("invalid prepaid GPU cost") from exc
        return {
            "reservation_id": rid, "shop_id": sid, "job_id": jid,
            "attempt": 1, "claim_token": token, "reserved_usd": amount,
        }

    def finish(self, job_id, claim_token, actual_usd, output_asset_id=None):
        jid, token = canonical_uuid(job_id), canonical_uuid(claim_token)
        aid = canonical_uuid(output_asset_id) if output_asset_id is not None else None
        amount = _money(actual_usd)
        result = self.db.request("rpc/feature3_finish_gpu_job", method="POST", data={
            "p_job_id": jid, "p_claim_token": token,
            "p_actual_usd": amount, "p_asset_id": aid,
        })
        if result is not True:
            # Never treat missing ACK as a successful financial settlement.
            raise StorageUnavailable("GPU settlement unconfirmed; do not retry")
        return True

    def commit_private_output(self, shop_id, job_id, attempt, claim_token,
                              object_path, image_sha256, object_bytes, source_asset_ids):
        """Bridge an existing trusted private Storage ACK to one-shot SQL CAS.

        The source adapter validates actual PNG bytes before this call. SQL
        rechecks live claim, registration, original shop, metadata and rights.
        Missing ACK is UNKNOWN, NOT permission to reupload/retry/settle.
        """
        sid, jid, token = map(canonical_uuid, (shop_id, job_id, claim_token))
        if type(attempt) is not int or attempt != 1:
            raise ValueError("Only the first immutable GPU attempt can register")
        if (not isinstance(image_sha256, str) or
                not _SHA256.fullmatch(image_sha256) or
                type(object_bytes) is not int or
                not 100 <= object_bytes <= 25 * 1024 * 1024):
            raise ValueError("Exact PNG checksum and byte count required")
        expected = f"{sid}/feature3/gpu/{jid}/{image_sha256}.png"
        if object_path != expected:
            raise ValueError("Output Storage path outside immutable job identity")
        if (not isinstance(source_asset_ids, (tuple, list)) or
                not 1 <= len(source_asset_ids) <= 12):
            raise ValueError("Trusted private source IDs required")
        sources = [canonical_uuid(aid) for aid in source_asset_ids]
        if len(set(sources)) != len(sources):
            raise ValueError("Duplicate GPU source IDs")
        result = self.db.request("rpc/feature3_commit_gpu_private_output",
                                 method="POST", data={
            "p_shop_id": sid, "p_job_id": jid, "p_attempt": 1,
            "p_claim_token": token, "p_object_path": expected,
            "p_image_sha256": image_sha256, "p_object_bytes": object_bytes,
            "p_source_asset_ids": sources,
        })
        required = {"media_asset_id", "shop_id", "job_id", "claim_token",
                    "attempt", "image_sha256", "object_path",
                    "review_status", "source", "private"}
        if (not isinstance(result, dict) or set(result) != required or
                result["shop_id"] != sid or result["job_id"] != jid or
                result["claim_token"] != token or
                type(result["attempt"]) is not int or result["attempt"] != 1 or
                result["image_sha256"] != image_sha256 or
                result["object_path"] != expected or
                result["review_status"] != "UNREVIEWED" or
                result["source"] != "GENERATED" or
                result["private"] is not True):
            raise StorageUnavailable("GPU output commit unknown; reconcile, do not retry")
        try:
            media_id = canonical_uuid(result["media_asset_id"])
        except (ValueError, TypeError, AttributeError):
            # The output CAS might have committed despite a malformed HTTP
            # return; do not treat this as safe to re-upload or charge.
            raise StorageUnavailable(
                "GPU output receipt identity unknown; reconcile first") from None
        return {"shop_id": sid, "job_id": jid, "claim_token": token,
                "attempt": 1, "media_asset_id": media_id,
                "image_sha256": image_sha256, "private": True,
                "review_status": "UNREVIEWED"}
