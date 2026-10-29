"""Feature2 stock B-roll screening. No remote fetch, source-to-video promotion or GPU.

Real source pages here are curated references only. Pexels' license permits
commercial ads in general but is not a model/property/brand release. Even
reviewed stock can fill environmental cutaways ONLY, never establish product
SKU/garment facts, retailer endorsement, human model consent or I2V grants.
Approved bytes must be imported privately by the coordinator using the
current shop JWT and verified signed media ownership/terms.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from pathlib import Path
from uuid import UUID
import json
import re

_SHA = re.compile(r"^[a-f0-9]{64}$")
_PAGE = re.compile(r"^https://(?:www\.)?(?:pexels\.com|commons\.wikimedia\.org)/")
_KINDS = {"ATMOSPHERE_BROLL", "CULTURAL_CUTAWAY"}
_TESTS = ("file_bytes_checked", "license_terms_checked", "no_people_or_verified_releases",
          "no_trademarks_or_verified_permissions", "not_false_product_endorsement",
          "retailer_approved_context", "private_tenant_import_verified")
_STOCK_FILE = Path(__file__).resolve().parents[2] / "stock-references" / "diwali_stock_candidates_20261028.json"


class StockMediaRejected(PermissionError):
    """No trusted stock rights in the exact current shop and reviewed bytes."""


@dataclass(frozen=True)
class BrollEvaluation:
    status: str
    shop_id: str
    stock_candidate_id: str
    candidate_source_page: str
    expected_duration_seconds: int
    can_show_in_offline_editor: bool
    can_use_as_product_ground_truth: bool = False
    can_imply_endorsement: bool = False
    can_dispatch_motion: bool = False
    can_publish: bool = False
    gpu_enabled: bool = False
    original_sha256: str = ""


def candidate_catalog() -> tuple[dict, ...]:
    """Static discovery pages only: source URLs are never download URLs."""
    parsed = json.loads(_STOCK_FILE.read_text("utf-8"))
    if type(parsed) is not list or len(parsed) != 3:
        raise StockMediaRejected("Expected frozen three-candidate discovery catalogue")
    ids = set()
    for row in parsed:
        if type(row) is not dict or set(row) != {
            "candidate_id", "source_page", "creator", "provider", "media_kind",
            "purpose", "license_page", "license_name", "attribution_required",
            "observed_on", "source_description", "expected_duration_seconds",
            "source_review_status", "downloaded_original_sha256",
        }:
            raise StockMediaRejected("Candidate missing frozen provenance")
        if row["candidate_id"] in ids or not _PAGE.match(row["source_page"]):
            raise StockMediaRejected("Unsupported or duplicated provenance")
        ids.add(row["candidate_id"])
        if (row["source_review_status"] != "CANDIDATE_NOT_IMPORTED" or
            row["downloaded_original_sha256"] is not None or
            row["purpose"] not in _KINDS or
            row["provider"] not in ("Pexels", "Wikimedia Commons") or
            row["attribution_required"] not in (True, False)):
            raise StockMediaRejected("External source may not assert already reviewed/licensed assets")
    return tuple(parsed)


def inspect_stock_broll(
    *, candidate: dict, shop_id: str, current_rights: dict | None,
    evidence: dict | None, trusted_member_check, originals_reader,
) -> BrollEvaluation:
    """Generate deterministic **offline preview only** from independently vetted bytes.

    Evidence must be from server-side curator workflow, not the browser or an
    LLM. Every approval flag is rechecked with the original shop JWT reader.
    This never forwards bytes, signs a source grant, enqueues motion or publishes.
    """
    try:
        sid = str(UUID(shop_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise StockMediaRejected("Canonical active shop ID required") from exc
    if not callable(trusted_member_check) or trusted_member_check(sid) is not True:
        raise StockMediaRejected("Current OWNER/EDITOR JWT shop authorization required")
    catalog = {c["candidate_id"]: c for c in candidate_catalog()}
    if (type(candidate) is not dict or
        candidate.get("candidate_id") not in catalog or
        candidate != catalog[candidate["candidate_id"]]):
        raise StockMediaRejected("Untrusted stock candidate metadata or license was modified")
    if type(current_rights) is not dict or type(evidence) is not dict:
        raise StockMediaRejected("Unreviewed source and local original")
    try:
        recorded_review_date = date.fromisoformat(current_rights["reviewed_on"])
        discovery_date = date.fromisoformat(candidate["observed_on"])
    except (KeyError, TypeError, ValueError) as exc:
        raise StockMediaRejected("Invalid stock reviewer date evidence") from exc
    if (current_rights.get("shop_id") != sid or
        current_rights.get("candidate_id") != candidate["candidate_id"] or
        current_rights.get("rights_state") != "ACTIVE_REVIEWED" or
        current_rights.get("revoked_at") is not None or
        current_rights.get("reviewed_licence_page") != candidate["license_page"] or
        current_rights.get("reviewed_source_page") != candidate["source_page"] or
        current_rights.get("creator") != candidate["creator"] or
        not isinstance(current_rights.get("reviewed_on"), str) or
        recorded_review_date < discovery_date or
        any(current_rights.get(k) is not True for k in _TESTS)):
        raise StockMediaRejected("Current commercial license/release/approval review incomplete")
    if (candidate["attribution_required"] and
        (not isinstance(current_rights.get("attribution_text"), str) or
         candidate["creator"] not in current_rights["attribution_text"])):
        raise StockMediaRejected("Mandatory Creative Commons attribution missing")
    if type(evidence.get("sha256")) is not str or not _SHA.fullmatch(evidence["sha256"]):
        raise StockMediaRejected("Source byte fingerprint unavailable")
    if evidence.get("shop_id") != sid or evidence.get("candidate_id") != candidate["candidate_id"]:
        raise StockMediaRejected("Cross-tenant stock evidence")
    if evidence.get("private") is not True or evidence.get("mime") not in ("image/jpeg", "video/mp4"):
        raise StockMediaRejected("Unprotected or unrecognized stock media")
    if candidate["media_kind"] == "VIDEO" and evidence["mime"] != "video/mp4":
        raise StockMediaRejected("Expected a reviewed stock video")
    if candidate["media_kind"] == "IMAGE" and evidence["mime"] != "image/jpeg":
        raise StockMediaRejected("Expected a reviewed still frame")
    if not callable(originals_reader):
        raise StockMediaRejected("Private original bytes reader unavailable")
    try:
        original = originals_reader(sid, candidate["candidate_id"])
    except Exception as exc:
        raise StockMediaRejected("Private original could not be reverified") from exc
    if type(original) is not bytes or not 100 <= len(original) <= 50_000_000:
        raise StockMediaRejected("Bounded original bytes not available")
    # A catalog URL and an arbitrary SHA cannot stand in for even a
    # plausibly typed original file. Container-level codec/dimension probes
    # and human rights review remain required on live import.
    if evidence["mime"] == "video/mp4" and original[4:8] != b"ftyp":
        raise StockMediaRejected("Original video container signature unavailable")
    if evidence["mime"] == "image/jpeg" and not (
        original.startswith(b"\xff\xd8\xff") and original.endswith(b"\xff\xd9")
    ):
        raise StockMediaRejected("Original JPEG signature unavailable")
    if sha256(original).hexdigest() != evidence["sha256"]:
        raise StockMediaRejected("Downloaded stock media bytes changed since review")
    if trusted_member_check(sid) is not True:
        raise StockMediaRejected("Member revoked during stock inspection")
    return BrollEvaluation(
        status="LICENSED_ATMOSPHERE_PREVIEW_ONLY",
        shop_id=sid, stock_candidate_id=candidate["candidate_id"],
        candidate_source_page=candidate["source_page"],
        expected_duration_seconds=candidate["expected_duration_seconds"],
        can_show_in_offline_editor=True,
        original_sha256=evidence["sha256"],
    )

def inspect_stock_from_trusted_shop_jwt(
    *, shop_id: str, authorization: str, candidate_id: str,
    verify_jwt, tenant_store, current_review_reader,
    private_import_reader, private_bytes_reader,
) -> BrollEvaluation:
    """Server-only source adapter: no browser-controlled approvals or public URLs.

    Inject only existing verified Supabase JWT and JWT-scoped RLS readers.
    This is source-level and remains unconnected to any deployed HTTP route.
    It does not authorize using a stock face as a fashion model.
    """
    if (type(authorization) is not str or
        not authorization.startswith("Bearer ") or
        type(candidate_id) is not str or
        not callable(verify_jwt) or
        not callable(getattr(tenant_store, "member", None)) or
        not all(callable(x) for x in (
            current_review_reader, private_import_reader, private_bytes_reader
        ))):
        raise StockMediaRejected("Trusted shop JWT and private source readers required")
    token = authorization.removeprefix("Bearer ").strip()
    if not 8 <= len(token) <= 16_384:
        raise StockMediaRejected("Invalid current JWT")
    try:
        sid = str(UUID(shop_id))
        actor = str(UUID(verify_jwt(token)))
        if tenant_store.member(token, actor, sid, write=True) is not True:
            raise StockMediaRejected("Active OWNER/EDITOR membership required")
    except StockMediaRejected:
        raise
    except (ValueError, TypeError, AttributeError) as exc:
        raise StockMediaRejected("Authenticated shop ID and actor required") from exc
    try:
        row = next(c for c in candidate_catalog() if c["candidate_id"] == candidate_id)
    except StopIteration as exc:
        raise StockMediaRejected("Unknown stock source page") from exc
    try:
        rights = current_review_reader(token, actor, sid, candidate_id)
        import_evidence = private_import_reader(token, actor, sid, candidate_id)
    except Exception as exc:
        raise StockMediaRejected("Current license and private original unavailable") from exc
    def member_check(target_shop):
        return tenant_store.member(token, actor, target_shop, write=True)
    def private_original(target_shop, target_candidate):
        return private_bytes_reader(token, actor, target_shop, target_candidate)
    try:
        return inspect_stock_broll(
            candidate=row, shop_id=sid,
            current_rights=rights, evidence=import_evidence,
            trusted_member_check=member_check, originals_reader=private_original,
        )
    except StockMediaRejected:
        raise
    except Exception as exc:
        raise StockMediaRejected("Current stock source evidence verification unavailable") from exc
