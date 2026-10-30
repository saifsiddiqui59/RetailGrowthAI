"""Feature3 -> Feature4/5 private worker-only media bytes and ephemeral files.

This is NOT an HTTP endpoint, browser download, signed URL, user-driven asset
export, or paid inference runner. Inject *trusted* tenant/RLS readers and a
current durable worker-claim callback; no callback can be supplied by a browser.
All inputs are rechecked against the existing fashion_reference_v1 authority.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile

from fashion_reference_v1 import (
    FashionReferenceDenied, prepare_fashion_references,
    resolve_first_frame, _read_image,
)

_PURPOSES = frozenset(("editing", "image_to_video"))
_FIELDS = frozenset((
    "read_asset", "authorize_asset", "read_private_bytes",
    "read_garment_metadata", "read_model", "read_review",
))
_MIME = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


def _reject():
    raise FashionReferenceDenied("Private Feature3 worker input no longer authorized")


def _ids(bundle):
    return tuple(sorted({
        item["source_asset_id"] for item in bundle["sources"].values()
        if isinstance(item, dict)
    }))


def _fresh(expected_manifest, readers, purpose):
    if (not isinstance(expected_manifest, dict) or
        expected_manifest.get("schema") != "retailgrowth.fashion-reference-bundle.v1" or
        expected_manifest.get("purpose") != purpose or
        not isinstance(readers, dict) or set(readers) != _FIELDS or
        not all(callable(value) for value in readers.values())):
        _reject()
    sources = expected_manifest.get("sources")
    if (not isinstance(sources, dict) or set(sources) !=
        {"garment", "model", "first_frame"} or
        not isinstance(sources.get("garment"), dict)):
        _reject()
    model = expected_manifest.get("model")
    if model is not None and not isinstance(model, dict):
        _reject()
    frame = sources.get("first_frame")
    if not isinstance(frame, dict):
        _reject()
    options = {
        "shop_id": expected_manifest.get("shop_id"),
        "garment_asset_id": sources["garment"].get("source_asset_id"),
        "purpose": purpose,
        "model_asset_id": sources["model"].get("source_asset_id")
            if isinstance(sources.get("model"), dict) else None,
        "model_id": model.get("model_id") if model else None,
        "try_on_asset_id": frame.get("source_asset_id")
            if expected_manifest.get("try_on_review") is not None else None,
        **readers,
    }
    actual = prepare_fashion_references(**options)
    if actual != expected_manifest or actual.get("gpu_authorized") is not False or \
            actual.get("output_approved") is not False:
        _reject()
    return actual, options


def _final_read(fresh, role, readers):
    ref = fresh["sources"][role]
    if ref is None:
        return None
    shop, asset = fresh["shop_id"], ref["source_asset_id"]
    # Explicit fresh grant, including the exact use, immediately before
    # reading bytes; don't rely on the earlier source-packet approval.
    grant = readers["authorize_asset"](shop, asset, fresh["purpose"])
    if (not isinstance(grant, dict) or grant.get("shop_id") != shop or
        grant.get("asset_id") != asset or grant.get("authorized") is not True or
        grant.get("license_verified") is not True or
        grant.get("approval_state") != "APPROVED" or
        grant.get("rights_revoked") is not False or
        grant.get("rights_revision") != ref["approval"]["rights_revision"]):
        _reject()
    row = readers["read_asset"](shop, asset)
    if (not isinstance(row, dict) or row.get("shop_id") != shop or
        row.get("id") != asset or
        row.get("storage_bucket") != "retailgrowth-media" or
        row.get("mime_type") != ref["mime_type"] or
        row.get("image_sha256") != ref["sha256"]):
        _reject()
    raw = readers["read_private_bytes"](shop, asset, row.get("object_path"))
    size, digest = _read_image(raw, ref["mime_type"])
    if size != ref["dimensions"] or digest != ref["sha256"]:
        _reject()
    return {"source_asset_id": asset, "sha256": digest,
            "mime_type": ref["mime_type"], "dimensions": size,
            "image_bytes": raw}


def resolve_private_worker_inputs(*, expected_manifest, current_readers,
                                  verify_worker_job):
    """Return private bytes only in a trusted Feature4/5 worker process.

    A current lease and all source IDs must be authorized. This performs a
    second authoritative source refresh AFTER the worker callback, so a
    rights revocation during a pending job blocks delivery.
    """
    if not callable(verify_worker_job):
        _reject()
    purpose = expected_manifest.get("purpose") if isinstance(expected_manifest, dict) else None
    if purpose not in _PURPOSES:
        _reject()
    fresh, options = _fresh(expected_manifest, current_readers, purpose)
    if verify_worker_job(fresh["shop_id"], _ids(fresh),
                         fresh["reference_fingerprint"]) is not True:
        _reject()
    # Resolve the Feature5 first frame via the preexisting leased worker gate;
    # it independently rechecks rights and actual private PNG/JPG bytes.
    if purpose == "image_to_video":
        first = resolve_first_frame(
            expected_manifest=fresh, current_readers=current_readers,
            verify_worker_job=verify_worker_job)
        # Private read here is in-process only, with identical image identity.
        if first["source_asset_id"] != fresh["sources"]["first_frame"]["source_asset_id"]:
            _reject()
    else:
        first = None
    # Re-read all currently approved sources, never trust the browser manifest.
    refs = {
        "garment": _final_read(fresh, "garment", current_readers),
        "model": _final_read(fresh, "model", current_readers),
        "first_frame": _final_read(fresh, "first_frame", current_readers),
    }
    if first is not None and refs["first_frame"]["image_bytes"] != first["image_bytes"]:
        _reject()
    # A second authoritative identity/rights refresh fences revocation or
    # changed product metadata after any byte stream has been fetched.
    if prepare_fashion_references(**options) != fresh:
        _reject()
    # A claim can expire while private images are read. Recheck the current
    # durable worker lease after the last byte/rights verification, not only
    # before staging; never return bytes for a revoked or replaced worker.
    if verify_worker_job(fresh["shop_id"], _ids(fresh),
                         fresh["reference_fingerprint"]) is not True:
        _reject()
    return {
        "schema": "retailgrowth.feature3-worker-private-inputs.v1",
        "shop_id": fresh["shop_id"], "purpose": purpose,
        "source_fingerprint": fresh["reference_fingerprint"],
        "garment_identity": fresh["garment"],
        "images": refs, "rights_checked": True,
        "recheck_before_next_job": True,
        "output_approved": False, "gpu_authorized": False,
        "provider_call_permitted": False,
    }


@contextmanager
def temporary_private_worker_inputs(*, expected_manifest, current_readers,
                                    verify_worker_job, trusted_temp_root=None):
    """Scoped private FFmpeg image folder. Deleted even if render raises.

    Caller must provide a trusted worker-only directory or leave it None for
    an OS temp directory. Never pass an HTTP-controlled destination or upload.
    """
    payload = resolve_private_worker_inputs(
        expected_manifest=expected_manifest, current_readers=current_readers,
        verify_worker_job=verify_worker_job)
    with tempfile.TemporaryDirectory(prefix="retailgrowth-f3-worker-",
                                     dir=trusted_temp_root) as folder:
        os.chmod(folder, 0o700)
        exported = {}
        for role, image in payload["images"].items():
            if image is None:
                continue
            filename = role + _MIME[image["mime_type"]]
            path = Path(folder) / filename
            path.write_bytes(image["image_bytes"])
            os.chmod(path, 0o600)
            exported[role] = {
                "relative_path": filename,
                "sha256": image["sha256"], "mime_type": image["mime_type"],
                "source_asset_id": image["source_asset_id"],
            }
        metadata = {
            "schema": "retailgrowth.feature3-worker-file-handoff.v1",
            "shop_id": payload["shop_id"],
            "purpose": payload["purpose"],
            "source_fingerprint": payload["source_fingerprint"],
            "images": exported, "rights_checked": True,
            "expires_when_context_closes": True,
            "publish_approved": False, "provider_call_permitted": False,
        }
        path = Path(folder) / "manifest.json"
        path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
        os.chmod(path, 0o600)
        # Writing private files can outlast a lease; check again immediately
        # before exposing the temporary paths to the worker. No retries on
        # uncertain or revoked lease outcomes.
        staged_ids = tuple(sorted({image["source_asset_id"]
                                   for image in payload["images"].values()
                                   if image is not None}))
        if verify_worker_job(payload["shop_id"], staged_ids,
                             payload["source_fingerprint"]) is not True:
            _reject()
        try:
            yield {"temporary_directory": folder, "manifest": metadata}
        finally:
            # TemporaryDirectory cleans up all private bytes and manifest.
            # The caller must not retain paths beyond this context.
            pass
