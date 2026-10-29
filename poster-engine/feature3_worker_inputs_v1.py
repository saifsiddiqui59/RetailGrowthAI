"""Feature3-approved PRIVATE image bytes to Feature4/5 workers, not browsers.

Reuses existing tenant/source/garment/model/human-review authorization and
verified PNG/JPEG/WebP readers. No URL, JWT, object path, service key or
provider credentials are serialized. Consumer must inject a real durable
render/paid job lease validator; demo fixtures never authorize production.
"""
from __future__ import annotations

from fashion_reference_v1 import (
    FashionReferenceDenied, prepare_fashion_references,
    resolve_first_frame, _approved_asset
)

READERS = frozenset((
    "read_asset", "authorize_asset", "read_private_bytes",
    "read_garment_metadata", "read_model", "read_review"
))


def _verify_inputs(manifest, readers, verify_job, purpose):
    if (not isinstance(manifest, dict) or manifest.get("schema") !=
        "retailgrowth.fashion-reference-bundle.v1" or
        manifest.get("purpose") != purpose or
        not isinstance(readers, dict) or set(readers) != READERS or
        not all(callable(value) for value in readers.values()) or
        not callable(verify_job)):
        raise FashionReferenceDenied("Authenticated worker references required")
    sources = manifest.get("sources")
    model = manifest.get("model")
    if (not isinstance(sources, dict) or
        set(sources) != {"garment", "model", "first_frame"} or
        not isinstance(model, dict) or
        not isinstance(sources.get("model"), dict) or
        not isinstance(sources.get("garment"), dict) or
        not isinstance(sources.get("first_frame"), dict) or
        manifest.get("output_approved") is not False or
        manifest.get("gpu_authorized") is not False):
        raise FashionReferenceDenied("Unapproved or incomplete fashion input")
    frame = sources["first_frame"]
    garment_id = sources["garment"].get("source_asset_id")
    model_id = sources["model"].get("source_asset_id")
    frame_id = frame.get("source_asset_id")
    try_on = frame_id if manifest.get("try_on_review") is not None else None
    fresh = prepare_fashion_references(
        shop_id=manifest.get("shop_id"), garment_asset_id=garment_id,
        purpose=purpose, model_asset_id=model_id, model_id=model.get("model_id"),
        try_on_asset_id=try_on, **readers
    )
    if fresh != manifest:
        raise FashionReferenceDenied("Tenant model, garment or reviewed frame has changed")
    ids = tuple(sorted({garment_id, model_id, frame_id}))
    if verify_job(fresh["shop_id"],ids,fresh["reference_fingerprint"]) is not True:
        raise FashionReferenceDenied("No current tenant render or motion worker lease")
    return fresh


def materialize_feature4_inputs(*, expected_manifest, current_readers,
                                verify_render_job):
    """Feature4: real private model, garment and reviewed first frame in memory.

    Call from backend after an active render claim; worker must not persist
    copies to public buckets or bypass output moderation/publishing policy.
    """
    fresh = _verify_inputs(expected_manifest,current_readers,
                           verify_render_job,"editing")
    shop=fresh["shop_id"]
    roles={}
    for role in ("garment", "model", "first_frame"):
        expected=fresh["sources"][role]
        source_role = "try_on" if role=="first_frame" and fresh.get("try_on_review") else (
            "model" if role=="model" else "garment"
        )
        # First frame without VTON == the original garment.
        actual, binary = _approved_asset(
            shop,expected["source_asset_id"],source_role,"editing",
            read_asset=current_readers["read_asset"],
            authorize_asset=current_readers["authorize_asset"],
            read_private_bytes=current_readers["read_private_bytes"]
        )
        if actual!=expected or not isinstance(binary,bytes):
            raise FashionReferenceDenied("Source was revoked or altered at delivery")
        roles[role]={
            "asset_id":expected["source_asset_id"],
            "sha256":expected["sha256"],
            "mime_type":expected["mime_type"],
            "image_bytes":binary,
        }
    return {
        "consumer":"feature4", "shop_id":shop,
        "reference_fingerprint":fresh["reference_fingerprint"],
        "garment":fresh["garment"],
        "sources":roles,"requires_output_review":True,
        "output_approved":False, "publish_approved":False,
        "gpu_authorized":False,
    }


def materialize_feature5_input(*, expected_manifest,current_readers,
                               verify_motion_job):
    """Feature5: bytes-only first frame with fresh model/garment verification.

    Resolving the image does not grant provider permission, billable retries,
    customer publication rights or paid reservations.
    """
    _verify_inputs(expected_manifest,current_readers,
                   verify_motion_job,"image_to_video")
    frame=resolve_first_frame(
        expected_manifest=expected_manifest,
        current_readers=current_readers,
        verify_worker_job=verify_motion_job,
    )
    return {
        "consumer":"feature5",
        "shop_id":frame["shop_id"],
        "first_frame_asset_id":frame["source_asset_id"],
        "reference_fingerprint":expected_manifest["reference_fingerprint"],
        "sha256":frame["sha256"], "mime_type":frame["mime_type"],
        "dimensions":frame["dimensions"],
        "image_bytes":frame["image_bytes"],
        "provider_call_permitted":False,
        "gpu_authorized":False,"publish_approved":False,
    }
