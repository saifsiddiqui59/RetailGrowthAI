"""Read-only bridge for Feature #2 APPROVED content to Feature #3 CPU posters.

The caller must load both inputs using the *authenticated shop JWT*, current
OWNER/EDITOR membership, approved content version and live asset rights.
Feature #2 draft sidecars alone are not proof of authorization; no direct
browser request may supply approval or a commercial offer.
"""
from __future__ import annotations

from studio_v2 import DesignError, compose_poster, validate_design

_BRIEF_KEYS = frozenset({
    "shop_id", "campaign_id", "day_id", "approved_version",
    "review_state", "headline", "cta", "offer_text", "visual_brief",
})
_REQUIRED_CONTEXT_KEYS = frozenset({
    "shop_id", "campaign_id", "day_id", "business_name",
    "accent_color", "background_color", "authorized_asset_ids",
})


def compose_approved_content(context, approved_brief, *, mode, asset_id=None,
                             template=None, format="square"):
    if (not isinstance(context, dict)
        or not _REQUIRED_CONTEXT_KEYS <= set(context)
        or set(context) - _REQUIRED_CONTEXT_KEYS - {"logo_asset_id"}
        or not isinstance(approved_brief, dict)
        or set(approved_brief) != _BRIEF_KEYS):
        raise DesignError("Approved v2 content bridge needs exact server-owned fields")
    if (approved_brief["shop_id"] != context["shop_id"]
        or approved_brief["campaign_id"] != context["campaign_id"]
        or approved_brief["day_id"] != context["day_id"]):
        raise DesignError("Cross-tenant or stale campaign content denied")
    if (approved_brief["review_state"] != "APPROVED"
        or type(approved_brief["approved_version"]) is not int
        or approved_brief["approved_version"] < 1):
        raise DesignError("Unapproved content cannot enter poster production")
    ids = context["authorized_asset_ids"]
    if (not isinstance(ids, (list, tuple)) or len(ids) > 24
        or any(not isinstance(item, str) for item in ids)
        or len(set(ids)) != len(ids)):
        raise DesignError("Unsafe authorized media manifest")
    if mode == "image" and (asset_id is None or asset_id not in ids):
        raise DesignError("Photo not authorized in this approved shop")
    if asset_id is not None and asset_id not in ids:
        raise DesignError("Unapproved source media")
    logo_asset_id = context.get("logo_asset_id")
    if logo_asset_id is not None and logo_asset_id not in ids:
        raise DesignError("Unapproved brand logo")
    design = compose_poster(
        shop_id=context["shop_id"], mode=mode,
        prompt=approved_brief["visual_brief"],
        business_name=context["business_name"],
        headline=approved_brief["headline"], cta=approved_brief["cta"],
        approved_offer=approved_brief["offer_text"], source_asset_id=asset_id,
        template=template, format=format, logo_asset_id=logo_asset_id,
        accent=context["accent_color"],
        background=context["background_color"],
    )
    return validate_design(design)
