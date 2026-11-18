"""GPU-off Feature3 fashion reference packets for Features 2, 4, 5 and 7.

Server-only metadata adapter, not a generator, lease or queue implementation.
The supplied readers MUST be authenticated trusted backend/RLS readers; client
manifests, browser licensing flags and URLs cannot authorize media.
"""
from __future__ import annotations

from copy import deepcopy
import re
from uuid import UUID
from fashion_reference_v1 import FashionReferenceDenied, prepare_fashion_references

_PURPOSES = ("creative_direction", "editing", "image_to_video")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_CAMERAS = frozenset(("static", "slow_push_in", "pan_left", "pan_right", "background_orbit"))
_SCHEMA = "retailgrowth.fashion-reference-bundle.v1"
_SHOT_KEYS = frozenset(("start_second", "duration_seconds", "camera", "scene", "overlay", "preserve_garment_identity"))
_BRIEF_KEYS = frozenset(("brief_id", "shop_id", "status", "approval_revision", "reference_fingerprint", "garment_sha256", "duration_seconds", "shots"))
_FOOTAGE_KEYS = frozenset(("asset_id", "shop_id", "source", "mime_type", "image_sha256", "rights_revision", "rights_revoked", "approval_state", "allowed_uses"))


def _denied():
    raise FashionReferenceDenied("Current, tenant-authorized creative handoff unavailable")


def _uuid(value, *, require_random=True):
    try:
        return isinstance(value, str) and str(UUID(value)) == value and (not require_random or UUID(value).version == 4)
    except (ValueError, TypeError, AttributeError):
        return False


def _source_ids(manifest):
    sources = manifest.get("sources")
    if not isinstance(sources, dict) or set(sources) != {"garment", "model", "first_frame"}:
        _denied()
    if not all(isinstance(sources[k], dict) for k in sources):
        _denied()
    return sources


def _refresh(expected, readers, purpose):
    if not isinstance(expected, dict) or expected.get("schema") != _SCHEMA or expected.get("purpose") != purpose:
        _denied()
    s = _source_ids(expected)
    model = expected.get("model")
    if not isinstance(model, dict) or not _uuid(model.get("model_id"), require_random=False):
        _denied()
    shop = expected.get("shop_id")
    garment_id = s["garment"].get("source_asset_id")
    model_asset_id = s["model"].get("source_asset_id")
    first_frame_id = s["first_frame"].get("source_asset_id")
    if not all(_uuid(v) for v in (shop, garment_id, model_asset_id, first_frame_id)):
        _denied()
    try_on_id = first_frame_id if expected.get("try_on_review") is not None else None
    if try_on_id is None and first_frame_id != garment_id:
        _denied()
    if try_on_id is not None and first_frame_id in (model_asset_id, garment_id):
        _denied()
    if not isinstance(readers, dict) or set(readers) != {
        "read_asset", "authorize_asset", "read_private_bytes",
        "read_garment_metadata", "read_model", "read_review"
    } or not all(callable(cb) for cb in readers.values()):
        _denied()
    # Existing authoritative gate re-reads registered private bytes and SHA,
    # current per-purpose rights, model approval and exact garment identity.
    current = prepare_fashion_references(
        shop_id=shop, garment_asset_id=garment_id, purpose=purpose,
        model_asset_id=model_asset_id, model_id=model["model_id"],
        try_on_asset_id=try_on_id, **readers,
    )
    if current != expected or current.get("output_approved") is not False or current.get("gpu_authorized") is not False:
        _denied()
    return current


def _validate_brief(brief, creative):
    if not isinstance(brief, dict) or set(brief) != _BRIEF_KEYS:
        _denied()
    if (not _uuid(brief["brief_id"]) or brief["shop_id"] != creative["shop_id"] or
        brief["status"] != "APPROVED" or type(brief["approval_revision"]) is not int or
        brief["approval_revision"] < 1 or
        brief["reference_fingerprint"] != creative["reference_fingerprint"] or
        brief["garment_sha256"] != creative["sources"]["garment"]["sha256"] or
        type(brief["duration_seconds"]) is not int or
        brief["duration_seconds"] not in (15, 30, 60) or
        not isinstance(brief["shots"], list) or not 1 <= len(brief["shots"]) <= 12):
        _denied()
    pos = 0
    for shot in brief["shots"]:
        if not isinstance(shot, dict) or set(shot) != _SHOT_KEYS:
            _denied()
        if (type(shot["start_second"]) is not int or shot["start_second"] != pos or
            type(shot["duration_seconds"]) is not int or not 1 <= shot["duration_seconds"] <= 15 or
            not isinstance(shot["camera"], str) or shot["camera"] not in _CAMERAS or shot["preserve_garment_identity"] is not True):
            _denied()
        for key in ("scene", "overlay"):
            value = shot[key]
            if not isinstance(value, str) or len(value) > (180 if key == "scene" else 90) or any(ord(c) < 32 for c in value):
                _denied()
        if not shot["scene"].strip():
            _denied()
        pos += shot["duration_seconds"]
    if pos != brief["duration_seconds"]:
        _denied()


