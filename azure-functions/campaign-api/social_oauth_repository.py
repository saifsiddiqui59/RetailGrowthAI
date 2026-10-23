"""Service-role-only Part 2 OAuth RPC adapter; no browser or provider exposure.

Requires reviewed, staged Part 2 SQL to be migrated under a separate owner
approval before this adapter can be enabled. All calls use POST body only,
HTTPS, fixed RPC allowlist and sanitized errors (never print credentials).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from admin_store import backend_headers
from social_oauth import OAuthDenied
from tenant_store import canonical_uuid, StorageUnavailable

_ALLOWED={
    "p2_issue_oauth_state",
    "p2_consume_oauth_state",
    "p2_connect_social_account",
    "p2_disconnect_social_account",
}


class SocialOAuthRpcRepository:
    def __init__(self, origin, backend_secret, transport=None):
        p=urlsplit(origin)
        if (p.scheme!="https" or not p.hostname or p.username or p.password
            or p.query or p.fragment or p.path not in ("", "/")):
            raise ValueError("Supabase OAuth repository requires one HTTPS project origin")
        self.origin=origin.rstrip("/")
        self.headers=backend_headers(backend_secret)
        self.transport=transport or urlopen

    def _post(self, rpc, payload):
        if rpc not in _ALLOWED:raise ValueError("unsupported social OAuth RPC")
        req=Request(self.origin+"/rest/v1/rpc/"+rpc,method="POST",
            headers={**self.headers,"Content-Type":"application/json",
                     "Accept":"application/json"},
            data=json.dumps(payload, separators=(",",":")).encode("utf-8"))
        try:
            with self.transport(req,timeout=10) as response:
                raw=response.read()
                return json.loads(raw.decode("utf-8")) if raw else None
        except HTTPError as exc:
            # Never attach PostgREST response body or backend secret to errors.
            if exc.code in (400,401,403,404,409):
                raise OAuthDenied("OAuth data operation not authorized or unavailable") from None
            raise StorageUnavailable("private OAuth database request failed") from None
        except (URLError,OSError,UnicodeDecodeError,json.JSONDecodeError) as exc:
            raise StorageUnavailable("private OAuth database request failed") from None

    @staticmethod
    def _hex(value,min_bytes):
        if not isinstance(value,bytes) or len(value)<min_bytes or len(value)>8192:
            raise OAuthDenied("invalid private OAuth ciphertext or digest")
        return value.hex()

    def issue(self,*,digest,shop_id,user_id,provider,expires_at,
              exact_redirect_uri,verifier_ciphertext):
        if expires_at.tzinfo is None or expires_at<=datetime.now(timezone.utc):
            raise OAuthDenied("expired OAuth initiation")
        result=self._post("p2_issue_oauth_state",{
            "p_digest_hex":self._hex(digest,32),
            "p_shop":canonical_uuid(shop_id),"p_actor":canonical_uuid(user_id),
            "p_provider":provider,
            "p_verifier_hex":self._hex(verifier_ciphertext,40),
            "p_redirect":exact_redirect_uri,
        })
        if result is not True:raise StorageUnavailable("OAuth state persistence not confirmed")

    def consume(self,*,digest,shop_id,user_id,provider,before):
        if not isinstance(before,datetime) or before.tzinfo is None:
            raise OAuthDenied("invalid state check clock")
        rows=self._post("p2_consume_oauth_state",{
            "p_digest_hex":self._hex(digest,32),
            "p_shop":canonical_uuid(shop_id),"p_actor":canonical_uuid(user_id),
            "p_provider":provider,
        })
        if rows is None:return None
        if not isinstance(rows,dict):
            raise StorageUnavailable("malformed OAuth state")
        try:
            expires=datetime.fromisoformat(rows["expires_at"].replace("Z","+00:00"))
            state_digest=bytes.fromhex(rows["state_digest"])
            verifier=bytes.fromhex(rows["verifier_ciphertext"])
            if (state_digest!=digest or rows["shop_id"]!=shop_id or
                rows["user_id"]!=user_id or rows["provider"]!=provider
                or rows["consumed_at"] is not None or expires.tzinfo is None
                or len(verifier)<40):
                raise ValueError("invalid server state")
            return {
                "state_digest":state_digest,"shop_id":shop_id,"user_id":user_id,
                "expires_at":expires,"consumed_at":None,
                "exact_redirect_uri":rows["exact_redirect_uri"],
                "verifier_ciphertext":verifier,
            }
        except (KeyError,ValueError,TypeError,AttributeError) as exc:
            raise StorageUnavailable("malformed OAuth state returned") from None

    def connect_atomic(self,*,id,shop_id,connected_by,provider,
                       provider_account_id,display_name,granted_scopes,
                       access_token_ciphertext,refresh_token_ciphertext,
                       encryption_key_version,expires_at):
        payload={
            "p_id":canonical_uuid(id),"p_shop":canonical_uuid(shop_id),
            "p_actor":canonical_uuid(connected_by),"p_provider":provider,
            "p_provider_account":provider_account_id,"p_name":display_name,
            "p_scopes":granted_scopes,
            "p_access_hex":self._hex(access_token_ciphertext,40),
            "p_refresh_hex":self._hex(refresh_token_ciphertext,40) if refresh_token_ciphertext else None,
            "p_key_version":encryption_key_version,
            "p_expires_at":expires_at.isoformat() if expires_at else None,
        }
        if self._post("p2_connect_social_account",payload) is not True:
            raise StorageUnavailable("OAuth account write not confirmed")

    def disconnect_atomic(self,*,shop_id,account_id,actor):
        result=self._post("p2_disconnect_social_account",{
            "p_shop":canonical_uuid(shop_id),
            "p_id":canonical_uuid(account_id),"p_actor":canonical_uuid(actor),
        })
        if result not in (True,False):
            raise StorageUnavailable("OAuth disconnect not confirmed")
        return result
