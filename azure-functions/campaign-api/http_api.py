"""Pure HTTP boundary: verifies JWT, RLS membership and asset ownership on every call."""
from __future__ import annotations

from uuid import uuid4
from ai_agents.schemas import CampaignBrief, ContractError, validate_campaign

from security import AuthenticationError
from tenant_store import StorageUnavailable, SubscriptionDenied, canonical_uuid
from draft_api import DraftAPI


class HTTPAPI:
    def __init__(self, verify_token, store, planning_queue=None, render_api=None, failure_store=None, durable_outbox=False, poster_api=None, poster_render_api=None, feature3_api=None):
        self.verify_token = verify_token
        self.store = store
        self.planning_queue = planning_queue
        self.render_api = render_api
        self.failure_store = failure_store
        self.durable_outbox = durable_outbox
        self.poster_api = poster_api
        self.poster_render_api = poster_render_api
        self.feature3_api = feature3_api

    def handle(self, method, path, authorization, body=None):
        try:
            if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
                raise AuthenticationError("bearer token required")
            token = authorization[7:].strip()
            user_id = self.verify_token(token)
            # Feature3 is additive and OFF unless specifically configured.
            if "/feature3-source-assets/" in path:
                if self.feature3_api is None:
                    return 503, {"error": "FEATURE3_V2_DISABLED"}
                parts = path.strip("/").split("/")
                if (method != "GET" or len(parts) != 4 or
                    parts[0] != "shops" or parts[2] != "feature3-source-assets"):
                    return 404, {"error": "NOT_FOUND"}
                return self.feature3_api.source_asset(
                    token, user_id, parts[1], parts[3])
            if path.endswith("/download") and "/feature3-gpu-jobs/" in path:
                if self.feature3_api is None:
                    return 503, {"error": "FEATURE3_V2_DISABLED"}
                parts=path.strip("/").split("/")
                if (method != "GET" or len(parts)!=5 or
                    parts[0]!="shops" or parts[2]!="feature3-gpu-jobs" or
                    parts[4]!="download"):
                    return 404, {"error": "NOT_FOUND"}
                return self.feature3_api.gpu_download(
                    token,user_id,parts[1],parts[3])
            if path.startswith("/shops/") and path.endswith("/feature3-gpu-jobs"):
                parts = path.strip("/").split("/")
                # No browser route can launch a GPU, even while Feature3 is OFF.
                if (method != "GET" or len(parts) != 3 or
                    parts[0] != "shops" or parts[2] != "feature3-gpu-jobs"):
                    return 404, {"error": "NOT_FOUND"}
                if self.feature3_api is None:
                    return 503, {"error": "FEATURE3_V2_DISABLED"}
                return self.feature3_api.gpu_jobs(token, user_id, parts[1])
            if path.startswith("/shops/") and path.endswith("/feature3-model-originals/register"):
                parts = path.strip("/").split("/")
                if (method != "POST" or len(parts) != 4 or
                    parts[0] != "shops" or parts[2] != "feature3-model-originals" or
                    parts[3] != "register"):
                    return 404, {"error": "NOT_FOUND"}
                if self.feature3_api is None:
                    return 503, {"error": "FEATURE3_V2_DISABLED"}
                return self.feature3_api.register_model_original(
                    token, user_id, parts[1], body)
            if path.startswith("/shops/") and path.endswith("/feature3-models/import"):
                parts = path.strip("/").split("/")
                if (method != "POST" or len(parts) != 4
                    or parts[0] != "shops" or parts[2] != "feature3-models"
                    or parts[3] != "import"):
                    return 404, {"error": "NOT_FOUND"}
                if self.feature3_api is None:
                    return 503, {"error": "FEATURE3_V2_DISABLED"}
                return self.feature3_api.import_model(token, user_id, parts[1], body)
            if "/feature3-models/" in path:
                # Model decisions are strictly signed OWNER/EDITOR writes.
                # This route never starts generation, uploads files or
                # invokes privileged service-role evidence insertion.
                parts = path.strip("/").split("/")
                if (method != "POST" or len(parts) != 5 or
                    parts[0] != "shops" or parts[2] != "feature3-models" or
                    parts[4] not in ("review", "revoke")):
                    return 404, {"error": "NOT_FOUND"}
                if self.feature3_api is None:
                    return 503, {"error": "FEATURE3_V2_DISABLED"}
                return self.feature3_api.review_model(
                    token, user_id, parts[1], parts[3], body,
                    action=parts[4])
            if path.startswith("/shops/") and path.endswith("/feature3-models"):
                if self.feature3_api is None:
                    return 503, {"error": "FEATURE3_V2_DISABLED"}
                parts = path.strip("/").split("/")
                if method != "GET" or len(parts) != 3 or parts[0] != "shops":
                    return 404, {"error": "NOT_FOUND"}
                return self.feature3_api.models(token, user_id, parts[1])
            if "/feature3-designs" in path:
                if self.feature3_api is None:
                    return 503, {"error": "FEATURE3_V2_DISABLED"}
                parts = path.strip("/").split("/")
                if len(parts) != 5 or parts[0] != "campaigns" or parts[2] != "days" or parts[4] != "feature3-designs":
                    return 404, {"error": "NOT_FOUND"}
                return self.feature3_api.day(token, user_id, parts[1], parts[3], method, body)
            if method == "POST" and path.startswith("/campaigns/") and path.endswith("/posters"):
                if self.poster_api is None:
                    return 503, {"error": "POSTER_DRAFT_NOT_CONFIGURED"}
                parts = path.strip("/").split("/")
                if len(parts) != 3 or parts[0] != "campaigns" or parts[2] != "posters":
                    return 404, {"error": "NOT_FOUND"}
                return self.poster_api.create(token, user_id, parts[1], body)
            if method == "GET" and path.startswith("/campaigns/") and path.endswith("/posters") and "/days/" in path:
                if self.poster_api is None:
                    return 503, {"error": "POSTER_DRAFT_NOT_CONFIGURED"}
                parts = path.strip("/").split("/")
                if len(parts) != 5 or parts[0] != "campaigns" or parts[2] != "days" or parts[4] != "posters":
                    return 404, {"error": "NOT_FOUND"}
                return self.poster_api.list_for_day(token, user_id, parts[1], parts[3])
            if method == "GET" and path.startswith("/poster-drafts/"):
                if self.poster_api is None:
                    return 503, {"error": "POSTER_DRAFT_NOT_CONFIGURED"}
                parts = path.strip("/").split("/")
                if len(parts) != 2 or parts[0] != "poster-drafts":
                    return 404, {"error": "NOT_FOUND"}
                return self.poster_api.get(token, user_id, parts[1])
            if method == "POST" and path.startswith("/poster-drafts/") and path.endswith("/select"):
                if self.poster_render_api is None:
                    return 503, {"error": "POSTER_RENDER_NOT_CONFIGURED"}
                parts = path.strip("/").split("/")
                if len(parts) != 3 or parts[0] != "poster-drafts" or parts[2] != "select":
                    return 404, {"error": "NOT_FOUND"}
                return self.poster_render_api.select(token, user_id, parts[1], body)
            if method == "POST" and path.startswith("/poster-drafts/") and path.endswith("/renders"):
                if self.poster_render_api is None:
                    return 503, {"error": "POSTER_RENDER_NOT_CONFIGURED"}
                parts = path.strip("/").split("/")
                if len(parts) != 3 or parts[0] != "poster-drafts" or parts[2] != "renders":
                    return 404, {"error": "NOT_FOUND"}
                if body not in (None, {}):
                    return 400, {"error": "INVALID_REQUEST"}
                return self.poster_render_api.create(token, user_id, parts[1])
            if method == "GET" and path.startswith("/poster-jobs/"):
                if self.poster_render_api is None:
                    return 503, {"error": "POSTER_RENDER_NOT_CONFIGURED"}
                parts = path.strip("/").split("/")
                if len(parts) == 3 and parts[0] == "poster-jobs" and parts[2] == "download":
                    return self.poster_render_api.download(token, user_id, parts[1])
                if len(parts) == 2 and parts[0] == "poster-jobs":
                    return self.poster_render_api.get(token, user_id, parts[1])
                return 404, {"error": "NOT_FOUND"}
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
                if self.durable_outbox:
                    # INSERT trigger persists dispatch in the same transaction.
                    # Even if Azure Queue is temporarily down, the outbox can replay.
                    return 202, {"campaign_id": cid, "status": "PLANNING"}
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
        except SubscriptionDenied as exc:
            if exc.code == "RG002":
                return 429, {"error": "QUOTA_EXCEEDED"}
            return 402, {"error": "SUBSCRIPTION_REQUIRED"}
        except AuthenticationError:
            return 401, {"error": "UNAUTHORIZED"}
        except (ContractError, ValueError, TypeError, AttributeError):
            return 400, {"error": "INVALID_REQUEST"}
        except (StorageUnavailable, KeyError):
            return 503, {"error": "SERVICE_UNAVAILABLE"}
