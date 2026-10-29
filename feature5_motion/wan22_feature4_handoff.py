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
    try:
        shop=canonical_uuid(info["shop_id"])
        job=canonical_uuid(storage_receipt["job_id"])
        token=canonical_uuid(storage_receipt["attempt_token"])
        clip=canonical_uuid(storage_receipt["clip_asset_id"])
        source=canonical_uuid(info["source_asset_id"])
    except (ValueError,TypeError,KeyError) as exc:
        raise WanCompatibilityError("Invalid current private Wan F4 tenant/job/attempt identifier") from exc
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
    # Cheap rights/path checks precede the authoritative DB/ledger lookup;
    # these client-shaped fields alone never authorize release.
    if (type(rights) is not dict or rights.get("commercial_use") is not True or
        rights.get("license") not in VALID_RIGHTS or
        not isinstance(rights.get("source"),str) or
        not rights["source"].strip() or
        not isinstance(rights.get("evidence"),str) or
        not rights["evidence"].strip()):
        raise WanCompatibilityError("Motion and reference imagery lack licensing evidence")
    if not isinstance(private_staged_path,str) or not SAFE_STAGED.fullmatch(private_staged_path):
        raise WanCompatibilityError("Feature4 expected private staged local MP4")
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


def pending_private_wan_receipt_for_feature4(*, package, inspection, storage_receipt):
    """Source-only F5->F4 rich review candidate; NEVER a release authorization.

    Makes Feature4's requested identifiers, codecs, source revisions and
    billing/storage evidence inspectable without trusting a fake APPROVED
    reviewer. The caller MUST independently authenticate live Part3 and
    current Feature3 rights before reusing this report; test callbacks,
    an upload ACK and a hash never prove genuine Wan model inference.
    """
    import hashlib
    import json

    if (not isinstance(package, WanShotPackage)
            or package.provider != "wan22_ti2v_5b_comfy_v1"
            or package.task != "image_to_video"
            or package.status != "NOT_GENERATED_REVIEW_REQUIRED"
            or not isinstance(inspection, NativeClipInspection)
            or inspection.status != "PENDING_PRIVATE_IMPORT_AND_VISUAL_REVIEW"
            or inspection.lineage_sha256 != package.lineage_sha256
            or (inspection.width, inspection.height, inspection.fps, inspection.frames,
                inspection.codec) != (704, 1280, 24, 121, "h264")
            or not 4.9 <= inspection.duration_seconds <= 5.2
            or type(inspection.size_bytes) is not int or inspection.size_bytes <= 0
            or type(inspection.sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", inspection.sha256) is None):
        raise WanCompatibilityError("Unqualified native Feature5 technical clip")
    info = package.lineage
    if type(info) is not dict or type(storage_receipt) is not dict or set(storage_receipt) != RECEIPT_KEYS:
        raise WanCompatibilityError("Missing native lineage or Part3 receipt")
    try:
        shop = canonical_uuid(info["shop_id"])
        source = canonical_uuid(info["source_asset_id"])
        job = canonical_uuid(storage_receipt["job_id"])
        attempt = canonical_uuid(storage_receipt["attempt_token"])
        clip = canonical_uuid(storage_receipt["clip_asset_id"])
        for key in ("campaign_id", "scene_id", "shot_id", "approval_id"):
            if not isinstance(info[key], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", info[key]):
                raise ValueError("Invalid editorial reference")
        for key in ("source_sha256", "staged_first_frame_sha256", "reference_facts_sha256",
                    "model_revision", "upstream_commit"):
            if not isinstance(info[key], str) or not re.fullmatch(r"[a-f0-9]{40,64}", info[key]):
                raise ValueError("Invalid immutable source revision")
        positive = package.graph["prompt"]["4"]["inputs"]["text"]
        negative = package.graph["prompt"]["5"]["inputs"]["text"]
        bundle_sha = hashlib.sha256(json.dumps(
            {"positive": positive, "negative": negative}, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise WanCompatibilityError("Missing original reviewed creative identity") from exc
    lineage_digest = hashlib.sha256(json.dumps(
        info, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")).hexdigest()
    if (positive != package.prompt or bundle_sha != package.prompt_sha256
            or lineage_digest != package.lineage_sha256
            or not isinstance(package.lineage_sha256, str)
            or not re.fullmatch(r"[a-f0-9]{64}", package.lineage_sha256)
            or not re.fullmatch(r"[a-f0-9]{64}", package.prompt_sha256)
            or storage_receipt["shop_id"] != shop
            or storage_receipt["source_asset_id"] != source
            or storage_receipt["model_provider"] != package.provider
            or storage_receipt["source_feature"] != "feature5"
            or storage_receipt["bucket"] != "retailgrowth-media"
            or storage_receipt["path"] != f"{shop}/renders/{job}/{attempt}.mp4"
            or storage_receipt["private"] is not True
            or storage_receipt["status"] != "SUCCEEDED"
            or storage_receipt["ledger_status"] != "SETTLED"
            or storage_receipt["rights_approved"] is not True
            or storage_receipt["prompt_sha256"] != package.prompt_sha256
            or storage_receipt["lineage_sha256"] != package.lineage_sha256
            or storage_receipt["media_sha256"] != inspection.sha256
            or storage_receipt["bytes"] != inspection.size_bytes):
        raise WanCompatibilityError("Part3 private receipt differs from inspected source")
    return {
        "schema": "retailgrowth.feature5-f4-motion-review-candidate.v1",
        "shop_id": shop, "campaign_id": info["campaign_id"],
        "scene_id": info["scene_id"], "shot_id": info["shot_id"],
        "job_id": job, "attempt_token": attempt,
        "source_media": {
            "asset_id": source, "source_sha256": info["source_sha256"],
            "first_frame_sha256": info["staged_first_frame_sha256"],
            "feature3_facts_sha256": info["reference_facts_sha256"],
        },
        "output_media": {
            "asset_id": clip, "bucket": "retailgrowth-media",
            "private_path": storage_receipt["path"],
            "sha256": inspection.sha256, "bytes": inspection.size_bytes,
            "public_url": None,
        },
        "native_video": {
            "codec": "h264", "width": 704, "height": 1280,
            "fps": 24, "frames": 121,
            "duration_seconds": inspection.duration_seconds,
            "requires_feature4_final_1080x1920": True,
        },
        "creative": {
            "source_feature": "feature2", "approval_id": info["approval_id"],
            "generation_prompt": package.prompt, "prompt_bundle_sha256": package.prompt_sha256,
            "lineage_sha256": package.lineage_sha256,
            "model_source_revision": info["upstream_commit"],
            "checkpoint_revision": info["model_revision"],
        },
        "part3_evidence": {
            "job_status_from_receipt": "SUCCEEDED",
            "ledger_status_from_receipt": "SETTLED",
            "live_trusted_lease_billing_and_storage_verified": False,
        },
        "review_status": "PENDING_INDEPENDENT_HUMAN_VISUAL_REVIEW",
        "review_decision": "NOT_APPROVED",
        "revoked": False,
        "requires_fresh_rights_and_revocation_recheck": True,
        "genuine_wan_origin_proven": False,
        "approved_for_feature4": False,
        "can_publish": False, "can_download": False,
    }
