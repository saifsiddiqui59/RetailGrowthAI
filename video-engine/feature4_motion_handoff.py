"""Feature4's source-only handoff from approved Feature2 direction to Feature5.

Does NOT run AI or directly enqueue a paid provider. The coordinator must fetch
trusted F2/F3/5 rows, reserve quota/claim once, and transactionally persist the
returned command through its existing outbox. Requires exact approved source
references; never reauthors creative text, camera direction or motion prompts.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from uuid import UUID

class Feature4MotionHandoffError(ValueError):
    pass

_SHA = re.compile(r"^[0-9a-f]{64}$")
_SAFE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
_ALLOWED = frozenset(("prompt", "negative_prompt", "source_asset_id", "duration_seconds",
                      "shot_id", "choreography", "camera", "lighting", "fidelity_requirements"))
_RETAIL_VIDEO_PROFILE = "feature5-v1"
_SUPPORTED_MODEL = "hunyuanvideo-1.5-480p"

def _id(value, label):
    try:
        if str(UUID(value)) != value: raise ValueError()
    except (ValueError, TypeError, AttributeError) as exc:
        raise Feature4MotionHandoffError("Invalid " + label) from exc
    return value

def _safe_copy(value):
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise Feature4MotionHandoffError("Invalid Feature2 motion details") from exc
    if len(encoded) > 9000:
        raise Feature4MotionHandoffError("Motion brief exceeds bounded approved contract")
    return copy.deepcopy(value), hashlib.sha256(encoded.encode()).hexdigest()

def prepare_feature5_requests(direction, snapshot):
    """Prepared commands for coordinator-owned outbox, not an API or billable send.

    All calls must use server-fetched versions of both arguments. We only
    support the actually source-tested F5 5s/480p profile, not pretend Wan is
    already deployed or silently truncate detailed prompts.
    """
    if type(direction) is not dict or type(snapshot) is not dict:
        raise Feature4MotionHandoffError("Trusted Feature2 direction and snapshot required")
    for key in ("shop_id", "campaign_id", "approval_id"):
        _id(snapshot.get(key), key)
        if direction.get(key) != snapshot[key]:
            raise Feature4MotionHandoffError("Stale or foreign creative direction")
    if (direction.get("version") != "creative_direction_v1" or
        direction.get("source_feature") != "feature2" or
        direction.get("approved") is not True or
        snapshot.get("approved") is not True or
        not _SHA.fullmatch(direction.get("review_hash", "")) or
        direction["review_hash"] != snapshot.get("review_hash")):
        raise Feature4MotionHandoffError("Unreviewed Feature2 creative direction")
    assets = snapshot.get("assets")
    scenes = direction.get("scenes")
    if type(assets) is not dict or type(scenes) is not list or not 1 <= len(scenes) <= 12:
        raise Feature4MotionHandoffError("Trusted private media and shots are required")
    commands = []
    seen = set()
    for scene in scenes:
        if type(scene) is not dict:
            raise Feature4MotionHandoffError("Malformed Feature2 scene")
        detail = scene.get("motion_direction_v1")
        if detail is None:
            continue
        if type(detail) is not dict or set(detail) != _ALLOWED:
            raise Feature4MotionHandoffError("Unsupported motion brief; request Feature2 review")
        shot_id = detail["shot_id"]
        if not isinstance(shot_id, str) or not _SAFE.fullmatch(shot_id) or shot_id in seen:
            raise Feature4MotionHandoffError("Duplicate or invalid F2 shot")
        seen.add(shot_id)
        prompt = detail["prompt"]
        if (type(prompt) is not str or not 1 <= len(prompt.strip()) <= 1500 or
                "\x00" in prompt or type(detail["negative_prompt"]) is not str or
                len(detail["negative_prompt"]) > 800):
            raise Feature4MotionHandoffError("Prompt exceeds the current Feature5 adapter; never truncate")
        if detail["duration_seconds"] != 5 or type(detail["duration_seconds"]) is not int:
            raise Feature4MotionHandoffError("Feature5 currently supports only 5-second motion clips")
        aid = _id(detail["source_asset_id"], "source asset")
        media = assets.get(aid)
        if (type(media) is not dict or media.get("shop_id") != snapshot["shop_id"] or
                media.get("approved") is not True or media.get("private") is not True or
                media.get("commercial_rights") is not True or
                media.get("kind") not in ("image", "poster") or
                (media.get("kind") == "poster" and media.get("clean_layers") is not True)):
            raise Feature4MotionHandoffError("Feature3 reference lacks tenant-private commercial grant")
        original, prompt_hash = _safe_copy(detail)
        # Prevent untrusted/ephemeral source URLs and services/command payloads.
        for value in detail.values():
            if isinstance(value, str) and ("http://" in value or "https://" in value or
                                           "file://" in value or "data:" in value):
                raise Feature4MotionHandoffError("Provider prompt must not include source URLs")
        key = hashlib.sha256(json.dumps(
            ["feature4-to-feature5-v1", snapshot["shop_id"], snapshot["campaign_id"],
             snapshot["approval_id"], shot_id, aid, prompt_hash],
            separators=(",", ":")).encode()).hexdigest()
        commands.append({
            "shot_id": shot_id, "shop_id": snapshot["shop_id"],
            "campaign_id": snapshot["campaign_id"],
            "approval_id": snapshot["approval_id"],
            "review_hash": snapshot["review_hash"],
            "source_asset_id": aid, "mode": "poster" if media["kind"] == "poster" else "image",
            "model_id": _SUPPORTED_MODEL, "prompt_version": _RETAIL_VIDEO_PROFILE,
            "resolution": "480p", "duration_seconds": 5,
            "prompt": prompt, "negative_prompt": detail["negative_prompt"],
            "motion_direction_v1": original, "motion_sha256": prompt_hash,
            "idempotency_key": key,
        })
    return tuple(commands)

def dispatch_via_coordinator(commands, transactionally_enqueue_once):
    """One transactionally idempotent handoff; no auto-retries on ambiguity.

    The injected callback MUST be the coordinator's tenant-RLS outbox writer,
    not a direct HTTP provider call or any browser-controlled function.
    """
    if type(commands) is not tuple or not callable(transactionally_enqueue_once):
        raise Feature4MotionHandoffError("Coordinator-controlled outbox callback required")
    if any(type(c) is not dict or not _SHA.fullmatch(c.get("idempotency_key", "")) for c in commands):
        raise Feature4MotionHandoffError("Invalid immutable motion command")
    # One atomic call, no internal retry: existing ledger owns dedup and costs.
    return transactionally_enqueue_once(copy.deepcopy(commands))
