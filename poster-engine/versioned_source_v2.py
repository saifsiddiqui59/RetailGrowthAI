"""Feature #3 versioned source -> renderer fencing contract (offline, no cloud job).

PostgreSQL currently stores a SHA256 of jsonb::text, while the validated
Pillow engine fingerprints canonical normalized JSON. These are intentionally
DIFFERENT formats. Their binding is the immutable (shop, design ID, revision)
tuple returned by a trusted DATABASE TRANSACTION and separately verified
against current source image authorization. Never equate either digest or
accept a browser-issued hash. A future queue must persist the entire receipt
and use an atomic job/usage/outbox transition before any render.
"""
from __future__ import annotations

from uuid import UUID
import re
from studio_v2 import validate_design, DesignError
from render_workflow_v2 import design_fingerprint

_SHA = re.compile(r"^[a-f0-9]{64}$")


class Feature3SourceDenied(PermissionError):
    pass


def _uuid(value):
    if not isinstance(value, str):
        raise Feature3SourceDenied("Canonical UUID required")
    try:
        if str(UUID(value)) != value:
            raise ValueError("Noncanonical UUID")
    except ValueError as exc:
        raise Feature3SourceDenied("Canonical UUID required") from exc
    return value


def bind_authorized_versioned_design(
    *, shop_id, design_id, expected_revision, expected_server_sha256,
    read_version_under_lock, authorize_current_images,
):
    """Pin a v2 DRAFT and media rights into an immutable future job receipt.

    The trust boundary is NOT client input: read_version_under_lock() MUST
    run inside a server-only Postgres transaction with a JWT/shop membership
    or securely authorized worker identity, enforce (shop_id, design_id,
    revision, server_document_sha256) equality, current DRAFT state,
    current approval status and subscription, and lock the database row.
    The transaction must also reserve quota and enqueue the outbox *atomically*
    before an actual queue job can claim production readiness.

    authorize_current_images(shop_id, asset_ids, trusted_row) checks RLS,
    license, media bytes and current rights under the same revision fence;
    merely passing an asset ID in browser JSON is not authorization.
    """
    sid, did = _uuid(shop_id), _uuid(design_id)
    if (type(expected_revision) is not int
        or not 1 <= expected_revision <= 1_000_000
        or not isinstance(expected_server_sha256, str)
        or not _SHA.fullmatch(expected_server_sha256)
        or not callable(read_version_under_lock)
        or not callable(authorize_current_images)):
        raise Feature3SourceDenied("Verified immutable source and callbacks required")
    row = read_version_under_lock(sid, did, expected_revision, expected_server_sha256)
    if not isinstance(row, dict) or set(row) != {
        "id", "shop_id", "revision", "status",
        "server_document_sha256", "design",
    } or (row["id"] != did or row["shop_id"] != sid
          or row["revision"] != expected_revision
          or row["server_document_sha256"] != expected_server_sha256
          or row["status"] != "DRAFT"):
        raise Feature3SourceDenied("Source row changed or no longer authorized")
    try:
        document = validate_design(row["design"])
    except (DesignError, TypeError, KeyError, ValueError) as exc:
        raise Feature3SourceDenied("Invalid persisted v2 document") from exc
    if document["shop_id"] != sid:
        raise Feature3SourceDenied("Cross-tenant design rejected")
    asset_ids = tuple(dict.fromkeys(
        layer["asset_id"] for layer in document["layers"]
        if layer["type"] == "image"
    ))
    if authorize_current_images(sid, asset_ids, row) is not True:
        raise Feature3SourceDenied("Media rights revoked or unavailable")
    return {
        "schema": "retailgrowth.poster-job-source.v2",
        "shop_id": sid,
        "design_id": did,
        "revision": expected_revision,
        "server_document_sha256": expected_server_sha256,
        "design_sha256": design_fingerprint(document),
        "asset_ids": asset_ids,
        "ready_for_queue": False,
        "usage_reserved": False,
        "rendered": False,
        "signed_output": False,
    }
