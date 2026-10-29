"""Service-only approved-model review authority for Feature3 GPU-OFF source proofs.

This reads only an exact, independently written human review/evidence verdict
from an explicitly approved *proposed* PostgREST RPC. It cannot determine the
licence of an arbitrary product/garment photo; those sources FAIL CLOSED.
The SQL proposal is not deployed. No GPU/queue/financial operation lives here.
"""
from __future__ import annotations

import re
from tenant_store import canonical_uuid

_HASH = re.compile(r"^[a-f0-9]{64}$")
_KEYS = frozenset((
    "shop_id", "asset_id", "image_sha256", "rights_revision",
    "independent_license_verified", "current_customer_approval", "rights_revoked",
))


class Feature3ModelReviewDenied(PermissionError):
    pass


class Feature3ApprovedModelReviewAuthority:
    """Read current approved rights and a separate reviewer/evidence record.

    RPC is service_role-only and returns NULL for missing, foreign, unapproved,
    revoked or non-model media. Never use a browser JWT or trust row license_name.
    """

    def __init__(self, *, admin_store):
        if not callable(getattr(admin_store, "request", None)):
            raise ValueError("Trusted service-only PostgREST store required")
        self.db = admin_store

    def __call__(self, shop_id, asset_id, digest, registered_media):
        try:
            shop = canonical_uuid(shop_id)
            asset = canonical_uuid(asset_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise Feature3ModelReviewDenied("Canonical reviewed source required") from exc
        if (not isinstance(digest, str) or not _HASH.fullmatch(digest) or
                not isinstance(registered_media, dict) or
                registered_media.get("shop_id") != shop or
                registered_media.get("id") != asset or
                registered_media.get("storage_bucket") != "retailgrowth-media" or
                registered_media.get("mime_type") != "image/png"):
            raise Feature3ModelReviewDenied("Private reviewed model identity required")
        # Read-only service RPC. NULL, no row or a transport error is denial;
        # no automatic retry is performed on uncertain network responses.
        result = self.db.request(
            "rpc/feature3_read_current_model_review", method="POST", data={
                "p_shop_id": shop, "p_media_asset_id": asset,
                "p_image_sha256": digest,
            })
        if (not isinstance(result, dict) or set(result) != _KEYS or
                result.get("shop_id") != shop or result.get("asset_id") != asset or
                result.get("image_sha256") != digest or
                type(result.get("rights_revision")) is not int or
                result["rights_revision"] < 2 or
                result.get("independent_license_verified") is not True or
                result.get("current_customer_approval") is not True or
                result.get("rights_revoked") is not False):
            raise Feature3ModelReviewDenied(
                "Current independent model review evidence unavailable")
        return result


def build_approved_model_gpu_off_preflight(*, admin_store, origin,
                                          backend_secret, transport=None):
    """Compose existing real private bytes and current model review.

    This is still only a READ-ONLY readiness checker: never infer that
    approved person/model images also approve garment/product images.
    Only usable AFTER the SQL proposal has been reviewed and installed.
    """
    from feature3_private_source_proof import build_verified_gpu_off_preflight
    reviewer = Feature3ApprovedModelReviewAuthority(admin_store=admin_store)
    return build_verified_gpu_off_preflight(
        admin_store=admin_store, origin=origin, backend_secret=backend_secret,
        review_authority=reviewer, transport=transport)
