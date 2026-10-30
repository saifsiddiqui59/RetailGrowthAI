"""Feature 3 additive immutable poster-draft revision contract.

This adapter is NOT database persistence. Integration requires an atomic
PostgREST/Supabase SECURITY DEFINER RPC with JWT-derived actor, server-side
OWNER/EDITOR check, same-shop campaign/day checks, quota and media rights.
Callbacks cannot be replaced by a browser request or arbitrary SQL.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID
from typing import Callable

from studio_v2 import DesignError, validate_design
from render_workflow_v2 import design_fingerprint


class DraftAccessDenied(PermissionError):
    pass


class DraftConflict(RuntimeError):
    pass


def _uuid(value):
    if not isinstance(value, str):
        raise DraftAccessDenied("Invalid draft identifier")
    try:
        if str(UUID(value)) != value:
            raise ValueError("non-canonical")
    except ValueError as exc:
        raise DraftAccessDenied("Invalid draft identifier") from exc
    return value


@dataclass(frozen=True)
class TrustedEditContext:
    """Populate exclusively from a cryptographically verified user JWT + RLS."""
    user_id: str
    shop_id: str
    campaign_id: str
    day_id: str
    role: str
    campaign_status: str
    day_status: str

    def authorize(self):
        for field in ("user_id", "shop_id", "campaign_id", "day_id"):
            _uuid(getattr(self, field))
        if (self.role not in ("OWNER", "EDITOR")
            or self.campaign_status != "DRAFT"
            or self.day_status != "DRAFT"):
            raise DraftAccessDenied("Poster revisions require an editable campaign/day")


@dataclass(frozen=True)
class RevisionToken:
    """New variation ID is never equal to prior approved design's ID."""
    design_id: str
    expected_revision: int
    variation_of: str | None = None

    def validate(self):
        _uuid(self.design_id)
        if type(self.expected_revision) is not int or not 0 <= self.expected_revision <= 1_000_000:
            raise DraftConflict("Invalid draft compare-and-swap version")
        if self.variation_of is not None:
            _uuid(self.variation_of)
            if self.variation_of == self.design_id:
                raise DraftConflict("Approved variation must use a new design ID")
            if self.expected_revision != 0:
                raise DraftConflict("New variation starts at revision zero")


def persist_versioned_draft(context, ticket, design, *,
                            fetch_current, authorize_assets, commit_if_revision):
    """Validate then request an atomic server-side compare-and-swap.

    fetch_current(context, design_id) returns a SAME-TENANT row or None.
    authorize_assets(context, ids) rechecks live media rights and lineage.
    commit_if_revision(context, ticket, design, hash, asset_ids) atomically
    checks row ACL, statuses, expected revision, quota and inserts immutable
    new revision. It MUST never update an approved image/design in place.
    """
    if not isinstance(context, TrustedEditContext) or not isinstance(ticket, RevisionToken):
        raise DraftAccessDenied("Trusted server-side context and revision token required")
    context.authorize()
    ticket.validate()
    checked = validate_design(design)
    if checked["shop_id"] != context.shop_id:
        raise DraftAccessDenied("Cross-shop poster document forbidden")
    callbacks = (fetch_current, authorize_assets, commit_if_revision)
    if not all(callable(fn) for fn in callbacks):
        raise DraftAccessDenied("RLS store and registered-media authorization required")
    current = fetch_current(context, ticket.variation_of or ticket.design_id)
    if current is None:
        if ticket.expected_revision != 0 or ticket.variation_of is not None:
            raise DraftConflict("Original draft missing or inaccessible")
    else:
        if not isinstance(current, dict) or set(current) != {
            "design_id", "shop_id", "campaign_id", "day_id",
            "status", "revision",
        } or (current["design_id"] != (ticket.variation_of or ticket.design_id)
              or current["shop_id"] != context.shop_id
              or current["campaign_id"] != context.campaign_id
              or current["day_id"] != context.day_id):
            raise DraftAccessDenied("Draft lineage does not belong to selected shop/day")
        if current["status"] == "APPROVED" and ticket.variation_of is None:
            raise DraftConflict("Approved poster cannot be overwritten; create a variation")
        if ticket.variation_of is not None:
            if current["status"] not in ("APPROVED", "READY", "DRAFT"):
                raise DraftConflict("Source variation no longer editable")
        elif (current["status"] != "DRAFT"
              or current["revision"] != ticket.expected_revision):
            raise DraftConflict("Draft changed since it was opened")
        if ticket.variation_of is None and ticket.expected_revision == 0:
            raise DraftConflict("Existing draft cannot be recreated as revision zero")
    if ticket.variation_of is None and current is None and ticket.expected_revision != 0:
        raise DraftConflict("New draft revision must start at zero")
    asset_ids = tuple(dict.fromkeys(
        layer["asset_id"] for layer in checked["layers"] if layer["type"] == "image"
    ))
    if authorize_assets(context, asset_ids) is not True:
        raise DraftAccessDenied("Media was revoked or belongs to another shop")
    fingerprint = design_fingerprint(checked)
    # The RPC callback must own transaction locks, approval immutability,
    # subscription/quota metering and idempotent response/retry semantics.
    result = commit_if_revision(context, ticket, checked, fingerprint, asset_ids)
    if (not isinstance(result, dict)
        or set(result) != {"design_id", "revision", "design_sha256"}
        or result["design_id"] != ticket.design_id
        or type(result["revision"]) is not int
        or result["revision"] != ticket.expected_revision + 1
        or result["design_sha256"] != fingerprint):
        raise DraftConflict("Atomic version commit was not confirmed")
    return result
