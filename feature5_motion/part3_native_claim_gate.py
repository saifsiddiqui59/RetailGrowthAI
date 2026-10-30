"""Strict Feature5-owned bridge for an authoritative Part3 Wan2.2 job claim.

Part3 PR #125 currently supports Wan2.7 720P/1080P ONLY; this versioned
profile is a proposed service-only contract, NOT a migration, wallet, signed
tenant grant, or approved paid call. Existing Part3 must independently issue a
fresh, lease-fenced record with these exact fields before any Comfy submission.

False-positive adaptation to Wan2.7, Hunyuan, legacy 480p or raw 1080p is
forbidden. A mock of this gate is never evidence of hosted JWT/RLS/credits.
"""
from __future__ import annotations

import math

from .contracts import canonical_uuid
from .wan22_motion_adapter import WanCompatibilityError, WanShotPackage, PROVIDER

SCHEMA = "retailgrowth.part3-f5-native-lease-claim.v1"
REQUIRED = frozenset({
    "schema", "shop_id", "job_id", "attempt_token", "source_asset_id",
    "campaign_id", "scene_id", "shot_id",
    "provider", "mode", "native_width", "native_height", "fps", "frames",
    "duration_seconds", "prompt_sha256", "lineage_sha256",
    "credit_reservation_id", "reserved_max_usd",
    "lease_valid", "source_rights_current", "budget_authorized",
})


def verify_native_wan22_claim(claim, *, package, shop, job, attempt):
    """Validate an independently read backend claim; return immutable tuple.

    Caller MUST obtain this record from an existing Part3 RLS/lease/credit
    transaction, not from the browser, user upload, or Comfy history. The tuple
    may be compared across two pre-submit reads without granting authority.
    """
    if not isinstance(package, WanShotPackage) or type(claim) is not dict or set(claim) != REQUIRED:
        raise WanCompatibilityError("Versioned Part3 native Wan2.2 claim missing")
    try:
        ids = tuple(canonical_uuid(claim[k]) for k in
                    ("shop_id", "job_id", "attempt_token", "source_asset_id",
                     "credit_reservation_id"))
        expected = (canonical_uuid(shop), canonical_uuid(job),
                    canonical_uuid(attempt),
                    canonical_uuid(package.lineage["source_asset_id"]))
        if ids[:4] != expected:
            raise ValueError("Foreign or expired Part3 job, lease, or source")
        for key in ("campaign_id", "scene_id", "shot_id"):
            if claim[key] != package.lineage[key] or not isinstance(claim[key], str):
                raise ValueError("Wrong approved creative identity")
        for key in ("prompt_sha256", "lineage_sha256"):
            if claim[key] != getattr(package, key):
                raise ValueError("Changed original approved prompt/lineage")
        if (claim["schema"] != SCHEMA or claim["provider"] != PROVIDER
                or claim["mode"] != "image_to_video"
                or any(type(claim[k]) is not int for k in
                       ("native_width", "native_height", "fps", "frames", "duration_seconds"))
                or (claim["native_width"], claim["native_height"],
                    claim["fps"], claim["frames"], claim["duration_seconds"]) !=
                    (704, 1280, 24, 121, 5)
                or any(claim[k] is not True for k in
                       ("lease_valid", "source_rights_current", "budget_authorized"))):
            raise ValueError("Legacy premium profile, unreserved spend or revoked rights")
        usd = claim["reserved_max_usd"]
        if (type(usd) not in (float, int) or
                not math.isfinite(usd) or not 0 < usd <= 1000):
            raise ValueError("Missing bounded backend spend reservation")
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        raise WanCompatibilityError("Part3 native Wan2.2 claim rejected") from exc
    # Immutable snapshot includes reservation and exact original creative
    # identity; a change while native node preflight runs aborts before CAS.
    return (ids, claim["campaign_id"], claim["scene_id"], claim["shot_id"],
            claim["prompt_sha256"], claim["lineage_sha256"],
            claim["provider"], claim["mode"], 704, 1280, 24, 121, 5,
            float(usd))
