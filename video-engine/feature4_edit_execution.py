"""F4-15: execute a trusted Feature #7 edit decision through existing Feature #4.

This is a pure, source-only integration seam. Feature #7 owns generating,
understanding and approving edits; the coordinator owns DB-backed approval,
JWT/RLS, immutable snapshots, quotas, queue dispatch and any public route.

A browser/model may NEVER supply this trusted record directly. The caller
must load the reviewed Feature #7 edit decision and approval snapshot in the
same authorized transaction, then store the returned compiler bundle.
Only existing rg_video_v2 scene primitives are emitted. No shell, HTML,
arbitrary media URI, provider call, billing or cloud access occurs here.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re

from creative_contract import CreativeContractError, safe_ref
from feature4_intent_compiler import compile_approved_storyboard

EDIT_FIELDS = frozenset({
    "source_feature", "approved", "approval_id", "timeline_version",
    "shop_id", "campaign_id", "draft_sha256", "scenes",
})
EDIT_SCENE_FIELDS = frozenset({
    "source_scene_index", "duration", "animation_preset", "transition",
    "trim_start", "mute_source",
})
ANIMATIONS = frozenset({"subtle_zoom", "fade", "slide", "pop", "glow"})
TRANSITIONS = frozenset({"fade", "slide", "cut"})
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MAX_SCENES = 12


def draft_fingerprint(draft):
    """Stable binding to the *original* client storyboard, before editing."""
    try:
        if type(draft) is not dict:
            raise ValueError("draft is not an object")
        data = json.dumps(
            draft, sort_keys=True, ensure_ascii=False,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise CreativeContractError("Invalid original storyboard") from exc
    return hashlib.sha256(data).hexdigest()


def execute_approved_edit(draft, snapshot, approved_edits):
    """Compile the same trusted v2 request, after deterministic AI edit choices.

    The source scenes must form a permutation of the already selected scenes:
    the editor may reorder, retime, change an allowed transition/animation or
    trim/mute an existing video. It cannot insert/change products, offers,
    logos, scripts, media rights, output format or soundtrack. Any media
    selection change must first pass the coordinator's reviewed asset workflow.
    The existing private-media compiler revalidates every resulting scene.
    """
    if type(draft) is not dict or type(snapshot) is not dict:
        raise CreativeContractError("Server-approved storyboard snapshot required")
    if type(approved_edits) is not dict or set(approved_edits) != EDIT_FIELDS:
        raise CreativeContractError("Unexpected Feature7 edit decision fields")
    if (approved_edits["source_feature"] != "feature7" or
            approved_edits["approved"] is not True or
            approved_edits["timeline_version"] != "creative_reel_v1"):
        raise CreativeContractError("Approved Feature7 timeline required")
    approval_id = safe_ref(approved_edits["approval_id"], "Feature7 approval")
    trusted_review = snapshot.get("edit_plan")
    if (type(trusted_review) is not dict or
            trusted_review != {
                "source_feature": "feature7",
                "approved": True,
                "approval_id": approval_id,
                "timeline_version": "creative_reel_v1",
            }):
        raise CreativeContractError("Feature7 review must match server snapshot")
    if (approved_edits["shop_id"] != snapshot.get("shop_id") or
            approved_edits["campaign_id"] != snapshot.get("campaign_id") or
            draft.get("shop_id") != snapshot.get("shop_id")):
        raise CreativeContractError("Feature7 approval tenant/campaign mismatch")
    digest = approved_edits["draft_sha256"]
    if type(digest) is not str or not SHA256.fullmatch(digest):
        raise CreativeContractError("Missing canonical draft hash")
    if digest != draft_fingerprint(draft):
        raise CreativeContractError("Stale Feature7 edit decision")
    sources = draft.get("scenes")
    edits = approved_edits["scenes"]
    if (type(sources) is not list or type(edits) is not list or
            not 1 <= len(sources) <= MAX_SCENES or len(edits) != len(sources)):
        raise CreativeContractError("Every approved original scene must be accounted for")

    new_draft = copy.deepcopy(draft)
    ordered = []
    seen = set()
    elapsed = 0.0
    for edit in edits:
        if (type(edit) is not dict or
                set(edit) - EDIT_SCENE_FIELDS or
                not {"source_scene_index", "duration"}.issubset(edit)):
            raise CreativeContractError("Unapproved editor instruction")
        index = edit["source_scene_index"]
        if type(index) is not int or not 0 <= index < len(sources) or index in seen:
            raise CreativeContractError("Duplicate or foreign source scene")
        seen.add(index)
        duration = edit["duration"]
        if (type(duration) not in (int, float) or
                not math.isfinite(duration) or not .5 <= duration <= 60):
            raise CreativeContractError("Invalid editor scene duration")
        scene = copy.deepcopy(sources[index])
        scene["start"] = round(elapsed, 6)
        scene["duration"] = duration
        if "animation_preset" in edit:
            if type(edit["animation_preset"]) is not str or edit["animation_preset"] not in ANIMATIONS:
                raise CreativeContractError("Unapproved animation")
            scene["animation_preset"] = edit["animation_preset"]
        if "transition" in edit:
            if type(edit["transition"]) is not str or edit["transition"] not in TRANSITIONS:
                raise CreativeContractError("Unapproved transition")
            scene["transition"] = edit["transition"]
        if "trim_start" in edit:
            start = edit["trim_start"]
            if (type(start) not in (int, float) or
                    not math.isfinite(start) or not 0 <= start <= 3600):
                raise CreativeContractError("Unapproved trim offset")
            scene["trim_start"] = start
        if "mute_source" in edit:
            if type(edit["mute_source"]) is not bool:
                raise CreativeContractError("Unapproved audio change")
            scene["mute_source"] = edit["mute_source"]
        ordered.append(scene)
        elapsed = round(elapsed + duration, 6)
    total = draft.get("duration_seconds")
    if type(total) is not int or total not in (15, 30, 60) or abs(elapsed - total) > .001:
        raise CreativeContractError("Feature7 timeline does not fill approved duration")
    new_draft["scenes"] = ordered

    # The existing compiler is authoritative for Feature2 copy, Feature3/5
    # media rights/provenance, source audio, transitions, user-supplied IDs and
    # duration. The lineage it emits records the actual Feature7 approval ID.
    return compile_approved_storyboard(new_draft, snapshot)
