"""F3-08 server-owned private PNG reader construction (source-only).

The Azure route must remain disabled until a reviewed runtime binding supplies
a real Supabase JWT verifier, user-RLS TenantStore and live rights authority.
No client-supplied rights, service-role store or mock fallback is permitted.
"""
from __future__ import annotations

import re
import base64
import json

from feature3_private_png_reader import Feature3RevocablePNGReader, PrivateGeneratedDownloadDenied

# Reject malformed JWT framing before any trusted verifier, RLS or Storage IO.
# Base64url segments with length modulo four == one cannot decode to bytes.
# This is only syntactic validation; cryptographic verification remains mandatory.
_JWT_SEGMENT = re.compile(r"[A-Za-z0-9_-]+")


def _canonical_jwt_signature(segment):
    """Reject ambiguous or empty JWS signature bytes before trusted IO.

    This checks wire encoding only. The server-owned verifier must still
    cryptographically authenticate the complete compact JWT.
    """
    try:
        raw = base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
        return (bool(raw) and
                base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") == segment)
    except (ValueError, TypeError, OverflowError):
        return False


def _safe_jwt_json(segment, *, header=False):
    """Reject ambiguous JWT JSON before auth or tenant IO.

    This is not JWT verification: the cryptographic verifier still checks
    signature, issuer, audience, expiry and user identity.
    """
    try:
        raw = base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
        if not 2 <= len(raw) <= (2048 if header else 8192):
            return False
        def unique_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate JWT JSON field")
                result[key] = value
            return result
        # Byte-bounded JSON can still exceed the parser recursion limit.
        # Fail closed rather than leaking a 500 response.
        def reject_nonfinite(value):
            raise ValueError("non-finite JWT JSON number")
        claims = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs,
                            parse_constant=reject_nonfinite)
        if type(claims) is not dict:
            return False
        # Enforce canonical unpadded base64url, not merely decodability.
        # Ambiguous encodings must not reach a verifier with different parsing.
        if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != segment:
            return False
        if not header:
            subject = claims.get("sub")
            # An opaque user identifier must not contain whitespace, control
            # characters or Unicode lookalikes. Signature verification remains
            # mandatory; this is only a pre-auth ambiguity fence.
            return (type(subject) is str and 1 <= len(subject) <= 256 and
                    all(33 <= ord(ch) <= 126 for ch in subject))
        return (type(claims.get("alg")) is str and
                claims["alg"] in ("HS256", "RS256", "ES256") and
                ("typ" not in claims or
                 (type(claims["typ"]) is str and claims["typ"] == "JWT")) and
                not any(key in claims for key in
                        ("crit", "jku", "jwk", "x5u", "x5c", "zip", "b64", "cty")))
    except (ValueError, UnicodeError, TypeError, OverflowError, RecursionError):
        return False


class TrustedPrivatePNGFactory:
    """Bind immutable backend dependencies; never accept authority from HTTP."""

    def __init__(self, *, tenant_store, verify_user_jwt, current_output_rights,
                 transport=None):
        if (not callable(verify_user_jwt) or
                not callable(current_output_rights) or
                not all(callable(getattr(tenant_store, method, None))
                        for method in ("member", "feature3_gpu_job",
                                       "feature3_generated_asset"))):
            raise ValueError("Verified user JWT, RLS store and current rights required")
        # Construct at configuration time to reject invalid origins/keys
        # before any HTTP request; never silently substitute a service role.
        self._reader = Feature3RevocablePNGReader(
            tenant_store=tenant_store,
            verify_user_jwt=verify_user_jwt,
            current_output_rights=current_output_rights,
            transport=transport,
        )

    def __call__(self, shop_id, job_id):
        # Canonical HTTP adapter validates these route UUIDs; independently
        # reject invalid scope if this factory is called from another path.
        from uuid import UUID
        if any(type(value) is not str for value in (shop_id, job_id)):
            raise ValueError("Invalid private output scope")
        try:
            if any(UUID(value).version != 4 or str(UUID(value)) != value
                   for value in (shop_id, job_id)):
                raise ValueError("Invalid private output scope")
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid private output scope") from exc

        reader = self._reader

        class ScopedReader:
            def read(self, *, user_token, shop_id: str, job_id: str):
                if (type(shop_id) is not str or type(job_id) is not str or
                        shop_id != expected_shop or job_id != expected_job):
                    raise PrivateGeneratedDownloadDenied("Private output unavailable")
                if (type(user_token) is not str or not 12 <= len(user_token) <= 8192 or
                        user_token.startswith(("sb_secret_", "sb_publishable_")) or
                        len(parts := user_token.split(".")) != 3 or
                        any(not 2 <= len(part) <= 4096 or
                            len(part) % 4 == 1 or
                            _JWT_SEGMENT.fullmatch(part) is None for part in parts) or
                        not _safe_jwt_json(parts[0], header=True) or
                        not _safe_jwt_json(parts[1]) or
                        not _canonical_jwt_signature(parts[2])):
                    raise PrivateGeneratedDownloadDenied("Private output unavailable")
                return reader.read(user_token=user_token, shop_id=expected_shop,
                                   job_id=expected_job)

        expected_shop, expected_job = shop_id, job_id
        return ScopedReader()
