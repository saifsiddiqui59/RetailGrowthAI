"""Feature 3 -> Features 4/5 private model reference contract (source only).

No generated AI content is claimed. Consumers use this as a request to their
authenticated media resolver / paid inference coordinator; do NOT expose the
storage key, source image or callback to browsers. Rights checked on each use.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re

from model_library_v2 import ModelLibraryDenied, checked_model_for_use

_SHA = re.compile(r"^[a-f0-9]{64}$")
_PROFILE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,79}$")
_POSES = frozenset({"front", "three_quarter", "side", "full_body", "portrait"})
_USES = frozenset({"poster", "try_on", "video_reference"})


def prepare_private_model_reference(*, model, requesting_shop_id, usage,
                                    authorize_reference, pose="front",
                                    garment_image_sha256=None,
                                    render_profile="default"):
    """Produce a shop-fenced cache/job reference after current authoritative rights.

    authorize_reference(shop_id, model_id, usage, image_sha256) must return
    {'authorized': True, 'rights_revision': positive_integer} from current
    trusted persisted approvals, tenant membership, licensing and asset state.
    Never accept a browser authorization flag or a client rights revision.
    Versioning must increment on ANY media/source/review/license change.
    """
    if usage not in _USES or not callable(authorize_reference):
        raise ModelLibraryDenied("Server-side usage authorizer required")
    if pose not in _POSES or not isinstance(render_profile, str) or not _PROFILE.fullmatch(render_profile):
        raise ModelLibraryDenied("Invalid requested model pose or rendering profile")
    if garment_image_sha256 is not None and (
        not isinstance(garment_image_sha256, str) or
        not _SHA.fullmatch(garment_image_sha256)
    ):
        raise ModelLibraryDenied("Garment source must be an authorized SHA256")
    if usage == "try_on" and garment_image_sha256 is None:
        raise ModelLibraryDenied("Try-on needs a separately authorized garment")
    if usage != "try_on" and garment_image_sha256 is not None:
        raise ModelLibraryDenied("Only try-on accepts a garment digest")
    grant = {}

    def verify(shop_id, model_id, requested_usage, model_sha):
        value = authorize_reference(shop_id, model_id, requested_usage, model_sha)
        if (not isinstance(value, dict) or value.get("authorized") is not True or
            type(value.get("rights_revision")) is not int or
            not 1 <= value["rights_revision"] <= 2_147_483_647):
            return False
        grant["rights_revision"] = value["rights_revision"]
        return True

    checked = checked_model_for_use(
        model=model, requesting_shop_id=requesting_shop_id, usage=usage,
        authorize_use=verify,
    )
    basis = {
        "schema": "retailgrowth.private-model-reference.v1",
        "requesting_shop_id": requesting_shop_id,
        "model_id": checked["model_id"],
        "image_sha256": checked["image_sha256"],
        "rights_revision": grant["rights_revision"],
        "usage": usage,
        "pose": pose,
        "garment_image_sha256": garment_image_sha256,
        "render_profile": render_profile,
    }
    fingerprint = sha256(json.dumps(
        basis, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")).hexdigest()
    return {
        **basis, "cache_fingerprint": fingerprint,
        "private_storage_key": checked["storage_key"],
        "attribution": checked["attribution"],
        "media_access_requires_current_rights": True,
        "authorized_garment_resolution_required": usage == "try_on",
        "generation_executed": False,
        "gpu_spend_authorized": False,
    }


def reference_can_reuse_cached_result(*, receipt, previous_fingerprint,
                                      media_still_authorized):
    """Only check a cache candidate after a FRESH prepare_private_model_reference.

    False means execute a newly separately approved job, not that a GPU can
    automatically be used. Caller must verify the immutable output's shop
    ownership, source rights and approval via media_still_authorized.
    """
    if not isinstance(receipt, dict) or receipt.get("schema") !=             "retailgrowth.private-model-reference.v1":
        raise ModelLibraryDenied("Fresh server model reference receipt required")
    digest = receipt.get("cache_fingerprint")
    if not isinstance(digest, str) or not _SHA.fullmatch(digest):
        raise ModelLibraryDenied("Invalid immutable reference fingerprint")
    if (not isinstance(previous_fingerprint, str) or
            not _SHA.fullmatch(previous_fingerprint)):
        return False
    if previous_fingerprint != digest:
        return False
    if not callable(media_still_authorized):
        raise ModelLibraryDenied("A server media reauthorization callback is required")
    return media_still_authorized(
        receipt["requesting_shop_id"], digest, receipt["usage"]
    ) is True
