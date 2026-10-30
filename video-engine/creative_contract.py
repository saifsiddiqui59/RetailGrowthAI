"""Feature #4 internal final Reel composition boundary for Features 2/3/5/7.

This is deliberately NOT a public API, user-authentication or billing service.
The coordinating backend must fetch all input, approval and media data under
the existing user JWT and RLS, then mint this private plan + media manifest.
Never rely on browser-supplied provenance or an attestation for authorization.
"""
import copy
import re
from dataclasses import dataclass
from uuid import UUID

from feature4_caption_track import checked_caption_cues
from professional import (
    VideoPlanError, compile_composition, validate,
    SUPPORTED_ANIMATIONS, SUPPORTED_TRANSITIONS,
)

CONTRACT_VERSION = "creative_reel_v1"
UUID_PATTERN = re.compile(r"^[0-9a-fA-F-]{36}$")
REF_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
IMAGE_KINDS = {"image", "poster", "logo"}
MEDIA_KINDS = IMAGE_KINDS | {"video", "audio"}
ORIGINS = {"feature3": {"image", "poster"}, "feature5": {"video"},
           "retailer": {"image", "poster", "video", "logo", "audio"},
           "stock": {"image", "video", "audio"}}
PRESETS = {"streetwear", "cinematic", "festival"}
# Reuse the actual trusted HyperFrames compiler allowlists: no UI/backend drift.
ANIMATIONS = SUPPORTED_ANIMATIONS
TRANSITIONS = SUPPORTED_TRANSITIONS


class CreativeContractError(VideoPlanError):
    pass


class PremiumMotionUnavailable(CreativeContractError):
    pass


@dataclass(frozen=True)
class CompiledReel:
    plan: dict
    manifest: dict
    audit: dict


def require_fields(obj, allowed, required, name):
    if type(obj) is not dict or set(obj) - set(allowed) or set(required) - set(obj):
        raise CreativeContractError(name + ": fields missing or forbidden")


def uuid(value, label):
    if type(value) is not str or not UUID_PATTERN.fullmatch(value):
        raise CreativeContractError(label + ": invalid UUID")
    try:
        if UUID(value).version is None:
            raise ValueError("not versioned")
    except (ValueError, TypeError) as exc:
        raise CreativeContractError(label + ": invalid UUID") from exc
    return value


def safe_ref(value, label):
    if type(value) is not str or not REF_PATTERN.fullmatch(value):
        raise CreativeContractError(label + ": invalid identifier")
    return value


def selected_media(asset_id, kind, source, manifest, shop_id, *, optional=False):
    """Source/tenant/approval consistency across all internal feature producers."""
    if asset_id is None and optional:
        return None
    safe_ref(asset_id, "asset_id")
    record = manifest["assets"].get(asset_id)
    if not isinstance(record, dict):
        raise CreativeContractError("Unrecognized tenant-authorized media ID")
    require_fields(record, {"shop_id", "kind", "source_feature", "approved", "path", "rights"},
                   {"shop_id", "kind", "source_feature", "approved", "path", "rights"}, "asset record")
    if (record["shop_id"] != shop_id or record["approved"] is not True or
            record["kind"] != kind or record["source_feature"] != source or
            source not in ORIGINS or kind not in ORIGINS[source]):
        raise CreativeContractError("Media tenant/approval/type/provenance mismatch")
    return record


