"""Feature2 offline draft content -> human-reviewable Feature4 direction proposal.

Pure transformation of existing Feature2 content_intelligence sidecar/v1
storyboard. It does NOT create a trusted approval_id/review hash or approve
media. The authenticated backend must persist and independently review the
proposal, freeze the exact approved script/media snapshot, and only then call
feature2_feature4_bridge.compile_feature2_direction. No provider or GPU use.
"""
from __future__ import annotations

import copy
import re

from creative_contract import CreativeContractError

_UUID = re.compile(r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$")
_MAX = 12


def propose_direction_from_content_draft(content, *, day_index=1):
    """Preserve original F2 lines/directions; return clearly UNAPPROVED draft."""
    if type(content) is not dict or content.get("generation_mode") != "deterministic":
        # Initial no-paid-provider CPU lane. Configured model outputs require
        # independent editorial review and an explicitly separate integration.
        raise CreativeContractError("Only offline deterministic F2 draft is supported")
    review = content.get("review")
    if (type(review) is not dict or review.get("status") != "DRAFT"
            or review.get("can_publish") is not False
            or review.get("requires_human_approval") is not True
            or review.get("issues")):
        raise CreativeContractError("Feature2 content must remain human-reviewed draft")
    campaign = content.get("campaign")
    sidecars = content.get("content_days")
    if (type(campaign) is not dict or type(sidecars) is not list
            or type(campaign.get("days")) is not list
            or len(sidecars) != len(campaign["days"])
            or type(day_index) is not int
            or day_index < 1 or day_index > len(sidecars)
            or not _UUID.fullmatch(str(campaign.get("id")))
            or not _UUID.fullmatch(str(campaign.get("shop_id")))):
        raise CreativeContractError("Malformed F2 campaign/sidecar identity")
    day, extra = campaign["days"][day_index - 1], sidecars[day_index - 1]
    if (type(day) is not dict or type(extra) is not dict
            or day.get("shop_id") != campaign["shop_id"]
            or day.get("campaign_id") != campaign["id"]
            or day.get("review_status") != "DRAFT"
            or day.get("id") != extra.get("day_id")
            or extra.get("approval_status") != "PENDING_RETAILER"):
        raise CreativeContractError("F2 day is cross-tenant, stale or already modified")
    reel = day.get("instagram", {}).get("reel")
    video = extra.get("video")
    if (type(reel) is not dict or type(video) is not dict
            or reel.get("duration_seconds") != 30
            or video.get("duration_seconds") != 30
            or type(reel.get("storyboard")) is not list
            or type(video.get("scenes")) is not list
            or not 1 <= len(reel["storyboard"]) == len(video["scenes"]) <= _MAX):
        raise CreativeContractError("F2 storyboard/scene direction incompatible")
    position = 0
    scenes = []
    approved_copy = []
    for i, (shot, detailed) in enumerate(zip(reel["storyboard"], video["scenes"])):
        if type(shot) is not dict or type(detailed) is not dict:
            raise CreativeContractError("Malformed F2 scene")
        if (shot.get("start_seconds") != position
                or detailed.get("start_seconds") != position
                or type(shot.get("duration_seconds")) is not int
                or shot["duration_seconds"] < 1
                or detailed.get("duration_seconds") != shot["duration_seconds"]
                or detailed.get("asset_id") != shot.get("asset_id")):
            raise CreativeContractError("F2 detailed storyboard disagrees with source timing/assets")
        headline = shot.get("overlay_text")
        narrative = detailed.get("script")
        if (type(headline) is not str or not 1 <= len(headline.strip()) <= 110
                or headline != headline.strip() or
                type(narrative) is not str or not 1 <= len(narrative.strip()) <= 900):
            raise CreativeContractError("Unsafe or missing approved copy / directions")
        asset = shot.get("asset_id")
        if type(asset) is not str or not _UUID.fullmatch(asset):
            raise CreativeContractError("Unrecognized media reference")
        scenes.append({
            "start": position, "duration": shot["duration_seconds"],
            "asset_id": asset, "headline": headline,
            "transition": "fade" if i else "cut",
            "animation_preset": "subtle_zoom",
        })
        approved_copy.append(headline)
        position += shot["duration_seconds"]
    if position != 30 or reel.get("cta") != scenes[-1]["headline"]:
        raise CreativeContractError("F2 CTA and full 30-second storyboard must agree")
    # This is an EDITORIAL PROPOSAL, not a completed RLS rights proof or
    # synthetic approval. Voiceover is text only until a reviewed audio grant.
    return {
        "version": "creative_direction_v1",
        "source_feature": "feature2", "approved": False,
        "shop_id": campaign["shop_id"], "campaign_id": campaign["id"],
        "day_id": day["id"], "duration_seconds": 30, "template": "cinematic",
        "cta": reel["cta"], "music_asset_id": reel.get("music_asset_id"),
        "scenes": scenes,
        "script": {
            "source_feature": "feature2", "approved": False,
            "approved_text": list(dict.fromkeys(approved_copy)),
            "cta": reel["cta"],
        },
        "voiceover_text": " ".join(approved_copy),
        "scene_directions": copy.deepcopy(video["scenes"]),
        "caption": day["instagram"]["caption"],
        "source_status": "PENDING_RETAILER_REVIEW",
    }
