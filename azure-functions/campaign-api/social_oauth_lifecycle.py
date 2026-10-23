"""Part 2 OAuth lifecycle service; never callable without verified owner membership.

Transport, state-store and credential-store are injected interfaces. OAuth code
exchange and provider account identity verification are NOT wired to production.
State-store.consume must be an atomic, one-use database compare-and-swap; token
persistence MUST be transactional with public account metadata. The service never
returns tokens, provider secrets, account ciphertext or PKCE verifier to browsers.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import uuid4

from security import AuthenticationError
from tenant_store import canonical_uuid
from social_oauth import OAuthDenied, new_oauth_state, verify_oauth_callback, exact_https_redirect


AUTH_HOSTS = {
    "instagram": "www.facebook.com",   # Facebook Login flow; confirm app permissions
    "facebook": "www.facebook.com",
    "linkedin": "www.linkedin.com",
    "youtube": "accounts.google.com",
}


@dataclass(frozen=True)
class LinkedIdentity:
    provider_account_id: str
    display_name: str
    granted_scopes: frozenset[str]
    access_token: str = field(repr=False)
    refresh_token: str | None = field(default=None, repr=False)
    expires_at: datetime | None = None


def validate_identity(identity, required_scopes):
    if not isinstance(identity, LinkedIdentity):
        raise OAuthDenied("unverified provider identity")
    if (not isinstance(identity.provider_account_id, str)
        or not re.fullmatch(r"[A-Za-z0-9:_-]{1,200}", identity.provider_account_id)
        or not isinstance(identity.display_name, str)
        or not 1 <= len(identity.display_name.strip()) <= 200
        or any(ord(c) < 32 for c in identity.display_name)
        or not isinstance(identity.granted_scopes, frozenset)
        or not required_scopes.issubset(identity.granted_scopes)
        or not isinstance(identity.access_token, str)
        or not 1 <= len(identity.access_token) <= 8192
        or (identity.refresh_token is not None and
            (not isinstance(identity.refresh_token, str) or
             not 1 <= len(identity.refresh_token) <= 8192))
        or (identity.expires_at is not None and identity.expires_at.tzinfo is None)):
        raise OAuthDenied("provider account or scopes failed verification")
    return identity


class OAuthLifecycle:
    """Owner-authenticated start, callback and local disconnect coordination.

    All DB repositories MUST reject service-side missing/wrong-shop identifiers.
    The callback is an authenticated POST from the same original user's session,
    NOT an unauthenticated redirect handler with a browser-stored refresh token.
    """

    def __init__(self, *, verify_user, owner_role, state_store, accounts,
                 vault, providers, clock=None):
        self.verify_user = verify_user
        self.owner_role = owner_role
        self.state_store = state_store
        self.accounts = accounts
        self.vault = vault
        self.providers = providers
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _owner(self, authorization, shop_id):
        if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
            raise AuthenticationError("signed-in user required")
        token = authorization[7:].strip()
        uid = canonical_uuid(self.verify_user(token))
        sid = canonical_uuid(shop_id)
        # Owner role, not merely writable EDITOR or VIEWER.
        if self.owner_role(token, uid, sid) != "OWNER":
            raise OAuthDenied("owner authorization required")
        return uid, sid

    def _provider(self, provider):
        if provider not in AUTH_HOSTS or provider not in self.providers:
            raise OAuthDenied("unconfigured provider")
        adapter = self.providers[provider]
        if not isinstance(adapter.required_scopes, frozenset) or not adapter.required_scopes:
            raise OAuthDenied("provider scopes are not reviewed")
        exact_https_redirect(adapter.redirect_uri, adapter.redirect_uri)
        return adapter

    def start(self, *, authorization, shop_id, provider):
        uid, sid = self._owner(authorization, shop_id)
        adapter = self._provider(provider)
        start = new_oauth_state(now=self.clock())
        verifier = self.vault.seal(
            shop_id=sid, provider=provider, account_id=uid, token=start.pkce_verifier)
        # Atomic unique state-digest insert, no OAuth state or verifier in logs.
        self.state_store.issue(
            digest=start.state_digest, shop_id=sid, user_id=uid,
            provider=provider, expires_at=start.expires_at,
            exact_redirect_uri=adapter.redirect_uri, verifier_ciphertext=verifier,
        )
        url = adapter.authorization_url(
            state=start.state, pkce_challenge=start.pkce_challenge,
            redirect_uri=adapter.redirect_uri)
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname != AUTH_HOSTS[provider]
            or parsed.username or parsed.password or parsed.fragment or
            not parsed.path.startswith("/") or len(url) > 4000):
            raise OAuthDenied("untrusted provider authorization endpoint")
        return {"authorization_url": url, "expires_at": start.expires_at.isoformat()}

    def complete(self, *, authorization, shop_id, provider, state, code):
        uid, sid = self._owner(authorization, shop_id)
        adapter = self._provider(provider)
        if not isinstance(state, str) or not 1 <= len(state) <= 256:
            raise OAuthDenied("invalid OAuth state")
        if not isinstance(code, str) or not 1 <= len(code) <= 4096:
            raise OAuthDenied("invalid OAuth authorization code")
        digest = hashlib.sha256(state.encode("utf-8")).digest()
        now = self.clock()
        # MUST consume atomically ONCE *before* exchanging the authorization code.
        # Return the pre-consume record; a second call must return None.
        previous = self.state_store.consume(
            digest=digest, shop_id=sid, user_id=uid, provider=provider,
            before=now)
        if not isinstance(previous, dict):
            raise OAuthDenied("missing or already consumed OAuth state")
        verify_oauth_callback(
            supplied_state=state, stored_state_digest=previous["state_digest"],
            expires_at=previous["expires_at"], consumed_at=previous["consumed_at"],
            expected_shop_id=previous["shop_id"], signed_in_shop_id=sid,
            expected_user_id=previous["user_id"], signed_in_user_id=uid, now=now)
        exact_https_redirect(previous["exact_redirect_uri"], adapter.redirect_uri)
        verifier = self.vault.open(
            shop_id=sid, provider=provider, account_id=uid,
            ciphertext=previous["verifier_ciphertext"])
        identity = validate_identity(
            adapter.exchange_code(code=code, verifier=verifier,
                                  redirect_uri=adapter.redirect_uri),
            adapter.required_scopes)
        account_id = str(uuid4())
        encrypted_access = self.vault.seal(
            shop_id=sid, provider=provider, account_id=account_id,
            token=identity.access_token)
        encrypted_refresh = (self.vault.seal(
            shop_id=sid, provider=provider, account_id=account_id,
            token=identity.refresh_token) if identity.refresh_token else None)
        # Implementor MUST store account+private credentials in one DB transaction.
        # A duplicate provider account must fail atomically, not change tenants.
        self.accounts.connect_atomic(
            id=account_id, shop_id=sid, connected_by=uid, provider=provider,
            provider_account_id=identity.provider_account_id,
            display_name=identity.display_name,
            granted_scopes=sorted(identity.granted_scopes),
            access_token_ciphertext=encrypted_access,
            refresh_token_ciphertext=encrypted_refresh,
            encryption_key_version=self.vault.version,
            expires_at=identity.expires_at,
        )
        return {"id": account_id, "provider": provider,
                "display_name": identity.display_name,
                "connection_status": "CONNECTED"}

    def disconnect(self, *, authorization, shop_id, account_id):
        uid, sid = self._owner(authorization, shop_id)
        aid = canonical_uuid(account_id)
        # Must atomically revoke local credentials and cancel pending social jobs.
        # Remote revocation is a separate provider-specific best-effort operation.
        if self.accounts.disconnect_atomic(shop_id=sid, account_id=aid, actor=uid) is not True:
            raise OAuthDenied("social account not found or not owned by business")
        return {"id": aid, "connection_status": "DISCONNECTED"}
