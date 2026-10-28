"""Wan2.2 -> existing Feature4 private media manifest, after REAL human approval.

No ledger/storage implementation here: a trusted coordinator checks the
existing Part3 fenced claim, reserved/subscription spend, current tenant rights,
immutable private output and persisted reviewer role. This adapter only
binds the *results*, never writes a database or certifies mocked inference.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .contracts import canonical_uuid
from .quality_review import VisualReview
from .wan22_motion_adapter import WanShotPackage, WanCompatibilityError
from .wan22_clip_validation import NativeClipInspection

SAFE_STAGED = re.compile(r"^[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*[.]mp4$")
VALID_RIGHTS = {"owned","cc0","royalty_free","commercial"}
RECEIPT_KEYS = {
    "shop_id","job_id","attempt_token","clip_asset_id",
    "source_asset_id","model_provider","bucket","path","private",
    "status","source_feature","prompt_sha256","lineage_sha256",
    "media_sha256","bytes","ledger_status","rights_approved",
}


def reviewed_wan_clip_for_feature4(
    *, package: WanShotPackage, inspection: NativeClipInspection,
    storage_receipt, human_review: VisualReview, rights,
    private_staged_path, reviewer_has_write_role, current_source_approved,
    verify_trusted_settlement_and_storage,
):
    """Return (asset_id, Feature4 manifest entry) only after trusted live checks.

    A TEST double of verify_trusted_settlement_and_storage is NEVER
    authorization in production. This must run server-side using an
    independent signed/DB record under the existing shop user JWT.
    """
    if not isinstance(package,WanShotPackage) or not isinstance(inspection,NativeClipInspection):
        raise WanCompatibilityError("No completed native Wan motion evidence")
    if package.status!="NOT_GENERATED_REVIEW_REQUIRED" or package.provider!="wan22_ti2v_5b_comfy_v1":
        raise WanCompatibilityError("Unknown native Wan provider")
    if inspection.status!="PENDING_PRIVATE_IMPORT_AND_VISUAL_REVIEW" or inspection.lineage_sha256!=package.lineage_sha256:
        raise WanCompatibilityError("Media file/reviewer lineage mismatch")
    if type(storage_receipt) is not dict or set(storage_receipt)!=RECEIPT_KEYS:
        raise WanCompatibilityError("Authoritative private media receipt missing")
    if (current_source_approved is not True or
        reviewer_has_write_role is not True or
        not callable(verify_trusted_settlement_and_storage)):
        raise WanCompatibilityError("Fresh active tenant, settled lease and private bytes required")
    info=package.lineage
    shop=canonical_uuid(info["shop_id"])
    job=canonical_uuid(storage_receipt["job_id"])
    token=canonical_uuid(storage_receipt["attempt_token"])
    clip=canonical_uuid(storage_receipt["clip_asset_id"])
    source=canonical_uuid(info["source_asset_id"])
    path=f"{shop}/renders/{job}/{token}.mp4"
    if (storage_receipt["shop_id"]!=shop or
        storage_receipt["source_asset_id"]!=source or
        storage_receipt["bucket"]!="retailgrowth-media" or
        storage_receipt["path"]!=path or
        storage_receipt["private"] is not True or
        storage_receipt["status"]!="SUCCEEDED" or
        storage_receipt["source_feature"]!="feature5" or
        storage_receipt["model_provider"]!=package.provider or
        storage_receipt["prompt_sha256"]!=package.prompt_sha256 or
        storage_receipt["lineage_sha256"]!=package.lineage_sha256 or
        storage_receipt["media_sha256"]!=inspection.sha256 or
        storage_receipt["bytes"]!=inspection.size_bytes or
        storage_receipt["ledger_status"]!="SETTLED" or
        storage_receipt["rights_approved"] is not True):
        raise WanCompatibilityError("Cross-tenant/attempt or unverified Wan receipt")
    # Validate the receipt's tenant and hash before contacting trusted DB.
    if verify_trusted_settlement_and_storage(storage_receipt) is not True:
        raise WanCompatibilityError("Fresh active tenant, settled lease and private bytes required")
    if (not isinstance(human_review,VisualReview) or
        human_review.shop_id!=shop or
        human_review.source_asset_id!=source or
        human_review.job_id!=job or
        human_review.output_asset_id!=clip):
        raise WanCompatibilityError("Current immutable human Wan visual review required")
    try:
        human_review.approved_for_feature4(
            authoritative_shop_id=shop,
            actual_media_sha256=inspection.sha256,
            reviewer_has_write_role=reviewer_has_write_role,
        )
    except ValueError as exc:
        raise WanCompatibilityError("Wan garment, anatomy or likeness review failed") from exc
    if (type(rights) is not dict or rights.get("commercial_use") is not True or
        rights.get("license") not in VALID_RIGHTS or
        not isinstance(rights.get("source"),str) or
        not rights["source"].strip() or
        not isinstance(rights.get("evidence"),str) or
        not rights["evidence"].strip()):
        raise WanCompatibilityError("Motion and reference imagery lack licensing evidence")
    if not isinstance(private_staged_path,str) or not SAFE_STAGED.fullmatch(private_staged_path):
        raise WanCompatibilityError("Feature4 expected private staged local MP4")
    # Still NOT an external URL or approval for publishing; Feature4 verifies
    # the actual bytes and authorized shop under its own renderer/ledger.
    return clip, {
        "shop_id":shop,
        "kind":"video",
        "source_feature":"feature5",
        "approved":True,
        "path":private_staged_path,
        "rights":dict(rights),
    }
