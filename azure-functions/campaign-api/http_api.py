"""Pure HTTP boundary: verifies JWT, RLS membership and asset ownership on every call."""
from __future__ import annotations

from uuid import uuid4
from ai_agents.schemas import CampaignBrief, ContractError, validate_campaign

from security import AuthenticationError
from tenant_store import StorageUnavailable, canonical_uuid\nfrom draft_api import DraftAPI


class HTTPAPI:
    def __init__(self, verify_token, store, planning_queue=None, render_api=None, failure_store=None):
        self.verify_token = verify_token
        self.store = store
        self.planning_queue = planning_queue
        self.render_api = render_api
        self.failure_store = failure_store

    def handle(self, method, path, authorization, body=None):
        try:
            if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
                raise AuthenticationError("bearer token required")
            token = authorization[7:].strip()
            user_id = self.verify_token(token)
            if method == "POST" and path.startswith("/campaigns/") and path.endswith("/renders"):
                if self.render_api is None:
                    return 503, {"error": "RENDER_NOT_CONFIGURED"}
                cid = path[len("/campaigns/"):-len("/renders")].strip("/")
                return self.render_api.create(token, user_id, cid, body)
            if method == "GET" and path.startswith("/render-jobs/"):
                if self.render_api is None:
                    return 503, {"error": "RENDER_NOT_CONFIGURED"}
                target = path[len("/render-jobs/"):]
                if target.endswith("/download"):
                    return self.render_api.download(token, user_id, target[:-len("/download")])
                return self.render_api.get(token, user_id, target)
            if method == "POST" and path == "/campaigns":
                # Fail closed BEFORE writing if durable queue is not yet configured.
                if self.planning_queue is None or self.failure_store is None:
                    return 503, {"error": "PLANNING_NOT_CONFIGURED"}
                brief = CampaignBrief.from_dict(body)
                if not self.store.member(token, user_id, brief.shop_id, write=True):
                    return 403, {"error": "FORBIDDEN"}
                if not self.store.assets(token, brief.shop_id, brief.media_asset_ids):
                    return 403, {"error": "FORBIDDEN"}
                cid = str(uuid4())
                self.store.save_pending(token, user_id, cid, brief)
                try:
                    self.planning_queue.enqueue(cid)
                except Exception:
                    # A failed durable enqueue must not masquerade as an accepted job.
                    self.failure_store.fail_pending(cid, brief.shop_id, user_id)
                    return 503, {"error": "QUEUE_UNAVAILABLE"}
                return 202, {"campaign_id": cid, "status": "PLANNING"}
            if method == "PATCH" and path.startswith("/campaigns/") and "/days/" in path:
                parts = path.strip("/").split("/")
                if len(parts) != 4 or parts[0] != "campaigns" or parts[2] != "days":
                    return 404, {"error": "NOT_FOUND"}
                return DraftAPI(self.store).save(token, user_id, parts[1], parts[3], body)
            if method == "GET" and path.startswith("/campaigns/"):
                cid = canonical_uuid(path.removeprefix("/campaigns/"))
                record = self.store.campaign(token, user_id, cid)
                if record is None:
                    return 404, {"error": "NOT_FOUND"}
                if record["status"] == "DRAFT":
                    validate_campaign(record)
                return 200, record
            return 404, {"error": "NOT_FOUND"}
        except AuthenticationError:
            return 401, {"error": "UNAUTHORIZED"}
        except (ContractError, ValueError, TypeError, AttributeError):
            return 400, {"error": "INVALID_REQUEST"}
        except (StorageUnavailable, KeyError):
            return 503, {"error": "SERVICE_UNAVAILABLE"}
