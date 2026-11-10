"""Feature 3: import-first, reusable adult synthetic fashion-model library.

This is a server-side contract, NOT a live HTTP endpoint, remote downloader or
Supabase migration. Source media is supplied as locally staged private bytes.
The server MUST inject its independently verified license/curator and RLS
authorization callbacks. Imported and newly created models share one record
shape; both require a human visual approval before try-on, poster or video use.

No GPU, external API, subscription charge or third-party image download occurs.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import re
from urllib.parse import urlsplit
from uuid import UUID, uuid5

from PIL import Image, UnidentifiedImageError


class ModelLibraryDenied(ValueError):
    pass


# Not every open-source repo permits commercial use or redistributing renders.
# This is a format allowlist, NEVER a substitute for a human license review.
KNOWN_LICENSES = frozenset({"CC0-1.0", "CC-BY-4.0", "REVIEWED-COMMERCIAL"})
SOURCE_KINDS = frozenset({"opensource_render", "created_ai", "retailer_licensed"})
SCOPES = frozenset({"shop", "platform"})
USES = frozenset({"poster", "try_on", "video_reference"})
POSES = frozenset({"front", "three_quarter", "side", "full_body", "portrait"})
SHA256 = re.compile(r"^[a-f0-9]{64}$")
_MODEL_NAMESPACE = UUID("ed15047b-d659-4488-af15-8d22057e7a09")
MAX_BYTES = 25 * 1024 * 1024
MAX_PIXELS = 24_000_000


def _uuid(value):
    try:
        canonical = str(UUID(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ModelLibraryDenied("Canonical shop UUID required") from exc
    if canonical != value:
        raise ModelLibraryDenied("Canonical shop UUID required")
    return canonical


def _source_uri(value):
    if not isinstance(value, str) or not 12 <= len(value) <= 1500:
        raise ModelLibraryDenied("Auditable HTTPS model provenance required")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or
        parsed.username or parsed.password or parsed.fragment or
        parsed.port not in (None, 443)):
        raise ModelLibraryDenied("Only clean HTTPS provenance links are allowed")
    return value


@dataclass(frozen=True)
class ModelCandidate:
    """All metadata is untrusted until reviewed by server-owned callbacks."""
    owner_shop_id: str
    scope: str                  # 'shop' or curator-approved 'platform'
    source_kind: str            # opensource_render / created_ai / retailer_licensed
    source_uri: str             # provenance only; never fetched by importer
    license_id: str             # per-IMAGE licence, not model CODE license
    license_evidence_sha256: str
    synthetic_adult: bool
    third_party_assets_cleared: bool
    label: str
    pose: str = "front"
    attribution: str = ""


def _validate_candidate(candidate):
    if not isinstance(candidate, ModelCandidate):
        raise ModelLibraryDenied("Structured model provenance required")
    _uuid(candidate.owner_shop_id)
    _source_uri(candidate.source_uri)
    if candidate.scope not in SCOPES or candidate.source_kind not in SOURCE_KINDS:
        raise ModelLibraryDenied("Unsupported model library scope or origin")
    if (candidate.license_id not in KNOWN_LICENSES or
        not isinstance(candidate.license_evidence_sha256, str) or
        not SHA256.fullmatch(candidate.license_evidence_sha256)):
        raise ModelLibraryDenied("Reviewed asset license evidence is required")
    if (candidate.synthetic_adult is not True or
        candidate.third_party_assets_cleared is not True):
        raise ModelLibraryDenied("Adult synthetic identity and component rights must be verified")
    if (not isinstance(candidate.label, str) or
        not 1 <= len(candidate.label.strip()) <= 64 or
        candidate.pose not in POSES or
        not isinstance(candidate.attribution, str) or
        len(candidate.attribution) > 200):
        raise ModelLibraryDenied("Invalid fashion model description or pose")
    if candidate.license_id == "CC-BY-4.0" and not candidate.attribution.strip():
        raise ModelLibraryDenied("CC-BY attribution must accompany all derivative exports")


def _private_png(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise ModelLibraryDenied("Bounded private image bytes required")
    try:
        with Image.open(BytesIO(raw)) as source:
            if (source.format not in {"PNG", "JPEG", "WEBP"} or
                source.width < 256 or source.height < 256 or
                source.width * source.height > MAX_PIXELS or
                getattr(source, "n_frames", 1) != 1):
                raise ModelLibraryDenied("Unsupported or oversized model portrait")
            # Strip source EXIF/GPS/metadata by rebuilding the pixel buffer.
            mode = "RGBA" if source.mode in ("RGBA", "LA") else "RGB"
            pixels = source.convert(mode)
        output = BytesIO()
        pixels.save(output, "PNG", optimize=True)
        cleaned = output.getvalue()
        if len(cleaned) > MAX_BYTES:
            raise ModelLibraryDenied("Normalized model exceeds storage limit")
        return cleaned
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ModelLibraryDenied("Private model image cannot be decoded") from exc


def import_model_image(*, candidate, image_bytes, authorize_import,
                       verify_image_license, write_private_png, register_model):
    """Import existing or generated local image into one reusable library.

    Callback contracts are provided by already-authenticated server code:
    authorize_import(candidate) -> {shop_id, scope, curator_approved}
    verify_image_license(candidate, image_sha256) -> {approved, license_id,
        evidence_sha256, allow_reuse, uses}
    write_private_png(key, bytes, metadata) -> {key, sha256, private,
        owner_shop_id, media_asset_id (registered in the same tenant)}
    register_model(record) -> {model_id, status, scope, owner_shop_id, media_asset_id}
    All callbacks must reauthorize; browser declarations never confer rights.
    """
    _validate_candidate(candidate)
    callbacks = (authorize_import, verify_image_license,
                 write_private_png, register_model)
    if not all(callable(fn) for fn in callbacks):
        raise ModelLibraryDenied("Authenticated rights/storage/registry callbacks required")
    clean = _private_png(image_bytes)
    digest = sha256(clean).hexdigest()
    grant = authorize_import(candidate)
    if (not isinstance(grant, dict) or
        grant.get("shop_id") != candidate.owner_shop_id or
        grant.get("scope") != candidate.scope or
        grant.get("authorized") is not True or
        (candidate.scope == "platform" and grant.get("curator_approved") is not True)):
        raise ModelLibraryDenied("Shop import permission or platform curator grant denied")
    rights = verify_image_license(candidate, digest)
    if (not isinstance(rights, dict) or rights.get("approved") is not True or
        rights.get("license_id") != candidate.license_id or
        rights.get("evidence_sha256") != candidate.license_evidence_sha256 or
        rights.get("allow_reuse") is not True or
        not isinstance(rights.get("uses"), (list, tuple, set, frozenset)) or
        not USES.issubset(set(rights["uses"]))):
        raise ModelLibraryDenied("Independent reusable-image commercial rights not verified")
    # Hash-pinned lineage allows dedupe/reopening without paying a GPU again.
    source = (candidate.owner_shop_id + "|" + candidate.scope + "|" +
              digest + "|" + candidate.source_uri + "|" +
              candidate.license_evidence_sha256 + "|" + candidate.pose)
    model_id = str(uuid5(_MODEL_NAMESPACE, source))
    # Storage RLS and the existing PrivateMedia adapter require the actual
    # owner tenant UUID as the first object-key component, even for a
    # curator-approved shared model. A platform metadata grant never grants
    # another tenant the original private bytes.
    path = (f"{candidate.owner_shop_id}/model-library/platform/{model_id}/{digest}.png"
            if candidate.scope == "platform" else
            f"{candidate.owner_shop_id}/model-library/{model_id}/{digest}.png")
    record = {
        "schema": "retailgrowth.model-library.v1",
        "model_id": model_id, "owner_shop_id": candidate.owner_shop_id,
        "scope": candidate.scope, "source_kind": candidate.source_kind,
        "source_uri": candidate.source_uri, "license_id": candidate.license_id,
        "license_evidence_sha256": candidate.license_evidence_sha256,
        "image_sha256": digest, "storage_key": path,
        "synthetic_adult": True, "label": candidate.label.strip(),
        "pose": candidate.pose, "attribution": candidate.attribution,
        "approved_uses": sorted(USES),
        "status": "PENDING_REVIEW",
        "review_required": True, "inference_executed_by_import": False,
    }
    receipt = write_private_png(path, clean, record)
    if (not isinstance(receipt, dict) or receipt.get("key") != path or
        receipt.get("sha256") != digest or receipt.get("private") is not True or
        receipt.get("owner_shop_id") != candidate.owner_shop_id):
        raise ModelLibraryDenied("Private storage did not confirm immutable owned media")
    try:
        asset_id = _uuid(receipt["media_asset_id"])
    except (TypeError, ValueError, KeyError) as exc:
        raise ModelLibraryDenied("Registered tenant-owned media asset UUID required") from exc
    record["media_asset_id"] = asset_id
    saved = register_model(record)
    if (not isinstance(saved, dict) or
        any(saved.get(key) != value for key, value in (
            ("model_id", model_id), ("owner_shop_id", candidate.owner_shop_id),
            ("scope", candidate.scope), ("status", "PENDING_REVIEW"),
            ("media_asset_id", asset_id)))):
        raise ModelLibraryDenied("Authenticated library registration mismatch")
    return record


def checked_model_for_use(*, model, requesting_shop_id, usage, authorize_use):
    """Safely prepare a shared/private model reference for poster/try-on/video.

    Final media loading and approval checks remain server-owned. In particular,
    a platform model cannot be exposed by changing 'scope' in browser JSON.
    """
    shop_id = _uuid(requesting_shop_id)
    if (not isinstance(model, dict) or model.get("schema") !=
        "retailgrowth.model-library.v1" or model.get("status") != "APPROVED"
        or usage not in USES or model.get("synthetic_adult") is not True or
        not isinstance(model.get("approved_uses"), (tuple, list, set, frozenset))
        or usage not in model["approved_uses"] or
        model.get("scope") not in SCOPES or
        not isinstance(model.get("image_sha256"), str) or
        not SHA256.fullmatch(model["image_sha256"]) or
        not callable(authorize_use)):
        raise ModelLibraryDenied("Model is unreviewed or not approved for this usage")
    _uuid(model.get("model_id"))
    owner = _uuid(model.get("owner_shop_id"))
    if model["scope"] == "shop" and owner != shop_id:
        raise ModelLibraryDenied("Another shop's private models are not accessible")
    if (model.get("license_id") == "CC-BY-4.0"
        and not model.get("attribution")):
        raise ModelLibraryDenied("Attribution required for derivative use")
    expected_prefix = (f"{owner}/model-library/platform/" if model["scope"] == "platform"
                       else f"{owner}/model-library/")
    key = model.get("storage_key")
    canonical_key = (expected_prefix + model["model_id"] + "/" +
                     model["image_sha256"] + ".png")
    if not isinstance(key, str) or key != canonical_key:
        raise ModelLibraryDenied("Private model storage lineage invalid")
    if authorize_use(shop_id, model["model_id"], usage,
                     model["image_sha256"]) is not True:
        raise ModelLibraryDenied("Current shop rights, model approval or license revoked")
    return {
        "model_id": model["model_id"], "image_sha256": model["image_sha256"],
        "storage_key": key, "attribution": model.get("attribution", ""),
        "requires_private_signed_media": True, "requires_current_rights": True,
    }
