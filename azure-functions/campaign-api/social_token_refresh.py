"""Server-only, claim-bound Google/approved LinkedIn credential refresh.

No live network client or Azure timer is wired here. A worker must hold a
valid active publish claim; token rotation is DB compare-and-swap, encrypted
with the existing shop/provider/account-specific AES-GCM authenticated data.
Meta Page tokens are intentionally excluded: business login/expiration must
be separately reviewed rather than guessing a supported refresh grant.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
import re

from social_dispatch import message_uuid
from social_oauth import TokenVault, OAuthDenied
from social_publish_policy import PublishDenied
from tenant_store import canonical_uuid

ENDPOINTS = {
    "youtube": "https://oauth2.googleapis.com/token",
    "linkedin": "https://www.linkedin.com/oauth/v2/accessToken",
}
PERMISSIONS = {
    "youtube": {"https://www.googleapis.com/auth/youtube.upload"},
    "linkedin": {"w_member_social"},
}


@dataclass(frozen=True)
class OAuthClient:
    client_id: str = field(repr=False)
    client_secret: str = field(repr=False)
    approved_refresh: bool = False

    def __post_init__(self):
        if (not isinstance(self.client_id,str) or not self.client_id
            or not isinstance(self.client_secret,str) or not self.client_secret):
            raise ValueError("missing confidential provider app")


class ClaimBoundTokenRefresher:
    def __init__(self, *, repository, vault, clients, transport, clock=None):
        if not isinstance(vault,TokenVault) or not callable(transport):
            raise ValueError("server vault and reviewed transport required")
        self.repository=repository
        self.vault=vault
        self.clients=clients
        self.transport=transport
        self.clock=clock or (lambda: datetime.now(timezone.utc))

    def refresh_job(self,job_id,claim_token):
        jid,lease=message_uuid(job_id),canonical_uuid(claim_token)
        raw=self.repository.refresh_context(jid,lease)
        if not isinstance(raw,dict):
            raise PublishDenied("REFRESH_CONTEXT_DENIED")
        try:
            sid=canonical_uuid(raw["shop_id"])
            aid=canonical_uuid(raw["account_id"])
            provider=raw["provider"]
            if provider not in ENDPOINTS or type(raw["key_version"]) is not int:
                raise ValueError()
            if raw["key_version"] != self.vault.version:
                raise PublishDenied("UNKNOWN_SOCIAL_KEY_VERSION")
            granted=raw["granted_scopes"]
            if not isinstance(granted,list) or not PERMISSIONS[provider].issubset(granted):
                raise PublishDenied("SOCIAL_SCOPE_REVOKED")
            client=self.clients.get(provider)
            if not isinstance(client,OAuthClient) or not client.approved_refresh:
                raise PublishDenied("PROVIDER_REFRESH_NOT_APPROVED")
            expiry=raw.get("expires_at")
            when=(datetime.fromisoformat(expiry.replace("Z","+00:00"))
                  if isinstance(expiry,str) else None)
            now=self.clock()
            if when is None or when.tzinfo is None or now.tzinfo is None:
                raise ValueError()
            if when>now+timedelta(minutes=5):
                return "TOKEN_STILL_VALID"
            access_cipher=bytes.fromhex(raw["access_ciphertext_hex"])
            refresh_cipher=bytes.fromhex(raw["refresh_ciphertext_hex"])
            refresh=self.vault.open(shop_id=sid,provider=provider,
                                     account_id=aid,ciphertext=refresh_cipher)
            # Avoid any provider-error data, access/refresh token in exceptions.
            try:
                result=self.transport(ENDPOINTS[provider], {
                    "grant_type":"refresh_token",
                    "refresh_token":refresh,
                    "client_id":client.client_id,
                    "client_secret":client.client_secret,
                })
            except Exception:
                raise PublishDenied("PROVIDER_REFRESH_FAILED") from None
            if not isinstance(result,dict):
                raise ValueError()
            token=result.get("access_token")
            seconds=result.get("expires_in")
            token_type=result.get("token_type","Bearer")
            if (not isinstance(token,str) or not 1<=len(token)<=8192
                or type(seconds) is not int or not 180<=seconds<=7776000
                or token_type.lower()!="bearer"):
                raise ValueError()
            if result.get("scope") is not None:
                new_scopes=str(result["scope"]).replace(","," ").split()
                if not PERMISSIONS[provider].issubset(new_scopes):
                    raise PublishDenied("SOCIAL_SCOPE_REVOKED")
            rotated=result.get("refresh_token")
            if rotated is not None and (not isinstance(rotated,str)
                                        or not 1<=len(rotated)<=8192):
                raise ValueError()
            new_access=self.vault.seal(shop_id=sid,provider=provider,
                        account_id=aid,token=token)
            new_refresh=(self.vault.seal(shop_id=sid,provider=provider,
                         account_id=aid,token=rotated) if rotated else None)
            committed=self.repository.rotate(
                jid,lease,expected_access_ciphertext=access_cipher,
                new_access_ciphertext=new_access,
                new_refresh_ciphertext=new_refresh,
                expires_at=now+timedelta(seconds=seconds),
                key_version=self.vault.version)
            if committed is not True:
                raise PublishDenied("REFRESH_RACED_OR_REVOKED")
            return "ROTATED"
        except PublishDenied:
            raise
        except (KeyError,TypeError,ValueError,AttributeError,OverflowError,OAuthDenied):
            raise PublishDenied("INVALID_REFRESH_CONTEXT") from None
