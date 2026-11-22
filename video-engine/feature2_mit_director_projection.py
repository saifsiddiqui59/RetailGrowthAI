"""Lossless professional MIT Feature2 Director -> F4 *unapproved* CPU proposal.

Unlike the deterministic campaign sidecar, Kuble MIT Director emits a nested
creative_direction_v1 (contract, version=1, scene.shots). This pure source-only
adapter preserves the entire original director bundle and original narration,
camera, motion and offer evidence while projecting bounded shot timing/media
IDs to the existing F4 rg_video_v2 authoring shape.

Never treat the upstream 'server_verified' fixture, proposal, plan hash, or
media aliases as a signed retailer review. The real server MUST check active
JWT/RLS, claims, right-to-use media, approve the EXACT projected revision,
and atomically snapshot it before calling compile_feature2_direction.
GPU and paid model/provider calls are forbidden in this module.
"""
from __future__ import annotations

import copy
import hashlib
import hmac
import json
import math
import re

from creative_contract import CreativeContractError, safe_ref, uuid

_ID = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
_SHA = re.compile(r"^[a-f0-9]{64}$")
_ROLES = frozenset({"hook", "product", "benefit", "offer", "cta", "story"})
_SCENE_LIMIT = 12
_ALLOWED = (15, 30, 60)
_TEXT_UNSAFE = re.compile(r"[<>\x00-\x1f\x7f]")


def _error(message):
    raise CreativeContractError("F2 MIT director projection: " + message)


def _bounded_json(value):
    try:
        serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"),
                                allow_nan=False)
    except (ValueError, TypeError, OverflowError) as exc:
        raise CreativeContractError("Non-finite or non-JSON F2 creative source") from exc
    if len(serialized.encode("utf-8")) > 250_000:
        _error("oversized original creative bundle")
    return serialized


def _ms(value, name):
    if type(value) not in (int, float) or not math.isfinite(value):
        _error(name + " must be a finite millisecond-exact number")
    millisecond = round(value * 1000)
    if abs(millisecond / 1000 - value) > 1e-7:
        _error(name + " not aligned to milliseconds")
    return millisecond


def _headline(value, label):
    if (type(value) is not str or value != value.strip() or
            not 1 <= len(value) <= 110 or _TEXT_UNSAFE.search(value)):
        _error(label + " cannot be shown in F4 without editing approved copy")
    return value


def _current_hash(plan, requests, motion_by_id):
    # Same ordered JSON shape as pinned director.js and offline-acceptance.js;
    # matches approved plan/garment-data lineage, NOT human approval/rights.
    garment_facts = []
    for request in requests:
        ref = request["asset_id"]
        original = next((m for m in motion_by_id.values()
                         if m.get("reference_media_id") == ref), None)
        if original is None:
            _error("missing original garment source")
        garment_facts.append(original["garment_lock"])
    payload = {"creative": plan, "source_media": garment_facts}
    return hashlib.sha256(_bounded_json(payload).encode("utf-8")).hexdigest()


