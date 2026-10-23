"""Fail-closed, standalone Part 3 premium HTTP adapter (NOT registered in Azure).

Reusable source contract for additive authenticated premium create/status/download
routes. Does not enable billing, create cloud queues, apply migrations or call Wan.
The production API may mount this ONLY after vetted SQL/worker/entitlement gates.
"""
from __future__ import annotations

import re

from security import AuthenticationError
from tenant_store import (
    StorageUnavailable, SubscriptionDenied, canonical_uuid,
)

CAMPAIGN_CREATE = re.compile(r"^/campaigns/([^/]+)/premium-videos$")
PREMIUM_JOB = re.compile(r"^/premium-video-jobs/([^/]+)(/download)?$")
PRIVATE_FILE = re.compile(
    r"^([0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})\\.mp4$"
)


class PremiumHTTPBoundary:
    """Dedicated private controller; no change to Part1 HTTPAPI public v1 API."""

    def __init__(self, verify_token, users, premium_store, coordinator,
                 *, enabled=False):
        self.verify_token = verify_token
        self.users = users
        self.store = premium_store
        self.coordinator = coordinator
        self.enabled = enabled

    def handle(self, method, path, authorization, body=None):
        try:
            if (not isinstance(authorization, str) or
                not authorization.startswith("Bearer ") or
                not authorization[7:].strip()):
                raise AuthenticationError("Bearer token required")
            token = authorization[7:].strip()
            user_id = canonical_uuid(self.verify_token(token))
            if not self.enabled or not self.coordinator:
                return 503, {"error": "PREMIUM_VIDEO_DISABLED"}
            if not isinstance(path, str):
                return 404, {"error": "NOT_FOUND"}

            match = CAMPAIGN_CREATE.fullmatch(path)
            if match is not None and method == "POST":
                campaign_id = canonical_uuid(match.group(1))
                return self.coordinator.create(token, user_id, campaign_id, body)

            match = PREMIUM_JOB.fullmatch(path)
            if match is not None:
                jid = canonical_uuid(match.group(1))
                if match.group(2) is None and method == "GET":
                    return self.coordinator.status(token, user_id, jid)
                if match.group(2) == "/download" and method == "GET":
                    return self._download(token, user_id, jid)
            return 404, {"error": "NOT_FOUND"}
        except AuthenticationError:
            return 401, {"error": "UNAUTHORIZED"}
        except SubscriptionDenied as exc:
            if exc.code == "RG002":
                return 429, {"error": "QUOTA_EXCEEDED"}
            return 402, {"error": "SUBSCRIPTION_REQUIRED"}
        except (ValueError, TypeError, AttributeError):
            return 400, {"error": "INVALID_REQUEST"}
        except (StorageUnavailable, KeyError):
            return 503, {"error": "SERVICE_UNAVAILABLE"}

    def _download(self, token, user_id, job_id):
        """Download is authorized from current DB and user JWT, never a URL input."""
        job = self.store.get_authenticated(token, job_id)
        if not isinstance(job, dict) or job.get("id") != job_id:
            return 404, {"error": "NOT_FOUND"}
        sid = canonical_uuid(job["shop_id"])
        if not self.users.member(token, user_id, sid):
            # 404 avoids disclosing tenant/job existence.
            return 404, {"error": "NOT_FOUND"}
        if job.get("status") != "SUCCEEDED" or not job.get("output_asset_id"):
            return 409, {"error": "OUTPUT_NOT_READY"}
        aid = canonical_uuid(job["output_asset_id"])
        asset = self.users.asset(token, sid, aid)
        if (not isinstance(asset, dict) or asset.get("id") != aid or
            asset.get("shop_id") != sid or
            asset.get("storage_bucket") != "retailgrowth-media" or
            asset.get("mime_type") != "video/mp4"):
            return 404, {"error": "OUTPUT_NOT_FOUND"}

        path = asset.get("object_path")
        prefix = f"{sid}/renders/{job_id}/"
        if not isinstance(path, str) or not path.startswith(prefix):
            return 404, {"error": "OUTPUT_NOT_FOUND"}
        if PRIVATE_FILE.fullmatch(path[len(prefix):]) is None:
            # Only the immutable lease-token path emitted by private importer.
            return 404, {"error": "OUTPUT_NOT_FOUND"}
        return 200, {"url": self.users.sign_download(token, sid, path)}
