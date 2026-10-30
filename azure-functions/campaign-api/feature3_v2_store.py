"""Feature #3 *source-only* JWT/RLS PostgREST adapter.

Existing v1 poster endpoints, workers and Blob paths are untouched.
The caller verifies the JWT and active shop membership before any method.
This adapter then uses ONLY the user's token; never a service-role key.
The v2 SQL migration must be separately approved/applied before enabling.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from security import AuthenticationError
from tenant_store import StorageUnavailable, canonical_uuid

_SHA256 = re.compile(r"[a-f0-9]{64}")


class Feature3V2Store:
    def __init__(self, origin, publishable_key, transport=None):
        if not isinstance(origin, str) or not origin.startswith("https://") or \
                not isinstance(publishable_key, str) or not publishable_key:
            raise ValueError("RetailGrowthAI Supabase URL and publishable key required")
        self.origin = origin.rstrip("/")
        self.key = publishable_key
        self.transport = transport or urlopen

    def _request(self, token, resource, *, query=None, body=None):
        if resource not in ("feature3_models", "feature3_poster_designs",
                            "rpc/save_feature3_poster_design",
                            "rpc/feature3_review_model", "rpc/feature3_revoke_model",
                            "rpc/feature3_import_pending_model",
                            "rpc/feature3_register_model_original"):
            raise ValueError("unsupported Feature 3 resource")
        if resource.startswith("rpc/") != (body is not None):
            raise ValueError("Feature 3 writes require RPC; direct writes denied")
        url = self.origin + "/rest/v1/" + resource
        if query:
            url += "?" + urlencode(query, safe="(),.*")
        req = Request(url, method="POST" if body is not None else "GET",
                      data=json.dumps(body).encode("utf-8") if body is not None else None,
                      headers={"apikey": self.key, "Authorization": "Bearer " + token,
                               "Accept": "application/json", "Content-Type": "application/json"})
        try:
            with self.transport(req, timeout=8) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise AuthenticationError("RLS credentials denied") from exc
            raise StorageUnavailable("Feature3 database/RPC unavailable") from exc
        except (URLError, OSError, UnicodeError, ValueError) as exc:
            raise StorageUnavailable("Feature3 store unavailable") from exc

    def save_design(self, token, shop_id, campaign_id, day_id, design,
                    *, design_id=None, expected_revision=0, variation_of=None):
        sid, cid, did = map(canonical_uuid, (shop_id, campaign_id, day_id))
        if design_id is not None:
            canonical_uuid(design_id)
        if variation_of is not None:
            canonical_uuid(variation_of)
        if type(expected_revision) is not int or not 0 <= expected_revision <= 1_000_000:
            raise ValueError("invalid expected revision")
        response = self._request(token, "rpc/save_feature3_poster_design", body={
            "p_shop_id": sid, "p_campaign_id": cid, "p_day_id": did,
            "p_design": design, "p_id": design_id,
            "p_expected_revision": expected_revision, "p_variation_of": variation_of,
        })
        if response is None:
            return None
        if not isinstance(response, dict) or set(response) != {
                "design_id", "revision", "server_document_sha256"}:
            raise StorageUnavailable("invalid Feature3 CAS receipt")
        result_id = canonical_uuid(response["design_id"])
        if type(response["revision"]) is not int or \
                response["revision"] != expected_revision + 1 or \
                (design_id is not None and result_id != design_id) or \
                not isinstance(response["server_document_sha256"], str) or \
                len(response["server_document_sha256"]) != 64 or \
                any(ch not in "0123456789abcdef" for ch in response["server_document_sha256"]):
            raise StorageUnavailable("invalid Feature3 revision or digest")
        return response

    def list_day_designs(self, token, shop_id, campaign_id, day_id):
        sid, cid, did = map(canonical_uuid, (shop_id, campaign_id, day_id))
        rows = self._request(token, "feature3_poster_designs", query={
            "select": "id,shop_id,campaign_id,day_id,revision,status,design,server_document_sha256,variation_of",
            "shop_id": "eq." + sid, "campaign_id": "eq." + cid,
            "day_id": "eq." + did, "order": "updated_at.desc", "limit": "51",
        })
        if not isinstance(rows, list) or len(rows) > 50 or any(
            not isinstance(row, dict) or row.get("shop_id") != sid or
            row.get("campaign_id") != cid or row.get("day_id") != did
            for row in rows
        ):
            raise StorageUnavailable("cross-shop poster metadata or excessive history")
        return rows

    def list_models(self, token, shop_id, tenant_store):
        sid = canonical_uuid(shop_id)
        rows = self._request(token, "feature3_models", query={
            "select": "model_id,owner_shop_id,media_asset_id,scope,status,"
                      "source_kind,label,image_sha256,license_id,rights_verified,"
                      "attribution,approved_uses",
            "status": "eq.APPROVED", "rights_verified": "eq.true",
            "order": "updated_at.desc", "limit": "51",
        })
        if not isinstance(rows, list) or len(rows) > 50:
            raise StorageUnavailable("invalid or excessive model catalog")
        checked = []
        for row in rows:
            if not isinstance(row, dict):
                raise StorageUnavailable("malformed model catalog row")
            # Platform metadata alone NEVER confers other tenants' private
            # image bytes; hold those back pending per-shop media delegation.
            if row.get("scope") != "shop" or row.get("owner_shop_id") != sid:
                continue
            if row.get("status") != "APPROVED" or row.get("rights_verified") is not True:
                continue
            if "poster" not in (row.get("approved_uses") or []):
                continue
            try:
                model_id, asset_id = canonical_uuid(row["model_id"]), canonical_uuid(row["media_asset_id"])
            except (ValueError, KeyError):
                raise StorageUnavailable("malformed model identity")
            if not tenant_store.assets(token, sid, [asset_id]):
                continue
            checked.append({
                "schema": "retailgrowth.model-library.v1",
                "model_id": model_id, "owner_shop_id": sid, "scope": "shop",
                "status": "APPROVED", "synthetic_adult": True,
                "image_sha256": row["image_sha256"],
                "media_asset_id": asset_id, "label": row["label"],
                "license_id": row["license_id"], "attribution": row["attribution"],
                "approved_uses": ["poster"],
            })
        return checked

    def _review_receipt(self, payload, *, sid, mid, revision, new_status):
        if payload is None:
            # The DB refuses invalid active membership, a changed SHA,
            # incomplete rights or a stale compare-and-swap without leaking.
            return None
        if not isinstance(payload, dict) or set(payload) != {
                "model_id", "owner_shop_id", "status", "rights_verified",
                "rights_revision", "review_event_id", "audit_persisted"} or (
            payload["model_id"] != mid or payload["owner_shop_id"] != sid or
            payload["status"] != new_status or
            payload["rights_verified"] is not (new_status == "APPROVED") or
            type(payload["rights_revision"]) is not int or
            payload["rights_revision"] != revision + 1 or
            payload["audit_persisted"] is not True
        ):
            raise StorageUnavailable("Model review was not durably confirmed")
        canonical_uuid(payload["review_event_id"])
        return payload

    def _model_review_token(self, token, shop_id, model_id, revision, image_sha256):
        # The server must first verify the caller's JWT and current shop
        # membership; SQL independently derives auth.uid from this SAME token.
        # A service key is never usable as a user principal for review.
        if (not isinstance(token, str) or not token.strip() or
                token.startswith("sb_secret_") or
                token.startswith("sb_publishable_") or
                not isinstance(image_sha256, str) or len(image_sha256) != 64 or
                any(c not in "0123456789abcdef" for c in image_sha256) or
                type(revision) is not int or not 1 <= revision < 2_147_483_647):
            raise ValueError("Current signed user token and model revision required")
        return canonical_uuid(shop_id), canonical_uuid(model_id)

    def review_model(self, token, shop_id, model_id, *, decision,
                     expected_revision, image_sha256, evidence_revision,
                     checks, notes):
        """Transport only; SQL owns human identity, role, review and audit."""
        sid, mid = self._model_review_token(
            token, shop_id, model_id, expected_revision, image_sha256)
        allowed = {"adult_synthetic", "likeness_and_consent", "image_license",
                   "private_media_integrity", "visual_quality", "approved_uses"}
        if (decision not in ("APPROVE", "REJECT") or
                evidence_revision != 1 or type(evidence_revision) is not int or
                not isinstance(checks, dict) or set(checks) != allowed or
                any(type(v) is not bool for v in checks.values()) or
                (decision == "APPROVE" and not all(checks.values())) or
                not isinstance(notes, str) or
                not 12 <= len(notes.strip()) <= 500 or
                any(ord(c) < 32 or ord(c) == 127 for c in notes)):
            raise ValueError("Six independent human review checks required")
        result = self._request(token, "rpc/feature3_review_model", body={
            "p_shop_id": sid, "p_model_id": mid, "p_decision": decision,
            "p_expected_revision": expected_revision,
            "p_expected_image_sha256": image_sha256,
            "p_expected_evidence_revision": evidence_revision,
            "p_checks": checks, "p_notes": notes.strip(),
        })
        return self._review_receipt(
            result, sid=sid, mid=mid, revision=expected_revision,
            new_status="APPROVED" if decision == "APPROVE" else "REJECTED")

    def revoke_model(self, token, shop_id, model_id, *, expected_revision,
                     image_sha256, reason):
        """Emergency signed revocation; never depends on currently valid license."""
        sid, mid = self._model_review_token(
            token, shop_id, model_id, expected_revision, image_sha256)
        if (not isinstance(reason, str) or
                not 12 <= len(reason.strip()) <= 500 or
                any(ord(c) < 32 or ord(c) == 127 for c in reason)):
            raise ValueError("Auditable revocation reason required")
        result = self._request(token, "rpc/feature3_revoke_model", body={
            "p_shop_id": sid, "p_model_id": mid,
            "p_expected_revision": expected_revision,
            "p_expected_image_sha256": image_sha256,
            "p_reason": reason.strip(),
        })
        return self._review_receipt(
            result, sid=sid, mid=mid, revision=expected_revision,
            new_status="REVOKED")

    def import_pending_model(self, token, shop_id, body):
        """Signed user JWT, shop-only PENDING_REVIEW; never verifies image rights.

        The database checks current shop role and exact registered private
        media key. Public request cannot directly insert models or approve.
        """
        sid = canonical_uuid(shop_id)
        if not isinstance(token, str) or not token.strip() or token.startswith(
                ("sb_secret_", "sb_publishable_")):
            raise ValueError("Current signed user JWT required")
        keys = {"model_id", "media_asset_id", "source_kind", "label",
                "image_sha256", "license_id", "license_evidence_sha256",
                "attribution", "approved_uses"}
        if not isinstance(body, dict) or set(body) != keys:
            raise ValueError("Exact pending model registration required")
        mid = canonical_uuid(body["model_id"])
        media_id = canonical_uuid(body["media_asset_id"])
        sha = body["image_sha256"]
        legal_sha = body["license_evidence_sha256"]
        if (not isinstance(sha, str) or len(sha) != 64
             or any(c not in "0123456789abcdef" for c in sha)
             or not isinstance(legal_sha, str) or len(legal_sha) != 64
             or any(c not in "0123456789abcdef" for c in legal_sha)
             or body["source_kind"] not in ("retailer_licensed", "created_ai",
                                            "opensource_render")
             or body["license_id"] not in ("CC0-1.0","CC-BY-4.0","REVIEWED-COMMERCIAL")
             or not isinstance(body["label"], str)
             or not 1 <= len(body["label"].strip()) <= 64
             or not isinstance(body["attribution"], str)
             or len(body["attribution"]) > 200
             or (body["license_id"] == "CC-BY-4.0"
                 and not body["attribution"].strip())
             or not isinstance(body["approved_uses"], list)
             or not 1 <= len(body["approved_uses"]) <= 3
             or any(type(v) is not str for v in body["approved_uses"])
             or set(body["approved_uses"]) - {"poster", "try_on", "video_reference"}
             or len(set(body["approved_uses"])) != len(body["approved_uses"])
             or any(ord(c) < 32 or ord(c) == 127 for c in (
                    body["label"] + body["attribution"]))):
            raise ValueError("Invalid bounded pending model metadata")
        data = self._request(token, "rpc/feature3_import_pending_model", body={
            "p_shop_id": sid, "p_model_id": mid,
            "p_media_asset_id": media_id, "p_source_kind": body["source_kind"],
            "p_label": body["label"].strip(),
            "p_image_sha256": sha, "p_license_id": body["license_id"],
            "p_license_evidence_sha256": legal_sha,
            "p_attribution": body["attribution"],
            "p_approved_uses": body["approved_uses"],
        })
        if data is None:
            return None
        if not isinstance(data, dict) or set(data) != {
                "shop_id", "model_id", "media_asset_id", "status",
                "rights_revision", "rights_verified", "evidence_verified",
                "gpu_authorized", "registered"} or (
              data["shop_id"] != sid or data["model_id"] != mid
              or data["media_asset_id"] != media_id
              or data["status"] != "PENDING_REVIEW"
              or type(data["rights_revision"]) is not int
              or data["rights_revision"] != 1
              or data["rights_verified"] is not False
              or data["evidence_verified"] is not False
              or data["gpu_authorized"] is not False
              or data["registered"] is not True):
            raise StorageUnavailable("Model import not durably confirmed")
        return data

    def register_model_original(self, token, shop_id, body):
        """Signed original model-private PNG row, never license/bytes approval."""
        sid = canonical_uuid(shop_id)
        if not isinstance(token, str) or not token.strip() or token.startswith(
                ("sb_secret_", "sb_publishable_")):
            raise ValueError("Retailer signed JWT required")
        keys = {"model_id", "image_sha256", "license_name",
                "license_url", "attribution"}
        if not isinstance(body, dict) or set(body) != keys:
            raise ValueError("Exact model original metadata required")
        mid = canonical_uuid(body["model_id"])
        digest = body["image_sha256"]
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise ValueError("Canonical private PNG SHA required")
        license_name, license_url, attribution = (
            body["license_name"], body["license_url"], body["attribution"])
        if (license_name not in ("owned","cc0","commercial","royalty_free")
            or not isinstance(attribution, str) or
            not 10 <= len(attribution.strip()) <= 200 or
            any(ord(ch) < 32 or ord(ch) == 127 for ch in attribution)
            or (license_url is not None and (
                not isinstance(license_url, str) or
                len(license_url) > 500 or not license_url.startswith("https://")))
            or (license_name != "owned" and license_url is None)):
            raise ValueError("Unverified source-license declaration invalid")
        result = self._request(token, "rpc/feature3_register_model_original", body={
            "p_shop_id": sid, "p_model_id": mid,
            "p_image_sha256": digest, "p_license_name": license_name,
            "p_license_url": license_url, "p_attribution": attribution.strip(),
        })
        if result is None:
            return None
        if not isinstance(result, dict) or set(result) != {
            "shop_id","model_id","media_asset_id","image_sha256",
            "registered","byte_sha_verified","license_verified",
            "status","gpu_authorized"
        } or (result["shop_id"] != sid or result["model_id"] != mid or
              result["image_sha256"] != digest or
              result["registered"] is not True or
              result["byte_sha_verified"] is not False or
              result["license_verified"] is not False or
              result["gpu_authorized"] is not False or
              result["status"] != "SOURCE_REGISTERED_PENDING_EVIDENCE"):
            raise StorageUnavailable("Unconfirmed original-media registration; do not retry")
        canonical_uuid(result["media_asset_id"])
        return result
