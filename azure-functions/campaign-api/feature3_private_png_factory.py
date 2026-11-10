"""F3-08 server-owned private PNG reader construction (source-only).

The Azure route must remain disabled until a reviewed runtime binding supplies
a real Supabase JWT verifier, user-RLS TenantStore and live rights authority.
No client-supplied rights, service-role store or mock fallback is permitted.
"""
from __future__ import annotations

import re

from feature3_private_png_reader import Feature3RevocablePNGReader, PrivateGeneratedDownloadDenied

# Reject malformed JWT framing before any trusted verifier, RLS or Storage IO.
# This is only syntactic validation; cryptographic verification remains mandatory.
_JWT_SEGMENT = re.compile(r"[A-Za-z0-9_-]+")


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
                            _JWT_SEGMENT.fullmatch(part) is None for part in parts)):
                    raise PrivateGeneratedDownloadDenied("Private output unavailable")
                return reader.read(user_token=user_token, shop_id=expected_shop,
                                   job_id=expected_job)

        expected_shop, expected_job = shop_id, job_id
        return ScopedReader()
