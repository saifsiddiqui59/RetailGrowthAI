"""Feature #2 PostgREST persistence adapters; caller supplies already vetted credentials.

Shared trend data is accessed only with a backend key. Tenant content uses the
verified *user* JWT and database RLS. No browser receives a service-role key.
"""
from __future__ import annotations

from datetime import datetime, timezone

from tenant_store import StorageUnavailable, canonical_uuid


class TrendSnapshotStore:
    def __init__(self, admin, *, clock=None):
        self.admin = admin
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self._claim = None

    def load(self, region: str):
        if region != "IN":
            raise ValueError("unsupported region")
        now = self.clock()
        if now.tzinfo is None:
            raise ValueError("aware clock required")
        result = self.admin.request("trend_snapshots", query={
            "select": "region,snapshot,expires_at",
            "region": "eq.IN", "expires_at": "gt." + now.astimezone(timezone.utc).isoformat(),
            "order": "utc_day.desc", "limit": "1",
        })
        if not isinstance(result, list) or len(result) > 1:
            raise StorageUnavailable("unexpected trend snapshot response")
        if not result:
            return None
        if result[0].get("region") != "IN" or not isinstance(result[0].get("snapshot"), dict):
            raise StorageUnavailable("invalid shared trend snapshot")
        return result[0]["snapshot"]

    def claim_day(self, region: str, day: str) -> bool:
        if region != "IN" or day != self.clock().astimezone(timezone.utc).date().isoformat():
            raise ValueError("invalid collection region or date")
        result = self.admin.request("rpc/feature2_claim_collection", method="POST",
                                    data={"p_region": region, "p_day": day})
        self._claim = (day, canonical_uuid(result)) if result else None
        return self._claim is not None

    def save(self, region: str, snapshot: dict):
        if region != "IN" or not isinstance(snapshot, dict):
            raise ValueError("invalid snapshot")
        if not self._claim:
            raise StorageUnavailable("trend claim missing")
        day, token = self._claim
        self._claim = None
        ok = self.admin.request("rpc/feature2_finish_collection", method="POST", data={
            "p_region": "IN", "p_day": day, "p_token": token, "p_snapshot": snapshot,
        })
        if ok is not True:
            raise StorageUnavailable("trend collection lease expired or lost")


def authorized_profile_reader(tenant_store):
    def read(token, user_id, shop_id):
        sid = canonical_uuid(shop_id)
        rows = tenant_store._request("business_profiles", token, query={
            "select": "shop_id,business_name,category,brand_voice,city,description",
            "shop_id": "eq." + sid, "limit": "1",
        })
        if not isinstance(rows, list) or len(rows) != 1 or rows[0].get("shop_id") != sid:
            return None
        row = rows[0]
        original_category = (row.get("category") or "").lower().strip()
        categories = {
            "clothing": ("fashion", "apparel", "boutique", "garment", "clothes", "clothing", "saree", "kurti"),
            "restaurant": ("restaurant", "cafe", "food", "hotel", "bakery", "dining"),
            "technology": ("technology", "software", "computer", "electronics", "it services"),
        }
        category = next((key for key, terms in categories.items()
                         if any(term in original_category for term in terms)), "general")
        # Product claims are NEVER inferred from free-form business description.
        # The currently versioned v1 onboarding schema has no product catalog.
        return {
            "shop_id": sid, "name": row.get("business_name", ""),
            "category": category, "city": row.get("city", ""),
            "brand_voice": row.get("brand_voice") or "helpful",
            "language": "en-IN", "products": [],
            "audience": "local customers", "objective": "awareness",
            "platforms": ["instagram", "linkedin"], "cta": "Contact the store",
        }
    return read


class TenantDraftStore:
    def __init__(self, tenant_store):
        self.tenant_store = tenant_store

    def save_draft(self, token, user_id, shop_id, draft: dict):
        sid, uid = canonical_uuid(shop_id), canonical_uuid(user_id)
        content_days = draft.get("content_days") or []
        if not content_days or not content_days[0].get("trend_id"):
            raise ValueError("a selected verified trend is required")
        if draft["campaign"].get("shop_id") != sid:
            raise PermissionError("cross-tenant draft denied")
        result = self.tenant_store._request("shop_content_drafts", token, method="POST", data={
            "shop_id": sid, "created_by": uid,
            "trend_id": content_days[0]["trend_id"],
            "content": draft,
        })
        if (not isinstance(result, list) or len(result) != 1 or
                result[0].get("shop_id") != sid or
                result[0].get("created_by") != uid):
            raise StorageUnavailable("draft insert acknowledgement invalid")
        return canonical_uuid(result[0]["id"])
