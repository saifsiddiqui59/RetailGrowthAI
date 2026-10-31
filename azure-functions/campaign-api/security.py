"""Supabase asymmetric JWT verification. No shared secret or unsigned fallback."""
from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlsplit
from uuid import UUID

import jwt
from jwt import PyJWKClient


class AuthenticationError(ValueError):
    pass


class SupabaseJWTVerifier:
    def __init__(self, supabase_url: str, *, jwks_client=None):
        url = urlsplit(supabase_url)
        if (url.scheme != "https" or not url.hostname or url.username or url.password
                or url.query or url.fragment or url.path not in ("", "/")):
            raise ValueError("SUPABASE_URL must be an HTTPS project origin")
        self.issuer = f"{supabase_url.rstrip('/')}/auth/v1"
        self.client = jwks_client or PyJWKClient(
            self.issuer + "/.well-known/jwks.json", cache_keys=False, cache_jwk_set=True, lifespan=300,
            timeout=5,
        )

    def __call__(self, token: str) -> str:
        if not isinstance(token, str) or not token or len(token) > 8192:
            raise AuthenticationError("missing or invalid bearer token")
        try:
            # The public key must be selected from this project's pinned JWKS.
            key = self.client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token, key.key, algorithms=["ES256", "RS256"],
                issuer=self.issuer, audience="authenticated",
                options={"require": ["exp", "iat", "sub", "aud", "iss"]},
                leeway=0,
            )
            if claims.get("role") != "authenticated" or claims.get("is_anonymous") is True:
                raise AuthenticationError("non-user token")
            return str(UUID(claims["sub"]))
        except (jwt.PyJWTError, KeyError, ValueError, TypeError) as exc:
            raise AuthenticationError("invalid authentication token") from exc


@lru_cache(maxsize=1)
def cached_supabase_verifier(supabase_url: str) -> SupabaseJWTVerifier:
    """Reuse the last HTTPS project's JWKS set across warm HTTP invocations.

    Cache the verifier, NEVER caller JWTs, decoded claims or permissions.
    Every request is still signature/issuer/audience/expiry checked and
    every downstream PostgREST operation still uses its original user JWT.
    The project JWKS set lives only up to 300s; per-kid key caching is OFF,
    so rotation/revocation is not silently pinned forever in a warm worker.
    The one-entry cache cannot retain multiple old project origins.
    """
    return SupabaseJWTVerifier(supabase_url)
