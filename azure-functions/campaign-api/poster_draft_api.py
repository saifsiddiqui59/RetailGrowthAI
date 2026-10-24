"""Part 1 poster-draft creation/lookup over the user's verified RLS JWT.

This only persists design *metadata*. It does not invoke image generation,
register private PNG output, apply migrations or publish anything.
"""
from __future__ import annotations

import re

from tenant_store import canonical_uuid

_HEX = re.compile(r"^#[a-fA-F0-9]{6}$")
_TEMPLATES = frozenset(("editorial", "bold", "minimal"))
_FORMATS = frozenset(("square", "portrait"))
_REQUIRED = frozenset((
    "day_id", "source_asset_id", "template", "format",
    "business_name", "accent_color", "background_color",
))
_OPTIONAL = frozenset(("logo_asset_id", "offer_text"))


class PosterDraftAPI:
    def __init__(self, user_store):
        self.store = user_store

    def create(self, token, user_id, campaign_id, body):
        cid = canonical_uuid(campaign_id)
        if not isinstance(body, dict) or not _REQUIRED <= body.keys() or body.keys() - (_REQUIRED | _OPTIONAL):
            return 400, {"error": "INVALID_REQUEST"}
        day_id, source_id = (canonical_uuid(body[k]) for k in ("day_id", "source_asset_id"))
        logo_id = (canonical_uuid(body["logo_asset_id"]) if body.get("logo_asset_id") else None)
        template, format_name = body["template"], body["format"]
        brand, accent, background = (body[k] for k in
                                     ("business_name", "accent_color", "background_color"))
        offer = body.get("offer_text")
        if (template not in _TEMPLATES or format_name not in _FORMATS
                or not isinstance(brand, str) or not 1 <= len(brand.strip()) <= 70
                or any(ord(ch) < 32 for ch in brand)
                or not isinstance(accent, str) or not _HEX.fullmatch(accent)
                or not isinstance(background, str) or not _HEX.fullmatch(background)
                or offer is not None and
                (not isinstance(offer, str) or not 1 <= len(offer.strip()) <= 110
                 or any(ord(ch) < 32 for ch in offer))):
            return 400, {"error": "INVALID_REQUEST"}
        campaign = self.store.campaign(token, user_id, cid)
        if campaign is None:
            return 404, {"error": "NOT_FOUND"}
        if campaign.get("status") != "DRAFT":
            return 409, {"error": "CAMPAIGN_NOT_DRAFT"}
        shop_id = canonical_uuid(campaign["shop_id"])
        if not self.store.member(token, user_id, shop_id, write=True):
            return 403, {"error": "FORBIDDEN"}
        matches = [d for d in campaign["days"] if d.get("id") == day_id
                   and d.get("shop_id") == shop_id and d.get("campaign_id", cid) == cid]
        if len(matches) != 1:
            return 404, {"error": "NOT_FOUND"}
        day = matches[0]
        if day.get("review_status") != "DRAFT":
            return 409, {"error": "DAY_NOT_DRAFT"}
        storyboard = day.get("instagram", {}).get("reel", {}).get("storyboard")
        if not isinstance(storyboard, list) or source_id not in [
                s.get("asset_id") for s in storyboard if isinstance(s, dict)]:
            return 403, {"error": "ASSET_ACCESS_DENIED"}
        ids = [source_id] + ([logo_id] if logo_id else [])
        if not self.store.assets(token, shop_id, ids):
            return 403, {"error": "ASSET_ACCESS_DENIED"}
        # The RLS-authenticated SQL RPC independently checks permissions,
        # lineage, rights evidence, trial and bounded draft creation again.
        draft_id = self.store.create_poster_draft(token, {
            "p_shop_id": shop_id,
            "p_campaign_id": cid,
            "p_day_id": day_id,
            "p_source_asset_id": source_id,
            "p_logo_asset_id": logo_id,
            "p_template": template,
            "p_format": format_name,
            "p_business_name": brand.strip(),
            "p_accent_color": accent,
            "p_background_color": background,
            "p_offer_text": offer.strip() if offer else None,
        })
        if draft_id is None:
            return 403, {"error": "POSTER_DRAFT_DENIED"}
        return 201, {"poster_id": canonical_uuid(draft_id), "status": "DRAFT"}

    def get(self, token, user_id, draft_id):
        pid = canonical_uuid(draft_id)
        draft = self.store.poster_draft(token, user_id, pid)
        if draft is None:
            return 404, {"error": "NOT_FOUND"}
        return 200, {
            "poster_id": pid, "status": draft["status"],
            "campaign_id": draft["campaign_id"], "day_id": draft["day_id"],
            "template": draft["template"], "format": draft["format"],
            "business_name": draft["business_name"],
            "accent_color": draft["accent_color"],
            "background_color": draft["background_color"],
            "offer_text": draft.get("offer_text"),
            "source_asset_id": draft["source_asset_id"],
            "output_asset_id": draft.get("output_asset_id"),
        }

    def list_for_day(self, token, user_id, campaign_id, day_id):
        """Only saved campaign days visible to the signed-in shop member."""
        cid, did = canonical_uuid(campaign_id), canonical_uuid(day_id)
        campaign = self.store.campaign(token, user_id, cid)
        if campaign is None:
            return 404, {"error": "NOT_FOUND"}
        sid = canonical_uuid(campaign["shop_id"])
        days = [d for d in campaign["days"] if d.get("id") == did and
                d.get("campaign_id") == cid and d.get("shop_id") == sid]
        if len(days) != 1 or not self.store.member(token, user_id, sid):
            return 404, {"error": "NOT_FOUND"}
        rows = self.store.posters_for_day(token, sid, cid, did)
        return 200, {"posters": [{
            "poster_id": row["id"],
            "status": row["status"], "revision": row["revision"],
            "template": row["template"], "format": row["format"],
            "business_name": row["business_name"],
            "accent_color": row["accent_color"],
            "background_color": row["background_color"],
            "offer_text": row.get("offer_text"),
            "source_asset_id": row["source_asset_id"],
            "output_asset_id": row.get("output_asset_id"),
            "job_id": row.get("job_id"), "job_status": row.get("job_status"),
        } for row in rows]}

