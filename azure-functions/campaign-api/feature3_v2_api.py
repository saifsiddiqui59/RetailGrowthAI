"""Feature #3 v2 signed-in HTTP boundary, disabled until reviewed migration.

No v1 poster behavior changes. Save only a private DRAFT design; no
render, publish, imported source approval, paid GPU or signed media URL.
"""
from __future__ import annotations

from tenant_store import canonical_uuid, StorageUnavailable
from security import AuthenticationError


class Feature3V2API:
    def __init__(self, tenant_store, design_store):
        self.tenant = tenant_store
        self.designs = design_store

    def _campaign_day(self, token, user_id, cid, did, *, write=False):
        campaign = self.tenant.campaign(token, user_id, cid)
        if campaign is None:
            return None
        sid = canonical_uuid(campaign["shop_id"])
        if not self.tenant.member(token, user_id, sid, write=write):
            return None
        if not any(d.get("id") == did and d.get("shop_id") == sid and
                   d.get("campaign_id", cid) == cid and
                   (not write or d.get("review_status") == "DRAFT")
                   for d in campaign.get("days", [])):
            return None
        if write and campaign.get("status") != "DRAFT":
            return None
        return sid

    def models(self, token, user_id, shop_id):
        sid = canonical_uuid(shop_id)
        if not self.tenant.member(token, user_id, sid):
            return 404, {"error": "NOT_FOUND"}
        entries = self.designs.list_models(token, sid, self.tenant)
        return 200, {"shop_id": sid, "models": entries,
                     "private_images_must_be_loaded_separately": True}


    def source_asset(self, token, user_id, shop_id, asset_id):
        """Read only a registered current-tenant private source metadata proof.

        It does NOT assert model/likeness approval, image SHA or that the
        Storage object can be read. A separate signed private binary read is
        required before the output can enter an image-conditioned model.
        """
        sid, aid = canonical_uuid(shop_id), canonical_uuid(asset_id)
        if not self.tenant.member(token, user_id, sid, write=True):
            return 404, {"error": "NOT_FOUND"}
        receipt = self.tenant.feature3_source_asset(token, sid, aid)
        if not isinstance(receipt, dict) or not (
            isinstance(receipt.get("mime_type"), str) and
            receipt.get("mime_type") in ("image/png", "image/jpeg", "image/webp") and
            receipt.get("license_name") in ("owned", "cc0", "commercial", "royalty_free")
        ):
            return 404, {"error": "NOT_FOUND"}
        return 200, {"shop_id": sid, "media_asset_id": aid,
                     "mime_type": receipt["mime_type"],
                     "license_name": receipt["license_name"],
                     "registered": True, "private_bytes_verified": False,
                     "model_reviewed": False, "gpu_eligible": False}

    def day(self, token, user_id, campaign_id, day_id, method, body=None):
        cid, did = canonical_uuid(campaign_id), canonical_uuid(day_id)
        if method not in ("GET", "POST"):
            return 405, {"error": "METHOD_NOT_ALLOWED"}
        sid = self._campaign_day(token, user_id, cid, did, write=method == "POST")
        if sid is None:
            return 404, {"error": "NOT_FOUND"}
        if method == "GET":
            return 200, {"shop_id": sid, "campaign_id": cid, "day_id": did,
                         "designs": self.designs.list_day_designs(token, sid, cid, did)}
        if not isinstance(body, dict) or not {"design", "expected_revision"} <= set(body) or \
                set(body) - {"design", "expected_revision", "design_id", "variation_of"}:
            return 400, {"error": "INVALID_REQUEST"}
        design = body["design"]
        if not isinstance(design, dict) or set(design) != {
                "schema", "shop_id", "format", "template", "background", "layers"
        } or design.get("schema") != "retailgrowth.poster.v2" or design.get("shop_id") != sid:
            return 400, {"error": "INVALID_REQUEST"}
        expected = body["expected_revision"]
        if type(expected) is not int or not 0 <= expected <= 1000000:
            return 400, {"error": "INVALID_REQUEST"}
        draft_id = body.get("design_id")
        variation = body.get("variation_of")
        if draft_id is not None:
            canonical_uuid(draft_id)
        if variation is not None:
            canonical_uuid(variation)
        if (draft_id is not None and expected == 0) or \
                (draft_id is None and expected != 0) or \
                (variation is not None and draft_id is not None):
            return 400, {"error": "INVALID_REQUEST"}
        result = self.designs.save_design(
            token, sid, cid, did, design, design_id=draft_id,
            expected_revision=expected, variation_of=variation,
        )
        if result is None:
            return 409, {"error": "DESIGN_STALE_OR_ACCESS_DENIED"}
        return (201 if draft_id is None else 200), {
            **result, "shop_id": sid, "campaign_id": cid, "day_id": did,
            "status": "DRAFT", "rendered": False,
        }
