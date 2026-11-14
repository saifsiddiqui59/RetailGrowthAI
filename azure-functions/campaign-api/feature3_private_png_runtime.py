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
    # The live composition path must use the concrete asymmetric verifier and
    # its real JWKS client. Callable fixtures and inert clients are permitted
    # only when an isolated test store is explicitly injected. An attacker-
    # controlled callable or fake JWKS client must not become live authority.
    if tenant_store is None:
        from jwt import PyJWKClient
        if (type(verifier) is not SupabaseJWTVerifier or
                type(getattr(verifier, "client", None)) is not PyJWKClient):
            raise ValueError("Live private PNG requires trusted JWT/JWKS verifier")
    # A preconstructed verifier must never authenticate tokens issued by a
    # different Supabase project. Synthetic test callables intentionally have
    # no issuer; real verifier instances always expose the pinned issuer.
    if isinstance(verifier, SupabaseJWTVerifier) and (
            type(verifier.issuer) is not str or
            verifier.issuer != supabase_origin.rstrip("/") + "/auth/v1" or
            type(getattr(getattr(verifier, "client", None), "uri", None)) is not str or
            verifier.client.uri != supabase_origin.rstrip("/") + "/auth/v1/.well-known/jwks.json"):
        raise ValueError("JWT verifier must match configured project")
    # Pin the exact JWKS client object; replacing it with a same-URI client 
    # must not silently rotate the trust authority of a cached reader.
    pinned_jwks_client = verifier.client if isinstance(verifier, SupabaseJWTVerifier) else None
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
        # A real verifier can rotate after composition or during backend IO.
        # Deny both cases before private bytes can leave this boundary.
        try:
            issuer_matches = True
            if isinstance(verifier, SupabaseJWTVerifier):
                # Snapshot both verifier trust anchors twice. Stateful or
                # swapped JWKS clients must not authenticate a foreign project.
                issuer_a, client_a = verifier.issuer, verifier.client
                jwks_a = getattr(client_a, "uri", None)
                issuer_b, client_b = verifier.issuer, verifier.client
                jwks_b = getattr(client_b, "uri", None)
                from jwt import PyJWKClient
                issuer_matches = (
                    type(verifier) is SupabaseJWTVerifier and
                    (tenant_store is not None or
                     (type(client_a) is PyJWKClient and type(client_b) is PyJWKClient)) and
                    type(issuer_a) is str and type(issuer_b) is str and
                    type(jwks_a) is str and type(jwks_b) is str and
                    issuer_a == issuer_b == supabase_origin.rstrip("/") + "/auth/v1" and
                    client_a is client_b and client_a is pinned_jwks_client and
                    jwks_a == jwks_b == supabase_origin.rstrip("/") + "/auth/v1/.well-known/jwks.json"
                )
        except Exception:
            return False
        return (issuer_matches and
                type(first_origin) is str and type(first_key) is str and
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
        # Bound hostile identifiers before UUID parsing. Reject noncanonical
        # versions/spellings without doing a second parse or backend IO.
        if len(shop_id) != 36 or len(job_id) != 36:
            raise ValueError("Canonical scoped route IDs required")
        try:
            for value in (shop_id, job_id):
                parsed = UUID(value)
                if parsed.version != 4 or str(parsed) != value:
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
                # A caller-provided token must be a primitive string. Reject
                # objects with side-effecting string/equality behavior before
                # JWT, RLS, rights or private Storage access.
                if (type(user_token) is not str or not 12 <= len(user_token) <= 8192 or
                        any(ord(ch) < 33 or ord(ch) > 126 for ch in user_token) or
                        user_token.startswith(("sb_secret_", "sb_publishable_", "Bearer ")) or
                        any(ch in user_token for ch in (",", ";", '"', "\\"))):
                    raise PrivateGeneratedDownloadDenied(
                        "Private generated output unavailable")
                # Only the live route accepts compact, three-part JWS tokens.
                # Synthetic fixture stores retain their isolated dummy tokens;
                # this framing check is not a substitute for JWT verification.
                if tenant_store is None:
                    parts = user_token.split(".")
                    if (len(parts) != 3 or any(not part for part in parts) or
                            any(any(not (ch.isascii() and
                                         (ch.isalnum() or ch in "-_"))
                                    for ch in part) for part in parts)):
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
