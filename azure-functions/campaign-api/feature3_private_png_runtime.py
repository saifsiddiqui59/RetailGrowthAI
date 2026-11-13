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
    # Do not permit equality-overloaded objects or string subclasses to
    # impersonate the configured project or public key at this trust boundary.
    store_origin = getattr(store, "origin", None)
    store_key = getattr(store, "key", None)
    if (type(store_origin) is not str or
            type(store_key) is not str or
            store_origin != supabase_origin.rstrip("/") or
            store_key != publishable_key):
        raise ValueError("Tenant store must match configured project")
    rights = Feature3CurrentOutputRights(
        authoritative_read=authoritative_rights_read,
        expected_output_sha256=expected_output_sha256,
        minimum_rights_revision=minimum_rights_revision,
    )
    def project_matches():
        """Fail closed on unreadable or rotated injected project credentials."""
        try:
            first_origin = store.origin
            first_key = store.key
            second_origin = store.origin
            second_key = store.key
            last_origin = store.origin
            last_key = store.key
            post_key_origin = store.origin
        except Exception:
            return False
        return (type(first_origin) is str and type(first_key) is str and
                type(second_origin) is str and type(second_key) is str and
                type(last_origin) is str and type(last_key) is str and
                type(post_key_origin) is str and
                first_origin == supabase_origin.rstrip("/") and
                first_key == publishable_key and
                second_origin == first_origin and
                second_key == first_key and last_origin == first_origin and
                last_key == first_key and post_key_origin == first_origin)

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
        # A long-lived server factory must not accept a store whose project
        # configuration was replaced after the initial trusted composition.
        # Re-check before any JWT, RLS, rights or Storage operation.
        if not project_matches():
            raise ValueError("Tenant store project changed after composition")
        reader = Feature3RevocablePNGReader(
            tenant_store=store,
            verify_user_jwt=verifier,
            current_output_rights=rights,
        )
        # Constructor hooks may read or mutate the injected store. Refuse to
        # hand out a scoped reader if project identity changed during setup.
        if not project_matches():
            raise ValueError("Tenant store project changed during reader construction")
        bound_shop, bound_job = shop_id, job_id

        class ScopedPrivatePNGReader:
            """Prevent accidental reuse of this reader for another route scope."""

            def read(self, *, user_token, shop_id, job_id):
                from feature3_private_png_reader import PrivateGeneratedDownloadDenied
                if (type(shop_id) is not str or type(job_id) is not str or
                        shop_id != bound_shop or job_id != bound_job):
                    raise PrivateGeneratedDownloadDenied(
                        "Private generated output unavailable")
                # Revalidate at use time as well as construction time: a
                # cached scoped reader may outlive a rotated/mutated store.
                # Deny before invoking JWT verification or any RLS/byte read.
                if not project_matches():
                    raise PrivateGeneratedDownloadDenied(
                        "Private generated output unavailable")
                result = reader.read(user_token=user_token,
                                     shop_id=bound_shop, job_id=bound_job)
                # Deny bytes if the backend changed project during JWT/RLS/IO.
                if not project_matches():
                    raise PrivateGeneratedDownloadDenied(
                        "Private generated output unavailable")
                return result

        return ScopedPrivatePNGReader()
    return factory
