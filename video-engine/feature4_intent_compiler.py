"""F4-02: pure, server-side rg_video_v2 -> creative_reel_v1 translator.

Only call AFTER the authenticated RLS store has frozen an immutable approval
snapshot. The shop/media/script in this function are server-provided, not
client-approved flags. NO database writes, AI inference, URL fetching or billing.
The coordinator must transactionally save the returned request and media rows
with the v2 render_job id and existing quota/outbox record.
"""
from __future__ import annotations

import copy
import math

from creative_contract import CreativeContractError, safe_ref, uuid
from feature4_worker_handoff import _bundle, Feature4HandoffError

SCENE_FIELDS = frozenset({
    "start", "duration", "headline", "asset_id", "animation_preset",
    "transition", "poster_overlay_asset_id", "offer", "trim_start",
    "mute_source", "sfx_asset_id",
})
DRAFT_FIELDS = frozenset({
    "version", "shop_id", "mode", "template", "duration_seconds",
    "output", "scenes", "cta", "music_asset_id",
})
OPTIONAL_DRAFT_FIELDS = frozenset({"voiceover_asset_id"})
PRESENTATION_FIELDS = frozenset({"width", "height", "fps"})
SNAPSHOT_FIELDS = frozenset({
    "shop_id", "campaign_id", "video_job_id", "approval_id",
    "script", "brand", "assets", "idempotency_key", "edit_plan", "beat_grid",
})
SERVER_ASSET_FIELDS = frozenset({
    "shop_id", "kind", "source_feature", "approved", "storage_bucket",
    "object_path", "mime_type", "license_name", "rights_evidence", "rights_source",
})
KINDS = {"image", "poster", "video", "audio", "logo"}
SOURCES = {
    "feature3": {"image", "poster"},
    "feature5": {"video"},
    "retailer": {"image", "poster", "video", "audio", "logo"},
    "stock": {"image", "video", "audio"},
}


def _finite(value, label):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise CreativeContractError(label + " must be finite")
    return value


def _source(asset_id, approved):
    safe_ref(asset_id, "asset ID")
    try:
        row = approved[asset_id]
    except (TypeError, KeyError) as exc:
        raise CreativeContractError("Selected asset is not server-approved") from exc
    if type(row) is not dict or set(row) != SERVER_ASSET_FIELDS:
        raise CreativeContractError("Malformed trusted media asset record")
    source, kind = row.get("source_feature"), row.get("kind")
    if source not in SOURCES or kind not in KINDS or kind not in SOURCES[source]:
        raise CreativeContractError("Unrecognized media origin or type")
    return row


