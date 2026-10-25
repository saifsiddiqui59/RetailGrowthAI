"""Private, disabled-by-default claim loader for the Part2 video sender.

No browser route, Azure trigger, token logging or production enablement.
Only service-role RPCs can reveal an AES-GCM ciphertext bound to the exact
claimed social job; decryption is performed in this worker's tenant/account AAD.
Use only after independently approved hosted SQL / provider-release gate.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from admin_store import backend_headers
from social_dispatch import message_uuid
from social_oauth import TokenVault, OAuthDenied
from tenant_store import canonical_uuid, StorageUnavailable

_HEX = re.compile(r"[a-f0-9]{64}\Z")
_ENVELOPE = re.compile(r"[a-f0-9]{80,16384}\Z")
_SCOPES = {"instagram":"instagram_content_publish","youtube":"youtube.upload"}


class VideoClaimDenied(ValueError):
    """Fixed error messages: no bearer token, encrypted bytes or URLs."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _uuid(value):
    try:
        return canonical_uuid(value)
    except (ValueError, TypeError, AttributeError):
        raise VideoClaimDenied("VIDEO_CLAIM_INVALID_ID") from None


def _time(value):
    if not isinstance(value, str) or len(value) > 64:
        raise VideoClaimDenied("VIDEO_CLAIM_INVALID_TIME")
    try:
        t = datetime.fromisoformat(value.replace("Z","+00:00"))
        if t.tzinfo is None:
            raise ValueError()
        return t.astimezone(timezone.utc)
    except (ValueError,OverflowError):
        raise VideoClaimDenied("VIDEO_CLAIM_INVALID_TIME") from None


