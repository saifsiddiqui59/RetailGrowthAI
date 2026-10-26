"""Opt-in Feature #2 API boundary, NOT registered in the global Functions router.

Coordinator must first approve an RLS-backed profile/snapshot/draft persistence
contract. No routes/timers or paid provider calls are activated by this module.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from ai_agents.content_intelligence import RetailerProfile, create_content_draft
from ai_agents.schemas import CampaignBrief, ContractError
from ai_agents.trend_intelligence import recommendations
from security import AuthenticationError
from tenant_store import StorageUnavailable, canonical_uuid


class TrendFeatureAdapter:
    def __init__(self, verify_token, tenant_store, profile_reader=None,
                 snapshot_store=None, draft_store=None, clock=None):
        self.verify_token = verify_token
        self.tenant_store = tenant_store
        self.profile_reader = profile_reader
        self.snapshot_store = snapshot_store
        self.draft_store = draft_store
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def handle(self, method: str, shop_id: str, authorization: str,
               payload: dict | None = None) -> tuple[int, dict]:
        try:
            sid = canonical_uuid(shop_id)
            if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
                return 401, {"error": "UNAUTHORIZED"}
            token = authorization[7:].strip()
            if not token:
                return 401, {"error": "UNAUTHORIZED"}
            try:
                user_id = canonical_uuid(self.verify_token(token))
            except (AuthenticationError, ValueError, TypeError):
                return 401, {"error": "UNAUTHORIZED"}
            if method not in ("GET", "POST"):
                return 405, {"error": "METHOD_NOT_ALLOWED"}
            if not self.tenant_store.member(token, user_id, sid, write=method == "POST"):
                return 404, {"error": "NOT_FOUND"}
            # All dependencies intentionally fail closed pending coordinator review.
            if not self.profile_reader or not self.snapshot_store:
                return 503, {"error": "TREND_STORAGE_NOT_CONFIGURED"}
            profile_source = self.profile_reader(token, user_id, sid)
            if not isinstance(profile_source, dict) or profile_source.get("shop_id") != sid:
                return 404, {"error": "NOT_FOUND"}
            retailer = RetailerProfile.from_authorized(profile_source)
            snapshot = self.snapshot_store.load("IN")
            if not isinstance(snapshot, dict):
                return 503, {"error": "TREND_SOURCES_UNAVAILABLE"}
            now = self.clock()
            matches = recommendations(snapshot, {
                "category": retailer.category, "city": retailer.city,
                "language": retailer.language, "products": list(retailer.products),
            }, now)
            if method == "GET":
                return 200, {
                    "shop_id": sid, "recommendations": matches,
                    "sources": snapshot.get("sources", []),
                    "complete": snapshot.get("complete", False),
                    "observed_at": snapshot.get("observed_at"),
                }
            if not isinstance(payload, dict) or set(payload) != {"trend_id", "campaign"}:
                return 400, {"error": "INVALID_REQUEST"}
            if not self.draft_store:
                return 503, {"error": "CONTENT_DRAFT_STORE_NOT_CONFIGURED"}
            target = payload["trend_id"]
            chosen = next((t for t in snapshot.get("trends", []) if t.get("trend_id") == target), None)
            if not chosen or not any(t["trend_id"] == target for t in matches):
                return 409, {"error": "TREND_UNAVAILABLE_OR_STALE"}
            brief = CampaignBrief.from_dict(payload["campaign"])
            if brief.shop_id != sid or not self.tenant_store.assets(token, sid, brief.media_asset_ids):
                return 403, {"error": "FORBIDDEN"}
            # Only deterministic approved-budget OFFLINE drafting here. The
            # existing live model and expensive jobs require coordinator gates.
            from uuid import uuid4
            campaign_id = str(uuid4())
            draft = create_content_draft(brief, retailer, campaign_id=campaign_id,
                                         now=now, trend=chosen)
            if not self.tenant_store.member(token, user_id, sid, write=True):
                return 403, {"error": "FORBIDDEN"}
            draft_id = self.draft_store.save_draft(token, user_id, sid, draft)
            return 201, {"draft_id": canonical_uuid(draft_id), "shop_id": sid,
                         "status": "DRAFT", "campaign_id": campaign_id}
        except AuthenticationError:
            return 401, {"error": "UNAUTHORIZED"}
        except (ContractError, ValueError, TypeError, KeyError, AttributeError):
            return 400, {"error": "INVALID_REQUEST"}
        except PermissionError:
            return 403, {"error": "FORBIDDEN"}
