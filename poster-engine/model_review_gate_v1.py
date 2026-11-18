"""Feature3 server-only model review and revocation gate.

Works with the existing model-library.v1 and feature3_models schema; intentionally
does not invent a public approval endpoint, SQL reviewer/audit table or JWT grant.
All injected callbacks MUST be trusted backend/DB operations. In particular the
persist callback MUST re-check current membership, license, asset SHA and model
revision under ONE atomic DB transaction, storing a separate durable human
review/audit record before promoting a model. A mocked callback only tests the
contract; it does not prove the missing durable adapter exists in DEV.

No renderer, AI model execution, GPU activation, storage upload or cost action.
"""
from __future__ import annotations

from hashlib import sha256
from uuid import UUID
from urllib.parse import urlsplit
import re

from fashion_reference_v1 import _read_image
from model_library_v2 import KNOWN_LICENSES, POSES, SOURCE_KINDS

_SHA = re.compile(r"^[a-f0-9]{64}$")
_LABEL = re.compile(r"^[^\x00-\x1f\x7f]{1,64}$")
_CHECKS = frozenset({
    "adult_synthetic", "likeness_and_consent", "image_license",
    "private_media_integrity", "visual_quality", "approved_uses",
})
_USES = frozenset({"poster", "try_on", "video_reference"})


class ModelReviewDenied(ValueError):
    """No distinction between absent, foreign, revoked and unreviewed objects."""


