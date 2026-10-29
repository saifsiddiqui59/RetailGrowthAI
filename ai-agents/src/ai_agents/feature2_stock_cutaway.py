"""Versioned Feature2 stock cutaway proposal, not a paid motion/editor dispatch.

The plan is immutable editorial planning for optional stock atmosphere B-roll,
not proof of a downloadable, licensed, tenant-owned video or final MP4. Any
approved source reference is checked by feature2_stock_media first and must
be revalidated by the actual Feature4 backend. Never substitute stock
footage for an explicitly approved garment or impersonate a stock person.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from copy import deepcopy
from .feature2_stock_media import BrollEvaluation, StockMediaRejected, candidate_catalog


class StockCutawayRejected(ValueError):
    pass


def compile_stock_cutaway_preview(
    *, creative_bundle: dict, reviewed_stock: BrollEvaluation,
    scene_id: str, trim_seconds: int = 0
) -> dict:
    if type(creative_bundle) is not dict or not isinstance(reviewed_stock, BrollEvaluation):
        raise StockCutawayRejected("Original creative bundle and reviewed stock required")
    plan = creative_bundle.get("creative_direction_v1")
    approval = creative_bundle.get("approval_record")
    motions = creative_bundle.get("motion_direction_v1")
    if (type(plan) is not dict or type(approval) is not dict or type(motions) is not list
        or plan.get("contract") != "creative_direction_v1"
        or plan.get("duration_seconds") not in (30, 60)
        or approval.get("review_status") != "DRAFT"
        or approval.get("approved") is not False
        or approval.get("can_publish") is not False
        or approval.get("can_run_paid_motion") is not False
        or not isinstance(approval.get("plan_sha256"), str)
        or len(approval["plan_sha256"]) != 64):
        raise StockCutawayRejected("Only unapproved 30/60s original creative can preview B-roll")
    if (reviewed_stock.status != "LICENSED_ATMOSPHERE_PREVIEW_ONLY"
        or not reviewed_stock.can_show_in_offline_editor
        or reviewed_stock.can_use_as_product_ground_truth
        or reviewed_stock.can_imply_endorsement
        or reviewed_stock.can_dispatch_motion
        or reviewed_stock.can_publish or reviewed_stock.gpu_enabled
        or reviewed_stock.shop_id != plan.get("shop_id")
        or len(reviewed_stock.original_sha256) != 64):
        raise StockCutawayRejected("B-roll rights are not valid for this preview")
    catalog = {c["candidate_id"]: c for c in candidate_catalog()}
    source = catalog.get(reviewed_stock.stock_candidate_id)
    if (not source or source["source_page"] != reviewed_stock.candidate_source_page
        or source["media_kind"] != "VIDEO" or source["purpose"] != "ATMOSPHERE_BROLL"):
        raise StockCutawayRejected("Only eligible real stock video reference can supply cutaway")
    scenes = plan.get("scenes")
    if (not isinstance(scenes, list) or type(scene_id) is not str
        or len([s for s in scenes if s.get("id") == scene_id]) != 1):
        raise StockCutawayRejected("Known original scene needed")
    scene = next(s for s in scenes if s["id"] == scene_id)
    if scene.get("role") != "story" or scene.get("duration_seconds") != 5:
        raise StockCutawayRejected("B-roll may replace only a story cutaway, never garment or CTA")
    if type(trim_seconds) is not int or trim_seconds < 0 or trim_seconds + 5 > source["expected_duration_seconds"]:
        raise StockCutawayRejected("Unbounded stock trim")
    original_motion = [m for m in motions if m.get("scene_id") == scene_id]
    if (len(original_motion) != 1 or original_motion[0].get("duration_seconds") != 5
        or original_motion[0].get("shot_start_seconds") != scene.get("start_seconds")):
        raise StockCutawayRejected("Original scene and shot timeline disagree")
    old = json.dumps(creative_bundle, sort_keys=True)
    item = {
        "contract": "feature2_stock_cutaway_preview_v1",
        "shop_id": plan["shop_id"], "campaign_id": plan["campaign_id"],
        "scene_id": scene_id, "original_motion_shot_id": original_motion[0]["shot_id"],
        "original_approved_plan_sha256": approval["plan_sha256"],
        "cutaway_timeline_start_seconds": scene["start_seconds"],
        "cutaway_duration_seconds": 5,
        "stock_clip_trim_start_seconds": trim_seconds,
        "stock_candidate_id": source["candidate_id"],
        "stock_source_page": source["source_page"],
        "stock_original_sha256": reviewed_stock.original_sha256,
        "stock_license_review_required_at_use": True,
        "garment_source_substitution_allowed": False,
        "script_and_voiceover_unchanged": True,
        "render_status": "NOT_RENDERED_PREVIEW_ONLY",
        "paid_motion_dispatch": False,
        "can_publish": False,
        "gpu_enabled": False,
    }
    if json.dumps(creative_bundle, sort_keys=True) != old:
        raise StockCutawayRejected("Stock preview cannot mutate original director")
    return item
