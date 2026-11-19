"""Feature4 visual/business acceptance gate, NEVER inferred from a successful encode.

This checks that a trusted coordinator-backed human-review record covers the
same immutable renderer job and actual uploaded product/motion asset IDs. It
does NOT computer-vision verify garment fidelity or produce a DB approval;
human review is mandatory, and browser assertions are never authoritative.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from creative_contract import CreativeContractError

CHECKS = frozenset({
    "human_model_realism", "garment_design_match", "natural_walking",
    "readable_shop_logo", "verified_sale_offer", "licensed_soundtrack",
    "speech_intelligibility", "mobile_legibility",
})
MAX_REVIEW_AGE_DAYS = 90
MAX_PROOF_BYTES = 80 * 1024 * 1024


class ReleaseNotApproved(CreativeContractError):
    """An ordinary engineering render is not a paying-customer approval."""


@dataclass(frozen=True)
class ReviewedVideo:
    shop_id: str
    video_job_id: str
    approved_product_id: str
    approved_motion_id: str
    review_id: str
    reviewer_id: str
    reviewed_at: str
    evidence_refs: tuple[str, ...]


def _identifier(value, name):
    if type(value) is not str:
        raise ReleaseNotApproved(name + ": canonical UUID required")
    try:
        result = str(UUID(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ReleaseNotApproved(name + ": canonical UUID required") from exc
    if result != value:
        raise ReleaseNotApproved(name + ": canonical UUID required")
    return value


def _parse_time(value):
    if type(value) is not str or not value.endswith("Z"):
        raise ReleaseNotApproved("Recorded UTC human review time required")
    try:
        when = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReleaseNotApproved("Invalid reviewed-at timestamp") from exc
    if when.utcoffset() != timedelta(0):
        raise ReleaseNotApproved("Review timestamp must be UTC")
    return when


def validate_feature4_release(*, job, lineage, reviewed, media, now=None):
    """Validate trusted service-fetched review; return lineage-only acceptance.

    In coordinator integration, job, lineage, reviewed and media MUST be loaded
    afresh from a server-owned DB under trusted service identity, NOT HTTP body.
    The review may only be stored after a real human views the actual MP4.
    """
    if not all(type(x) is dict for x in (job, lineage, reviewed, media)):
        raise ReleaseNotApproved("Server-owned job, lineage, media and review required")
    shop = _identifier(job.get("shop_id"), "shop_id")
    jid = _identifier(job.get("id"), "job_id")
    if job.get("status") != "SUCCEEDED" or job.get("output_asset_id") is None:
        raise ReleaseNotApproved("Only verified, completed private renders are eligible")
    # A present-but-foreign/empty output reference is not an immutable asset ID.
    _identifier(job["output_asset_id"], "output_asset_id")
    if (lineage.get("video_job_id") != jid or
            lineage.get("rendered_as") != "AUTHORIZED_ASSEMBLY" or
            lineage.get("fallback_events") != []):
        raise ReleaseNotApproved("Synthetic fallback or mismatched render lineage")
    if reviewed.get("shop_id") != shop or reviewed.get("video_job_id") != jid:
        raise ReleaseNotApproved("Review must match the same tenant and immutable video job")
    product = _identifier(reviewed.get("approved_product_id"), "product media")
    motion = _identifier(reviewed.get("approved_motion_id"), "motion media")
    expected = lineage.get("media_asset_ids")
    if (type(expected) is not list or not 2 <= len(expected) <= 36 or
            product not in expected or motion not in expected or product == motion):
        raise ReleaseNotApproved("Review must cover actually assembled product and motion media")
    # Product/motion approval alone is insufficient: an otherwise approved Reel
    # could still embed revoked, foreign-shop or synthetic audio/stock/logo.
    # All rows must be fresh trusted DB reads, not browser-provided grants.
    for asset_id in expected:
        _identifier(asset_id, "lineage media asset")
    if len(set(expected)) != len(expected):
        raise ReleaseNotApproved("Duplicate media asset IDs in render lineage")
    for asset_id in expected:
        row = media.get(asset_id)
        if type(row) is dict and row.get("synthetic_fixture") is not False:
            raise ReleaseNotApproved("Synthetic or unknown fixture provenance cannot be published")
        if (type(row) is not dict or row.get("shop_id") != shop or
                row.get("approved") is not True or
                row.get("commercial_use") is not True or
                row.get("synthetic_fixture") is not False or
                type(row.get("kind")) is not str or
                row["kind"] not in {"image", "poster", "logo", "video", "audio"} or
                type(row.get("source_feature")) is not str or
                not row["source_feature"].strip() or
                type(row.get("rights_evidence")) is not str or
                not row["rights_evidence"].strip()):
            raise ReleaseNotApproved("Every rendered media asset requires current same-shop rights")
    p, m = media.get(product), media.get(motion)
    for row, kind, origin in ((p, "image", "feature3"), (m, "video", "feature5")):
        if (type(row) is not dict or row.get("shop_id") != shop
                or row.get("kind") != kind or row.get("source_feature") != origin
                or row.get("approved") is not True or
                row.get("commercial_use") is not True or
                not row.get("rights_evidence")):
            raise ReleaseNotApproved("Real source media rights and provenance unverified")
        # Explicitly never treat a source provider's SYNTHETIC_TEST_ONLY flag
        # as a real user-approved human or retailer product.
        if row.get("synthetic_fixture") is not False:
            raise ReleaseNotApproved("Synthetic or unknown fixture provenance cannot be published")
    if (type(reviewed.get("approved")) is not bool or reviewed["approved"] is not True
            or type(reviewed.get("review_id")) is not str
            or not reviewed["review_id"].strip()
            or type(reviewed.get("reviewer_id")) is not str
            or not reviewed["reviewer_id"].strip()):
        raise ReleaseNotApproved("Independently saved reviewer approval required")
    checklist = reviewed.get("checks")
    if (type(checklist) is not dict or set(checklist) != CHECKS or
            any(value is not True for value in checklist.values())):
        raise ReleaseNotApproved("All professional video quality checks must be human-approved")
    refs = reviewed.get("evidence_refs")
    if (type(refs) is not list or not 2 <= len(refs) <= 20 or
            any(type(ref) is not str or not ref or len(ref) > 180 for ref in refs)):
        raise ReleaseNotApproved("Recorded verified product/motion comparison evidence required")
    checked = _parse_time(reviewed.get("reviewed_at"))
    current = now if now is not None else datetime.now(timezone.utc)
    if current.tzinfo is None or checked > current + timedelta(minutes=5) or (
            current - checked > timedelta(days=MAX_REVIEW_AGE_DAYS)):
        raise ReleaseNotApproved("Human review too old or future-dated")
    proof = job.get("output_probe")
    if (type(proof) is not dict or proof.get("video_codec") != "h264" or
            proof.get("audio_codec") != "aac" or
            proof.get("width") != 1080 or proof.get("height") != 1920 or
            proof.get("duration_seconds") not in (15.0, 30.0, 60.0) or
            type(proof.get("bytes")) is not int or not 1024 < proof["bytes"] <= MAX_PROOF_BYTES):
        raise ReleaseNotApproved("Actual production Full-HD MP4 output proof required")
    return ReviewedVideo(
        shop_id=shop, video_job_id=jid, approved_product_id=product,
        approved_motion_id=motion, review_id=reviewed["review_id"],
        reviewer_id=reviewed["reviewer_id"], reviewed_at=reviewed["reviewed_at"],
        evidence_refs=tuple(refs),
    )
