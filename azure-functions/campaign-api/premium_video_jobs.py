"""Part 3 premium-video orchestration boundary (not wired to live Functions).

Create/status is JWT/RLS scoped through injected existing RetailGrowthAI stores.
Only a dedicated service-only database INSERT with a BEFORE INSERT quota trigger
may reserve premium seconds. Workers only pass UUIDs in Azure Queue messages.
Provider activation remains disabled by default; no paid request happens here.
"""
from __future__ import annotations

import hashlib
import json
import os
from uuid import uuid4

from ai_agents.premium_video import (
    WanRequest, AlibabaWanProvider, PremiumVideoDisabled, campaign_video_prompt
)
from tenant_store import canonical_uuid, StorageUnavailable

AVAILABLE_MODES = ("text", "image")
AVAILABLE_RESOLUTIONS = ("720P", "1080P")
AVAILABLE_DURATIONS = range(2, 16)


class PremiumVideoCoordinator:
    def __init__(self, user_store, premium_store, rights_store,
                 *, enabled=False):
        self.user_store = user_store
        self.premium_store = premium_store
        self.rights_store = rights_store
        self.enabled = enabled

    def create(self, token, user_id, campaign_id, payload):
        # Preserve the free FFmpeg path even if premium has no entitlement.
        if not self.enabled:
            return 503, {"error": "PREMIUM_VIDEO_DISABLED"}
        if not isinstance(payload, dict) or set(payload) != {
            "day_id", "mode", "resolution", "duration_seconds", "input_asset_id"
        }:
            return 400, {"error": "INVALID_REQUEST"}
        try:
            cid = canonical_uuid(campaign_id)
            did = canonical_uuid(payload["day_id"])
            uid = canonical_uuid(user_id)
            mode, resolution = payload["mode"], payload["resolution"]
            duration = payload["duration_seconds"]
            if (mode not in AVAILABLE_MODES or resolution not in AVAILABLE_RESOLUTIONS
                or type(duration) is not int or duration not in AVAILABLE_DURATIONS):
                return 400, {"error": "INVALID_REQUEST"}
            asset = payload["input_asset_id"]
            if mode == "image":
                asset = canonical_uuid(asset)
            elif asset is not None:
                return 400, {"error": "INVALID_REQUEST"}
            campaign = self.user_store.campaign(token, uid, cid)
            if campaign is None:
                return 404, {"error": "NOT_FOUND"}
            sid = canonical_uuid(campaign["shop_id"])
            if campaign["status"] != "DRAFT":
                return 409, {"error": "CAMPAIGN_NOT_DRAFT"}
            if not self.user_store.member(token, uid, sid, write=True):
                return 403, {"error": "FORBIDDEN"}
            days = [d for d in campaign["days"]
                    if d.get("id") == did and d.get("shop_id") == sid]
            if len(days) != 1 or days[0].get("review_status") == "REJECTED":
                return 409, {"error": "DAY_NOT_APPROVED"}
            if mode == "image":
                # Existing user-JWT RLS asset check + service-only rights check.
                owned = self.user_store.asset(token, sid, asset)
                if owned is None or owned.get("mime_type") not in (
                        "image/png", "image/jpeg", "image/webp"):
                    return 403, {"error": "IMAGE_NOT_AUTHORIZED"}
                if not self.rights_store.valid_media(sid, [asset]):
                    return 403, {"error": "ASSET_RIGHTS_UNVERIFIED"}
            # Only approved (already reviewed) day content enters the provider.
            prompt = campaign_video_prompt(days[0])
            canonical = [uid, sid, cid, did, mode, resolution, duration,
                         asset, prompt]
            digest = hashlib.sha256(json.dumps(canonical, sort_keys=True,
                separators=(",", ":")).encode("utf-8")).hexdigest()
            previous = self.premium_store.find_authenticated(token, sid, digest)
            if previous is not None:
                return 200, self._public(previous)
            row = {
                "id": str(uuid4()), "shop_id": sid, "campaign_id": cid,
                "day_id": did, "requested_by": uid, "mode": mode,
                "model_id": ("wan2.7-t2v-2026-06-12" if mode == "text"
                             else "wan2.7-i2v-2026-04-25"),
                "resolution": resolution, "seconds": duration,
                "input_asset_id": asset, "idempotency_key": digest,
                "status": "QUEUED"
            }
            # insert_reserved is a *single* DB write, protected by the new
            # subscription row-lock + shared usage ledger trigger. A second
            # distinct client POST cannot create spend outside that trigger.
            try:
                created = self.premium_store.insert_reserved(row)
            except StorageUnavailable:
                existing = self.premium_store.find_authenticated(token, sid, digest)
                if existing is not None:
                    return 200, self._public(existing)
                raise
            if not isinstance(created, dict) or created.get("id") != row["id"]:
                raise StorageUnavailable("premium insert verification failed")
            # Queue publication is NOT performed here: a durable outbox trigger
            # and idempotent service worker are required before this API may
            # be routed in production.
            return 202, self._public(created)
        except (TypeError, ValueError, AttributeError, KeyError):
            return 400, {"error": "INVALID_REQUEST"}

    def status(self, token, user_id, job_id):
        if not self.enabled:
            return 503, {"error": "PREMIUM_VIDEO_DISABLED"}
        jid = canonical_uuid(job_id)
        job = self.premium_store.get_authenticated(token, jid)
        if job is None or not self.user_store.member(token, user_id, job["shop_id"]):
            return 404, {"error": "NOT_FOUND"}
        return 200, self._public(job)

    @staticmethod
    def _public(job):
        # Never include cost controls, backend provider task IDs, signed URLs,
        # API credentials or storage object paths in JSON returned to users.
        return {k: job.get(v) for k,v in {
            "job_id": "id", "status": "status", "output_asset_id": "output_asset_id",
            "error_code": "error_code"
        }.items()}


