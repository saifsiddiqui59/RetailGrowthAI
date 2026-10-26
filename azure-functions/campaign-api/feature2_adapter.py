"""Feature #2 JWT/tenant-gated Azure Functions boundary.

Shared trends and protected shop drafts are deployed in RetailGrowthAI DEV.
All writes require server-side shop, media, and source checks and stay DRAFT.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from ai_agents.content_intelligence import RetailerProfile, create_content_draft
from ai_agents.schemas import CampaignBrief, ContractError
from ai_agents.providers import FoundryUnavailable
from ai_agents.trend_intelligence import recommendations
from security import AuthenticationError
from tenant_store import StorageUnavailable, canonical_uuid


class TrendFeatureAdapter:
    def __init__(self, verify_token, tenant_store, profile_reader=None,
                 snapshot_store=None, draft_store=None, clock=None, ai_service=None):
        self.verify_token = verify_token
        self.tenant_store = tenant_store
        self.profile_reader = profile_reader
        self.snapshot_store = snapshot_store
        self.draft_store = draft_store
        self.ai_service = ai_service
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def handle(self, method: str, shop_id: str, authorization: str,
               payload: dict | None = None, *, ai_mode=False) -> tuple[int, dict]:
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
            # A just-created business has city='' until onboarding is completed.
            # Never infer its location from the device, a model, or the national trend feed.
            city = profile_source.get("city")
            if not isinstance(city, str) or not city.strip():
                if method == "GET":
                    return 200, {
                        "shop_id": sid, "profile_required": True,
                        "recommendations": [], "sources": [], "complete": False,
                        "observed_at": None,
                    }
                return 422, {"error": "BUSINESS_PROFILE_INCOMPLETE"}
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
            if (not isinstance(payload, dict) or
                set(payload) not in ({"trend_id", "campaign"},
                                     {"trend_id", "campaign", "submission_id"})):
                return 400, {"error": "INVALID_REQUEST"}
            submission_id = payload.get("submission_id")
            if "submission_id" in payload:
                try:
                    canonical_uuid(submission_id)
                except (ValueError, TypeError):
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
            if ai_mode:
                if self.ai_service is None:
                    return 503, {"error": "AI_NOT_ENABLED_OR_NOT_APPROVED"}
                # Signed shop/actor and server-validated submission ID pin
                # the billable ledger request across a lost HTTP acknowledgement.
                # Replays get RG005 before network egress; never auto-retry.
                ai_kwargs = dict(
                    brief=brief, retailer=retailer, campaign_id=campaign_id,
                    now=now, trend=chosen, shop_id=sid, actor_id=user_id)
                if submission_id is not None:
                    ai_kwargs["request_id"] = submission_id
                draft = self.ai_service.draft(**ai_kwargs)
            else:
                draft = create_content_draft(brief, retailer, campaign_id=campaign_id,
                                             now=now, trend=chosen)
            # Non-sensitive correlation nonce for read-after-uncertain-POST.
            # Not a DB idempotency lock: clients MUST NOT replay a POST just
            # because Azure timed out before returning the insert acknowledgement.
            if submission_id is not None:
                draft["submission_id"] = submission_id
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
        except StorageUnavailable:
            return 503, {"error": "TREND_STORAGE_UNAVAILABLE"}
        except FoundryUnavailable:
            return 503, {"error": "AI_MODEL_UNAVAILABLE"}

    def improve(self, shop_id: str, authorization: str,
                payload: dict | None, *, ai_mode=False) -> tuple[int, dict]:
        """Zero-paid-inference editorial preview. No trends, media or DB writes.

        Only authenticated OWNER/EDITOR, with server-read RLS business context.
        The request cannot supply or override an authorized business profile.
        """
        try:
            sid = canonical_uuid(shop_id)
            if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
                return 401, {"error": "UNAUTHORIZED"}
            token = authorization[7:].strip()
            if not token:
                return 401, {"error": "UNAUTHORIZED"}
            try:
                uid = canonical_uuid(self.verify_token(token))
            except (AuthenticationError, ValueError, TypeError):
                return 401, {"error": "UNAUTHORIZED"}
            if not self.tenant_store.member(token, uid, sid, write=True):
                return 403, {"error": "FORBIDDEN"}
            if self.profile_reader is None:
                return 503, {"error": "PROFILE_UNAVAILABLE"}
            if not isinstance(payload, dict) or set(payload) != {
                "original_prompt", "output_formats", "language"
            }:
                return 400, {"error": "INVALID_REQUEST"}
            row = self.profile_reader(token, uid, sid)
            if not isinstance(row, dict) or row.get("shop_id") != sid:
                return 404, {"error": "NOT_FOUND"}
            if not isinstance(row.get("city"), str) or not row["city"].strip():
                return 422, {"error": "BUSINESS_PROFILE_INCOMPLETE"}
            profile = RetailerProfile.from_authorized(row)
            if ai_mode:
                if self.ai_service is None:
                    return 503, {"error": "AI_NOT_ENABLED_OR_NOT_APPROVED"}
                result = self.ai_service.improve(
                    original_prompt=payload["original_prompt"], retailer=profile,
                    output_formats=payload["output_formats"],
                    language=payload["language"], shop_id=sid, actor_id=uid)
            else:
                from ai_agents.prompt_improver import improve_prompt
                result = improve_prompt(
                    payload["original_prompt"], profile,
                    output_formats=payload["output_formats"], language=payload["language"],
                )
            return 200, {"shop_id": sid, **result}
        except AuthenticationError:
            return 401, {"error": "UNAUTHORIZED"}
        except (ValueError, TypeError, KeyError, ContractError):
            return 400, {"error": "INVALID_REQUEST"}
        except PermissionError:
            return 403, {"error": "FORBIDDEN"}
        except StorageUnavailable:
            return 503, {"error": "PROFILE_UNAVAILABLE"}
        except FoundryUnavailable:
            return 503, {"error": "AI_MODEL_UNAVAILABLE"}

    def list_drafts(self, shop_id: str, authorization: str) -> tuple[int, dict]:
        """Read saved drafts with the *user's* RLS identity, even when RSS is down."""
        try:
            sid = canonical_uuid(shop_id)
            if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
                return 401, {"error": "UNAUTHORIZED"}
            token = authorization[7:].strip()
            if not token:
                return 401, {"error": "UNAUTHORIZED"}
            try:
                uid = canonical_uuid(self.verify_token(token))
            except (AuthenticationError, ValueError, TypeError):
                return 401, {"error": "UNAUTHORIZED"}
            if not self.tenant_store.member(token, uid, sid, write=False):
                return 404, {"error": "NOT_FOUND"}
            if not self.draft_store:
                return 503, {"error": "CONTENT_DRAFT_STORE_NOT_CONFIGURED"}
            rows = self.draft_store.list_drafts(token, sid, limit=5)
            return 200, {"shop_id": sid, "drafts": rows}
        except AuthenticationError:
            return 401, {"error": "UNAUTHORIZED"}
        except (ValueError, TypeError, KeyError):
            return 400, {"error": "INVALID_REQUEST"}
        except StorageUnavailable:
            return 503, {"error": "CONTENT_DRAFT_READ_UNAVAILABLE"}
