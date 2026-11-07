"""F3-08 trusted private PNG reader composition (source-only, GPU-OFF).

The caller must supply a real current-rights authority. This module never
substitutes an approval fixture or a historical asset flag for that authority.
It does not register an Azure route or authorize deployment.
"""
from __future__ import annotations

from feature3_private_png_reader import Feature3RevocablePNGReader
from security import SupabaseJWTVerifier
from tenant_store import TenantStore, canonical_uuid


def build_private_png_reader_factory(*, origin, publishable_key,
                                     current_output_rights,
                                     verifier=None, tenant=None,
                                     transport=None):
    """Bind server-controlled JWT/RLS and rights dependencies, never request data.

    Production callers must supply a reviewed live rights provider; no
    default True or service-role access exists. Test doubles are only for
    isolated deterministic tests, not hosted acceptance.
    """
    if not callable(current_output_rights):
        raise ValueError("Reviewed live output-rights callback required")
    if verifier is not None and not callable(verifier):
        raise ValueError("JWT verifier must be callable")
    if tenant is not None and not all(
        callable(getattr(tenant, method, None))
        for method in ("member", "feature3_gpu_job", "feature3_generated_asset")
    ):
        raise ValueError("RLS tenant store required")

    # Even injected test dependencies must use an exact public project origin
    # and publishable key; the reader enforces both at construction.
    verified_jwt = verifier if verifier is not None else SupabaseJWTVerifier(origin)
    user_store = tenant if tenant is not None else TenantStore(origin, publishable_key)

    def factory(shop_id, job_id):
        # Fail before constructing the private reader on malformed route scope.
        canonical_uuid(shop_id)
        canonical_uuid(job_id)
        return Feature3RevocablePNGReader(
            tenant_store=user_store,
            verify_user_jwt=verified_jwt,
            current_output_rights=current_output_rights,
            transport=transport,
        )

    return factory
