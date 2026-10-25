"""Source-only claim-locked storage facade for Instagram/YouTube upload adapters.

Never constructs provider HTTP clients or registers Azure worker triggers. A
separately approved worker must supply one active P2 DB claim, independently
verified media SHA/size, vetted account, AES-256-GCM key and same-shop scope.
Every provider side-effect stage is persisted using P2 service-role CAS RPCs
BEFORE calling external Meta/Google APIs. Ambiguous commits deny second send.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from admin_store import backend_headers
from social_dispatch import message_uuid
from social_oauth import TokenVault, OAuthDenied
from social_providers import youtube_upload_location, ProviderRejected
from tenant_store import canonical_uuid, StorageUnavailable

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_IG_ID = re.compile(r"[0-9]{1,32}\Z")
_SAFE_RPC = frozenset({
    "p2_begin_social_video_upload",
    "p2_advance_social_video_upload",
    "p2_save_youtube_session",
    "p2_video_container_for_claim",
    "p2_youtube_session_for_claim",
    "p2_begin_youtube_resume",
})


class VideoUploadStorageDenied(ValueError):
    """Generic safe error without tokens, session URLs or payloads."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _id(raw):
    try:
        return canonical_uuid(raw)
    except (ValueError, TypeError, AttributeError):
        raise VideoUploadStorageDenied("UPLOAD_SCOPE_INVALID") from None