def _read_footage(*, shop_id, asset_id, read_footage):
    if not _uuid(asset_id) or not callable(read_footage):
        _denied()
    footage = read_footage(shop_id, asset_id)
    if not isinstance(footage, dict) or set(footage) != _FOOTAGE_KEYS:
        _denied()
    if (footage["asset_id"] != asset_id or footage["shop_id"] != shop_id or
        footage["source"] != "UPLOAD" or footage["mime_type"] != "video/mp4" or
        not isinstance(footage["image_sha256"], str) or not _SHA.fullmatch(footage["image_sha256"]) or
        type(footage["rights_revision"]) is not int or footage["rights_revision"] < 1 or
        footage["rights_revoked"] is not False or footage["approval_state"] != "APPROVED" or
        not isinstance(footage["allowed_uses"], (list, tuple)) or "editing" not in footage["allowed_uses"] or
        len(footage["allowed_uses"]) > 6 or
        any(not isinstance(use, str) for use in footage["allowed_uses"]) or
        len(set(footage["allowed_uses"])) != len(footage["allowed_uses"])):
        _denied()
    return {"asset_id": asset_id, "sha256": footage["image_sha256"],
            "rights_revision": footage["rights_revision"], "mime_type": "video/mp4"}


def assemble_consumer_packets(*, expected_manifests, current_readers,
                              brief_id, read_approved_brief,
                              footage_asset_id=None, read_footage=None):
    """Generate offline metadata handoffs, never executable authorizations.

    A trusted signed server assembles per-purpose manifests from existing
    fashion_reference_v1, then independently refreshes them here. A real
    Feature5 worker must still call resolve_first_frame with its fresh
    tenant-authorized durable claim directly before inference.
    """
    if (not isinstance(expected_manifests, dict) or set(expected_manifests) != set(_PURPOSES)
        or not _uuid(brief_id) or not callable(read_approved_brief)):
        _denied()
    current = {purpose: _refresh(expected_manifests[purpose], current_readers, purpose)
               for purpose in _PURPOSES}
    creative = current["creative_direction"]
    def common(bundle):
        return {k: v for k, v in bundle.items() if k not in ("purpose", "reference_fingerprint")}
    if any(common(bundle) != common(creative) for bundle in current.values()):
        _denied()
    brief = read_approved_brief(creative["shop_id"], brief_id)
    _validate_brief(brief, creative)
    s = creative["sources"]
    source = {
        "shop_id": creative["shop_id"],
        "garment_asset_id": s["garment"]["source_asset_id"],
        "garment_sha256": s["garment"]["sha256"],
        "model_asset_id": s["model"]["source_asset_id"],
        "model_id": creative["model"]["model_id"],
        "model_sha256": s["model"]["sha256"],
        "model_pose": creative["model"]["pose"],
        "first_frame_asset_id": s["first_frame"]["source_asset_id"],
        "first_frame_sha256": s["first_frame"]["sha256"],
        "model_rights_revision": creative["model"]["rights_revision"],
        "garment_rights_revision": s["garment"]["approval"]["rights_revision"],
        "garment_approval_revision": creative["garment_approval_revision"],
        "garment": deepcopy(creative["garment"]),
        "preservation": deepcopy(creative["preservation"]),
    }
    shots = deepcopy(brief["shots"])
    footage = None
    if footage_asset_id is not None:
        footage = _read_footage(shop_id=creative["shop_id"], asset_id=footage_asset_id, read_footage=read_footage)
    return {
        "schema": "retailgrowth.feature3-offline-consumer-packets.v1",
        "shop_id": creative["shop_id"], "brief_id": brief_id,
        "source": source,
        "feature2": {"reference_fingerprint": creative["reference_fingerprint"],
                     "approved_brief_revision": brief["approval_revision"],
                     "shots": shots, "duration_seconds": brief["duration_seconds"]},
        "feature4": {"reference_fingerprint": current["editing"]["reference_fingerprint"],
                     "timeline": [{"start_second": v["start_second"], "duration_seconds": v["duration_seconds"],
                                   "camera": v["camera"], "scene": v["scene"], "overlay": v["overlay"],
                                   "first_frame_asset_id": source["first_frame_asset_id"],
                                   "preserve_garment_identity": True} for v in shots],
                     "output_requires_human_review": True},
        "feature5": {"reference_fingerprint": current["image_to_video"]["reference_fingerprint"],
                     "first_frame_asset_id": source["first_frame_asset_id"],
                     "first_frame_sha256": source["first_frame_sha256"],
                     "lease_claim_required": True, "fresh_rights_check_required": True,
                     "cost_reservation_required": True, "provider_call_permitted": False},
        "feature7": {"optional_approved_upload": footage,
                     "editor_requires_fresh_media_rights": True,
                     "publish_approved": False},
        "mock_orchestration_only": True, "gpu_authorized": False,
        "paid_inference_authorized": False, "publish_approved": False,
    }
