"""Private Part 2 worker claim RPCs and server-authoritative decrypting context.

Not registered with any Azure trigger. Requires staged P2 claim-context SQL,
an authorized service-role backend, a 32-byte secret AES-GCM key, and an
independently approved worker release. No browser accepts this module's data.
"""
from __future__ import annotations

import base64
import json
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from admin_store import backend_headers
from social_dispatch import message_uuid
from social_oauth import TokenVault, OAuthDenied
from social_publish_policy import PublishDenied
from tenant_store import StorageUnavailable, canonical_uuid

_RPCS = frozenset({
    "p2_claim_social_text_publish", "p2_social_claim_context",
    "p2_mark_social_inflight", "p2_finish_social_publish",
    "p2_social_refresh_context", "p2_rotate_social_access",
    "p2_record_social_poison",
})
_REQUIRED_SCOPES = {
    "facebook": frozenset({"pages_manage_posts"}),
    "linkedin": frozenset({"w_member_social"}),
}
_SAFE_ERROR = re.compile(r"[A-Z][A-Z0-9_]{0,63}\Z")
_SAFE_HEX = re.compile(r"[0-9a-f]{80,16384}\Z")


class _NeverRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _aware(value):
    if not isinstance(value, str) or len(value) > 64:
        raise PublishDenied("INVALID_SERVER_TIMESTAMP")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise PublishDenied("INVALID_SERVER_TIMESTAMP") from None
    if dt.tzinfo is None:
        raise PublishDenied("INVALID_SERVER_TIMESTAMP")
    return dt


