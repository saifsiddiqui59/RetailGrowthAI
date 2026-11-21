"""CPU-only Feature #2 approved direction -> Feature #4 storyboard compiler.

SOURCE-ONLY pure adapter. Call only with a Feature2 plan AND an independent
immutable, RLS-authorized/approval-checked snapshot loaded by the backend.
The expected review hash must come from the trusted saved approval receipt,
never the HTTP request. This module cannot approve plans, reserve credits,
queue jobs, grant rights, or sign downloads.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import hmac
import re

from creative_contract import CreativeContractError, safe_ref
from feature4_intent_compiler import compile_approved_storyboard

VERSION = "creative_direction_v1"
SUPPORTED_DURATIONS = (15, 30, 60)
SCENE_RENDER_FIELDS = frozenset({
    "duration", "headline", "asset_id", "animation_preset", "transition",
    "poster_overlay_asset_id", "offer", "trim_start", "mute_source", "sfx_asset_id",
})


def _direction_json(value):
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError, OverflowError) as exc:
        raise CreativeContractError("Creative direction must be finite JSON") from exc
    if len(encoded.encode("utf-8")) > 96_000:
        raise CreativeContractError("Creative direction exceeds trusted input limit")
    return encoded


def direction_review_digest(direction):
    """Canonical SHA for entire frozen approval, excluding its own hash field.

    Caller MUST read the expected digest from independently trusted approval
    storage; hashing client input alone does not authorize a review.
    """
    if type(direction) is not dict:
        raise CreativeContractError("Malformed creative approval")
    immutable = copy.deepcopy(direction)
    immutable.pop("review_hash", None)
    return hashlib.sha256(b"rgai-f2-f4-approved-v1\0" +
                          _direction_json(immutable).encode("utf-8")).hexdigest()


def _scenes(direction):
    raw_scenes = direction.get("scenes")
    if type(raw_scenes) is not list or not 1 <= len(raw_scenes) <= 12:
        raise CreativeContractError("Feature2 direction requires 1-12 reviewed scenes")
    duration = direction["duration_seconds"]
    if type(duration) is not int or duration not in SUPPORTED_DURATIONS:
        raise CreativeContractError("Unsupported approved direction duration")
    position_ms = 0
    scenes = []
    for index, shot in enumerate(raw_scenes):
        if type(shot) is not dict or not {"headline", "duration", "asset_id"} <= shot.keys():
            raise CreativeContractError("Incomplete Feature2 storyboard scene")
        if "order" in shot and (type(shot["order"]) is not int or shot["order"] != index):
            raise CreativeContractError("Feature2 scene order changed after approval")
        seconds = shot["duration"]
        if (type(seconds) not in (int, float) or not math.isfinite(seconds)
                or seconds < 0.5 or seconds > duration):
            raise CreativeContractError("Invalid Feature2 scene length")
        milliseconds = round(seconds * 1000)
        if abs(milliseconds / 1000 - seconds) > 0.000001:
            raise CreativeContractError("Scene duration must be millisecond aligned")
        if "start" in shot and (type(shot["start"]) not in (int, float)
                or not math.isfinite(shot["start"])
                or abs(shot["start"] * 1000 - position_ms) > 0.001):
            raise CreativeContractError("Feature2 scene timeline has a gap or overlap")
        if type(shot["headline"]) is not str or not shot["headline"].strip():
            raise CreativeContractError("Feature2 scene has no approved headline")
        if type(shot["asset_id"]) is not str or not shot["asset_id"]:
            raise CreativeContractError("Feature2 scene requires reviewed stock/retailer media")
        scene = {key: copy.deepcopy(value) for key, value in shot.items()
                 if key in SCENE_RENDER_FIELDS}
        scene["start"] = position_ms / 1000
        # Camera/voice/motion annotations remain in source_direction, but may
        # NOT introduce arbitrary FFmpeg filters, URLs, or scripts to F4.
        scenes.append(scene)
        position_ms += milliseconds
    if position_ms != duration * 1000:
        raise CreativeContractError("Feature2 storyboard does not fill approved duration")
    return scenes


def compile_feature2_direction(direction, snapshot, *, reviewed_hash):
    """Create an F4 request/bundle without rewriting F2's approved storyboard.

    snapshot: existing server-frozen F4 approval snapshot (NOT client input).
    reviewed_hash: revision token read separately from trusted approval storage.
    Return source_direction separately for immutable lineage persistence.
    """
    if type(direction) is not dict or type(snapshot) is not dict:
        raise CreativeContractError("Trusted Feature2 direction and F4 snapshot required")
    _direction_json(direction)
    required = {"version", "source_feature", "approved", "shop_id",
                "campaign_id", "approval_id", "review_hash", "duration_seconds",
                "template", "cta", "scenes", "script"}
    if not required <= set(direction):
        raise CreativeContractError("Feature2 plan is missing required reviewed fields")
    if (direction["version"] != VERSION or direction["source_feature"] != "feature2"
            or direction["approved"] is not True):
        raise CreativeContractError("Feature2 direction is not approved or versioned")
    if (type(reviewed_hash) is not str or not re.fullmatch(r"[0-9a-f]{64}", reviewed_hash)
            or not hmac.compare_digest(direction_review_digest(direction), reviewed_hash)):
        raise CreativeContractError("Creative direction bytes differ from immutable approval")
    if (direction["review_hash"] != reviewed_hash
            or direction["shop_id"] != snapshot.get("shop_id")
            or direction["campaign_id"] != snapshot.get("campaign_id")
            or direction["approval_id"] != snapshot.get("approval_id")):
        raise CreativeContractError("Feature2 approval revision or tenant changed")
    trusted_script = snapshot.get("script")
    if (type(trusted_script) is not dict
            or trusted_script.get("approved") is not True
            or trusted_script.get("source_feature") != "feature2"
            or trusted_script.get("approval_id") != direction["approval_id"]
            or direction["script"] != trusted_script
            or direction["cta"] != trusted_script.get("cta")):
        raise CreativeContractError("Creative text is not the immutable approved script")
    if direction["template"] not in ("cinematic", "streetwear", "festival"):
        raise CreativeContractError("Feature2 selected unsupported F4 template")
    # Reject output overrides: render size is a deliberate, versioned F4 preset.
    if ("output" in direction and direction["output"] !=
            {"width": 1080, "height": 1920, "fps": 30}):
        raise CreativeContractError("Unreviewed output format override")
    draft = {
        "version": "rg_video_v2", "shop_id": snapshot["shop_id"],
        "mode": "media", "template": direction["template"],
        "duration_seconds": direction["duration_seconds"],
        "output": {"width": 1080, "height": 1920, "fps": 30},
        "cta": direction["cta"],
        "music_asset_id": direction.get("music_asset_id"),
        "scenes": _scenes(direction),
    }
    if direction.get("voiceover_asset_id") is not None:
        draft["voiceover_asset_id"] = direction["voiceover_asset_id"]
    # Existing F4 compiler performs current rights/tenant/media checks and
    # renders exactly the original approved text, cue timings and asset IDs.
    result = compile_approved_storyboard(draft, snapshot)
    source = copy.deepcopy(direction)
    encoded = _direction_json(source).encode("utf-8")
    # Exact server-created v2 intent for the read-only editor; never browser authority.
    result["approved_draft"] = copy.deepcopy(draft)
    result["source_direction"] = source
    result["source_review_hash"] = reviewed_hash
    result["source_sha256"] = hashlib.sha256(encoded).hexdigest()
    return result
