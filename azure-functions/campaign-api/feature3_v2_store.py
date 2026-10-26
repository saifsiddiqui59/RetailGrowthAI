"""Feature #3 *source-only* JWT/RLS PostgREST adapter.

Existing v1 poster endpoints, workers and Blob paths are untouched.
The caller verifies the JWT and active shop membership before any method.
This adapter then uses ONLY the user's token; never a service-role key.
The v2 SQL migration must be separately approved/applied before enabling.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from security import AuthenticationError
from tenant_store import StorageUnavailable, canonical_uuid


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
                            "rpc/save_feature3_poster_design"):
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
