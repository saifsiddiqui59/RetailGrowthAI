"""Feature3 generated PNG private registration with an atomic CAS boundary.

Trusted private worker only. Does not start GPU, dispatch queue, confer
commercial rights, or provide DB writes. The injected registrar MUST lock
an existing live lease, source rights, subscription, and output hash. Lost
database commit acknowledgements are AMBIGUOUS: reconcile, never retry.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import math
import re
from uuid import UUID
from PIL import Image, UnidentifiedImageError
from ai_providers_v2 import ProviderBlocked

_SHA = re.compile(r"^[0-9a-f]{64}$")
_PROVIDER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{1,79}$")
_MAX_IMAGE_BYTES = 25 * 1024 * 1024
_MAX_PIXELS = 24_000_000
_REQUIRED_METADATA = frozenset({
    "provider", "provider_version", "weights_license", "synthetic",
    "attempt", "claim_token", "source_asset_ids", "image_sha256",
    "quoted_cost_usd", "inference_wall_seconds", "requires_human_review",
    "garment_fidelity_not_guaranteed",
})


def _uuid4(value):
    try:
        parsed = UUID(value)
        if type(value) is str and str(parsed) == value and parsed.version == 4:
            return value
    except (ValueError, TypeError, AttributeError):
        pass
    raise ProviderBlocked("Noncanonical durable GPU output identity")


def _verified_png(raw):
    if type(raw) is not bytes or not 100 <= len(raw) <= _MAX_IMAGE_BYTES:
        raise ProviderBlocked("Private output PNG bytes absent or oversized")
    try:
        with Image.open(BytesIO(raw)) as image:
            if (image.format != "PNG" or getattr(image, "n_frames", 1) != 1 or
                not 256 <= image.width <= 8192 or not 256 <= image.height <= 8192 or
                image.width * image.height > _MAX_PIXELS or
                any(key.lower() in ("exif", "xmp", "xml:com.adobe.xmp") for key in image.info)):
                raise ProviderBlocked("Invalid private output PNG")
            image.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError, ValueError) as exc:
        raise ProviderBlocked("Unsafe generated PNG output") from exc
    return sha256(raw).hexdigest()


def _metadata(metadata, image_sha):
    if not isinstance(metadata, dict) or set(metadata) != _REQUIRED_METADATA:
        raise ProviderBlocked("Unexpected or missing GPU output metadata")
    for key in ("provider", "provider_version", "weights_license"):
        if not isinstance(metadata[key], str) or not _PROVIDER.fullmatch(metadata[key]):
            raise ProviderBlocked("Untrusted provider metadata")
    if (metadata["synthetic"] is not True or metadata["requires_human_review"] is not True or
        type(metadata["garment_fidelity_not_guaranteed"]) is not bool or
        type(metadata["attempt"]) is not int or metadata["attempt"] != 1 or
        metadata["image_sha256"] != image_sha):
        raise ProviderBlocked("Source or unreviewed output constraints failed")
    token = _uuid4(metadata["claim_token"])
    ids = metadata["source_asset_ids"]
    if (not isinstance(ids, list) or not 1 <= len(ids) <= 12 or
        any(not isinstance(item, str) for item in ids) or len(set(ids)) != len(ids)):
        raise ProviderBlocked("Invalid GPU source identity set")
    for item in ids:
        _uuid4(item)
    for key, minimum, maximum in (("quoted_cost_usd", 0, 2.5), ("inference_wall_seconds", 0, 900)):
        value = metadata[key]
        if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= maximum:
            raise ProviderBlocked("Untrusted GPU price or duration measurement")
    return token, tuple(ids)


class PrivateOutputRegistrar:
    """OptionalGPUProvider.write_private_output signature, service-only callbacks.

    validate_claim(shop, job, attempt, token, source_ids, sha) -> True
    reauthorize(shop, job, token, source_ids) -> True
    stage(shop, key, PNG, token) -> exact SHA/private/byte-count ACK
    commit(shop, job, attempt, token, key, sha, bytes, source_ids)
        -> immutable one-time atomic registered-media receipt
    quarantine(shop, key, token) -> True (only before DB commit attempt)

    Real DB commit must be a single transactional CAS; callbacks injected by
    untrusted clients must never be accepted as authenticated authority.
    """
    def __init__(self, *, validate_claim, reauthorize, stage, commit, quarantine):
        if not all(callable(f) for f in (validate_claim, reauthorize, stage, commit, quarantine)):
            raise ProviderBlocked("Private output requires durable service-only callbacks")
        self._claim = validate_claim
        self._rights = reauthorize
        self._stage = stage
        self._commit = commit
        self._quarantine = quarantine

    def __call__(self, shop_id, job_id, image, metadata):
        shop, job = _uuid4(shop_id), _uuid4(job_id)
        digest = _verified_png(image)
        token, ids = _metadata(metadata, digest)
        if (self._claim(shop, job, 1, token, ids, digest) is not True or
            self._rights(shop, job, token, ids) is not True):
            raise ProviderBlocked("Stale job lease, source rights or subscription")
        key = f"{shop}/feature3/gpu/{job}/{digest}.png"
        ack = self._stage(shop, key, image, token)
        if (not isinstance(ack, dict) or set(ack) != {"object_key", "sha256", "bytes", "private"} or
            ack.get("object_key") != key or ack.get("sha256") != digest or
            type(ack.get("bytes")) is not int or ack.get("bytes") != len(image) or
            ack.get("private") is not True):
            raise ProviderBlocked("Private object stage unconfirmed; reconcile, do not retry")
        if self._rights(shop, job, token, ids) is not True:
            if self._quarantine(shop, key, token) is not True:
                raise ProviderBlocked("Revoked output quarantining not confirmed")
            raise ProviderBlocked("Rights revoked before output registration")
        # SQL must atomically lock lease, source rights, subscription and hash.
        # Once invoked, lost ACK could represent a successful write. Never
        # retry or delete after the DB call without separate reconciliation.
        receipt = self._commit(shop, job, 1, token, key, digest, len(image), ids)
        if (not isinstance(receipt, dict) or set(receipt) != {
            "media_asset_id", "shop_id", "job_id", "claim_token", "attempt",
            "image_sha256", "object_path", "review_status", "source", "private",
        } or receipt.get("shop_id") != shop or receipt.get("job_id") != job or
            receipt.get("claim_token") != token or
            type(receipt.get("attempt")) is not int or receipt["attempt"] != 1 or
            receipt.get("image_sha256") != digest or receipt.get("object_path") != key or
            receipt.get("review_status") != "UNREVIEWED" or
            receipt.get("source") != "GENERATED" or receipt.get("private") is not True):
            raise ProviderBlocked("Media commit unconfirmed; reconcile, do not retry")
        asset_id = _uuid4(receipt["media_asset_id"])
        return {"shop_id": shop, "job_id": job, "attempt": 1, "claim_token": token,
                "media_asset_id": asset_id, "image_sha256": digest,
                "private": True, "review_status": "UNREVIEWED"}
