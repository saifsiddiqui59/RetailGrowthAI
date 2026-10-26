"""Feature 5 bridge to the existing Part 3 premium job/ledger semantics.

No independent database, booking, credits or queue. Every value comes from
an existing *server-side* claim, approved campaign and tenant media resolver.
Shared DB migrations and live RPC bindings remain coordinator-owned.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Protocol
from uuid import UUID

from .contracts import MotionError, MotionSpec, canonical_uuid

HUNYUAN_MODEL = "hunyuanvideo-1.5-480p"
FEATURE4_VERSION = "creative_reel_v1"


def _money(value) -> Decimal:
    if type(value) is bool:
        raise MotionError("Invalid premium reservation")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise MotionError("Invalid premium reservation") from exc
    if not amount.is_finite() or amount <= 0 or amount > 1000:
        raise MotionError("Invalid premium reservation")
    return amount


def planned_motion_key(shop_id: str, campaign_day_id: str, source_asset_id: str | None,
                       prompt_version: str, mode: str, model_id: str) -> str:
    """Deterministic key for coordinator's EXISTING shop-scoped reservation.

    Does not create any reservation, and never contains private media URLs.
    """
    canonical_uuid(shop_id)
    canonical_uuid(campaign_day_id)
    if source_asset_id is not None:
        canonical_uuid(source_asset_id)
    if mode not in ("text", "image", "poster") or model_id != HUNYUAN_MODEL:
        raise MotionError("Unapproved premium model or mode")
    if prompt_version != "feature5-v1":
        raise MotionError("Unreviewed prompt version")
    values = [shop_id, campaign_day_id, source_asset_id, prompt_version, mode, model_id]
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()


def verified_claim_to_motion(raw: dict) -> tuple[MotionSpec, Decimal]:
    """Translate a transactionally claimed Part3 row, never a browser payload.

    A real coordinator must atomically lease the row and reserve existing
    shop_usage_reservations before invoking this function. No client-supplied
    claim may be accepted.
    """
    if type(raw) is not dict:
        raise MotionError("Missing service-only premium claim")
    required = {
        "id", "shop_id", "attempt_token", "model_id", "mode", "prompt",
        "source_asset_id", "resolution", "seconds", "status", "review_status",
        "reserved_usd", "reservation_id", "idempotency_key", "prompt_version",
        "rights_approved", "user_approved", "subscription_active",
    }
    if required - raw.keys():
        raise MotionError("Premium claim missing authoritative fields")
    if raw["model_id"] != HUNYUAN_MODEL or raw["status"] != "RUNNING":
        raise MotionError("Wrong model or unclaimed motion job")
    if raw["review_status"] != "APPROVED" or raw["rights_approved"] is not True or raw["user_approved"] is not True or raw["subscription_active"] is not True:
        raise MotionError("Motion not approved by tenant or subscription")
    canonical_uuid(raw["attempt_token"])
    canonical_uuid(raw["reservation_id"])
    key = raw["idempotency_key"]
    if type(key) is not str or len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
        raise MotionError("Invalid persisted idempotency key")
    price = _money(raw["reserved_usd"])
    # Reject WAN's incompatible provider settings rather than silently convert.
    if raw["resolution"] != "480p" or type(raw["seconds"]) is not int or raw["seconds"] != 5:
        raise MotionError("Unapproved model quality or duration settings")
    mode = raw["mode"]
    spec = MotionSpec(
        job_id=raw["id"], shop_id=raw["shop_id"], prompt=raw["prompt"],
        mode=mode, source_asset_id=raw["source_asset_id"],
        duration_seconds=raw["seconds"], resolution=raw["resolution"],
        seed=raw.get("seed", 1), prompt_version=raw["prompt_version"],
    )
    return spec, price


@dataclass(frozen=True)
class ApprovedMotionClip:
    """Backend-attested media after actual Hunyuan inference AND human review."""
    job_id: str
    shop_id: str
    clip_asset_id: str
    attempt_token: str
    storage_path: str
    status: str
    provenance: str
    quality_status: str
    output_codec: str
    rights_approved: bool
    duration_seconds: float

    def __post_init__(self):
        for value in (self.job_id, self.shop_id, self.clip_asset_id, self.attempt_token):
            canonical_uuid(value)


def feature4_asset_entry(clip: ApprovedMotionClip, *,
                         shop_id: str, local_staged_path: str, rights: dict) -> tuple[str, dict]:
    """Mint Feature4's SERVER-TRUSTED manifest entry; never accept browser data.

    Feature4 still independently validates staged bytes, rights, signatures,
    FPS/codec and timeline trim. The signed media URL stays in backend storage.
    """
    canonical_uuid(shop_id)
    expected = f"{shop_id}/renders/{clip.job_id}/{clip.attempt_token}.mp4"
    if (clip.shop_id != shop_id or clip.storage_path != expected or
        clip.status != "SUCCEEDED" or clip.provenance != HUNYUAN_MODEL or
        clip.quality_status != "APPROVED" or clip.rights_approved is not True or
        clip.output_codec != "h264" or not 4.5 <= clip.duration_seconds <= 5.5):
        raise MotionError("Premium clip has not passed private and visual approval")
    if not isinstance(rights, dict) or rights.get("commercial") is not True or rights.get("redistribution") is not True:
        raise MotionError("Motion rights do not permit campaign composition")
    # A local path is produced only by the existing private, server-side media
    # importer. Reject absolute paths, traversal, URL schemes, and weird chars.
    if (type(local_staged_path) is not str or not local_staged_path.endswith(".mp4") or
        len(local_staged_path) > 200 or local_staged_path.startswith(("/", "\\")) or
        any(part in ("", ".", "..") for part in local_staged_path.split("/")) or
        ":" in local_staged_path or "\\" in local_staged_path):
        raise MotionError("Unsafe Feature4 staged media reference")
    # Feature4 REF_PATTERN permits UUID strings as media IDs.
    return clip.clip_asset_id, {
        "shop_id": shop_id,
        "kind": "video",
        "source_feature": "feature5",
        "approved": True,
        "path": local_staged_path,
        "rights": dict(rights),
    }


def feature4_scene(clip_asset_id: str, *, order: int, start_time: int,
                   headline: str, duration: int = 5) -> dict:
    canonical_uuid(clip_asset_id)
    if (type(order) is not int or not 0 <= order <= 11 or
        type(start_time) is not int or start_time < 0 or
        type(duration) is not int or not 1 <= duration <= 5 or
        type(headline) is not str or not 1 <= len(headline) <= 110):
        raise MotionError("Invalid reviewed Feature4 scene")
    # Do not invent/promote a discount here: Feature4 checks approved copy.
    return {"order": order, "start_time": start_time, "duration": duration,
            "asset_id": clip_asset_id, "asset_type": "video",
            "source_feature": "feature5", "motion_status": "ready",
            "headline": headline, "mute_source": True}


class ExistingPart3Ledger(Protocol):
    """Coordinator-owned transactional service-role RPC; NOT implemented here."""
    def claim_authorized_motion(self, job_id: str) -> dict | None: ...
    def complete_motion(self, job_id: str, attempt_token: str, receipt: dict) -> bool: ...
    def fail_motion(self, job_id: str, attempt_token: str, category: str) -> bool: ...
    def unknown_motion(self, job_id: str, attempt_token: str, category: str) -> bool: ...


class Part3MotionStoreAdapter:
    """Injection-only wrapper around the EXISTING shared Part3 ledger RPCs."""
    def __init__(self, ledger: ExistingPart3Ledger):
        self.ledger = ledger

    def claim(self, job_id: str) -> dict | None:
        jid = canonical_uuid(job_id)
        row = self.ledger.claim_authorized_motion(jid)
        if row is None:
            return None
        spec, price = verified_claim_to_motion(row)
        if spec.job_id != jid:
            raise MotionError("Part3 ledger returned a foreign job")
        return {"spec": spec, "attempt_token": row["attempt_token"],
                "reserved_usd": price, "review_status": "APPROVED",
                "reservation_id": row["reservation_id"]}

    def complete(self, job_id: str, attempt_token: str, media_record: dict) -> bool:
        return bool(self.ledger.complete_motion(canonical_uuid(job_id), canonical_uuid(attempt_token), media_record))

    def fail(self, job_id: str, attempt_token: str, category: str) -> bool:
        return bool(self.ledger.fail_motion(canonical_uuid(job_id), canonical_uuid(attempt_token), category))

    def mark_unknown(self, job_id: str, attempt_token: str, category: str) -> bool:
        return bool(self.ledger.unknown_motion(canonical_uuid(job_id), canonical_uuid(attempt_token), category))
