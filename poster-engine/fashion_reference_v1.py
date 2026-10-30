"""Feature3 -> Feature2/4/5: approved, tenant-owned fashion reference handoff.

Pure server-side application boundary. The caller MUST inject current
authenticated DB/RLS + human rights decisions and private Storage reads.
No browser payload, signed URL, provider key, storage path or paid request
is accepted as an authorization grant. Nothing here runs VTON or a GPU.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
import re
from uuid import UUID

from PIL import Image, UnidentifiedImageError

from garment_review_v2 import FEATURES, validate_review

_SCHEMA = "retailgrowth.fashion-reference-bundle.v1"
_SHA = re.compile(r"^[0-9a-f]{64}$")
_HEX = re.compile(r"^#[A-Fa-f0-9]{6}$")
_SAFE = re.compile(r"^[A-Za-z0-9 _.,&()+/-]{1,90}$")
_PURPOSES = frozenset(("creative_direction", "editing", "image_to_video"))
_EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
_MAX_BYTES = 25 * 1024 * 1024
_MAX_PIXELS = 24_000_000
_GARMENT_FIELDS = (
    "sku", "garment_type", "shape", "base_color", "pattern",
    "neckline", "sleeves", "length", "embroidery",
)


class FashionReferenceDenied(ValueError):
    """Fail closed; do not leak whether foreign media exists."""


def _id(value, *, require_random=True):
    try:
        uid = UUID(value)
        if str(uid) == value and (not require_random or uid.version == 4):
            return value
    except (TypeError, ValueError, AttributeError):
        pass
    raise FashionReferenceDenied("Canonical tenant, media or model UUID required")


def _human_garment(value):
    if not isinstance(value, dict) or set(value) != set(_GARMENT_FIELDS):
        raise FashionReferenceDenied("Complete human-reviewed garment identity required")
    for key in _GARMENT_FIELDS:
        entry = value[key]
        if not isinstance(entry, str) or not entry.strip() or (
            not (_HEX if key == "base_color" else _SAFE).fullmatch(entry)
        ):
            raise FashionReferenceDenied("Invalid or missing garment identity metadata")
    if not _HEX.fullmatch(value["base_color"]):
        raise FashionReferenceDenied("Garment reference needs recorded hex colour")
    return {key: value[key] for key in _GARMENT_FIELDS}


def _read_image(raw, mime_type):
    if type(raw) is not bytes or not 100 <= len(raw) <= _MAX_BYTES:
        raise FashionReferenceDenied("Registered private image bytes unavailable")
    try:
        with Image.open(BytesIO(raw)) as im:
            if (im.format != {"image/png": "PNG", "image/jpeg": "JPEG",
                              "image/webp": "WEBP"}[mime_type] or
                getattr(im, "n_frames", 1) != 1 or
                im.width < 256 or im.height < 256 or
                im.width * im.height > _MAX_PIXELS):
                raise FashionReferenceDenied("Unsupported first-frame image dimensions")
            size = [im.width, im.height]
            im.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError,
            KeyError, ValueError) as exc:
        raise FashionReferenceDenied("Private source image could not be verified") from exc
    return size, sha256(raw).hexdigest()


def _approved_asset(shop, asset_id, role, purpose, *, read_asset, authorize_asset,
                    read_private_bytes):
    """Always obtain a FRESH persisted rights grant, registered row and blob."""
    asset_id = _id(asset_id)
    row = read_asset(shop, asset_id)
    grant = authorize_asset(shop, asset_id, purpose)
    if not isinstance(row, dict) or not isinstance(grant, dict):
        raise FashionReferenceDenied("Current private media approval unavailable")
    if (row.get("id") != asset_id or row.get("shop_id") != shop or
        row.get("storage_bucket") != "retailgrowth-media" or
        row.get("mime_type") not in _EXT or
        row.get("license_name") not in ("owned", "cc0", "commercial", "royalty_free") or
        not isinstance(row.get("attribution"), str) or len(row["attribution"].strip()) < 10 or
        (row["license_name"] != "owned" and
         (not isinstance(row.get("license_url"), str) or
          not row["license_url"].startswith("https://"))) or
        grant.get("shop_id") != shop or grant.get("asset_id") != asset_id or
        grant.get("authorized") is not True or
        grant.get("approval_state") != "APPROVED" or
        grant.get("license_verified") is not True or
        grant.get("rights_revoked") is not False or
        type(grant.get("rights_revision")) is not int or
        not 1 <= grant["rights_revision"] <= 2_147_483_647):
        raise FashionReferenceDenied("Source not tenant-owned and approved for this use")
    if (row.get("fixture_only") is True or grant.get("fixture_only") is True or
        row.get("revoked") is True):
        raise FashionReferenceDenied("Synthetic/revoked test media cannot be production inputs")
    path = row.get("object_path")
    if not isinstance(path, str) or len(path) > 260 or "\\" in path or "//" in path:
        raise FashionReferenceDenied("Invalid private media object identity")
    parts = path.split("/")
    if any(segment in ("", ".", "..") for segment in parts) or parts[0] != shop:
        raise FashionReferenceDenied("Private media object outside owning tenant")
    if role == "garment":
        # The existing register_uploaded_image RPC creates media_assets.id
        # independently of the UUID filename placed in private Storage. The
        # row is authoritative for its exact object_path; do not assume the
        # two identifiers are equal or fabricate a Storage object key.
        # The RPC only accepts {shop}/uploads/{storage_uuid}.{png|jpg|webp}.
        if (row.get("source") != "UPLOAD" or len(parts) != 3 or
            parts[1] != "uploads" or
            not path.endswith(_EXT[row["mime_type"]])):
            raise FashionReferenceDenied("Garment must be the registered original upload")
        storage_id = parts[2][:-len(_EXT[row["mime_type"]])]
        _id(storage_id)
    elif role == "model":
        if (row.get("source") not in ("UPLOAD", "GENERATED") or
            len(parts) < 4 or parts[1] != "model-library" or
            row.get("mime_type") != "image/png"):
            raise FashionReferenceDenied("Model portrait must be private registered library media")
    else:
        if (row.get("source") != "GENERATED" or row.get("mime_type") != "image/png" or
            len(parts) != 5 or parts[1:3] != ["feature3", "gpu"] or
            not _SHA.fullmatch(parts[4][:-4]) or not parts[4].endswith(".png")):
            raise FashionReferenceDenied("Try-on needs registered private generated PNG")
    promised_sha = row.get("image_sha256")
    if not isinstance(promised_sha, str) or not _SHA.fullmatch(promised_sha):
        raise FashionReferenceDenied("Storage hash evidence absent from authoritative media reader")
    image = read_private_bytes(shop, asset_id, path)
    dimensions, actual_sha = _read_image(image, row["mime_type"])
    if promised_sha != actual_sha:
        raise FashionReferenceDenied("Private media bytes differ from persisted identity")
    return {
        "source_asset_id": asset_id, "shop_id": shop,
        "mime_type": row["mime_type"], "dimensions": dimensions,
        "sha256": actual_sha, "source": row["source"],
        "license": {"name": row["license_name"], "attribution": row["attribution"].strip()},
        "approval": {"state": "APPROVED", "rights_revision": grant["rights_revision"]},
    }, image


def _model_approval(shop, model_id, image, read_model):
    model = read_model(shop, _id(model_id, require_random=False))
    if (not isinstance(model, dict) or model.get("model_id") != model_id or
        model.get("owner_shop_id") != shop or
        model.get("media_asset_id") != image["source_asset_id"] or
        model.get("status") != "APPROVED" or
        model.get("rights_verified") is not True or
        model.get("synthetic_adult") is not True or
        "video_reference" not in (model.get("approved_uses") or []) or
        model.get("image_sha256") != image["sha256"] or
        type(model.get("rights_revision")) is not int or
        model["rights_revision"] < 1 or
        model.get("pose") not in ("front", "three_quarter", "side", "full_body", "portrait") or
        not isinstance(model.get("label"), str) or
        not 1 <= len(model["label"].strip()) <= 64 or
        model.get("license_id") not in ("CC0-1.0", "CC-BY-4.0", "REVIEWED-COMMERCIAL") or
        not isinstance(model.get("attribution"), str) or
        (model["license_id"] == "CC-BY-4.0" and not model["attribution"].strip())):
        raise FashionReferenceDenied("Model catalog approval or current rights missing")
    return {"model_id": model_id, "source_kind": model.get("source_kind"),
            "label": model["label"].strip(), "pose": model["pose"],
            "license_id": model["license_id"],
            "attribution": model["attribution"],
            "rights_revision": model["rights_revision"], "synthetic_adult": True}


def _reviewed_try_on(shop, garment, model, candidate, read_review):
    if model is None or not callable(read_review):
        raise FashionReferenceDenied("Try-on output needs original model and human review")
    review = read_review(shop, candidate["source_asset_id"])
    if (not isinstance(review, dict) or review.get("inference_verified") is not True or
        review.get("output_sha256") != candidate["sha256"] or
        review.get("model_asset_id") != model["source_asset_id"] or
        type(review.get("review_revision")) is not int or review["review_revision"] < 1):
        raise FashionReferenceDenied("Try-on has no verified immutable human review")
    evaluation = {key: review.get(key) for key in (
        "shop_id", "source_asset_id", "output_asset_id", "checks",
        "reviewer_confirmation", "notes",
    )}
    if (evaluation["shop_id"] != shop or
        evaluation["source_asset_id"] != garment["source_asset_id"] or
        evaluation["output_asset_id"] != candidate["source_asset_id"]):
        raise FashionReferenceDenied("Try-on reviewer checked a different garment/output")
    try:
        result = validate_review(
            review=evaluation, shop_id=shop,
            source_asset_id=garment["source_asset_id"],
            output_asset_id=candidate["source_asset_id"],
        )
    except ValueError as exc:
        raise FashionReferenceDenied("Try-on requires six human fidelity decisions") from exc
    if result["status"] != "HUMAN_REVIEW_PASSED":
        raise FashionReferenceDenied("Try-on altered identity or needs regeneration")
    return {"state": "HUMAN_REVIEW_PASSED", "review_revision": review["review_revision"],
            "checks": list(FEATURES), "publish_approved": False}


def prepare_fashion_references(*, shop_id, garment_asset_id, purpose,
                               read_asset, authorize_asset, read_private_bytes,
                               read_garment_metadata, model_asset_id=None,
                               model_id=None, read_model=None,
                               try_on_asset_id=None, read_review=None):
    """Return metadata-only safe handoff to Feature2, Feature4 and Feature5.

    All callbacks are trusted backend services; apparel specifications are
    supplied by an *independently reviewed* retailer-owned product record.
    The image-conditioned model gets only an in-process worker frame after
    a separate fresh, identical authorization through resolve_first_frame().
    """
    shop = _id(shop_id)
    if purpose not in _PURPOSES or not all(callable(c) for c in
            (read_asset, authorize_asset, read_private_bytes, read_garment_metadata)):
        raise FashionReferenceDenied("Trusted media reader, rights and consumer required")
    garment, _ = _approved_asset(
        shop, garment_asset_id, "garment", purpose,
        read_asset=read_asset, authorize_asset=authorize_asset,
        read_private_bytes=read_private_bytes)
    product = read_garment_metadata(shop, garment_asset_id)
    if (not isinstance(product, dict) or product.get("shop_id") != shop or
        product.get("media_asset_id") != garment_asset_id or
        product.get("status") != "APPROVED" or
        type(product.get("approval_revision")) is not int or
        not 1 <= product["approval_revision"] <= 2_147_483_647):
        raise FashionReferenceDenied("Human-reviewed retailer product identity unavailable")
    garment_info = _human_garment(product.get("garment"))
    model = None
    model_ref = None
    if model_asset_id is not None or model_id is not None:
        if model_asset_id is None or model_id is None or not callable(read_model):
            raise FashionReferenceDenied("Registered model catalog is required")
        model, _ = _approved_asset(
            shop, model_asset_id, "model", purpose,
            read_asset=read_asset, authorize_asset=authorize_asset,
            read_private_bytes=read_private_bytes)
        model_ref = _model_approval(shop, model_id, model, read_model)
    frame = garment
    reviewed = None
    if try_on_asset_id is not None:
        frame, _ = _approved_asset(
            shop, try_on_asset_id, "try_on", purpose,
            read_asset=read_asset, authorize_asset=authorize_asset,
            read_private_bytes=read_private_bytes)
        reviewed = _reviewed_try_on(shop, garment, model, frame, read_review)
    sources = {"garment": garment, "model": model, "first_frame": frame}
    # A human-authored specification is a PRESERVATION constraint, never
    # a hallucinated product claim or proof an AI renderer maintained it.
    restrictions = {
        "keep_exact_source_identity": True, "no_fabric_or_pattern_replacement": True,
        "no_embroidered_motif_redraw": True, "no_sleeve_neckline_length_shape_change": True,
        "no_unreviewed_model_try_on": True,
        "motion_instruction": "Animate camera or background only; keep garment pixels and identity stable.",
        "requires_output_visual_review": True,
    }
    identity = {
        "schema": _SCHEMA, "shop_id": shop, "purpose": purpose,
        "garment": garment_info, "garment_approval_revision": product["approval_revision"],
        "sources": sources, "model": model_ref,
        "try_on_review": reviewed, "preservation": restrictions,
        "output_approved": False, "gpu_authorized": False,
    }
    digest = sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {**identity, "reference_fingerprint": digest}


def resolve_first_frame(*, expected_manifest, current_readers,
                        verify_worker_job):
    """Feature5 private worker ONLY: reverify every source, approval and hash.

    This deliberately does NOT return a URL, token, Storage path, queue job,
    cost permission, or model output. A fingerprint mismatch stops the run.
    """
    if not isinstance(expected_manifest, dict) or (
        expected_manifest.get("schema") != _SCHEMA or
        expected_manifest.get("purpose") != "image_to_video" or
        not isinstance(current_readers, dict) or
        not callable(verify_worker_job)):
        raise FashionReferenceDenied("Fresh, leased private worker first-frame request required")
    fields = ("read_asset", "authorize_asset", "read_private_bytes",
              "read_garment_metadata", "read_model", "read_review")
    if any(k in current_readers and not callable(current_readers[k]) for k in fields):
        raise FashionReferenceDenied("Invalid live server rights reader")
    s = expected_manifest.get("sources")
    if not isinstance(s, dict) or not isinstance(s.get("garment"), dict):
        raise FashionReferenceDenied("Missing original garment lineage")
    model = expected_manifest.get("model")
    if model is not None and not isinstance(model, dict):
        raise FashionReferenceDenied("Invalid model identity")
    inputs = {
        "shop_id": expected_manifest.get("shop_id"),
        "garment_asset_id": s["garment"].get("source_asset_id"),
        "purpose": "image_to_video",
        "model_asset_id": (s["model"].get("source_asset_id") if model and
                           isinstance(s.get("model"), dict) else None),
        "model_id": model.get("model_id") if model else None,
        "try_on_asset_id": (s["first_frame"].get("source_asset_id")
                            if isinstance(s.get("first_frame"), dict) and
                            expected_manifest.get("try_on_review") else None),
        **current_readers,
    }
    fresh = prepare_fashion_references(**inputs)
    if fresh != expected_manifest:
        raise FashionReferenceDenied("Media rights, model or product changed before consumption")
    # This callback is supplied by the authenticated durable-job service,
    # NEVER by a client. It must validate the current worker lease, tenant,
    # source IDs, subscription and independently approved cost cap. It must
    # not grant paid work merely because approved images exist.
    source_ids = tuple(sorted({
        value["source_asset_id"] for value in fresh["sources"].values()
        if isinstance(value, dict)
    }))
    if verify_worker_job(fresh["shop_id"], source_ids, fresh["reference_fingerprint"]) is not True:
        raise FashionReferenceDenied("No current authorized motion worker claim")
    frame = fresh["sources"]["first_frame"]
    # The first pass revalidated all sources, while this final read pins the
    # exact frame bytes immediately before delivery to the private worker.
    row = current_readers["read_asset"](fresh["shop_id"], frame["source_asset_id"])
    if not isinstance(row, dict) or row.get("shop_id") != fresh["shop_id"]:
        raise FashionReferenceDenied("Private first frame no longer exists")
    raw = current_readers["read_private_bytes"](
        fresh["shop_id"], frame["source_asset_id"], row.get("object_path"))
    size, digest = _read_image(raw, frame["mime_type"])
    if digest != frame["sha256"] or size != frame["dimensions"]:
        raise FashionReferenceDenied("First frame changed after authorization")
    return {"shop_id": fresh["shop_id"], "source_asset_id": frame["source_asset_id"],
            "sha256": digest, "mime_type": frame["mime_type"],
            "dimensions": size, "image_bytes": raw,
            "generation_executed": False, "gpu_authorized": False}


def plan_virtual_try_on(*, manifest):
    """Describes a non-billable task; never runs an unlicensed FASHN parser."""
    if not isinstance(manifest, dict) or manifest.get("schema") != _SCHEMA or (
        not isinstance(manifest.get("model"), dict) or
        manifest.get("try_on_review") is not None):
        raise FashionReferenceDenied("Original garment and approved model needed for VTON planning")
    if manifest.get("garment", {}).get("garment_type", "").lower() not in (
        "kurti", "tunic", "dress", "top", "blouse"):
        raise FashionReferenceDenied("Garment not accepted by current tops/one-piece model")
    return {"shop_id": manifest["shop_id"],
            "garment_asset_id": manifest["sources"]["garment"]["source_asset_id"],
            "model_asset_id": manifest["sources"]["model"]["source_asset_id"],
            "category": "tops", "status": "BLOCKED_PROVIDER_APPROVAL",
            "provider_license_review_required": True, "paid_gpu_approved": False,
            "generation_executed": False, "human_fidelity_review_required": list(FEATURES)}
