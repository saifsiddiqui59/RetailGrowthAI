"""Source-only P2 Instagram durable container receipt loader.

The returned ID is ONLY an existing Meta *container* receipt for a private,
active job lease; it is never proof that media_publish completed or a reason
to repeat the remote POST. Reads the staged service-role-only
p2_video_container_for_claim RPC (191600); it is not an Azure route.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from admin_store import backend_headers
from social_dispatch import message_uuid
from tenant_store import canonical_uuid

_META_ID = re.compile(r"[0-9]{1,32}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")


class InstagramReceiptDenied(ValueError):
    """Fixed safe codes; never expose OAuth tokens, paths or private IDs."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _uuid(value):
    try:
        return canonical_uuid(value)
    except (ValueError, TypeError, AttributeError):
        raise InstagramReceiptDenied("IG_RECEIPT_SCOPE_DENIED") from None


class ScopedInstagramReceiptLoader:
    """Load existing container under current DB claim and immutable revision.

    `claims` must be the real ScopedVideoClaimAuthority in a service worker.
    No bearer/token is derived from the browser or this repository. A caller
    must additionally run independent account-bound FINAL post verification.
    """

    def __init__(self, *, origin, service_key, claims,
                 job_id, claim_token, enabled=False, transport=None):
        if enabled is not True or claims is None:
            raise InstagramReceiptDenied("IG_RECEIPT_RELEASE_DISABLED")
        try:
            if (not isinstance(origin, str) or origin != origin.strip()
                    or any(ord(c) <= 32 or ord(c) == 127 for c in origin)):
                raise ValueError()
            parsed = urlsplit(origin)
            if (parsed.scheme != "https" or not parsed.hostname
                    or parsed.port not in (None, 443)
                    or parsed.username or parsed.password or parsed.query
                    or parsed.fragment or parsed.path not in ("", "/")):
                raise ValueError()
            headers = backend_headers(service_key)
            job = message_uuid(job_id)
            lease = _uuid(claim_token)
        except (ValueError, TypeError, AttributeError):
            raise InstagramReceiptDenied("IG_RECEIPT_CONFIG_DENIED") from None
        self.url = origin.rstrip("/") + "/rest/v1/rpc/p2_video_container_for_claim"
        self.headers = headers
        self.claims = claims
        self.job = job
        self.lease = lease
        self.transport = transport or build_opener(_NoRedirect()).open

    def load(self, job_id, claim_token):
        try:
            job, lease = message_uuid(job_id), _uuid(claim_token)
            if job != self.job or lease != self.lease:
                raise ValueError()
            context = self.claims.load(job, lease)
            if (not isinstance(context, dict)
                    or context.get("job_id") != job
                    or context.get("claim_token") != lease
                    or context.get("provider") != "instagram"
                    or context.get("status") != "SENDING"
                    or context.get("connection_status") != "CONNECTED"
                    or "instagram_content_publish" not in context.get("granted_scopes", [])
                    or type(context.get("revision")) is not int
                    or context["revision"] < 1
                    or not isinstance(context.get("source_sha256"), str)
                    or _SHA.fullmatch(context["source_sha256"]) is None):
                raise ValueError()
            shop = _uuid(context["shop_id"])
            account = _uuid(context["social_account_id"])
            if self.claims.allow(context) is not True:
                raise ValueError()
        except Exception:
            raise InstagramReceiptDenied("IG_RECEIPT_SCOPE_DENIED") from None

        request = Request(
            self.url, method="POST",
            data=json.dumps({"p_job": job, "p_claim": lease},
                            separators=(",", ":")).encode(),
            headers={**self.headers, "Content-Type": "application/json",
                     "Accept": "application/json"},
        )
        try:
            with self.transport(request, timeout=10) as response:
                if response.status != 200 or response.geturl() != self.url:
                    raise ValueError()
                raw = response.read(129)
                if len(raw) > 128:
                    raise ValueError()
                remote = json.loads(raw)
            if not isinstance(remote, str) or _META_ID.fullmatch(remote) is None:
                raise ValueError()
            if self.claims.allow(context) is not True:
                raise InstagramReceiptDenied("IG_RECEIPT_CLAIM_REVOKED")
        except InstagramReceiptDenied:
            raise
        except (HTTPError, URLError, OSError, UnicodeError, ValueError,
                TypeError, json.JSONDecodeError):
            raise InstagramReceiptDenied("IG_RECEIPT_REMOTE_UNCERTAIN") from None

        # All matching record fields are obtained from the service-owned
        # current claim; the DB RPC returns a container only when the same
        # claim, shop, revision and account still own a durable container.
        return {
            "shop_id": shop, "job_id": job, "claim_token": lease,
            "provider": "instagram", "social_account_id": account,
            "revision": context["revision"],
            "source_sha256": context["source_sha256"],
            "receipt_state": "REMOTE_ID_KNOWN",
            "remote_id": remote,
        }
