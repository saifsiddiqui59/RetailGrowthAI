"""Part 2 owner/editor authoring API, disabled until separately approved release.

Never trusts browser approval flags or reviewed digests. The authenticated
backend reads the current DB draft, computes a canonical content digest, and
uses a version/field-bound DB-atomic approval + quota reservation RPC.
"""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4

from security import AuthenticationError
from tenant_store import StorageUnavailable, SubscriptionDenied, canonical_uuid
from social_publish_policy import approved_digest, PublishDenied
from social_scheduling import schedule_utc, ScheduleDenied


_PROVIDERS = {"facebook", "linkedin", "instagram", "youtube"}


class SocialJobsAPI:
    def __init__(self, verifier, tenant_store, repository, *, clock=None):
        self.verifier = verifier
        self.tenant = tenant_store
        self.repository = repository
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def handle(self, operation, authorization, body):
        try:
            if operation not in ("create", "approve", "cancel"):
                return 404, {"error": "NOT_FOUND"}
            if (not isinstance(authorization, str) or
                    not authorization.startswith("Bearer ")):
                raise AuthenticationError("sign-in required")
            if not isinstance(body, dict):
                return 400, {"error": "INVALID_REQUEST"}
            token = authorization[7:].strip()
            user_id = canonical_uuid(self.verifier(token))
            sid = canonical_uuid(body.get("shop_id"))
            if not self.tenant.member(token, user_id, sid, write=True):
                return 403, {"error": "FORBIDDEN"}
            if operation == "create":
                return self._create(token, user_id, sid, body)
            if operation == "approve":
                return self._approve(user_id, sid, body)
            return self._cancel(user_id, sid, body)
        except AuthenticationError:
            return 401, {"error": "UNAUTHORIZED"}
        except SubscriptionDenied as denied:
            return ((429, {"error": "PUBLISH_QUOTA_EXCEEDED"})
                    if denied.code == "RG002" else
                    (402, {"error": "PUBLISH_SUBSCRIPTION_REQUIRED"}))
        except (PublishDenied, ScheduleDenied, ValueError, TypeError, KeyError):
            return 400, {"error": "INVALID_REQUEST"}
        except StorageUnavailable:
            return 503, {"error": "SERVICE_UNAVAILABLE"}

    def _create(self, token, uid, sid, body):
        required = {"shop_id", "provider", "account_id", "day_id",
                    "caption", "media_asset_id", "day", "clock", "timezone",
                    "idempotency_key"}
        if set(body) != required:
            return 400, {"error": "INVALID_REQUEST"}
        provider = body["provider"]
        account_id, day_id = canonical_uuid(body["account_id"]), canonical_uuid(body["day_id"])
        if provider not in _PROVIDERS:
            return 400, {"error": "UNSUPPORTED_PLATFORM"}
        caption = body["caption"]
        if (not isinstance(caption, str) or not 1 <= len(caption.strip()) <= 5000
                or any(ord(char) < 32 for char in caption)):
            return 400, {"error": "INVALID_CAPTION"}
        media_id = body["media_asset_id"]
        if media_id is not None:
            media_id = canonical_uuid(media_id)
        if ((provider in ("facebook", "linkedin") and media_id is not None)
                or (provider in ("instagram", "youtube") and media_id is None)):
            return 400, {"error": "MEDIA_REQUIRED_OR_UNSUPPORTED"}
        key = body["idempotency_key"]
        if (not isinstance(key, str) or not 8 <= len(key) <= 128 or
                any(not (c.isalnum() and c.isascii() or c in "_:-") for c in key)):
            return 400, {"error": "INVALID_IDEMPOTENCY_KEY"}
        timestamp = schedule_utc(day=body["day"], clock=body["clock"],
                                 zone=body["timezone"], now_utc=self.clock())
        rows = self.tenant._request("campaign_days", token, query={
            "select": "id,shop_id", "id": "eq." + day_id,
            "shop_id": "eq." + sid, "limit": "1",
        })
        if (not isinstance(rows, list) or len(rows) != 1 or
                rows[0].get("id") != day_id or rows[0].get("shop_id") != sid):
            return 403, {"error": "CAMPAIGN_DAY_FORBIDDEN"}
        if media_id is not None and not self.tenant.assets(token, sid, [media_id]):
            return 403, {"error": "MEDIA_FORBIDDEN"}
        result = self.repository.create_draft(
            id=str(uuid4()), shop_id=sid, actor=uid, account_id=account_id,
            day_id=day_id, provider=provider, caption=caption, media_id=media_id,
            scheduled_at=timestamp, timezone_name=body["timezone"],
            idempotency_key=key)
        if (not isinstance(result, dict) or
                result.get("status") not in ("DRAFT", "APPROVED", "CANCELED") or
                result.get("revision") != 1):
            raise StorageUnavailable("invalid database draft receipt")
        jid = canonical_uuid(result.get("id"))
        return 201, {"id": jid, "status": result["status"], "revision": 1}

    def _approve(self, uid, sid, body):
        if set(body) != {"shop_id", "job_id", "revision"}:
            return 400, {"error": "INVALID_REQUEST"}
        jid = canonical_uuid(body["job_id"])
        revision = body["revision"]
        if type(revision) is not int or not 1 <= revision <= 2147483647:
            return 400, {"error": "INVALID_REVISION"}
        job = self.repository.read_job(sid, jid)
        if job is None:
            return 404, {"error": "NOT_FOUND"}
        if (job.get("shop_id") != sid or job.get("id") != jid
                or job.get("status") != "DRAFT" or job.get("revision") != revision):
            return 409, {"error": "REVIEWED_CONTENT_CHANGED"}
        try:
            at = datetime.fromisoformat(job["scheduled_at"].replace("Z", "+00:00"))
            account_id = canonical_uuid(job["social_account_id"])
            day_id = canonical_uuid(job["campaign_day_id"])
            media_id = (canonical_uuid(job["media_asset_id"])
                        if job.get("media_asset_id") else None)
            digest = approved_digest(
                shop_id=sid, day_id=day_id, account_id=account_id,
                platform=job["provider"], caption=job["caption"],
                media_asset_id=media_id, scheduled_at=at,
                timezone_name=job["timezone"], revision=revision)
        except (KeyError, TypeError, AttributeError, ValueError, PublishDenied) as ex:
            raise StorageUnavailable("untrusted social draft") from None
        result = self.repository.approve(
            shop_id=sid, job_id=jid, actor=uid, revision=revision,
            digest=digest, caption=job["caption"], scheduled_at=at,
            timezone_name=job["timezone"], media_id=media_id)
        if result is not True:
            return 409, {"error": "REVIEWED_CONTENT_CHANGED"}
        return 200, {"id": jid, "status": "APPROVED", "revision": revision}

    def _cancel(self, uid, sid, body):
        if set(body) != {"shop_id", "job_id", "revision"}:
            return 400, {"error": "INVALID_REQUEST"}
        jid = canonical_uuid(body["job_id"])
        revision = body["revision"]
        if type(revision) is not int or not 1 <= revision <= 2147483647:
            return 400, {"error": "INVALID_REVISION"}
        if self.repository.cancel(
                shop_id=sid, job_id=jid, actor=uid, revision=revision) is not True:
            return 409, {"error": "CANNOT_CANCEL_POSSIBLY_SENT"}
        return 200, {"id": jid, "status": "CANCELED"}


def build_social_jobs_api(config=None):
    """Fail closed unless P2 social authoring explicitly enabled on server."""
    import os
    from security import SupabaseJWTVerifier
    from tenant_store import TenantStore
    from social_jobs_repository import SocialAuthoringRepository
    env = os.environ if config is None else config
    if (env.get("RETAIL_PART2_SOCIAL_ENABLED") != "true" or
            env.get("RETAIL_PART2_AUTHORING_ENABLED") != "true"):
        raise ValueError("Part 2 authoring disabled")
    origin = env["RETAIL_SUPABASE_URL"]
    return SocialJobsAPI(
        SupabaseJWTVerifier(origin),
        TenantStore(origin, env["RETAIL_SUPABASE_PUBLISHABLE_KEY"]),
        SocialAuthoringRepository(origin, env["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]),
    )