class SocialPublishRpcRepository:
    """Only service-role calls; private token is revealed after claim and AAD check.

    This instance must live solely inside a guarded queue worker. Its returned
    context contains a decrypted token and must NEVER be logged or serialized.
    """
    def __init__(self, origin, backend_secret, vault, *, transport=None,
                 clock=None):
        uri = urlsplit(origin)
        if (uri.scheme != "https" or not uri.hostname or uri.username
                or uri.password or uri.query or uri.fragment
                or uri.path not in ("", "/") or uri.port not in (None, 443)
                or not isinstance(vault, TokenVault)):
            raise ValueError("invalid social worker service configuration")
        self.origin = origin.rstrip("/")
        self.headers = backend_headers(backend_secret)
        self.vault = vault
        self.transport = transport or build_opener(_NeverRedirect()).open
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _rpc(self, name, payload):
        if name not in _RPCS:
            raise ValueError("unapproved worker RPC")
        target = self.origin + "/rest/v1/rpc/" + name
        req = Request(target, method="POST",
            headers={**self.headers, "Content-Type": "application/json",
                     "Accept": "application/json"},
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        try:
            with self.transport(req, timeout=10) as response:
                if response.geturl() != target:
                    raise StorageUnavailable("unexpected service RPC redirect")
                content = response.read(65537)
                if len(content) > 65536:
                    raise StorageUnavailable("oversized worker response")
                return json.loads(content) if content else None
        except (HTTPError, URLError, OSError, UnicodeError,
                json.JSONDecodeError):
            raise StorageUnavailable("private social database unavailable") from None

    def claim(self, job_id):
        jid = message_uuid(job_id)
        result = self._rpc("p2_claim_social_text_publish", {"p_job": jid})
        if result is None:
            return None
        if (not isinstance(result, dict) or set(result) != {"job_id", "claim_token"}
                or result["job_id"] != jid):
            raise StorageUnavailable("malformed private claim")
        try:
            token = canonical_uuid(result["claim_token"])
        except (TypeError, ValueError):
            raise StorageUnavailable("malformed private claim") from None
        return {"job_id": jid, "claim_token": token}

    def load_context(self, job_id, claim_token):
        jid, lease = message_uuid(job_id), canonical_uuid(claim_token)
        data = self._rpc("p2_social_claim_context",
                         {"p_job": jid, "p_claim": lease})
        if data is None:
            raise PublishDenied("PRIVATE_PUBLISH_CONTEXT_DENIED")
        if not isinstance(data, dict) or set(data) != {
            "shop_id", "job", "account", "membership",
            "entitlement", "credential"}:
            raise PublishDenied("MALFORMED_PRIVATE_CONTEXT")
        try:
            sid = canonical_uuid(data["shop_id"])
            job, account = data["job"], data["account"]
            membership, ent = data["membership"], data["entitlement"]
            cred = data["credential"]
            if any(not isinstance(item, dict) for item in
                   (job, account, membership, ent, cred)):
                raise ValueError()
            aid = canonical_uuid(account["id"])
            if (job["id"] != jid or job["shop_id"] != sid
                    or job["social_account_id"] != aid
                    or account["shop_id"] != sid
                    or membership["shop_id"] != sid
                    or ent["shop_id"] != sid
                    or job["provider"] != account["provider"]
                    or job["status"] not in ("APPROVED", "QUEUED", "RETRYABLE")
                    or job.get("quota_reserved") is not True
                    or membership["active"] is not True
                    or membership["user_id"] != job["approved_by"]
                    or membership["role"] not in ("OWNER", "EDITOR")
                    or account["connection_status"] != "CONNECTED"):
                raise ValueError()
            provider = job["provider"]
            if provider not in _REQUIRED_SCOPES or job.get("media_asset_id") is not None:
                raise ValueError()
            required = _REQUIRED_SCOPES[provider]
            granted = account["granted_scopes"]
            if (not isinstance(granted, list)
                    or not all(isinstance(x, str) for x in granted)
                    or not required.issubset(granted)):
                raise ValueError()
            now = self.clock()
            if now.tzinfo is None:
                raise ValueError()
            exp = _aware(cred["expires_at"])
            if exp <= now + timedelta(seconds=90):
                raise PublishDenied("SOCIAL_ACCOUNT_REAUTH_REQUIRED")
            if type(cred["key_version"]) is not int or cred["key_version"] != self.vault.version:
                raise PublishDenied("UNKNOWN_SOCIAL_KEY_VERSION")
            ciphertext_hex = cred["access_ciphertext_hex"]
            if (not isinstance(ciphertext_hex, str)
                    or not _SAFE_HEX.fullmatch(ciphertext_hex)
                    or len(ciphertext_hex) % 2 != 0):
                raise ValueError()
            cipher = bytes.fromhex(ciphertext_hex)
            access = self.vault.open(shop_id=sid, provider=provider,
                                     account_id=aid, ciphertext=cipher)
            approved = job["approved_content_sha256"]
            if (not isinstance(approved, str) or
                    re.fullmatch(r"[0-9a-f]{64}", approved) is None):
                raise ValueError()
            normalized_job = {
                **job,
                "campaign_day_id": canonical_uuid(job["campaign_day_id"]),
                "approved_content_sha256": bytes.fromhex(approved),
                "approved_at": _aware(job["approved_at"]),
                "scheduled_at": _aware(job["scheduled_at"]),
            }
            if (type(normalized_job.get("revision")) is not int or
                    normalized_job["revision"] < 1):
                raise ValueError()
            normalized_ent = {**ent, "valid_until": _aware(ent["valid_until"])}
            if normalized_ent["valid_until"] <= now:
                raise ValueError()
            return {
                "job": normalized_job, "shop_id": sid, "account": account,
                "membership": membership, "entitlement": normalized_ent,
                "required_scopes": required, "media": None,
                # Never pass to browser / logs / check_approval kwargs.
                "provider_access_token": access,
            }
        except PublishDenied:
            raise
        except (KeyError, TypeError, ValueError, OAuthDenied):
            raise PublishDenied("MALFORMED_PRIVATE_CONTEXT") from None

    def refresh_context(self, job_id, claim_token):
        """Claim-bound read: ciphertext only, returned to backend refresher."""
        raw=self._rpc("p2_social_refresh_context",{
            "p_job":message_uuid(job_id),"p_claim":canonical_uuid(claim_token)})
        if raw is not None and not isinstance(raw,dict):
            raise StorageUnavailable("malformed private refresh context")
        return raw

    def rotate(self, job_id, claim_token, *, expected_access_ciphertext,
               new_access_ciphertext, new_refresh_ciphertext,
               expires_at, key_version):
        """Strict DB CAS; credentials never leave server except encrypted."""
        for item in (expected_access_ciphertext,new_access_ciphertext):
            if not isinstance(item,bytes) or not 40<=len(item)<=8192:
                raise ValueError("invalid private token envelope")
        if (new_refresh_ciphertext is not None
            and (not isinstance(new_refresh_ciphertext,bytes)
                 or not 40<=len(new_refresh_ciphertext)<=8192)):
            raise ValueError("invalid private refresh envelope")
        if not isinstance(expires_at,datetime) or expires_at.tzinfo is None:
            raise ValueError("invalid access expiry")
        raw=self._rpc("p2_rotate_social_access",{
            "p_job":message_uuid(job_id),"p_claim":canonical_uuid(claim_token),
            "p_expected_access_hex":expected_access_ciphertext.hex(),
            "p_new_access_hex":new_access_ciphertext.hex(),
            "p_new_refresh_hex":new_refresh_ciphertext.hex()
                if new_refresh_ciphertext else None,
            "p_expires_at":expires_at.isoformat(),
            "p_key_version":key_version,
        })
        if raw not in (True,False):
            raise StorageUnavailable("unconfirmed private refresh receipt")
        return raw

    def mark_external_inflight(self, job_id, claim_token):
        result = self._rpc("p2_mark_social_inflight", {
            "p_job": message_uuid(job_id), "p_claim": canonical_uuid(claim_token)})
        return result is True

    def _finish(self, job_id, claim_token, outcome, error_code=None, remote_id=None):
        if not isinstance(outcome, str) or outcome not in {
            "FAILED", "RETRYABLE", "RECONCILE", "PUBLISHED", "PROCESSING"}:
            raise ValueError("invalid publish outcome")
        if error_code is not None and (not isinstance(error_code, str)
                                       or not _SAFE_ERROR.fullmatch(error_code)):
            raise ValueError("invalid sanitized publish code")
        result = self._rpc("p2_finish_social_publish", {
            "p_job": message_uuid(job_id),
            "p_claim": canonical_uuid(claim_token),
            "p_outcome": outcome, "p_error": error_code, "p_remote": remote_id,
        })
        if result is not True:
            raise StorageUnavailable("publish receipt was not durably confirmed")

    def fail_claim(self, job_id, claim_token, code):
        self._finish(job_id, claim_token, "FAILED", code)

    def retry_no_send(self, job_id, claim_token, code):
        self._finish(job_id, claim_token, "RETRYABLE", code)

    def require_reconciliation(self, job_id, claim_token, code):
        self._finish(job_id, claim_token, "RECONCILE", code)

    def record_receipt(self, job_id, claim_token, remote_id, status):
        self._finish(job_id, claim_token, status, remote_id=remote_id)

    def record_poison(self, job_id):
        """Mandatory durable receipt; if DB is down leave Azure poison queued."""
        result = self._rpc("p2_record_social_poison", {
            "p_job": message_uuid(job_id)})
        if result is not True:
            raise StorageUnavailable("social poison receipt not confirmed")
        return True


def build_social_publish_repository(config=None, *, transport=None, clock=None):
    """An explicit worker-only release switch; no timer/queue registration here."""
    env = os.environ if config is None else config
    if (env.get("RETAIL_PART2_SOCIAL_ENABLED") != "true" or
            env.get("RETAIL_PART2_PUBLISH_WORKER_ENABLED") != "true"):
        raise ValueError("social publisher worker disabled")
    key = base64.b64decode(env["RETAIL_PART2_VAULT_KEY_B64"], validate=True)
    vault = TokenVault(key, int(env["RETAIL_PART2_VAULT_VERSION"]))
    return SocialPublishRpcRepository(
        env["RETAIL_SUPABASE_URL"], env["RETAIL_SUPABASE_SERVICE_ROLE_KEY"],
        vault, transport=transport, clock=clock)
