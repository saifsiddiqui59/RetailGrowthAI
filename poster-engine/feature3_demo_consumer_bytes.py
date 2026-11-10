"""Offline-only pinned MIT synthetic media handoff to Features 2/4/5/7.

Never accepts a signed URL, service key, user JWT, arbitrary file path,
model inference receipt, retailer licence grant or paid provider enablement.
Every consumer rechecks original OpenVTO Git blobs at point of use.
Live tenant media must instead use current backend rights + worker leases.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from feature3_demo_inputs import SOURCES, _validate, REPOSITORY, REVISION
from feature3_demo_footage import DemoFootageDenied, _verify_inputs

_SCHEMA = "retailgrowth.feature3-demo-consumer-bytes.v1"
# Explicit roles keep model, garment and first-frame distinct. They never
# claim that a source avatar already wears the separately pictured garment.
_ROLES = {
    "F2": {"product_still": "synthetic_garment_front.jpg",
           "fictional_avatar_reference": "synthetic_avatar.png",
           "pose_reference": "synthetic_model_pose.jpg"},
    "F4": {"garment_product_still": "synthetic_garment_front.jpg",
           "timeline_first_frame": "synthetic_avatar.png",
           "model_pose_reference": "synthetic_model_pose.jpg"},
    "F5": {"image_to_video_first_frame": "synthetic_avatar.png",
           "garment_reference": "synthetic_garment_front.jpg",
           "model_pose_reference": "synthetic_model_pose.jpg"},
    "F7": {"editor_product_still": "synthetic_garment_front.jpg",
           "editor_first_frame": "synthetic_avatar.png",
           "model_pose_reference": "synthetic_model_pose.jpg"},
}


def load_demo_consumer_bytes(directory, feature):
    """Return verified original bytes and rights-denial flags, never a URL.

    No keys/permission decisions may be inferred from this offline packet.
    The same three originals are independently Git-blob-checked by the
    existing footage verifier AND decoded/hashed again after consumer read.
    """
    if not isinstance(feature, str) or feature not in _ROLES:
        raise DemoFootageDenied("Unknown feature consumer; no privileged demo fallback")
    root = _verify_inputs(directory)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("source_repository") != REPOSITORY or
        manifest.get("source_revision") != REVISION or
        manifest.get("customer_approved") is not False or
        manifest.get("gpu_authorized") is not False or
        manifest.get("publish_approved") is not False or
        manifest.get("actual_vton_inference_performed") is not False):
        raise DemoFootageDenied("Demo rights or generation claims cannot be upgraded")
    rows = {row["filename"]: row for row in manifest["assets"]}
    originals = {}
    for name, upstream_path, pinned_blob, size, image_format in SOURCES:
        image_path = root / name
        if image_path.is_symlink() or not image_path.is_file():
            raise DemoFootageDenied("Untrusted consumer source path")
        raw = image_path.read_bytes()
        try:
            checksum = _validate(raw, expected_git_sha=pinned_blob,
                                 expected_size=size, image_format=image_format)
        except (ValueError, OSError) as exc:
            raise DemoFootageDenied("Source changed after initial verification") from exc
        if (rows[name]["sha256"] != checksum or
            rows[name]["source_path"] != upstream_path or
            rows[name]["source_git_blob_sha1"] != pinned_blob or
            sha256(raw).hexdigest() != checksum):
            raise DemoFootageDenied("Consumer source checksum or authority changed")
        originals[name] = {
            "filename": name,
            "source_path": upstream_path,
            "source_git_blob_sha1": pinned_blob,
            "sha256": checksum,
            "mime_type": "image/png" if image_format == "PNG" else "image/jpeg",
            "bytes": len(raw),
            "image_bytes": raw,
        }
    return {
        "schema": _SCHEMA, "feature": feature,
        "source_repository": REPOSITORY, "source_revision": REVISION,
        "assets": {role: dict(originals[name]) for role, name in _ROLES[feature].items()},
        "source_license": "MIT demo only",
        "customer_approved": False,
        "publish_approved": False,
        "provider_call_permitted": False,
        "paid_inference_authorized": False,
        "actual_vton_inference_performed": False,
        "model_wears_product_garment": False,
        "requires_live_tenant_rights_and_worker_lease": True,
    }