class PremiumSubmissionWorker:
    """Lease-fenced source-only worker bridge for durable Azure UUID triggers.

    If an async task submission response is uncertain, mark UNKNOWN; NEVER
    issue another provider POST automatically because that might double charge.
    """
    def __init__(self, store, provider: AlibabaWanProvider):
        self.store, self.provider = store, provider

    def submit_once(self, job_id):
        jid = canonical_uuid(job_id)
        claim = self.store.claim(jid)
        if claim is None:
            return "NOT_CLAIMED"
        if claim.get("status") != "SUBMITTING" or not claim.get("attempt_token"):
            raise StorageUnavailable("invalid premium lease")
        try:
            request = WanRequest(
                mode=claim["mode"], prompt=claim["prompt"],
                duration_seconds=claim["seconds"],
                resolution=claim["resolution"],
                signed_first_frame=claim.get("signed_first_frame"),
                shop_id=claim["shop_id"]
            )
            result = self.provider.submit(request)
        except PremiumVideoDisabled:
            self.store.finish_attempt(jid, claim["attempt_token"],
                                      "FAILED", error_code="PROVIDER_NOT_APPROVED")
            return "FAILED"
        except Exception:
            # Even if a request might have reached the provider, it is never
            # safe to auto-post again. Human reconciliation must inspect it.
            self.store.finish_attempt(jid, claim["attempt_token"],
                                      "UNKNOWN", error_code="PROVIDER_RESULT_UNKNOWN")
            return "UNKNOWN"
        self.store.record_task(jid, claim["attempt_token"], result["task_id"])
        return "PENDING"

    def poll_once(self, job_id):
        jid = canonical_uuid(job_id)
        claim = self.store.claim_poll(jid)
        if claim is None:
            return "NOT_CLAIMED"
        task_id, lease = claim["provider_task_id"], claim["attempt_token"]
        result = self.provider.poll(task_id)
        if result["status"] in ("PENDING", "RUNNING"):
            self.store.record_poll(jid, lease, result["status"])
        elif result["status"] == "SUCCEEDED":
            # MUST NOT mark SUCCEEDED until provider bytes have been safely
            # imported, ffprobed, uploaded to PRIVATE shop storage and a signed
            # RetailGrowthAI link is provisioned. Keep pending importer state.
            self.store.record_poll(jid, lease, "IMPORTING")
        else:
            self.store.record_poll(jid, lease, "FAILED")
        return result["status"]
