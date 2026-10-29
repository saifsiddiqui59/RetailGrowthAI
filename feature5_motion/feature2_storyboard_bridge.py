"""Validate actual Feature2 MIT Director 15/30/60s offline F4/F5 export.

Source contract: ai-agents/creative-director/export-feature4-feature5-fixture.js
(PR #551). This is a NON-BILLABLE editorial preview only; original hashes
prove byte continuity within the exported fixture, not signed tenant grants.
The coordinator must add a separately authenticated adapter for live jobs.
No HTTP, media staging, model inference, credits or Feature4 approval here.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re

from .wan22_motion_adapter import WanCompatibilityError, DIRECTION_KEYS, PROVIDER

_SHA = re.compile(r"^[0-9a-f]{64}$")
_PROFILE = {"model": PROVIDER, "width": 704, "height": 1280, "fps": 24, "frames": 121}


def _deny(message):
    raise WanCompatibilityError("Feature2 offline storyboard denied: " + message)


def _digest(value):
    try:
        return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                 allow_nan=False).encode("utf-8")).hexdigest()
    except (TypeError, ValueError) as exc:
        raise WanCompatibilityError("Non-JSON editorial packet") from exc


def qualify_feature2_offline_storyboard(packet):
    """Check every original five-second instruction and F4 counterpart.

    Treat caller-supplied packets as untrusted. Never return a provider-ready
    WanShotPackage: genuine approval, source bytes and Part3 leases are absent.
    The feature owner may wire the actual Feature2 exporter after PR #551 merge.
    """
    if type(packet) is not dict or packet.get("schema") != "retailgrowth.feature2-f4-f5-offline-fixture.v1":
        _deny("unknown source version")
    duration = packet.get("duration_seconds")
    if type(duration) is not int or duration not in (15, 30, 60):
        _deny("unreviewed story duration")
    if (packet.get("source_engine") != "pinned MIT Kuble-Lab Open Creative Director"
            or packet.get("shop_id") != "SYNTHETIC_NOT_REAL_OWNER"
            or type(packet.get("source_plan_sha256")) is not str
            or not _SHA.fullmatch(packet["source_plan_sha256"])):
        _deny("missing pinned source and synthetic-only identity")
    review = packet.get("review")
    f5, f4 = packet.get("feature5"), packet.get("feature4")
    audio, media = packet.get("audio"), packet.get("source_media")
    if any(type(item) is not dict for item in (review, f5, f4, audio, media)):
        _deny("incomplete review and consumer contracts")
    if (review.get("status") != "SYNTHETIC_DRAFT"
            or any(review.get(flag) is not False for flag in (
                "signed_customer_approval", "licensed_media_approval",
                "approved_product_or_model", "owner_confirmed_offer",
                "can_publish", "hosted_reel_rendered"))
            or type(review.get("paid_calls")) is not int or review["paid_calls"] != 0
            or any(f5.get(flag) is not False for flag in (
                "can_run_paid_motion", "approved_feature3_first_frame_present", "gpu_enabled"))
            or f5.get("native_output_not_full_hd") is not True
            or f4.get("approved_render_request") is not None
            or f4.get("ready_to_render_customer_reel") is not False
            or media.get("approved_feature3_frame_present") is not False
            or audio.get("licensed_music_bytes_present") is not False
            or audio.get("voiceover_audio_bytes_present") is not False):
        _deny("synthetic source was promoted to customer/provider approval")
    target = f4.get("target")
    if type(target) is not dict or target != {
        "width": 1080, "height": 1920, "fps": 24,
        "video_codec": "h264", "audio_codec": "aac"
    }:
        _deny("Feature4 final profile drift")
    candidates = media.get("candidates")
    if type(candidates) is not list or any(
        type(item) is not dict or item.get("sha256") is not None
        or item.get("private_asset_id") is not None
        or item.get("can_claim_retailer_product") is not False
        for item in candidates
    ):
        _deny("external source mistaken for licensed private media")
    shots, timeline, cues = (f5.get("clip_requests"),
                             f4.get("timeline"), audio.get("narration_cues"))
    count = duration // 5
    if any(type(seq) is not list or len(seq) != count for seq in (shots, timeline, cues)):
        _deny("timeline length mismatch")
    facts = packet.get("garment_facts")
    if type(facts) is not dict or not facts or any(
        type(x) is not str or not x.strip() for x in facts.values()
    ):
        _deny("missing retailer garment locks")
    identity = (packet.get("original_fixture_shop_id"),
                packet.get("original_fixture_campaign_id"))
    if any(type(x) is not str or not x for x in identity):
        _deny("original editorial identity missing")
    checked = []
    seen = set()
    for i, (request, item, cue) in enumerate(zip(shots, timeline, cues)):
        if any(type(x) is not dict for x in (request, item, cue)):
            _deny("invalid shot rows")
        direction = request.get("original_direction")
        if (type(direction) is not dict or set(direction) != DIRECTION_KEYS
                or direction.get("contract") != "motion_direction_v1"
                or (direction.get("shop_id"), direction.get("campaign_id")) != identity):
            _deny("lost original Feature2 direction or shop identity")
        shot_id, scene_id = direction.get("shot_id"), direction.get("scene_id")
        if (type(shot_id) is not str or not shot_id
                or type(scene_id) is not str or not scene_id
                or (scene_id, shot_id) in seen):
            _deny("duplicate or invalid scene")
        seen.add((scene_id, shot_id))
        prompt = direction.get("generation_prompt")
        if type(prompt) is not str or len(prompt) < 180 or len(prompt) > 1600:
            _deny("original director prompt missing or rewritten")
        digest = sha256(prompt.encode("utf-8")).hexdigest()
        if (request.get("original_prompt_sha256") != digest
                or item.get("immutable_motion_prompt_sha256") != digest):
            _deny("Feature2/F4/F5 original prompt SHA changed")
        if (any(v.casefold() not in prompt.casefold() for v in facts.values())
                or any(direction.get("garment_lock", {}).get(k) != v
                       for k, v in facts.items())):
            _deny("approved source garment identity drift")
        if (any(type(row.get("start_seconds")) is not int or
                row["start_seconds"] != i * 5 or
                type(row.get("duration_seconds")) is not int or
                row["duration_seconds"] != 5 for row in (request, item, cue))
                or direction.get("shot_start_seconds") != i * 5
                or direction.get("duration_seconds") != 5
                or any(row.get("shot_id") != shot_id for row in (request, item, cue))
                or any(row.get("scene_id") != scene_id for row in (request, item))):
            _deny("five-second scene boundaries drifted")
        if (request.get("native_wan_profile") != _PROFILE
                or any(request.get(field) is not False for field in (
                    "provider_call_permitted", "gpu_enabled", "cost_reserved",
                    "ready_for_feature5_lease"))
                or request.get("first_frame_asset_id") is not None
                or request.get("first_frame_sha256") is not None
                or item.get("asset_id") is not None
                or item.get("ready_to_render") is not False
                or cue.get("real_speech_audio_verified") is not False):
            _deny("untrusted first frame, cost, speech or runtime authorization")
        if (item.get("camera") != direction.get("camera")
                or item.get("lighting") != direction.get("lighting")
                or item.get("garment_lock") != direction.get("garment_lock")):
            _deny("Feature4 timeline diverged from original motion")
        checked.append({
            "scene_id": scene_id, "shot_id": shot_id,
            "start_seconds": i * 5, "duration_seconds": 5,
            "original_prompt_sha256": digest,
            "original_direction_sha256": _digest(direction),
            "provider_call_permitted": False,
        })
    return {
        "schema": "retailgrowth.feature5-f2-offline-qualified.v1",
        "source_schema": packet["schema"],
        "source_plan_sha256": packet["source_plan_sha256"],
        "original_packet_sha256": _digest(packet),
        "duration_seconds": duration,
        "segment_count": count,
        "segments": checked,
        "status": "SOURCE_ONLY_NOT_AUTHORIZED_FOR_INFERENCE",
        "can_submit_provider": False,
        "can_publish": False,
        "approved_for_feature4": False,
    }