def propose_mit_director_reel(bundle, *, media_aliases):
    """Return a F2-origin proposal requiring fresh HUMAN approval before F4.

    media_aliases maps F2 original-media reference to F4 media ID; it is merely
    a proposed ID mapping. A real authenticated backend must fetch/store actual
    same-shop rights/bytes separately. Never pass user-supplied media as trusted.
    """
    if type(bundle) is not dict or set(bundle) != {
        "creative_direction_v1", "motion_direction_v1", "approval_record"
    } or type(media_aliases) is not dict:
        _error("invalid professional Creative Director bundle")
    _bounded_json(bundle)
    plan, motion, record = (
        bundle["creative_direction_v1"], bundle["motion_direction_v1"],
        bundle["approval_record"])
    if (type(plan) is not dict or type(record) is not dict
            or plan.get("contract") != "creative_direction_v1"
            or type(plan.get("version")) is not int or plan["version"] != 1
            or plan.get("aspect_ratio") != "9:16"
            or type(plan.get("duration_seconds")) is not int
            or plan["duration_seconds"] not in _ALLOWED
            or record.get("review_status") != "DRAFT"
            or record.get("approved") is not False
            or record.get("human_approval_required") is not True
            or record.get("can_publish") is not False
            or record.get("can_run_paid_motion") is not False
            or type(motion) is not list or not 3 <= len(motion) <= _SCENE_LIMIT):
        _error("original director must be a bounded UNAPPROVED portrait draft")
    shop = uuid(plan.get("shop_id"), "F2 shop")
    campaign = uuid(plan.get("campaign_id"), "F2 campaign")
    originals = plan.get("scenes")
    requests = plan.get("reference_media_requests")
    if (type(originals) is not list or not 3 <= len(originals) <= _SCENE_LIMIT
            or type(requests) is not list or not requests):
        _error("missing ordered original scenes/media")
    source_ids = set()
    for ref in requests:
        if (type(ref) is not dict or ref.get("feature") != 3
                or ref.get("same_shop_required") is not True
                or ref.get("rights_review_required") is not True):
            _error("unsupported original source media lineage")
        source_ids.add(safe_ref(ref.get("asset_id"), "source reference"))
    if len(source_ids) != len(requests) or set(media_aliases) != source_ids:
        _error("media alias mapping must cover exactly the original references")
    for asset in media_aliases.values():
        safe_ref(asset, "F4 candidate media ID")
    source_motion = {}
    for item in motion:
        if (type(item) is not dict or item.get("contract") != "motion_direction_v1"
                or item.get("shop_id") != shop or item.get("campaign_id") != campaign
                or type(item.get("shot_id")) is not str
                or not _ID.fullmatch(item["shot_id"])
                or item["shot_id"] in source_motion):
            _error("cross-shop or duplicated original motion details")
        profile = item.get("requested_profile")
        if (type(profile) is not dict or profile.get("inference_approved") is not False
                or profile.get("provider_profile_verified") is not False):
            _error("GPU/model inference is not part of this CPU projection")
        source_motion[item["shot_id"]] = item
    expected = _current_hash(plan, requests, source_motion)
    if (type(record.get("plan_sha256")) is not str
            or not _SHA.fullmatch(record["plan_sha256"])
            or not hmac.compare_digest(record["plan_sha256"], expected)):
        _error("original pinned MIT Director revision hash changed")
    if (type(plan.get("voiceover_script")) is not str
            or not plan["voiceover_script"].strip()
            or type(plan.get("cta")) is not str):
        _error("missing original narration/CTA")
    cta = _headline(plan["cta"], "CTA")
    if (type(plan.get("authorized_offer_ids")) is not list or
            not _SHA.fullmatch(str(plan.get("approved_media_evidence_sha256"))) or
            not _SHA.fullmatch(str(plan.get("approved_offer_evidence_sha256")))):
        _error("missing original claims/media source lineage")
    output, directions, narration = [], [], []
    seen_scenes, seen_shots = set(), set()
    position = 0
    for index, scene in enumerate(originals):
        if (type(scene) is not dict or
                scene.get("role") not in _ROLES or
                type(scene.get("sequence")) is not int or
                scene["sequence"] != index + 1 or
                type(scene.get("id")) is not str or
                not _ID.fullmatch(scene["id"]) or
                scene["id"] in seen_scenes):
            _error("scene order, role or identity changed")
        seen_scenes.add(scene["id"])
        start, duration = _ms(scene.get("start_seconds"), "scene start"), _ms(
            scene.get("duration_seconds"), "scene duration")
        if start != position or duration < 500:
            _error("gapped/overlapping professional storyboard")
        voice, dialogue = scene.get("voiceover"), scene.get("dialogue")
        if type(voice) is not str or type(dialogue) is not str:
            _error("missing authored F2 narration")
        if voice:
            narration.append(voice)
        headline = _headline(voice or dialogue, "scene headline")
        transition = scene.get("transition_out")
        if type(transition) is not str:
            _error("missing editor transition")
        lower = transition.lower()
        if "fade" in lower:
            preset = "fade"
        elif "cut" in lower:
            preset = "cut"
        else:
            _error("unreviewed original transition needs editor mapping")
        shots = scene.get("shots")
        if type(shots) is not list or not 1 <= len(shots) <= 4:
            _error("missing nested professional shot")
        offset = position
        for shot_index, shot in enumerate(shots):
            if type(shot) is not dict:
                _error("malformed original F2 shot")
            key = shot.get("shot_id")
            if type(key) is not str or key not in source_motion or key in seen_shots:
                _error("unmatched or repeated F2 shot")
            seen_shots.add(key)
            seconds = _ms(shot.get("duration_seconds"), "shot duration")
            if (seconds <= 0 or seconds > 5000
                    or _ms(shot.get("start_seconds"), "shot start") != offset):
                _error("shot start or bounded duration changed")
            orig = source_motion[key]
            if (shot.get("motion_direction") != orig
                    or orig.get("shot_start_seconds") != offset / 1000
                    or _ms(orig.get("duration_seconds"), "motion duration") != seconds
                    or orig.get("scene_id") != scene["id"]):
                _error("original scene/motion facts disagree")
            original_id = safe_ref(orig.get("reference_media_id"), "source ID")
            if original_id not in media_aliases:
                _error("unmapped original private media")
            output.append({
                "start": offset / 1000, "duration": seconds / 1000,
                "headline": headline,
                "asset_id": media_aliases[original_id],
                "transition": preset if shot_index == len(shots) - 1 else "cut",
                "animation_preset": "subtle_zoom",
            })
            directions.append({
                "scene_id": scene["id"], "shot_id": key,
                "original_motion_direction": copy.deepcopy(orig),
            })
            offset += seconds
        if offset != position + duration:
            _error("original scene shot lengths disagree")
        position = offset
    if (position != plan["duration_seconds"] * 1000
            or set(source_motion) != seen_shots
            or originals[0].get("role") != "hook"
            or originals[-1].get("role") != "cta"
            or len(output) > _SCENE_LIMIT
            or " ".join(narration) != plan["voiceover_script"]):
        _error("original full narration, storyboard or CTA continuity changed")
    approved_copy = list(dict.fromkeys([shot["headline"] for shot in output] + [cta]))
    # The F4 compiler only learns copy/assets approved later by the independent
    # current-rights human approval transaction. Text-only narration does NOT
    # authorize a recorded voiceover, captions or copyrighted music.
    return {
        "version": "creative_direction_v1", "source_feature": "feature2",
        "approved": False, "shop_id": shop, "campaign_id": campaign,
        "duration_seconds": plan["duration_seconds"],
        "template": "cinematic", "cta": cta, "scenes": output,
        "music_asset_id": None,
        "script": {
            "source_feature": "feature2", "approved": False,
            "approved_text": approved_copy, "cta": cta,
        },
        "voiceover_text": plan["voiceover_script"],
        "scene_directions": directions,
        "source_plan_sha256": record["plan_sha256"],
        "director_source": copy.deepcopy(bundle),
        "source_status": "PENDING_RETAILER_REVIEW",
        "gpu_enabled": False,
    }
