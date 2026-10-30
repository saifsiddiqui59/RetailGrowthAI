"""Feature3 server-only private model evidence writer (GPU remains OFF).

A source-level callback contract, NOT a deployed Storage connection, binary
license verification service or authorized runtime route. The trusted DB
writer must independently recheck the model, source and current rights in an
atomic service-only INSERT before acknowledging persistence.
"""
from __future__ import annotations

from io import BytesIO
from urllib.parse import urlsplit
from uuid import UUID

from PIL import Image, UnidentifiedImageError
from fashion_reference_v1 import _read_image
from model_library_v2 import POSES, SOURCE_KINDS, KNOWN_LICENSES

_MAX_BYTES = 25 * 1024 * 1024


class EvidenceDenied(ValueError):
    """Do not reveal whether a denied model exists in a different shop."""


def _uuid(value):
    try:
        u = UUID(value)
        if str(u) == value:
            return value
    except (ValueError, TypeError, AttributeError):
        pass
    raise EvidenceDenied("Canonical shop/model/user UUID required")


def _sha(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise EvidenceDenied("Registered SHA256 required")
    return value


def _source_uri(value):
    if not isinstance(value, str) or not 12 <= len(value) <= 1500:
        raise EvidenceDenied("Independent HTTPS image provenance missing")
    try:
        parsed = urlsplit(value)
        good = parsed.scheme == "https" and bool(parsed.hostname) and (
            parsed.username is None and parsed.password is None and
            parsed.fragment == "" and parsed.port in (None, 443) and
            not any(c.isspace() for c in value))
    except ValueError as exc:
        raise EvidenceDenied("Malformed image provenance URL") from exc
    if not good:
        raise EvidenceDenied("Untrusted image provenance URL")
    return value


def prepare_verified_model_evidence(*, shop_id, model_id, verifier_id,
                                    read_model, authorize_verifier,
                                    read_media, read_private_bytes,
                                    verify_image_license, write_evidence_once):
    """Build evidence only from a fresh backend model/media/private object.

    Callbacks are injected by a trusted server with current authorization.
    The image-license verifier must independently verify *per-image*
    commercial rights; a source code license or user-declared string is NOT
    evidence. The service-role writer must do an immutable one-time
    transaction with current source/revision CAS, not a blind upsert.
    Failed/ambiguous writes must never be reported as confirmed or retried.
    """
    shop_id, model_id, verifier_id = map(_uuid, (shop_id, model_id, verifier_id))
    if not all(callable(fn) for fn in (read_model, authorize_verifier, read_media,
                                       read_private_bytes, verify_image_license,
                                       write_evidence_once)):
        raise EvidenceDenied("Trusted verifier and private backend callbacks required")

    grant = authorize_verifier(shop_id, verifier_id, model_id)
    if not isinstance(grant, dict) or grant.get("authorized") is not True or \
            grant.get("service_verified") is not True or \
            grant.get("shop_id") != shop_id or grant.get("verifier_id") != verifier_id:
        raise EvidenceDenied("Current independent verifier authorization required")
    model = read_model(shop_id, model_id)
    if not isinstance(model, dict) or model.get("owner_shop_id") != shop_id or \
            model.get("model_id") != model_id or model.get("status") != "PENDING_REVIEW" or \
            model.get("rights_verified") is not False or \
            type(model.get("rights_revision")) is not int or model["rights_revision"] != 1 or \
            model.get("scope") not in ("shop", "platform") or \
            model.get("source_kind") not in SOURCE_KINDS or \
            model.get("license_id") not in KNOWN_LICENSES or \
            model.get("synthetic_adult") is not True:
        raise EvidenceDenied("Pending tenant model registration unavailable")
    media_id = _uuid(model.get("media_asset_id"))
    digest = _sha(model.get("image_sha256"))
    license_sha = _sha(model.get("license_evidence_sha256"))
    if model["license_id"] == "CC-BY-4.0" and not (
            isinstance(model.get("attribution"), str) and model["attribution"].strip()):
        raise EvidenceDenied("Image attribution missing")

    asset = read_media(shop_id, media_id)
    prefix = shop_id + "/model-library/" + ("platform/" if model["scope"] == "platform" else "")
    key = prefix + model_id + "/" + digest + ".png"
    if not isinstance(asset, dict) or asset.get("id") != media_id or \
            asset.get("shop_id") != shop_id or \
            asset.get("storage_bucket") != "retailgrowth-media" or \
            asset.get("object_path") != key or \
            asset.get("mime_type") != "image/png" or \
            asset.get("source") not in ("UPLOAD", "GENERATED"):
        raise EvidenceDenied("Registered original image not private/tenant-owned")

    raw = read_private_bytes("retailgrowth-media", key)
    if type(raw) is not bytes or not 100 <= len(raw) <= _MAX_BYTES:
        raise EvidenceDenied("Private original bytes missing or too large")
    try:
        dims, actual_sha = _read_image(raw, "image/png")
        with Image.open(BytesIO(raw)) as im:
            if any(k in im.info for k in ("exif", "gps", "GPSInfo", "XML:com.adobe.xmp")):
                raise EvidenceDenied("Private original contains unnormalized location/EXIF metadata")
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError, ValueError) as exc:
        raise EvidenceDenied("Invalid registered private PNG bytes") from exc
    if actual_sha != digest:
        raise EvidenceDenied("Original model bytes changed after registration")

    rights = verify_image_license(model, actual_sha)
    if not isinstance(rights, dict) or \
            rights.get("model_id") != model_id or \
            rights.get("image_sha256") != actual_sha or \
            rights.get("license_id") != model["license_id"] or \
            rights.get("license_evidence_sha256") != license_sha or \
            rights.get("pose") not in POSES or \
            rights.get("synthetic_adult_verified") is not True or \
            rights.get("component_rights_cleared") is not True or \
            rights.get("commercial_reuse_approved") is not True:
        raise EvidenceDenied("Independent per-image commercial rights unverified")
    source_uri = _source_uri(rights.get("source_uri"))
    row = {
        "owner_shop_id": shop_id, "model_id": model_id,
        "media_asset_id": media_id, "image_sha256": actual_sha,
        "license_id": model["license_id"],
        "license_evidence_sha256": license_sha,
        "source_kind": model["source_kind"], "source_uri": source_uri,
        "pose": rights["pose"], "synthetic_adult_verified": True,
        "component_rights_cleared": True, "commercial_reuse_approved": True,
        "evidence_revision": 1, "verified_by": verifier_id,
    }
    receipt = write_evidence_once(row)
    if not isinstance(receipt, dict) or \
            receipt.get("owner_shop_id") != shop_id or \
            receipt.get("model_id") != model_id or \
            receipt.get("media_asset_id") != media_id or \
            receipt.get("image_sha256") != digest or \
            receipt.get("license_evidence_sha256") != license_sha or \
            receipt.get("evidence_revision") != 1 or \
            receipt.get("persisted") is not True:
        raise EvidenceDenied("Trusted immutable evidence persistence not confirmed")
    return {
        "owner_shop_id": shop_id, "model_id": model_id,
        "media_asset_id": media_id, "image_sha256": digest,
        "evidence_revision": 1, "pose": rights["pose"],
        "image_dimensions": dims, "evidence_persisted": True,
        "model_approved": False, "gpu_authorized": False,
        "generated_media": False,
    }