def render_inputs(request, media_manifest, *, allow_synthetic_test=False):
    """Lower a reviewed cross-feature edit plan to the pinned trusted renderer plan.

    No provider, billing, queue, storage or network writes occur here. The stable
    video_job_id/idempotency_key must be passed to the EXISTING atomic claim-fenced
    job ledger; this module does not decide or charge for retries.
    """
    require_fields(request, {
        "version", "shop_id", "campaign_id", "video_job_id", "idempotency_key",
        "script", "brand", "scenes", "template", "duration_seconds", "output",
        "music_asset_id", "music_source", "voiceover_asset_id", "voiceover_source", "beat_grid", "edit_plan",
        "allow_image_fallback", "mode",
    }, {"version", "shop_id", "campaign_id", "video_job_id", "idempotency_key",
        "script", "brand", "scenes", "template", "duration_seconds", "output"}, "reel request")
    if request["version"] != CONTRACT_VERSION:
        raise CreativeContractError("Unsupported internal cross-feature contract version")
    shop_id = uuid(request["shop_id"], "shop_id")
    uuid(request["campaign_id"], "campaign_id")
    uuid(request["video_job_id"], "video_job_id")
    safe_ref(request["idempotency_key"], "idempotency_key")
    if request["template"] not in PRESETS:
        raise CreativeContractError("Unknown application-owned video style")
    if type(request["allow_image_fallback"] if "allow_image_fallback" in request else False) is not bool:
        raise CreativeContractError("Fallback permission must be explicit")
    if not isinstance(media_manifest, dict) or media_manifest.get("shop_id") != shop_id or not isinstance(media_manifest.get("assets"), dict):
        raise CreativeContractError("Server-supplied manifest tenant mismatch")
    script = request["script"]
    require_fields(script, {"source_feature", "approved", "approval_id", "approved_text", "cta", "transcript"},
                   {"source_feature", "approved", "approval_id", "approved_text", "cta"}, "reviewed script")
    if script["source_feature"] != "feature2" or script["approved"] is not True:
        raise CreativeContractError("Feature #2 approved script is required")
    safe_ref(script["approval_id"], "script approval")
    if (not isinstance(script["approved_text"], list) or not script["approved_text"]
            or len(script["approved_text"]) > 30):
        raise CreativeContractError("Approved script text list is required")
    approved_text = set()
    for line in script["approved_text"]:
        if not isinstance(line, str) or not 1 <= len(line.strip()) <= 110 or line != line.strip():
            raise CreativeContractError("Unreviewed or oversized script copy")
        approved_text.add(line)
    if script["cta"] not in approved_text:
        raise CreativeContractError("Final CTA must be approved by Feature #2")
    captions=None
    if script.get("transcript") is not None:
        if request.get("voiceover_asset_id") is None:
            raise CreativeContractError("Timed subtitles require approved voice recording")
        try:
            captions=checked_caption_cues(script["transcript"],request["duration_seconds"])
        except ValueError as exc:
            raise CreativeContractError("Invalid approved Feature2 subtitle timing: "+str(exc)) from exc
    brand = request["brand"]
    require_fields(brand, {"shop_name", "primary_color", "secondary_color", "logo_asset_id"},
                   {"shop_name", "primary_color", "logo_asset_id"}, "approved brand")
    if not isinstance(brand["shop_name"], str) or not brand["shop_name"].strip() or len(brand["shop_name"]) > 85:
        raise CreativeContractError("Unverified shop name")
    logo_id = brand["logo_asset_id"]
    if logo_id is not None:
        selected_media(logo_id, "logo", "retailer", media_manifest, shop_id)
    sound_id = request.get("music_asset_id")
    if sound_id is not None:
        selected_media(sound_id, "audio", request.get("music_source", "retailer"), media_manifest, shop_id)
    voice_id = request.get("voiceover_asset_id")
    if voice_id is not None:
        selected_media(voice_id, "audio", request.get("voiceover_source", "retailer"), media_manifest, shop_id)
    if "edit_plan" in request:
        edit = request["edit_plan"]
        require_fields(edit, {"source_feature", "approved", "approval_id", "timeline_version"},
                       {"source_feature", "approved", "approval_id", "timeline_version"}, "smart edit")
        if edit["source_feature"] != "feature7" or edit["approved"] is not True or edit["timeline_version"] != CONTRACT_VERSION:
            raise CreativeContractError("Unapproved or incompatible Feature #7 edit plan")
        safe_ref(edit["approval_id"], "smart editor approval")
    if not isinstance(request["scenes"], list) or not 1 <= len(request["scenes"]) <= 12:
        raise CreativeContractError("Expected 1–12 scenes")
    lowered = []
    fallback_events = []
    used_ids = set()
    for index, scene in enumerate(request["scenes"]):
        require_fields(scene, {"order", "start_time", "duration", "asset_id", "asset_type",
                               "source_feature", "headline", "text_overlay", "poster_overlay_asset_id",
                               "animation_preset", "transition", "trim_start", "mute_source",
                               "sfx_asset_id", "sfx_source", "motion_status", "fallback_image_asset_id"},
                       {"order", "start_time", "duration", "headline"}, "scene")
        if type(scene["order"]) is not int or scene["order"] != index:
            raise CreativeContractError("Scene ordering must be continuous and immutable")
        if scene["headline"] not in approved_text:
            raise CreativeContractError("Scene headline not in approved script")
        if scene.get("text_overlay") is not None and scene["text_overlay"] not in approved_text:
            raise CreativeContractError("Promotional overlay not in approved script")
        if scene.get("animation_preset", "subtle_zoom") not in ANIMATIONS or scene.get("transition", "fade") not in TRANSITIONS:
            raise CreativeContractError("Unapproved animation/transition")
        asset_id, kind, origin = scene.get("asset_id"), scene.get("asset_type"), scene.get("source_feature")
        motion_status = scene.get("motion_status")
        if asset_id is None:
            if kind is not None or origin is not None:
                raise CreativeContractError("Missing authorized scene asset")
        elif origin == "feature5" and motion_status == "failed":
            # A failed premium producer has NO valid clip. It must not be
            # fabricated in storage merely to satisfy the normal clip gate.
            safe_ref(asset_id, "failed motion request ID")
            if kind != "video":
                raise CreativeContractError("Failed AI motion request must be typed video")
        else:
            selected_media(asset_id, kind, origin, media_manifest, shop_id)
        if origin == "feature5":
            if motion_status not in ("ready", "failed"):
                raise CreativeContractError("Feature #5 motion status must be explicit")
            if motion_status == "failed":
                if request.get("allow_image_fallback") is not True:
                    raise PremiumMotionUnavailable("Premium motion failed; fallback not approved")
                still = scene.get("fallback_image_asset_id")
                selected_media(still, "image", "feature3", media_manifest, shop_id)
                fallback_events.append({"scene_order": index, "failed_motion_asset_id": asset_id,
                                        "fallback_image_asset_id": still,
                                        "disclosure": "IMAGE_ANIMATION_NOT_AI_HUMAN_MOTION"})
                asset_id, kind, origin = still, "image", "feature3"
        elif motion_status is not None or scene.get("fallback_image_asset_id") is not None:
            raise CreativeContractError("Unexpected premium-motion fallback fields")
        poster_id = scene.get("poster_overlay_asset_id")
        if poster_id:
            selected_media(poster_id, "poster", "feature3", media_manifest, shop_id)
        sfx_id = scene.get("sfx_asset_id")
        if sfx_id:
            selected_media(sfx_id, "audio", scene.get("sfx_source", "retailer"), media_manifest, shop_id)
        base = {"start": scene["start_time"], "duration": scene["duration"],
                "headline": scene["headline"],
                "animation_preset": scene.get("animation_preset", "subtle_zoom"),
                "transition": scene.get("transition", "fade")}
        if asset_id:
            base["asset_id"] = asset_id
            used_ids.add(asset_id)
        if scene.get("text_overlay") is not None:
            base["offer"] = scene["text_overlay"]
        if poster_id:
            base["poster_overlay_asset_id"] = poster_id
            used_ids.add(poster_id)
        if sfx_id:
            base["sfx_asset_id"] = sfx_id
            used_ids.add(sfx_id)
        if scene.get("trim_start") is not None:
            base["trim_start"] = scene["trim_start"]
        if scene.get("mute_source") is not None:
            base["mute_source"] = scene["mute_source"]
        lowered.append(base)
    if logo_id:
        used_ids.add(logo_id)
    if sound_id:
        used_ids.add(sound_id)
    if voice_id:
        used_ids.add(voice_id)
    media = {}
    for asset_id in used_ids:
        entry = media_manifest["assets"][asset_id]
        media[asset_id] = {key: copy.deepcopy(entry[key]) for key in ("kind", "path", "rights")}
    output = request["output"]
    require_fields(output, {"format", "width", "height", "fps"},
                   {"format", "width", "height", "fps"}, "requested export")
    if output["format"] != "mp4":
        raise CreativeContractError("Only H.264/AAC MP4 export is supported")
    mode = request.get("mode", "media")
    if mode not in ("text", "image", "poster", "media", "music_sync"):
        raise CreativeContractError("Unsupported composition mode")
    # Video/clip scenes and interspersed images may all be placed in media mode.
    if any(x.get("asset_id") for x in lowered) and mode == "text":
        mode = "media"
    if any(media[x.get("asset_id")]["kind"] == "video" for x in lowered if x.get("asset_id")):
        mode = "media" if mode != "music_sync" else mode
    composition = {"version": "rg_video_v2", "shop_id": shop_id,
                   "mode": mode, "template": request["template"],
                   "duration_seconds": request["duration_seconds"],
                   "output": {key: output[key] for key in ("width", "height", "fps")},
                   "scenes": lowered, "cta": script["cta"],
                   "brand": {"name": brand["shop_name"],
                             "primary_color": brand["primary_color"],
                             **({"secondary_color": brand["secondary_color"]}
                                if "secondary_color" in brand else {})},
                   "logo_asset_id": logo_id,
                   "music_asset_id": sound_id,
                   "voiceover_asset_id": voice_id}
    if request.get("beat_grid") is not None:
        composition["beats"] = copy.deepcopy(request["beat_grid"])
    if captions is not None:
        composition["caption_cues"] = captions
    selected = {"shop_id": shop_id, "assets": media}
    audit = {"version": CONTRACT_VERSION, "campaign_id": request["campaign_id"],
             "video_job_id": request["video_job_id"], "idempotency_key": request["idempotency_key"],
             "script_approval_id": script["approval_id"],
             "source_edit_approval": request.get("edit_plan", {}).get("approval_id"),
             "fallback_events": fallback_events,
             "media_asset_ids": sorted(used_ids),
             "rendered_as": "IMAGE_ANIMATION_FALLBACK" if fallback_events else "AUTHORIZED_ASSEMBLY"}
    return CompiledReel(composition, selected, audit)


def compile_creative_reel(request, media_manifest, asset_root, output_dir, *, allow_synthetic_test=False):
    """Compile private deterministic HTML media package; does NOT render, bill or upload."""
    inputs = render_inputs(request, media_manifest, allow_synthetic_test=allow_synthetic_test)
    validate(inputs.plan, inputs.manifest, asset_root, allow_synthetic_test)
    package = compile_composition(inputs.plan, inputs.manifest, asset_root, output_dir, allow_synthetic_test)
    (package / "lineage.json").write_text(
        __import__("json").dumps(inputs.audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return package