class ScopedVideoUploadStorage:
    """Adapt existing media-upload interfaces to strict DB claim CAS.

    Caller has already completed authenticated member/plan/rights verification.
    This facade will additionally require the matching exact service-side
    claim for every state transition; it is NOT an authorization substitute.
    """

    def __init__(self, *, origin, service_key, shop_id, job_id,
                 claim_token, provider, social_account_id,
                 provider_account_id, source_sha256, media_size,
                 vault, enabled=False, transport=None):
        if enabled is not True:
            raise VideoUploadStorageDenied("UPLOAD_RELEASE_DISABLED")
        if not isinstance(vault, TokenVault):
            raise VideoUploadStorageDenied("UPLOAD_TOKEN_VAULT_REQUIRED")
        if provider not in ("instagram", "youtube"):
            raise VideoUploadStorageDenied("UPLOAD_PROVIDER_INVALID")
        try:
            if (not isinstance(origin,str) or origin!=origin.strip() or
                    any(ord(c)<=32 or ord(c)==127 for c in origin)):
                raise ValueError()
            parsed=urlsplit(origin)
            if (parsed.scheme!="https" or not parsed.hostname or
                    parsed.port not in (None,443)
                    or parsed.username or parsed.password
                    or parsed.query or parsed.fragment
                    or parsed.path not in ("","/")):
                raise ValueError()
            self.headers=backend_headers(service_key)
        except (TypeError,ValueError):
            raise VideoUploadStorageDenied("UPLOAD_DB_ORIGIN_INVALID") from None
        self.shop_id=_id(shop_id)
        self.job_id=message_uuid(job_id)
        self.claim_token=_id(claim_token)
        self.social_account_id=_id(social_account_id)
        if (not isinstance(provider_account_id,str) or not provider_account_id
                or len(provider_account_id)>200):
            raise VideoUploadStorageDenied("UPLOAD_ACCOUNT_INVALID")
        if provider=="instagram" and not _IG_ID.fullmatch(provider_account_id):
            raise VideoUploadStorageDenied("UPLOAD_ACCOUNT_INVALID")
        if (not isinstance(source_sha256,str) or
                _SHA.fullmatch(source_sha256) is None or
                type(media_size) is not int or
                not 0 < media_size <= 80*1024*1024):
            raise VideoUploadStorageDenied("UPLOAD_MEDIA_INVALID")
        self.url=origin.rstrip("/")
        self.provider=provider
        self.provider_account_id=provider_account_id
        self.source_sha256=source_sha256
        self.media_size=media_size
        self.vault=vault
        self.transport=transport or build_opener(_NoRedirect()).open

    def _rpc(self,name,params):
        if name not in _SAFE_RPC:
            raise VideoUploadStorageDenied("UPLOAD_RPC_FORBIDDEN")
        target=self.url+"/rest/v1/rpc/"+name
        req=Request(target,method="POST",
           headers={**self.headers,"Content-Type":"application/json",
                    "Accept":"application/json"},
           data=json.dumps(params,separators=(",",":")).encode("utf-8"))
        try:
            with self.transport(req,timeout=10) as response:
                if response.status!=200 or response.geturl()!=target:
                    raise StorageUnavailable("private media state unavailable")
                raw=response.read(16385)
                if len(raw)>16384:
                    raise StorageUnavailable("private media state oversized")
                return json.loads(raw) if raw else None
        except (HTTPError,URLError,OSError,UnicodeError,
                json.JSONDecodeError,TypeError):
            raise StorageUnavailable("private media state unavailable") from None

    def _scope(self,jid,account=None):
        if message_uuid(jid)!=self.job_id or (
                account is not None and account!=self.provider_account_id):
            raise VideoUploadStorageDenied("UPLOAD_SCOPE_INVALID")

    def _advance(self,from_stage,to_stage,remote=None):
        result=self._rpc("p2_advance_social_video_upload",{
            "p_job":self.job_id,"p_claim":self.claim_token,
            "p_from":from_stage,"p_to":to_stage,
            "p_remote":remote,"p_session_hex":None})
        return result is True

    def _begin(self):
        result=self._rpc("p2_begin_social_video_upload",{
            "p_job":self.job_id,"p_claim":self.claim_token,
            "p_sha":self.source_sha256,"p_size":self.media_size})
        return result is True

    # Instagram media container
    def begin_container(self,jid,account):
        self._scope(jid,account)
        if self.provider!="instagram":
            raise VideoUploadStorageDenied("UPLOAD_PROVIDER_INVALID")
        return self._begin()

    def save_container(self,jid,account,container):
        self._scope(jid,account)
        if self.provider!="instagram" or not isinstance(container,str) or (
                _IG_ID.fullmatch(container) is None):
            raise VideoUploadStorageDenied("UPLOAD_CONTAINER_INVALID")
        return self._advance("INITIATED","CONTAINER_KNOWN",container)

    def get_container(self,jid,account):
        self._scope(jid,account)
        if self.provider!="instagram":
            raise VideoUploadStorageDenied("UPLOAD_PROVIDER_INVALID")
        remote=self._rpc("p2_video_container_for_claim",{
            "p_job":self.job_id,"p_claim":self.claim_token})
        if not isinstance(remote,str) or _IG_ID.fullmatch(remote) is None:
            raise VideoUploadStorageDenied("UPLOAD_CONTAINER_NOT_CONFIRMED")
        return remote

    def record_publish_intent(self,jid,container):
        self._scope(jid)
        if self.provider!="instagram" or self.get_container(jid,self.provider_account_id)!=container:
            raise VideoUploadStorageDenied("UPLOAD_CONTAINER_MISMATCH")
        return self._advance("CONTAINER_KNOWN","PUBLISH_INTENT")

    def record_publish_receipt(self,jid,container,remote):
        self._scope(jid)
        if self.provider!="instagram" or self.get_container(jid,self.provider_account_id)!=container:
            raise VideoUploadStorageDenied("UPLOAD_CONTAINER_MISMATCH")
        if not isinstance(remote,str) or _IG_ID.fullmatch(remote) is None:
            raise VideoUploadStorageDenied("UPLOAD_REMOTE_ID_INVALID")
        return self._advance("PUBLISH_INTENT","PUBLISHED",remote)

    # Google YouTube resumable session
    def begin_upload(self,jid,size):
        self._scope(jid)
        if self.provider!="youtube" or type(size) is not int or size!=self.media_size:
            raise VideoUploadStorageDenied("UPLOAD_MEDIA_INVALID")
        return self._begin()

    def save_session(self,jid,session):
        self._scope(jid)
        if self.provider!="youtube":
            raise VideoUploadStorageDenied("UPLOAD_PROVIDER_INVALID")
        try:
            approved=youtube_upload_location(session)
            encrypted=self.vault.seal(shop_id=self.shop_id,provider="youtube",
                account_id=self.social_account_id,token=approved)
        except (ProviderRejected,OAuthDenied):
            raise VideoUploadStorageDenied("UPLOAD_SESSION_INVALID") from None
        return self._rpc("p2_save_youtube_session",{
            "p_job":self.job_id,"p_claim":self.claim_token,
            "p_cipher_hex":encrypted.hex(),
            "p_version":self.vault.version}) is True

    def get_session(self,jid):
        self._scope(jid)
        if self.provider!="youtube":
            raise VideoUploadStorageDenied("UPLOAD_PROVIDER_INVALID")
        raw=self._rpc("p2_youtube_session_for_claim",{
            "p_job":self.job_id,"p_claim":self.claim_token})
        if not isinstance(raw,dict) or set(raw)!={"ciphertext_hex","key_version"}:
            raise VideoUploadStorageDenied("UPLOAD_SESSION_NOT_CONFIRMED")
        hext=raw["ciphertext_hex"]
        if (type(raw["key_version"]) is not int or
                raw["key_version"]!=self.vault.version or
                not isinstance(hext,str) or len(hext)%2!=0 or
                not 80<=len(hext)<=16384 or
                re.fullmatch("[0-9a-f]+",hext) is None):
            raise VideoUploadStorageDenied("UPLOAD_SESSION_KEY_DENIED")
        try:
            session=self.vault.open(shop_id=self.shop_id,provider="youtube",
                account_id=self.social_account_id,ciphertext=bytes.fromhex(hext))
            return youtube_upload_location(session)
        except (ProviderRejected,OAuthDenied,ValueError):
            raise VideoUploadStorageDenied("UPLOAD_SESSION_DECRYPT_DENIED") from None

    def record_binary_intent(self,jid,size):
        self._scope(jid)
        if self.provider!="youtube" or type(size) is not int or size!=self.media_size:
            raise VideoUploadStorageDenied("UPLOAD_MEDIA_INVALID")
        return self._advance("SESSION_KNOWN","BINARY_INTENT")

    def record_resume_intent(self,jid,next_byte,size_bytes,source_sha256):
        """Persist one resume side effect BEFORE reissuing any binary bytes.

        Always fail closed on a previously durable or ambiguous intent.
        A service-only SQL CAS repeats current claim, consent, rights, quota,
        immutable finalized SHA and encrypted-session checks.
        """
        self._scope(jid)
        if (self.provider!="youtube"
                or type(next_byte) is not int or type(size_bytes) is not int
                or size_bytes!=self.media_size
                or not 0<=next_byte<size_bytes
                or source_sha256!=self.source_sha256):
            raise VideoUploadStorageDenied("UPLOAD_RESUME_SCOPE_DENIED")
        return self._rpc("p2_begin_youtube_resume",{
            "p_job":self.job_id,"p_claim":self.claim_token,
            "p_next_byte":next_byte,"p_size":size_bytes,
            "p_sha":self.source_sha256}) is True

    def record_upload_receipt(self,jid,remote):
        self._scope(jid)
        if (self.provider!="youtube" or not isinstance(remote,str)
                or re.fullmatch("[A-Za-z0-9_-]{11}",remote) is None):
            raise VideoUploadStorageDenied("UPLOAD_REMOTE_ID_INVALID")
        return self._advance("BINARY_INTENT","PUBLISHED",remote)
