"""Source-only authenticated F2 approval -> F4 atomic submission bridge.

The injected storage implementation MUST run atomic_create_feature4_intent()
in a single DB transaction: lock current JWT-owned shop membership and exact
approved F2 revision; verify current media rights; generate a render-job UUID;
call prepare() with those server-read rows BEFORE inserting anything; reserve
quota+idempotency+outbox+immutable request/media bundle in the SAME commit.
Any failure rolls back all writes. No direct browser grant, queue ACK, signed
URL, AI/GPU provider or auto-approval is allowed in this adapter.

This repository does not yet have that v2 transaction or hosted registration.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re

from creative_contract import CreativeContractError, uuid
from feature2_feature4_bridge import _direction_json, compile_feature2_direction

_KEYS = frozenset({
    "shop_id", "campaign_id", "requested_by", "approval_id",
    "draft", "idempotency_key", "preset",
})
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_APPROVAL = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
_STATES = {"QUEUED", "RUNNING", "SUCCEEDED", "FAILED"}


class Feature4IntakeUnavailable(RuntimeError):
    """No approved atomic v2 backend; fail closed without reserving credits."""


class Feature4ApprovedPlanIntake:
    """Inject as the F4 HTTP admin ONLY after storage transaction review."""

    def __init__(self, transactional_store):
        if not callable(getattr(transactional_store, "atomic_create_feature4_intent", None)):
            raise Feature4IntakeUnavailable("Approved feature4 atomic backend unavailable")
        self.store = transactional_store

    def create_feature4_intent(self, item):
        if type(item) is not dict or set(item) != _KEYS:
            raise CreativeContractError("Malformed v2 approved intent")
        sid = uuid(item["shop_id"], "shop_id")
        cid = uuid(item["campaign_id"], "campaign_id")
        uid = uuid(item["requested_by"], "requested_by")
        approval = item["approval_id"]
        if (type(approval) is not str or not _APPROVAL.fullmatch(approval) or
                item["preset"] != "feature4_reel_v1" or
                type(item["draft"]) is not dict or
                type(item["idempotency_key"]) is not str or
                not _HEX64.fullmatch(item["idempotency_key"])):
            raise CreativeContractError("Invalid approved revision or video preset")
        # Browser intent's revision+requested_by must be bound exactly to the
        # JWT-verified actor already validated by Feature4HTTP. Never use a
        # browser-supplied idempotency key, output URL, manifest or job ID.
        digest = hashlib.sha256(json.dumps(
            [sid, uid, cid, approval, item["draft"]],
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")).hexdigest()
        if not hmac.compare_digest(digest, item["idempotency_key"]):
            raise CreativeContractError("Untrusted render idempotency fingerprint")
        if len(_direction_json(item["draft"]).encode("utf-8")) > 64_000:
            raise CreativeContractError("Unbounded v2 browser storyboard")

        def prepare(trusted):
            # Trusted is loaded under a DB lock by the backend, NOT the client.
            if (type(trusted) is not dict or set(trusted) != {
                "direction", "snapshot", "reviewed_hash", "active_editor",
            } or trusted["active_editor"] is not True):
                raise CreativeContractError("No current tenant editor or immutable approval")
            snapshot = trusted["snapshot"]
            if (type(snapshot) is not dict or
                    snapshot.get("shop_id") != sid or
                    snapshot.get("campaign_id") != cid or
                    snapshot.get("approval_id") != approval or
                    snapshot.get("idempotency_key") != digest):
                raise CreativeContractError("Locked F2 review or job belongs to another request")
            uuid(snapshot.get("video_job_id"), "server-allocated job")
            compiled = compile_feature2_direction(
                trusted["direction"], snapshot,
                reviewed_hash=trusted["reviewed_hash"])
            # The customer may edit the review *before* approval. After
            # approval a changed script/scene/audio requires a NEW F2 revision,
            # not an unauthorized F4 render with old approval metadata.
            if _direction_json(compiled["approved_draft"]) != _direction_json(item["draft"]):
                raise CreativeContractError("Browser storyboard differs from approved F2 direction")
            return compiled

        # Neither an idempotent replay nor a lease may skip current RLS/media
        # checks. Store must roll back *everything* if prepare raises.
        receipt = self.store.atomic_create_feature4_intent(item, prepare)
        if (type(receipt) is not dict or receipt.get("shop_id") != sid or
                receipt.get("status") not in _STATES):
            raise Feature4IntakeUnavailable("Atomic render ledger returned invalid receipt")
        uuid(receipt.get("id"), "registered render job")
        return receipt