def _uuid(value):
    try:
        result = str(UUID(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ModelReviewDenied("Invalid model/shop/reviewer identifier") from exc
    if result != value:
        raise ModelReviewDenied("Canonical UUID required")
    return value


def _positive_revision(value):
    if type(value) is not int or not 1 <= value < 2_147_483_647:
        raise ModelReviewDenied("Missing immutable rights revision")
    return value


def _required_callbacks(**callbacks):
    if not all(callable(v) for v in callbacks.values()):
        raise ModelReviewDenied("Authenticated reviewer, evidence and atomic persistence required")


def _model_current(row, shop_id, model_id, allowed_statuses):
    if not isinstance(row, dict) or row.get("owner_shop_id") != shop_id or \
            row.get("model_id") != model_id or \
            row.get("status") not in allowed_statuses or \
            row.get("scope") not in ("shop", "platform") or \
            row.get("source_kind") not in SOURCE_KINDS or \
            row.get("synthetic_adult") is not True or \
            row.get("license_id") not in KNOWN_LICENSES or \
            not isinstance(row.get("image_sha256"), str) or \
            not _SHA.fullmatch(row["image_sha256"]) or \
            not isinstance(row.get("license_evidence_sha256"), str) or \
            not _SHA.fullmatch(row["license_evidence_sha256"]) or \
            not isinstance(row.get("approved_uses"), list) or \
            not 1 <= len(row["approved_uses"]) <= 3 or \
            not set(row["approved_uses"]) <= _USES or \
            len(row["approved_uses"]) != len(set(row["approved_uses"])) or \
            not isinstance(row.get("label"), str) or \
            not _LABEL.fullmatch(row["label"]) or \
            not row["label"].strip():
        raise ModelReviewDenied("Model registry record not eligible")
    _uuid(row.get("media_asset_id"))
    _uuid(row.get("created_by"))
    _positive_revision(row.get("rights_revision"))
    if row.get("license_id") == "CC-BY-4.0" and not (
            isinstance(row.get("attribution"), str) and row["attribution"].strip()):
        raise ModelReviewDenied("Attribution required")
    return row


def _reviewer(shop_id, model_id, reviewer_id, row, authorize_reviewer):
    grant = authorize_reviewer(shop_id, reviewer_id, model_id)
    if not isinstance(grant, dict) or grant.get("authorized") is not True or \
            grant.get("shop_id") != shop_id or \
            grant.get("user_id") != reviewer_id or \
            grant.get("active") is not True or \
            grant.get("role") not in ("OWNER", "EDITOR") or \
            (row["scope"] == "platform" and (
                grant.get("platform_curator") is not True or
                reviewer_id == row["created_by"])):
        raise ModelReviewDenied("Current independent human reviewer authorization required")


def _evidence(shop_id, model_id, row, read_license_evidence):
    evidence = read_license_evidence(shop_id, model_id)
    if not isinstance(evidence, dict) or \
            evidence.get("shop_id") != shop_id or \
            evidence.get("model_id") != model_id or \
            evidence.get("media_asset_id") != row["media_asset_id"] or \
            evidence.get("image_sha256") != row["image_sha256"] or \
            evidence.get("license_id") != row["license_id"] or \
            evidence.get("license_evidence_sha256") != row["license_evidence_sha256"] or \
            evidence.get("source_kind") != row["source_kind"] or \
            evidence.get("pose") not in POSES or \
            evidence.get("synthetic_adult_verified") is not True or \
            evidence.get("component_rights_cleared") is not True or \
            evidence.get("commercial_reuse_approved") is not True or \
            type(evidence.get("evidence_revision")) is not int or \
            evidence["evidence_revision"] < 1:
        raise ModelReviewDenied("Independently verified per-image provenance is required")
    provenance = evidence.get("source_uri")
    if not isinstance(provenance, str) or len(provenance) > 1500:
        raise ModelReviewDenied("Original provenance missing")
    try:
        u = urlsplit(provenance)
        permitted = (u.scheme == "https" and bool(u.hostname) and
                     not u.username and not u.password and not u.fragment and
                     u.port in (None, 443))
    except ValueError as exc:
        raise ModelReviewDenied("Malformed original source URL") from exc
    if not permitted:
        raise ModelReviewDenied("Verified HTTPS original required")
    return evidence


def _registered_image(shop_id, model_id, row, load_private_media):
    """Exact first-owner Storage key, registered media row and genuine PNG digest."""
    receipt = load_private_media(shop_id, row["media_asset_id"])
    if not isinstance(receipt, tuple) or len(receipt) != 2:
        raise ModelReviewDenied("Registered private source was not read")
    asset, raw = receipt
    prefix = f"{shop_id}/model-library/"
    if row["scope"] == "platform":
        prefix += "platform/"
    expected = f"{prefix}{model_id}/{row['image_sha256']}.png"
    if not isinstance(asset, dict) or asset.get("id") != row["media_asset_id"] or \
            asset.get("shop_id") != shop_id or \
            asset.get("storage_bucket") != "retailgrowth-media" or \
            asset.get("object_path") != expected or \
            asset.get("mime_type") != "image/png" or \
            asset.get("source") not in ("UPLOAD", "GENERATED"):
        raise ModelReviewDenied("Unregistered/cross-tenant original model object")
    try:
        dims, digest = _read_image(raw, "image/png")
    except ValueError as exc:
        raise ModelReviewDenied("Model image bytes unavailable or invalid") from exc
    if digest != row["image_sha256"]:
        raise ModelReviewDenied("Original model binary changed after registration")
    return dims, digest


def _result(result, *, model_id, shop_id, previous_revision, target_status):
    """Require positive acknowledgement of a durable, audited, one-time CAS."""
    if not isinstance(result, dict) or result.get("model_id") != model_id or \
            result.get("owner_shop_id") != shop_id or \
            result.get("status") != target_status or \
            result.get("rights_verified") is not (target_status == "APPROVED") or \
            type(result.get("rights_revision")) is not int or \
            result["rights_revision"] != previous_revision + 1 or \
            result.get("audit_persisted") is not True:
        raise ModelReviewDenied("Atomic model review not durably confirmed")
    _uuid(result.get("review_event_id"))
    return {
        "model_id": model_id, "owner_shop_id": shop_id,
        "status": target_status, "rights_verified": target_status == "APPROVED",
        "rights_revision": result["rights_revision"],
        "review_event_id": result["review_event_id"],
        "audit_persisted": True, "gpu_authorized": False,
        "generation_executed": False,
    }


def decide_model_review(*, shop_id, model_id, reviewer_id, decision, checks,
                        notes, read_model, authorize_reviewer,
                        read_license_evidence, load_private_media,
                        persist_review_atomic):
    """Server-owned authenticated human decision over an exact private image.

    The write callback must compare status=PENDING_REVIEW + old revision and
    independently reconfirm membership, media identity, license/review
    provenance under the same transaction as the audit + status update.
    This module does NOT implement or bypass that coordinator-owned DB RPC.
    """
    shop_id, model_id, reviewer_id = map(_uuid, (shop_id, model_id, reviewer_id))
    _required_callbacks(read_model=read_model, authorize_reviewer=authorize_reviewer,
                        read_license_evidence=read_license_evidence,
                        load_private_media=load_private_media,
                        persist_review_atomic=persist_review_atomic)
    if decision not in ("APPROVE", "REJECT") or not isinstance(checks, dict) or \
            set(checks) != _CHECKS or any(type(v) is not bool for v in checks.values()):
        raise ModelReviewDenied("Six explicit human decisions are required")
    if not isinstance(notes, str) or not 12 <= len(notes.strip()) <= 500 or \
            any(ord(c) < 32 or ord(c) == 127 for c in notes):
        raise ModelReviewDenied("Auditable human review notes required")
    target = "APPROVED" if decision == "APPROVE" else "REJECTED"
    if decision == "APPROVE" and not all(checks.values()):
        raise ModelReviewDenied("Any failed check blocks model approval")
    row = _model_current(read_model(shop_id, model_id), shop_id, model_id, ("PENDING_REVIEW",))
    if row.get("rights_verified") is not False:
        raise ModelReviewDenied("Already verified model cannot bypass human review")
    _reviewer(shop_id, model_id, reviewer_id, row, authorize_reviewer)
    evidence = _evidence(shop_id, model_id, row, read_license_evidence)
    dims, digest = _registered_image(shop_id, model_id, row, load_private_media)
    # Snapshot expected CAS identity BEFORE calling a persistence adapter:
    # even a local in-memory adapter may mutate the row in place, and a real
    # database adapter may rehydrate a newer row during a settlement check.
    expected_revision = row["rights_revision"]
    proposal = {
        "shop_id": shop_id, "model_id": model_id, "reviewer_id": reviewer_id,
        "decision": target, "checks": dict(checks), "notes": notes.strip(),
        "expected_status": "PENDING_REVIEW",
        "expected_rights_revision": expected_revision,
        "expected_image_sha256": digest, "media_asset_id": row["media_asset_id"],
        "source_scope": row["scope"], "license_id": row["license_id"],
        "license_evidence_sha256": row["license_evidence_sha256"],
        "evidence_revision": evidence["evidence_revision"],
        "pose": evidence["pose"], "dimensions": dims,
    }
    outcome = persist_review_atomic(proposal)
    return _result(outcome, model_id=model_id, shop_id=shop_id,
                   previous_revision=expected_revision, target_status=target)


def _revoke_current(row, shop_id, model_id):
    """Revocation must remain possible after license/metadata corruption.

    A license can be withdrawn or attribution deleted; requiring that
    revoked external evidence still be valid would block an urgent revoke.
    The atomic DB writer must fence the stored identity, SHA and revision.
    """
    if not isinstance(row, dict) or row.get("owner_shop_id") != shop_id or \
            row.get("model_id") != model_id or \
            row.get("status") != "APPROVED" or \
            row.get("rights_verified") is not True or \
            row.get("scope") not in ("shop", "platform") or \
            not isinstance(row.get("image_sha256"), str) or \
            not _SHA.fullmatch(row["image_sha256"]):
        raise ModelReviewDenied("No currently approved same-shop model")
    _uuid(row.get("media_asset_id"))
    _uuid(row.get("created_by"))
    _positive_revision(row.get("rights_revision"))
    return row


def revoke_approved_model(*, shop_id, model_id, reviewer_id, reason,
                          read_model, authorize_reviewer, persist_revocation_atomic):
    """Revoke active model rights with monotonic revision and durable audit."""
    shop_id, model_id, reviewer_id = map(_uuid, (shop_id, model_id, reviewer_id))
    _required_callbacks(read_model=read_model, authorize_reviewer=authorize_reviewer,
                        persist_revocation_atomic=persist_revocation_atomic)
    if not isinstance(reason, str) or not 12 <= len(reason.strip()) <= 500 or \
            any(ord(c) < 32 or ord(c) == 127 for c in reason):
        raise ModelReviewDenied("Human revocation reason required")
    row = _revoke_current(read_model(shop_id, model_id), shop_id, model_id)
    _reviewer(shop_id, model_id, reviewer_id, row, authorize_reviewer)
    expected_revision = row["rights_revision"]
    result = persist_revocation_atomic({
        "shop_id": shop_id, "model_id": model_id, "reviewer_id": reviewer_id,
        "expected_status": "APPROVED", "expected_rights_revision": expected_revision,
        "expected_image_sha256": row["image_sha256"],
        "media_asset_id": row["media_asset_id"], "reason": reason.strip(),
        "new_status": "REVOKED", "must_invalidate_media_cache": True,
    })
    return _result(result, model_id=model_id, shop_id=shop_id,
                   previous_revision=expected_revision, target_status="REVOKED")
