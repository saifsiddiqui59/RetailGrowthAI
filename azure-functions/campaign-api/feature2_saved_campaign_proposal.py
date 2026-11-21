"""F2 existing persisted campaign storyboard -> unapproved F4 creative proposal.

This is the lowest-cost basic-campaign lane, NOT a replacement for the actual
pinned MIT Creative Director: no provider motion, music, speech or GPU. Current
tenant JWT/RLS/campaign/day/media ownership is established by the calling
server. Exact retailer copy, assets and timing are carried through unchanged.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re

from tenant_store import canonical_uuid


class CreativeContractError(ValueError):
    """Same strict pure JSON contract, with no video/codec import on HTTP host."""


def uuid(value, label):
    try:
        return canonical_uuid(value)
    except (TypeError, AttributeError, ValueError) as exc:
        raise CreativeContractError("Invalid " + label) from exc

SAFE_SHOP_IMAGE = re.compile(r"^([0-9a-f-]{36})/uploads/([0-9a-f-]{36})\.(png|jpg|webp)$")
MIME = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
HEX = re.compile(r"^[0-9a-f]{64}$")


def proposal_json(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False)
    if len(encoded.encode("utf-8")) > 96_000:
        raise CreativeContractError("F2 proposal exceeds bounded SQL approval")
    return encoded


def saved_campaign_creative_proposal(campaign, day_id, media):
    if (type(campaign) is not dict or
            campaign.get("status") != "DRAFT" or
            type(campaign.get("days")) is not list):
        raise CreativeContractError("Current signed campaign must be a saved draft")
    sid = uuid(campaign["shop_id"], "shop_id")
    cid = uuid(campaign["id"], "campaign_id")
    did = uuid(day_id, "day_id")
    days = [day for day in campaign["days"] if day.get("id") == did]
    if (len(days) != 1 or days[0].get("shop_id") != sid or
            days[0].get("campaign_id") != cid or
            days[0].get("review_status") != "DRAFT"):
        raise CreativeContractError("No current editable day for same shop")
    day = days[0]
    original = day.get("instagram", {}).get("reel")
    if (type(original) is not dict or
            original.get("duration_seconds") != 30 or
            original.get("aspect_ratio") != "9:16" or
            type(original.get("storyboard")) is not list or
            not 1 <= len(original["storyboard"]) <= 12 or
            original.get("music_asset_id") is not None):
        raise CreativeContractError("30s still-image F2 storyboard only; music requires separate rights")
    if type(media) is not list or not media:
        raise CreativeContractError("No server-verified private source stills")
    assets = {}
    for row in media:
        if type(row) is not dict or row.get("shop_id") != sid:
            raise CreativeContractError("Mixed-shop media rows")
        aid = uuid(row.get("id"), "private media id")
        bucket, src, license_name = (row.get("storage_bucket"),
                                     row.get("source"), row.get("license_name"))
        path, mime = row.get("object_path"), row.get("mime_type")
        m = SAFE_SHOP_IMAGE.fullmatch(path or "")
        if (aid in assets or bucket != "retailgrowth-media" or src != "UPLOAD"
                or license_name != "owned" or mime not in MIME
                or m is None or m[1] != sid or m[2] != aid
                or m[3] != MIME[mime]):
            raise CreativeContractError("Source image lacks exact same-shop private owned rights")
        assets[aid] = copy.deepcopy(row)
    start = 0
    texts, scenes, used = [], [], set()
    for raw in original["storyboard"]:
        if type(raw) is not dict or set(raw) != {
            "start_seconds", "duration_seconds", "asset_id", "overlay_text"
        }:
            raise CreativeContractError("Saved source storyboard changed")
        aid = uuid(raw["asset_id"], "scene source asset")
        length = raw["duration_seconds"]
        text = raw["overlay_text"]
        if (aid not in assets or type(length) is not int or length < 1
                or length > 30 or type(raw["start_seconds"]) is not int
                or raw["start_seconds"] != start or type(text) is not str
                or not 1 <= len(text) <= 110 or text != text.strip()
                or "<" in text or ">" in text
                or any(ord(x) < 32 for x in text)):
            raise CreativeContractError("Unapproved or discontinuous saved scene")
        scenes.append({
            "duration": length, "headline": text, "asset_id": aid,
            "transition": "cut" if not scenes else "fade",
            "animation_preset": "subtle_zoom",
        })
        used.add(aid)
        texts.append(text)
        start += length
    cta = original.get("cta")
    if start != 30 or type(cta) is not str or cta != texts[-1] or set(assets) != used:
        raise CreativeContractError("Saved F2 reel timeline, CTA or media references differ")
    # Build a fresh *unapproved* proposal from server-fetched, RLS-scoped
    # campaign data. Client POST contains only saved day_id, never this copy.
    result = {
        "version": "creative_direction_v1", "source_feature": "feature2",
        "shop_id": sid, "campaign_id": cid, "day_id": did,
        "duration_seconds": 30, "approved": False,
        "template": "cinematic", "cta": cta, "music_asset_id": None,
        "scenes": scenes,
        "script": {"source_feature": "feature2", "approved": False,
                   "approved_text": list(dict.fromkeys(texts)), "cta": cta},
        "source_status": "PENDING_RETAILER_REVIEW",
        "source_reel": copy.deepcopy(original),
    }
    digest = hashlib.sha256(proposal_json(result).encode("utf-8")).hexdigest()
    if not HEX.fullmatch(digest):
        raise CreativeContractError("Unable to hash proposed F2 draft")
    return {"proposal": result, "proposal_sha256": digest,
            "media_asset_ids": sorted(used)}
