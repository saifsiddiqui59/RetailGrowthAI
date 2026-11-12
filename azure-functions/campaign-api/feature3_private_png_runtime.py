"""F3-08 server-owned private PNG reader composition (not a deployed route).

Only trusted application configuration may construct this factory. In
particular, neither request headers nor browser-supplied rights/identity
claims are accepted as dependencies. Hosted integration remains gated.
"""
from __future__ import annotations

from uuid import UUID

from feature3_current_output_rights import Feature3CurrentOutputRights
from feature3_private_png_reader import Feature3RevocablePNGReader
from security import SupabaseJWTVerifier
from tenant_store import TenantStore


def build_private_png_reader_factory(*, supabase_origin, publishable_key,
                                     authoritative_rights_read,
                                     expected_output_sha256=None,
                                     minimum_rights_revision=None,
                                     jwt_verifier=None, tenant_store=None):
    """Return a scoped reader factory from backend-owned dependencies only.

    A current authoritative rights provider is mandatory even for tests.
    Optional injected JWT/store dependencies are for isolated deterministic
    tests; production callers must supply trusted server-owned instances.
    """
    if not callable(authoritative_rights_read):
        raise ValueError("Trusted current output-rights provider required")
    if type(supabase_origin) is not str or type(publishable_key) is not str:
        raise ValueError("Trusted Supabase project configuration required")
    # Validate the actual project origin and public key before returning a
    # callable. No service-role key or HTTP client-provided credentials.
    store = tenant_store if tenant_store is not None else TenantStore(
        supabase_origin, publishable_key)
    verifier = jwt_verifier if jwt_verifier is not None else SupabaseJWTVerifier(
        supabase_origin)
    if not callable(verifier):
        raise ValueError("Trusted JWT verifier required")
    if (getattr(store, "origin", None) != supabase_origin.rstrip("/") or
            getattr(store, "key", None) != publishable_key):
        raise ValueError("Tenant store must match configured project")
    rights = Feature3CurrentOutputRights(
        authoritative_read=authoritative_rights_read,
        expected_output_sha256=expected_output_sha256,
        minimum_rights_revision=minimum_rights_revision,
    )
    # Reader constructor checks exact HTTPS Supabase origin, publishable
    # key and RLS read methods. Never silently fall back to a mock reader.
    def factory(shop_id, job_id):
        if type(shop_id) is not str or type(job_id) is not str:
            raise ValueError("Canonical scoped route IDs required")
        try:
            if any(UUID(value).version != 4 or str(UUID(value)) != value
                   for value in (shop_id, job_id)):
                raise ValueError("Canonical scoped route IDs required")
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError("Canonical scoped route IDs required") from exc
        return Feature3RevocablePNGReader(
            tenant_store=store,
            verify_user_jwt=verifier,
            current_output_rights=rights,
        )
    return factory