class ScopedVideoClaimAuthority:
    """One job+lease, server-owned, with real service-role SQL revalidation."""

    def __init__(self, *, origin, service_key, vault, job_id, claim_token,
                 transport=None, clock=None, enabled=False):
        if enabled is not True:
            raise VideoClaimDenied("VIDEO_CLAIM_RELEASE_DISABLED")
        if not isinstance(vault,TokenVault):
            raise VideoClaimDenied("VIDEO_CLAIM_VAULT_MISSING")
        try:
            if (not isinstance(origin,str) or origin!=origin.strip()
                or any(ord(c)<=32 or ord(c)==127 for c in origin)):
                raise ValueError()
            uri=urlsplit(origin)
            if (uri.scheme!="https" or not uri.hostname
                or uri.port not in (None,443)
                or uri.username or uri.password or uri.query or uri.fragment
                or uri.path not in ("","/")):
                raise ValueError()
            self.headers=backend_headers(service_key)
        except (ValueError,TypeError):
            raise VideoClaimDenied("VIDEO_CLAIM_CONFIG_DENIED") from None
        self.origin=origin.rstrip("/")
        self.job_id=message_uuid(job_id)
        self.claim_token=_uuid(claim_token)
        self.vault=vault
        self.transport=transport or build_opener(_NoRedirect()).open
        self.clock=clock or (lambda:datetime.now(timezone.utc))

    def _rpc(self,name,params):
        if name not in ("p2_video_send_claim_context","p2_video_send_claim_valid"):
            raise VideoClaimDenied("VIDEO_CLAIM_RPC_DENIED")
        url=self.origin+"/rest/v1/rpc/"+name
        req=Request(url,method="POST",
            data=json.dumps(params,separators=(",",":")).encode(),
            headers={**self.headers,"Content-Type":"application/json",
                     "Accept":"application/json"})
        try:
            with self.transport(req,timeout=10) as response:
                if response.status!=200 or response.geturl()!=url:
                    raise VideoClaimDenied("VIDEO_CLAIM_SERVICE_DENIED")
                data=response.read(16385)
                if len(data)>16384:
                    raise VideoClaimDenied("VIDEO_CLAIM_RESPONSE_DENIED")
                return json.loads(data) if data else None
        except VideoClaimDenied:
            raise
        except (HTTPError,URLError,OSError,UnicodeError,
                ValueError,TypeError,json.JSONDecodeError):
            raise VideoClaimDenied("VIDEO_CLAIM_SERVICE_UNAVAILABLE") from None

    def load(self,job_id,claim_token):
        if message_uuid(job_id)!=self.job_id or _uuid(claim_token)!=self.claim_token:
            raise VideoClaimDenied("VIDEO_CLAIM_SCOPE_DENIED")
        row=self._rpc("p2_video_send_claim_context",{
            "p_job":self.job_id,"p_claim":self.claim_token})
        if not isinstance(row,dict):
            raise VideoClaimDenied("VIDEO_CLAIM_NOT_ACTIVE")
        try:
            sid=_uuid(row["shop_id"])
            account=_uuid(row["social_account_id"])
            provider=row["provider"]
            if (row["job_id"]!=self.job_id or row["claim_token"]!=self.claim_token
                    or provider not in _SCOPES
                    or row["status"]!="SENDING"
                    or row["source"]!="PART1_RENDER_FINALIZED"
                    or row["storage_bucket"]!="retailgrowth-media"
                    or row["connection_status"]!="CONNECTED"
                    or _SCOPES[provider] not in row["granted_scopes"]
                    or type(row["revision"]) is not int or row["revision"]<1
                    or type(row["key_version"]) is not int
                    or row["key_version"]!=self.vault.version
                    or not isinstance(row["source_sha256"],str)
                    or not _HEX.fullmatch(row["source_sha256"])
                    or not isinstance(row["approved_digest"],str)
                    or not _HEX.fullmatch(row["approved_digest"])
                    or not isinstance(row["rights_evidence_sha256"],str)
                    or not _HEX.fullmatch(row["rights_evidence_sha256"])):
                raise ValueError()
            encrypted=row["access_ciphertext_hex"]
            if (not isinstance(encrypted,str) or
                    not _ENVELOPE.fullmatch(encrypted)
                    or len(encrypted)%2):
                raise ValueError()
            now=self.clock()
            if now.tzinfo is None or _time(row["credential_expires_at"])<=now+timedelta(seconds=90):
                raise VideoClaimDenied("VIDEO_CLAIM_ACCOUNT_REAUTH")
            scheduled=_time(row["scheduled_at"])
            expiration=_time(row["rights_expires_at"])
            if scheduled>now or expiration<=now+timedelta(hours=6):
                raise VideoClaimDenied("VIDEO_CLAIM_RIGHTS_DENIED")
            access=self.vault.open(
                shop_id=sid,provider=provider,account_id=account,
                ciphertext=bytes.fromhex(encrypted))
            # Never return private encrypted bytes or credential expiry to
            # user/browser; only the worker receives transient decrypted token.
            stripped={k:v for k,v in row.items()
                      if k not in ("access_ciphertext_hex","key_version",
                                   "credential_expires_at")}
            stripped["scheduled_at"]=scheduled
            stripped["rights_expires_at"]=expiration
            stripped["access_token"]=access
            return stripped
        except VideoClaimDenied:
            raise
        except (KeyError,ValueError,TypeError,AttributeError,OAuthDenied):
            raise VideoClaimDenied("VIDEO_CLAIM_MALFORMED") from None

    def allow(self,context):
        if (not isinstance(context,dict) or
                context.get("job_id")!=self.job_id or
                context.get("claim_token")!=self.claim_token or
                type(context.get("revision")) is not int or
                not isinstance(context.get("source_sha256"),str) or
                not _HEX.fullmatch(context["source_sha256"])):
            raise VideoClaimDenied("VIDEO_CLAIM_SCOPE_DENIED")
        result=self._rpc("p2_video_send_claim_valid",{
            "p_job":self.job_id,"p_claim":self.claim_token,
            "p_revision":context["revision"],
            "p_source_sha":context["source_sha256"]})
        return result is True
