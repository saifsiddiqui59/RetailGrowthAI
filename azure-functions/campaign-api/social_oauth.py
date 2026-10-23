"""Part 2 OAuth primitives: encrypted server-side tokens and one-use state.

No OAuth redirect or provider token exchange is activated in this source-only
module. Public callbacks must separately validate the logged-in Supabase user,
shop membership, exact redirect URI, expiry and atomically consume stored state.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class OAuthDenied(ValueError):
    pass


@dataclass(frozen=True)
class OAuthStart:
    state: str = field(repr=False)
    state_digest: bytes = field(repr=False)
    pkce_verifier: str = field(repr=False)
    pkce_challenge: str
    expires_at: datetime


def new_oauth_state(*, now=None):
    issued = now or datetime.now(timezone.utc)
    if issued.tzinfo is None:
        raise OAuthDenied("naive clock")
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    return OAuthStart(state, hashlib.sha256(state.encode("ascii")).digest(),
                      verifier, challenge, issued + timedelta(minutes=10))


def verify_oauth_callback(*, supplied_state, stored_state_digest, expires_at,
                          consumed_at, expected_shop_id, signed_in_shop_id,
                          expected_user_id, signed_in_user_id, now=None):
    current = now or datetime.now(timezone.utc)
    try:
        same_shop = UUID(expected_shop_id) == UUID(signed_in_shop_id)
        same_user = UUID(expected_user_id) == UUID(signed_in_user_id)
    except (ValueError, AttributeError, TypeError):
        raise OAuthDenied("invalid callback binding") from None
    if (not same_shop or not same_user or consumed_at is not None
            or expires_at.tzinfo is None or current >= expires_at
            or not isinstance(supplied_state, str) or len(supplied_state) > 256
            or not isinstance(stored_state_digest, bytes)
            or not hmac.compare_digest(
                hashlib.sha256(supplied_state.encode("utf-8")).digest(),
                stored_state_digest,
            )):
        raise OAuthDenied("invalid or replayed OAuth callback")
    # Caller's database transaction must consume the state with compare-and-swap.
    return True


def exact_https_redirect(uri, configured_uri):
    a, b = urlsplit(uri), urlsplit(configured_uri)
    if (a.scheme != "https" or a.username or a.password or a.fragment or
        a != b or not a.netloc):
        raise OAuthDenied("unapproved OAuth redirect URI")
    return uri


class TokenVault:
    """AES-256-GCM. Use isolated server env key; ciphertext is not public API data."""
    def __init__(self, key: bytes, version: int):
        if not isinstance(key, bytes) or len(key) != 32 or not isinstance(version, int) or version < 1:
            raise OAuthDenied("invalid backend encryption key configuration")
        self._aead = AESGCM(key)
        self.version = version

    def _aad(self, shop_id, provider, account_id):
        if provider not in ("instagram", "facebook", "linkedin", "youtube"):
            raise OAuthDenied("invalid provider")
        try:
            shop = str(UUID(shop_id))
            account = str(UUID(account_id))
        except (ValueError, TypeError, AttributeError):
            raise OAuthDenied("invalid credential tenant binding") from None
        return f"retailgrowthai:p2:v{self.version}:{shop}:{provider}:{account}".encode()

    def seal(self, *, shop_id, provider, account_id, token):
        if not isinstance(token, str) or not token or len(token) > 8192:
            raise OAuthDenied("invalid provider token")
        nonce = secrets.token_bytes(12)
        return nonce + self._aead.encrypt(
            nonce, token.encode("utf-8"),
            self._aad(shop_id, provider, account_id),
        )

    def open(self, *, shop_id, provider, account_id, ciphertext):
        if not isinstance(ciphertext, bytes) or len(ciphertext) < 40:
            raise OAuthDenied("invalid encrypted credential")
        try:
            return self._aead.decrypt(ciphertext[:12], ciphertext[12:],
                                      self._aad(shop_id, provider, account_id)).decode("utf-8")
        except Exception as exc:
            raise OAuthDenied("credential decryption or tenant binding failed") from exc
