"""F3-08 trusted private PNG reader composition (source-only, GPU-OFF).

The caller must supply a real current-rights authority. This module never
substitutes an approval fixture or a historical asset flag for that authority.
It does not register an Azure route or authorize deployment.
"""
from __future__ import annotations

from feature3_private_png_reader import Feature3RevocablePNGReader, PrivateGeneratedDownloadDenied
from security import SupabaseJWTVerifier
from tenant_store import TenantStore, canonical_uuid
from feature3_private_png_tenant import VerifiedGeneratedAssetTenant


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

    # A mismatched injected tenant could read a different project while the
    # verifier validates tokens for the configured project. Never compose
    # cross-project credentials, even in tests or an accidental deployment.
    if tenant is not None and (
        type(origin) is not str or type(publishable_key) is not str or
        type(getattr(tenant, "origin", None)) is not str or
        type(getattr(tenant, "key", None)) is not str or
        tenant.origin != origin or tenant.key != publishable_key
    ):
        raise ValueError("Tenant store must match configured JWT project and public key")

    # Even injected test dependencies must use an exact public project origin
    # and publishable key; the reader enforces both at construction.
    verified_jwt = verifier if verifier is not None else SupabaseJWTVerifier(origin)
    user_store = tenant if tenant is not None else TenantStore(origin, publishable_key)

    def project_matches():
        return (type(getattr(user_store, "origin", None)) is str and
                type(getattr(user_store, "key", None)) is str and
                user_store.origin == origin and
                user_store.key == publishable_key)

    def factory(shop_id, job_id):
        # An injected store can be reconfigured after composition. Refuse
        # before any JWT, tenant or Storage access, including cached readers.
        if not project_matches():
            raise ValueError("Tenant store project changed after composition")
        # Fail before constructing the private reader on malformed route scope.
        scoped_shop = canonical_uuid(shop_id)
        scoped_job = canonical_uuid(job_id)
        # Bind each reader to its factory scope, even if a later caller
        # accidentally reuses the instance for another retailer or job.
        inner = Feature3RevocablePNGReader(
            tenant_store=VerifiedGeneratedAssetTenant(user_store),
            verify_user_jwt=verified_jwt,
            current_output_rights=current_output_rights,
            transport=transport,
        )

        class ScopedPrivatePNGReader:
            def read(self, *, user_token, shop_id, job_id):
                if (type(shop_id) is not str or type(job_id) is not str or
                        shop_id != scoped_shop or job_id != scoped_job):
                    from feature3_private_png_reader import PrivateGeneratedDownloadDenied
                    raise PrivateGeneratedDownloadDenied("Private output unavailable")
                if not project_matches():
                    raise PrivateGeneratedDownloadDenied("Private output unavailable")
                return inner.read(user_token=user_token, shop_id=shop_id, job_id=job_id)

        return ScopedPrivatePNGReader()

    return factory