def compile_approved_storyboard(draft, snapshot):
    """Return a {request, manifest} pair prepared from a reviewed DB snapshot.

    The coordinator's trusted transaction MUST ensure the snapshot has
    verified rights, membership, an approved immutable script, verified
    actual Feature3/5 media and a once-only billing reservation.
    """
    if type(draft) is not dict or (set(draft) - (DRAFT_FIELDS | OPTIONAL_DRAFT_FIELDS)
                                  or DRAFT_FIELDS - set(draft)):
        raise CreativeContractError("Unexpected or missing browser draft fields")
    if type(snapshot) is not dict or not set(snapshot).issubset(SNAPSHOT_FIELDS) or not {
        "shop_id", "campaign_id", "video_job_id", "approval_id",
        "script", "brand", "assets", "idempotency_key",
    }.issubset(snapshot):
        raise CreativeContractError("Missing trusted approval snapshot")
    # The approved copy must be a structured exact-match list. A bare string
    # would turn Python's "headline in approved_text" into a substring check,
    # allowing unreviewed promotional claims through the trusted compiler.
    script = snapshot["script"]
    if type(script) is not dict:
        raise CreativeContractError("Malformed trusted Feature2 script")
    approved_text = script.get("approved_text")
    if (type(approved_text) is not list or not approved_text or
            any(type(item) is not str or not item for item in approved_text)):
        raise CreativeContractError("Malformed trusted approved text")
    shop_id = uuid(snapshot["shop_id"], "shop ID")
    campaign_id = uuid(snapshot["campaign_id"], "campaign ID")
    job_id = uuid(snapshot["video_job_id"], "render job")
    if draft.get("version") != "rg_video_v2" or draft["shop_id"] != shop_id:
        raise CreativeContractError("Foreign tenant or draft revision")
    if snapshot["approval_id"] != snapshot["script"].get("approval_id"):
        raise CreativeContractError("Unreviewed Feature2 script revision")
    if type(snapshot["script"]) is not dict or snapshot["script"].get("approved") is not True:
        raise CreativeContractError("Feature2 approval is not active")
    if type(snapshot["brand"]) is not dict or type(snapshot["assets"]) is not dict:
        raise CreativeContractError("Trusted brand/media rows required")
    if type(draft["scenes"]) is not list or not 1 <= len(draft["scenes"]) <= 12:
        raise CreativeContractError("Invalid video scene count")
    if draft["mode"] not in ("text", "image", "poster", "media", "music_sync"):
        raise CreativeContractError("Unsupported video mode")
    if draft["template"] not in ("streetwear", "cinematic", "festival"):
        raise CreativeContractError("Unsupported reviewed template")
    duration = draft["duration_seconds"]
    if type(duration) is not int or duration not in (15, 30, 60):
        raise CreativeContractError("Unsupported export duration")
    out = draft["output"]
    if type(out) is not dict or set(out) != PRESENTATION_FIELDS or (
        type(out["width"]), type(out["height"]), type(out["fps"])
    ) != (int, int, int):
        raise CreativeContractError("Unexpected output format")
    if (out["width"], out["height"]) not in ((540, 960), (1080, 1920)) or out["fps"] not in (24, 30):
        raise CreativeContractError("Unsupported export resolution or FPS")
    if draft["cta"] != snapshot["script"].get("cta"):
        raise CreativeContractError("CTA differs from approved Feature2 copy")
    selected_ids = set()
    music_id = draft.get("music_asset_id")
    if music_id is not None:
        soundtrack = _source(music_id, snapshot["assets"])
        if soundtrack["kind"] != "audio":
            raise CreativeContractError("Approved soundtrack must be audio")
        selected_ids.add(music_id)
    voice_id = draft.get("voiceover_asset_id")
    if voice_id is not None:
        voice = _source(voice_id, snapshot["assets"])
        if voice["kind"] != "audio":
            raise CreativeContractError("Approved narration must be audio")
        selected_ids.add(voice_id)
    scenes = []
    t = 0
    for index, raw in enumerate(draft["scenes"]):
        if type(raw) is not dict or set(raw) - SCENE_FIELDS or not {
            "start", "duration", "headline",
        }.issubset(raw):
            raise CreativeContractError("Scene has unknown fields")
        start = _finite(raw["start"], "Scene start")
        length = _finite(raw["duration"], "Scene duration")
        if abs(start - t) > .001 or length < .5 or length > duration:
            raise CreativeContractError("Scenes must be contiguous and bounded")
        if type(raw["headline"]) is not str or raw["headline"] not in snapshot["script"]["approved_text"]:
            raise CreativeContractError("Unreviewed promotional headline")
        scene = {"order": index, "start_time": start, "duration": length,
                 "headline": raw["headline"],
                 "animation_preset": raw.get("animation_preset", "subtle_zoom"),
                 "transition": raw.get("transition", "fade")}
        if raw.get("offer") is not None:
            if type(raw["offer"]) is not str or raw["offer"] not in snapshot["script"]["approved_text"]:
                raise CreativeContractError("Unreviewed promotional offer")
            scene["text_overlay"] = raw["offer"]
        source_id = raw.get("asset_id")
        if source_id is not None:
            row = _source(source_id, snapshot["assets"])
            if row["shop_id"] != shop_id or row["approved"] is not True:
                raise CreativeContractError("Asset is not approved for current shop")
            kind = row["kind"]
            if (draft["mode"] == "text" or
                (draft["mode"] == "image" and kind != "image") or
                (draft["mode"] == "poster" and kind != "poster") or
                (draft["mode"] in ("media", "music_sync") and kind not in ("image", "poster", "video"))):
                raise CreativeContractError("Asset incompatible with selected media mode")
            scene.update(asset_id=source_id, asset_type=kind,
                         source_feature=row["source_feature"])
            if row["source_feature"] == "feature5":
                # Only actual persisted approved video row counts as motion.
                # No browser-side 'motion_status' may promote a still to a human clip.
                scene["motion_status"] = "ready"
            selected_ids.add(source_id)
        elif draft["mode"] != "text":
            raise CreativeContractError("Non-text scene requires reviewed source media")
        poster = raw.get("poster_overlay_asset_id")
        if poster is not None:
            row = _source(poster, snapshot["assets"])
            if row["kind"] != "poster" or row["source_feature"] != "feature3" or poster == source_id:
                raise CreativeContractError("Overlay must be a distinct Feature3 reviewed poster")
            scene["poster_overlay_asset_id"] = poster
            selected_ids.add(poster)
        sfx = raw.get("sfx_asset_id")
        if sfx is not None:
            row = _source(sfx, snapshot["assets"])
            if row["kind"] != "audio":
                raise CreativeContractError("Scene SFX must be reviewed audio")
            scene["sfx_asset_id"] = sfx
            scene["sfx_source"] = row["source_feature"]
            selected_ids.add(sfx)
        for k in ("trim_start", "mute_source"):
            if k in raw:
                if k == "trim_start":
                    if source_id is None or scene.get("asset_type") != "video" or _finite(raw[k], k) < 0:
                        raise CreativeContractError("Trimming requires a valid video source")
                elif type(raw[k]) is not bool:
                    raise CreativeContractError("Mute flag must be boolean")
                scene[k] = raw[k]
        scenes.append(scene)
        t = round(t + length, 6)
    if abs(t-duration) > .001:
        raise CreativeContractError("Storyboard does not fill its approved duration")
    brand = copy.deepcopy(snapshot["brand"])
    if brand.get("logo_asset_id") is not None:
        selected_ids.add(brand["logo_asset_id"])
    authoritative_rows = {
        asset_id: copy.deepcopy(snapshot["assets"][asset_id]) for asset_id in selected_ids
    }
    request = {
        "version": "creative_reel_v1", "shop_id": shop_id,
        "campaign_id": campaign_id, "video_job_id": job_id,
        "idempotency_key": snapshot["idempotency_key"],
        "script": copy.deepcopy(snapshot["script"]), "brand": brand,
        "scenes": scenes, "template": draft["template"],
        "duration_seconds": duration,
        "mode": draft["mode"],
        "output": {"format": "mp4", **out},
    }
    if music_id:
        request["music_asset_id"] = music_id
        request["music_source"] = snapshot["assets"][music_id]["source_feature"]
    if voice_id:
        request["voiceover_asset_id"] = voice_id
        request["voiceover_source"] = snapshot["assets"][voice_id]["source_feature"]
    if draft["mode"] == "music_sync":
        if snapshot.get("beat_grid") is None:
            raise CreativeContractError("Server-derived approved beat grid required")
        request["beat_grid"] = copy.deepcopy(snapshot["beat_grid"])
    if snapshot.get("edit_plan") is not None:
        request["edit_plan"] = copy.deepcopy(snapshot["edit_plan"])
    # Reuse EXACTLY the same tenant-private bundle gate as the Azure worker,
    # rather than inventing a second media rights/path schema. It generates
    # local filenames and preserves the approved DB object keys separately.
    claim = {"id": job_id, "shop_id": shop_id, "campaign_id": campaign_id,
             "idempotency_key": snapshot["idempotency_key"]}
    bundle = {"request": request, "assets": authoritative_rows}
    try:
        _, manifest, _, audit = _bundle(claim, bundle)
    except Feature4HandoffError as exc:
        raise CreativeContractError("Unapproved private-media source: " + str(exc)) from exc
    if set(audit["media_asset_ids"]) != selected_ids:
        raise CreativeContractError("Unreferenced or unapproved media introduced")
    return {"request": request, "manifest": manifest,
            "bundle": bundle, "lineage": audit}
