"""Disabled-by-default backend VIDEO approval orchestration, NOT an HTTP route.

Every call requires verified JWT + active writable tenant membership. The
server re-reads the current P2 draft and independently authorized render and
commercial-rights ledgers, computes its OWN canonical content digest and then
invokes a one-transaction DB approval+quota CAS. No browser hash, consent
flag or signed media URL can enter the request. Nothing calls a provider.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import re

from security import AuthenticationError
from social_publish_policy import approved_digest, PublishDenied
from tenant_store import StorageUnavailable, SubscriptionDenied, canonical_uuid


_SHA = re.compile(r"[0-9a-f]{64}\Z")
_VIDEO = frozenset(("instagram", "youtube"))
_ALLOWED_KINDS = frozenset(("OWNER_ATTESTED", "STOCK_LICENSE_VERIFIED",
                            "GENERATED_RIGHTS_VERIFIED"))


class ReviewedVideoApprovalDisabled(RuntimeError):
    pass


class ReviewedVideoApprovalService:
    def __init__(self, verifier, tenant, repository, source_store_factory,
                 *, enabled=False, clock=None):
        if enabled is not True:
            raise ReviewedVideoApprovalDisabled("video publishing approval OFF")
        if any(x is None for x in
               (verifier,tenant,repository,source_store_factory)):
            raise ValueError("trusted video approval dependencies missing")
        self.verifier=verifier
        self.tenant=tenant
        self.repository=repository
        self.source_store_factory=source_store_factory
        self.clock=clock or (lambda:datetime.now(timezone.utc))

    def approve(self,authorization,body):
        """Body accepts ONLY shop_id, job_id, revision, never SHA or rights."""
        if not isinstance(authorization,str) or not authorization.startswith("Bearer "):
            return 401,{"error":"UNAUTHORIZED"}
        if not isinstance(body,dict) or set(body)!={"shop_id","job_id","revision"}:
            return 400,{"error":"INVALID_REQUEST"}
        try:
            uid=canonical_uuid(self.verifier(authorization[7:].strip()))
            sid=canonical_uuid(body["shop_id"])
            jid=canonical_uuid(body["job_id"])
            revision=body["revision"]
            if type(revision) is not int or not 1<=revision<=2147483647:
                return 400,{"error":"INVALID_REVISION"}
            if not self.tenant.member(authorization[7:].strip(),uid,sid,write=True):
                return 403,{"error":"FORBIDDEN"}
            current=self.repository.read_job(sid,jid)
            if current is None:
                return 404,{"error":"NOT_FOUND"}
            if (current.get("shop_id")!=sid or current.get("id")!=jid
                    or current.get("provider") not in _VIDEO
                    or current.get("status")!="DRAFT"
                    or current.get("revision")!=revision):
                return 409,{"error":"REVIEWED_CONTENT_CHANGED"}
            media_id=canonical_uuid(current["media_asset_id"])
            account=canonical_uuid(current["social_account_id"])
            day=canonical_uuid(current["campaign_day_id"])
            at=datetime.fromisoformat(current["scheduled_at"].replace("Z","+00:00"))
            now=self.clock()
            if (at.tzinfo is None or now.tzinfo is None
                    or at<=now+timedelta(minutes=1)):
                return 409,{"error":"REVIEWED_CONTENT_CHANGED"}

            # A factory owned solely by backend config binds shop+job+actor
            # to service-role RPCs, never to request-supplied URLs/keys.
            source=self.source_store_factory(sid,jid,uid)
            candidate=source.get_source(sid,jid,uid)
            if not isinstance(candidate,dict):
                return 409,{"error":"REVIEW_REQUIRED"}
            scheduled=candidate.get("scheduled_at")
            if (candidate.get("shop_id")!=sid
                    or candidate.get("job_id")!=jid
                    or candidate.get("media_asset_id")!=media_id
                    or candidate.get("revision")!=revision
                    or candidate.get("source")!="GENERATED"
                    or candidate.get("storage_bucket")!="retailgrowth-media"
                    or not isinstance(scheduled,datetime)
                    or scheduled.tzinfo is None
                    or scheduled.astimezone(timezone.utc)!=at.astimezone(timezone.utc)):
                return 409,{"error":"REVIEW_REQUIRED"}
            receipt=source.get_render_receipt(sid,media_id)
            clearance=source.get_clearance(sid,media_id,uid,revision)
            if not isinstance(receipt,dict) or not isinstance(clearance,dict):
                return 409,{"error":"REVIEW_REQUIRED"}
            sha=receipt.get("source_sha256")
            evidence=clearance.get("rights_evidence_sha256")
            expires=clearance.get("rights_expires_at")
            if (receipt.get("shop_id")!=sid
                    or receipt.get("media_asset_id")!=media_id
                    or receipt.get("source")!="PART1_RENDER_FINALIZED"
                    or receipt.get("object_path")!=candidate.get("object_path")
                    or not isinstance(sha,str) or _SHA.fullmatch(sha) is None
                    or clearance.get("shop_id")!=sid
                    or clearance.get("media_asset_id")!=media_id
                    or clearance.get("reviewed_by")!=uid
                    or clearance.get("revision")!=revision
                    or clearance.get("rights_kind") not in _ALLOWED_KINDS
                    or not isinstance(evidence,str) or _SHA.fullmatch(evidence) is None
                    or not isinstance(expires,datetime) or expires.tzinfo is None
                    or expires<=max(now,at)+timedelta(hours=6)):
                return 409,{"error":"REVIEW_REQUIRED"}

            digest=approved_digest(
                shop_id=sid, day_id=day, account_id=account,
                platform=current["provider"], caption=current["caption"],
                media_asset_id=media_id, scheduled_at=at,
                timezone_name=current["timezone"], revision=revision)
            success=self.repository.approve_reviewed_video(
                shop_id=sid,job_id=jid,actor=uid,revision=revision,
                digest=digest,caption=current["caption"],scheduled_at=at,
                timezone_name=current["timezone"],media_id=media_id,
                source_sha256=sha)
            if success is not True:
                return 409,{"error":"REVIEWED_CONTENT_CHANGED"}
            return 200,{"id":jid,"status":"APPROVED","revision":revision}
        except AuthenticationError:
            return 401,{"error":"UNAUTHORIZED"}
        except SubscriptionDenied as denied:
            return ((429,{"error":"PUBLISH_QUOTA_EXCEEDED"})
                    if denied.code=="RG002" else
                    (402,{"error":"PUBLISH_SUBSCRIPTION_REQUIRED"}))
        except (PublishDenied,ValueError,TypeError,KeyError,AttributeError):
            return 400,{"error":"INVALID_REQUEST"}
        except StorageUnavailable:
            return 503,{"error":"SERVICE_UNAVAILABLE"}
