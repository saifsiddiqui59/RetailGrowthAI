"""Service-role-only authoring PostgREST RPC client, isolated from browser JWT.

Requires the reviewed staged P2 authoring migration before rollout. All RPCs
have a fixed allowlist, no browser-provided SQL, no raw error-body leakage.
"""
from __future__ import annotations
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

from admin_store import backend_headers
from tenant_store import StorageUnavailable, SubscriptionDenied, canonical_uuid

_RPCS = {
    "p2_create_social_draft", "p2_approve_social_job", "p2_cancel_social_job",
    "p2_revise_social_draft",
}
class _NoRedirect(HTTPRedirectHandler):
    """Never forward server service-role headers to a redirected endpoint."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_ROW_FIELDS = ("id,shop_id,social_account_id,campaign_day_id,provider,"
               "caption,media_asset_id,scheduled_at,timezone,revision,status")


class SocialAuthoringRepository:
    def __init__(self, origin, service_key, *, transport=None):
        uri = urlsplit(origin)
        if (uri.scheme != "https" or not uri.hostname or uri.username or uri.password
                or uri.path not in ("", "/") or uri.query or uri.fragment
                or uri.port not in (None, 443)):
            raise ValueError("one HTTPS Supabase project origin is required")
        self.origin = origin.rstrip("/")
        self.headers = backend_headers(service_key)
        self.transport = transport or build_opener(_NoRedirect()).open

    def _send(self, request):
        try:
            with self.transport(request, timeout=8) as response:
                if response.geturl() != request.full_url:
                    raise StorageUnavailable("unexpected social backend redirect")
                body = response.read(65537)
                if len(body) > 65536:
                    raise StorageUnavailable("oversized social API response")
                return json.loads(body) if body else None
        except HTTPError as exc:
            code = None
            if exc.code in (400, 402, 409, 429):
                try:
                    code = json.loads(exc.read(1024)).get("code")
                except (AttributeError, TypeError, ValueError):
                    pass
            if code in ("RG001", "RG002"):
                raise SubscriptionDenied(code) from None
            if exc.code in (400, 401, 403, 404, 409):
                raise StorageUnavailable("social authoring database rejected request") from None
            raise StorageUnavailable("social authoring unavailable") from None
        except (URLError, OSError, UnicodeDecodeError, ValueError) as exc:
            raise StorageUnavailable("social authoring unavailable") from None

    def _rpc(self, name, payload):
        if name not in _RPCS:
            raise ValueError("unsupported RPC")
        req = Request(
            self.origin + "/rest/v1/rpc/" + name,
            headers={**self.headers, "Content-Type":"application/json",
                     "Accept":"application/json"},
            data=json.dumps(payload,separators=(",",":")).encode("utf-8"),
            method="POST",
        )
        return self._send(req)

    def create_draft(self, *, id, shop_id, actor, account_id, day_id, provider,
                     caption, media_id, scheduled_at, timezone_name, idempotency_key):
        return self._rpc("p2_create_social_draft", {
            "p_id": canonical_uuid(id), "p_shop":canonical_uuid(shop_id),
            "p_actor":canonical_uuid(actor), "p_day":canonical_uuid(day_id),
            "p_account":canonical_uuid(account_id), "p_provider":provider,
            "p_caption":caption, "p_media":canonical_uuid(media_id) if media_id else None,
            "p_scheduled_at":scheduled_at.isoformat(), "p_timezone":timezone_name,
            "p_idempotency":idempotency_key,
        })

    def read_job(self, shop_id, job_id):
        sid, jid = canonical_uuid(shop_id), canonical_uuid(job_id)
        req = Request(self.origin + "/rest/v1/social_publish_jobs?" + urlencode({
            "shop_id":"eq."+sid, "id":"eq."+jid,
            "select":_ROW_FIELDS, "limit":"1",
        }),headers={**self.headers,"Accept":"application/json"},method="GET")
        rows = self._send(req)
        if (not isinstance(rows, list) or len(rows) > 1 or
                any(not isinstance(row,dict) or row.get("id") != jid
                    or row.get("shop_id") != sid for row in rows)):
            raise StorageUnavailable("social job tenant read mismatch")
        return rows[0] if rows else None

    def revise(self, *, shop_id, job_id, actor, revision, caption,
               scheduled_at, timezone_name):
        return self._rpc("p2_revise_social_draft", {
            "p_shop":canonical_uuid(shop_id), "p_job":canonical_uuid(job_id),
            "p_actor":canonical_uuid(actor), "p_revision":revision,
            "p_caption":caption, "p_scheduled_at":scheduled_at.isoformat(),
            "p_timezone":timezone_name,
        })

    def approve(self, *, shop_id, job_id, actor, revision, digest,
                caption, scheduled_at, timezone_name, media_id):
        if not isinstance(digest, bytes) or len(digest) != 32:
            raise ValueError("invalid canonical content digest")
        return self._rpc("p2_approve_social_job", {
            "p_shop":canonical_uuid(shop_id), "p_job":canonical_uuid(job_id),
            "p_actor":canonical_uuid(actor), "p_revision":revision,
            "p_digest_hex":digest.hex(), "p_caption":caption,
            "p_scheduled_at":scheduled_at.isoformat(),
            "p_timezone":timezone_name,
            "p_media":canonical_uuid(media_id) if media_id else None,
        })

    def cancel(self, *, shop_id, job_id, actor, revision):
        return self._rpc("p2_cancel_social_job", {
            "p_shop":canonical_uuid(shop_id), "p_job":canonical_uuid(job_id),
            "p_actor":canonical_uuid(actor), "p_expected_revision":revision,
        })
