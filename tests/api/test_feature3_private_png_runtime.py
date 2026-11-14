"""F3-08 synthetic-only server composition tests; no hosted auth claims."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_runtime import build_private_png_reader_factory
from feature3_private_png_reader import PrivateGeneratedDownloadDenied


ORIGIN = "https://synthetic-dev-project.supabase.co"
KEY = "sb_publishable_synthetic_test_only_12345"


class SyntheticStore:
    origin = ORIGIN
    key = KEY

    def member(self, *args):
        raise AssertionError("not a hosted test")

    def feature3_gpu_job(self, *args):
        raise AssertionError("not a hosted test")

    def feature3_generated_asset(self, *args):
        raise AssertionError("not a hosted test")


class RuntimeCompositionTests(unittest.TestCase):
    def build(self, **overrides):
        values = dict(supabase_origin=ORIGIN, publishable_key=KEY,
                      authoritative_rights_read=lambda *args: None,
                      jwt_verifier=lambda token: str(uuid4()),
                      tenant_store=SyntheticStore())
        values.update(overrides)
        return build_private_png_reader_factory(**values)

    def test_reader_is_real_fail_closed_reader_not_mock_grant(self):
        factory = self.build()
        reader = factory(str(uuid4()), str(uuid4()))
        self.assertTrue(callable(reader.read))
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            reader.read(user_token="synthetic-test-token",
                        shop_id=str(uuid4()), job_id=str(uuid4()))

    def test_reader_rejects_foreign_scope_before_jwt_or_storage(self):
        shop, job = str(uuid4()), str(uuid4())
        reader = self.build()(shop, job)
        for foreign_shop, foreign_job in (
            (str(uuid4()), job), (shop, str(uuid4())),
            (shop.upper(), job), (shop, job.upper()),
            (object(), job), (shop, object()),
        ):
            with self.subTest(foreign_shop=foreign_shop, foreign_job=foreign_job):
                with self.assertRaises(PrivateGeneratedDownloadDenied):
                    reader.read(user_token="synthetic-test-token",
                                shop_id=foreign_shop, job_id=foreign_job)

    def test_nonprimitive_tokens_denied_before_backend_read(self):
        """Synthetic hostile token objects never reach a private reader."""
        from unittest.mock import patch

        class TokenSubclass(str):
            pass

        class HostileToken:
            def __str__(self):
                raise AssertionError("token coercion must not run")

            def __eq__(self, other):
                raise AssertionError("token equality must not run")

        calls = []

        class CountingReader:
            def __init__(self, **kwargs):
                pass

            def read(self, **kwargs):
                calls.append("backend")
                return b"synthetic-bytes"

        shop, job = str(uuid4()), str(uuid4())
        with patch("feature3_private_png_runtime.Feature3RevocablePNGReader",
                   CountingReader):
            scoped = self.build()(shop, job)
            for token in (None, b"fake-token", "", TokenSubclass("fake-token"),
                          HostileToken()):
                with self.subTest(token_type=type(token).__name__):
                    with self.assertRaises(PrivateGeneratedDownloadDenied):
                        scoped.read(user_token=token, shop_id=shop, job_id=job)
        self.assertEqual(calls, [])

    def test_malformed_direct_reader_tokens_denied_without_backend_io(self):
        """Synthetic direct callers cannot bypass route-level token framing."""
        from unittest.mock import patch

        calls = []
        class CountingReader:
            def __init__(self, **kwargs):
                pass
            def read(self, **kwargs):
                calls.append("private-io")
                return b"synthetic-only"

        shop, job = str(uuid4()), str(uuid4())
        with patch("feature3_private_png_runtime.Feature3RevocablePNGReader",
                   CountingReader):
            scoped = self.build()(shop, job)
            for token in ("short", "Bearer synthetic-valid-token",
                          "sb_secret_synthetic_test_only",
                          "sb_publishable_synthetic_test_only",
                          "synthetic token with spaces",
                          "synthetic\\nnewline-token", "synthetic,comma-token",
                          "synthetic;semicolon-token",
                          "synthetic" + "a" * 8192):
                with self.subTest(token=token[:30]):
                    with self.assertRaises(PrivateGeneratedDownloadDenied):
                        scoped.read(user_token=token, shop_id=shop, job_id=job)
        self.assertEqual(calls, [])

    def test_well_formed_direct_reader_token_reaches_backend(self):
        """Synthetic test only: valid framing does not imply JWT authorization."""
        from unittest.mock import patch

        calls = []
        class CountingReader:
            def __init__(self, **kwargs):
                pass
            def read(self, **kwargs):
                calls.append("backend")
                return b"synthetic-only"

        shop, job = str(uuid4()), str(uuid4())
        with patch("feature3_private_png_runtime.Feature3RevocablePNGReader",
                   CountingReader):
            scoped = self.build()(shop, job)
            self.assertEqual(
                scoped.read(user_token="synthetic-test-token-123",
                            shop_id=shop, job_id=job), b"synthetic-only")
        self.assertEqual(calls, ["backend"])

    def test_cross_project_real_verifier_is_rejected_before_reader_io(self):
        """Synthetic configuration regression; no hosted JWT is minted."""
        from security import SupabaseJWTVerifier

        # Construct an inert verifier without a network JWKS client.
        verifier = object.__new__(SupabaseJWTVerifier)
        from types import SimpleNamespace
        verifier.client = SimpleNamespace(uri=ORIGIN + "/auth/v1/.well-known/jwks.json")
        verifier.issuer = "https://foreign-project.supabase.co/auth/v1"
        with self.assertRaisesRegex(ValueError, "JWT verifier must match"):
            self.build(jwt_verifier=verifier)

        # Correctly pinned issuer is accepted for composition only; it does
        # not authorize any bytes or substitute for a signed JWT.
        verifier.issuer = ORIGIN + "/auth/v1"
        shop, job = str(uuid4()), str(uuid4())
        scoped = self.build(jwt_verifier=verifier)(shop, job)
        self.assertTrue(callable(scoped.read))

    def test_real_verifier_foreign_jwks_is_denied_before_and_after_io(self):
        """A matching issuer cannot mask a foreign signing-key endpoint."""
        from types import SimpleNamespace
        from unittest.mock import patch
        from security import SupabaseJWTVerifier

        verifier = object.__new__(SupabaseJWTVerifier)
        verifier.issuer = ORIGIN + "/auth/v1"
        verifier.client = SimpleNamespace(
            uri="https://foreign-project.supabase.co/auth/v1/.well-known/jwks.json")
        with self.assertRaisesRegex(ValueError, "JWT verifier must match"):
            self.build(jwt_verifier=verifier)

        verifier.client.uri = ORIGIN + "/auth/v1/.well-known/jwks.json"
        calls = []

        class CountingReader:
            def __init__(self, **kwargs):
                pass

            def read(self, **kwargs):
                calls.append("private-io")
                return b"synthetic-only"

        shop, job = str(uuid4()), str(uuid4())
        with patch("feature3_private_png_runtime.Feature3RevocablePNGReader",
                   CountingReader):
            scoped = self.build(jwt_verifier=verifier)(shop, job)
            verifier.client.uri = "https://foreign-project.supabase.co/auth/v1/.well-known/jwks.json"
            with self.assertRaises(PrivateGeneratedDownloadDenied):
                scoped.read(user_token="synthetic-test-token-123",
                            shop_id=shop, job_id=job)
            self.assertEqual(calls, [])
            verifier.client.uri = ORIGIN + "/auth/v1/.well-known/jwks.json"

            class RotatingReader:
                def __init__(self, **kwargs):
                    pass

                def read(self, **kwargs):
                    calls.append("private-io")
                    verifier.client.uri = "https://foreign-project.supabase.co/auth/v1/.well-known/jwks.json"
                    return b"synthetic-private-bytes"

            with patch("feature3_private_png_runtime.Feature3RevocablePNGReader",
                       RotatingReader):
                scoped = self.build(jwt_verifier=verifier)(shop, job)
                with self.assertRaises(PrivateGeneratedDownloadDenied):
                    scoped.read(user_token="synthetic-test-token-123",
                                shop_id=shop, job_id=job)
            self.assertEqual(calls, ["private-io"])

    def test_real_verifier_issuer_rotation_denies_before_and_after_io(self):
        """Synthetic mutation tests; not hosted JWT authorization."""
        from unittest.mock import patch
        from security import SupabaseJWTVerifier

        verifier = object.__new__(SupabaseJWTVerifier)
        verifier.issuer = ORIGIN + "/auth/v1"
        from types import SimpleNamespace
        verifier.client = SimpleNamespace(uri=ORIGIN + "/auth/v1/.well-known/jwks.json")
        calls = []

        class CountingReader:
            def __init__(self, **kwargs):
                pass

            def read(self, **kwargs):
                calls.append("backend")
                verifier.issuer = "https://foreign-project.supabase.co/auth/v1"
                return b"synthetic-private-bytes"

        shop, job = str(uuid4()), str(uuid4())
        with patch("feature3_private_png_runtime.Feature3RevocablePNGReader",
                   CountingReader):
            scoped = self.build(jwt_verifier=verifier)(shop, job)
            verifier.issuer = "https://foreign-project.supabase.co/auth/v1"
            with self.assertRaises(PrivateGeneratedDownloadDenied):
                scoped.read(user_token="synthetic-test-token-123",
                            shop_id=shop, job_id=job)
            self.assertEqual(calls, [])
            verifier.issuer = ORIGIN + "/auth/v1"
            with self.assertRaises(PrivateGeneratedDownloadDenied):
                scoped.read(user_token="synthetic-test-token-123",
                            shop_id=shop, job_id=job)
            self.assertEqual(calls, ["backend"])

    def test_no_authoritative_rights_provider_is_never_allowed(self):
        for provider in (None, False, {}, "approved"):
            with self.subTest(provider=provider):
                with self.assertRaises(ValueError):
                    self.build(authoritative_rights_read=provider)

    def test_mutated_project_store_is_rejected_before_reader_creation(self):
        class MutableStore(SyntheticStore):
            pass
        for field, value in (("origin", "https://foreign.supabase.co"),
                             ("key", "sb_publishable_foreign_test_key"),
                             ("origin", object()), ("key", object())):
            with self.subTest(field=field, value_type=type(value).__name__):
                store = MutableStore()
                factory = self.build(tenant_store=store)
                setattr(store, field, value)
                with self.assertRaises(ValueError):
                    factory(str(uuid4()), str(uuid4()))

    def test_cached_reader_denies_store_rotation_before_any_backend_call(self):
        class MutableStore(SyntheticStore):
            pass

        class CountingVerifier:
            def __init__(self):
                self.calls = 0

            def __call__(self, token):
                self.calls += 1
                raise AssertionError("JWT must not run after project rotation")

        for field, replacement in (
            ("origin", "https://foreign-project.supabase.co"),
            ("key", "sb_publishable_foreign_test_key"),
            ("origin", object()),
            ("key", object()),
        ):
            with self.subTest(field=field, value_type=type(replacement).__name__):
                store = MutableStore()
                verifier = CountingVerifier()
                shop, job = str(uuid4()), str(uuid4())
                reader = self.build(tenant_store=store, jwt_verifier=verifier)(
                    shop, job)
                setattr(store, field, replacement)
                with self.assertRaises(PrivateGeneratedDownloadDenied):
                    reader.read(user_token="synthetic-test-token",
                                shop_id=shop, job_id=job)
                self.assertEqual(verifier.calls, 0)

    def test_constructor_rotation_never_returns_scoped_reader(self):
        """Synthetic constructor side effect cannot yield an authorized reader."""
        from unittest.mock import patch

        class MutableStore(SyntheticStore):
            pass

        store = MutableStore()
        calls = []

        class RotatingReader:
            def __init__(self, **kwargs):
                calls.append("constructed")
                store.origin = "https://foreign-project.supabase.co"

            def read(self, **kwargs):
                calls.append("read")
                return b"synthetic-only"

        shop, job = str(uuid4()), str(uuid4())
        with patch("feature3_private_png_runtime.Feature3RevocablePNGReader",
                   RotatingReader):
            factory = self.build(tenant_store=store)
            with self.assertRaisesRegex(ValueError, "during reader construction"):
                factory(shop, job)
        self.assertEqual(calls, ["constructed"])

    def test_runtime_denies_bytes_when_project_rotates_during_backend_read(self):
        """Synthetic backend cannot release bytes after project-key rotation."""
        from unittest.mock import patch

        class MutableStore(SyntheticStore):
            pass

        store = MutableStore()
        calls = []

        class SyntheticReader:
            def __init__(self, **kwargs):
                calls.append("constructed")

            def read(self, **kwargs):
                calls.append("read")
                store.key = "sb_publishable_rotated_test_only"
                return b"synthetic-private-bytes-not-hosted"

        shop, job = str(uuid4()), str(uuid4())
        with patch("feature3_private_png_runtime.Feature3RevocablePNGReader",
                   SyntheticReader):
            scoped = self.build(tenant_store=store)(shop, job)
            with self.assertRaises(PrivateGeneratedDownloadDenied):
                scoped.read(user_token="synthetic-only", shop_id=shop, job_id=job)
        self.assertEqual(calls, ["constructed", "read"])

    def test_runtime_configuration_getter_failure_denies_before_jwt(self):
        """A broken injected store never falls through to authentication."""
        class FlakyStore(SyntheticStore):
            def __init__(self):
                self.fail = False

            @property
            def origin(self):
                if self.fail:
                    raise RuntimeError("synthetic config unavailable")
                return ORIGIN

        store = FlakyStore()
        calls = []
        def verifier(token):
            calls.append("jwt")
            return str(uuid4())

        shop, job = str(uuid4()), str(uuid4())
        factory = self.build(tenant_store=store, jwt_verifier=verifier)
        scoped = factory(shop, job)
        store.fail = True
        with self.assertRaises(ValueError):
            factory(shop, job)
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            scoped.read(user_token="synthetic-only", shop_id=shop, job_id=job)
        self.assertEqual(calls, [])

    def test_side_effecting_key_getter_rotates_origin_before_reader_use(self):
        """Synthetic getter rotation must deny before JWT or private bytes."""
        class RotatingStore(SyntheticStore):
            def __init__(self):
                self._origin = ORIGIN
                self.rotate = False
                self.key_reads = 0

            @property
            def origin(self):
                return self._origin

            @property
            def key(self):
                self.key_reads += 1
                if self.rotate:
                    self._origin = "https://foreign-project.supabase.co"
                return KEY

        store = RotatingStore()
        calls = []
        def verifier(token):
            calls.append("jwt")
            return str(uuid4())

        shop, job = str(uuid4()), str(uuid4())
        factory = self.build(tenant_store=store, jwt_verifier=verifier)
        reader = factory(shop, job)
        store.rotate = True
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            reader.read(user_token="synthetic-only", shop_id=shop, job_id=job)
        self.assertEqual(calls, [])
        self.assertEqual(store.origin, "https://foreign-project.supabase.co")

    def test_final_key_getter_rotation_denies_before_reader_construction(self):
        """A key getter changing origin on the last read must fail closed."""
        class RotatingStore(SyntheticStore):
            def __init__(self):
                self._origin = ORIGIN
                self.key_reads = 0

            @property
            def origin(self):
                return self._origin

            @property
            def key(self):
                self.key_reads += 1
                if self.key_reads == 4:
                    self._origin = "https://foreign-project.supabase.co"
                return KEY

        store = RotatingStore()
        shop, job = str(uuid4()), str(uuid4())
        with self.assertRaises(ValueError):
            self.build(tenant_store=store)(shop, job)
        self.assertEqual(store.origin, "https://foreign-project.supabase.co")

    def test_cross_project_store_is_rejected(self):
        class ForeignStore(SyntheticStore):
            origin = "https://foreign-project.supabase.co"
        with self.assertRaises(ValueError):
            self.build(tenant_store=ForeignStore())

    def test_project_config_cannot_be_spoofed_by_overloaded_equality(self):
        class MatchesAnything:
            def __eq__(self, other):
                return True

        class StringSubclass(str):
            pass

        for origin, key in (
            (MatchesAnything(), KEY),
            (ORIGIN, MatchesAnything()),
            (StringSubclass(ORIGIN), KEY),
            (ORIGIN, StringSubclass(KEY)),
        ):
            with self.subTest(origin_type=type(origin).__name__,
                              key_type=type(key).__name__):
                class ForgedStore(SyntheticStore):
                    pass
                forged = ForgedStore()
                forged.origin = origin
                forged.key = key
                with self.assertRaises(ValueError):
                    self.build(tenant_store=forged)

    def test_service_key_and_insecure_origin_are_rejected(self):
        for origin, key in (
            (ORIGIN, "synthetic-service-role-key"),
            ("http://synthetic-dev-project.supabase.co", KEY),
            ("https://synthetic-dev-project.supabase.co.evil.test", KEY),
        ):
            with self.subTest(origin=origin, key=key):
                with self.assertRaises(ValueError):
                    self.build(supabase_origin=origin, publishable_key=key)

    def test_invalid_digest_and_revision_fail_at_factory_creation(self):
        for options in (dict(expected_output_sha256="not-a-sha"),
                        dict(minimum_rights_revision=0),
                        dict(minimum_rights_revision=True)):
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    self.build(**options)

    def test_canonical_scoped_reader_constructs_without_backend_access(self):
        """Valid route scope must construct without JWT, RLS or Storage IO."""
        class NoBackendStore(SyntheticStore):
            def member(self, *args):
                raise AssertionError("factory must not query membership")

        shop, job = str(uuid4()), str(uuid4())
        reader = self.build(tenant_store=NoBackendStore())(shop, job)
        self.assertTrue(callable(reader.read))

    def test_cached_reader_rejects_rotation_even_after_config_restored(self):
        """A reader must not authorize a mismatched project during rotation."""
        class MutableStore(SyntheticStore):
            pass

        store = MutableStore()
        shop, job = str(uuid4()), str(uuid4())
        reader = self.build(tenant_store=store)(shop, job)
        store.key = "sb_publishable_rotated_synthetic_only"
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            reader.read(user_token="synthetic-test-token", shop_id=shop, job_id=job)
        store.key = KEY
        # Restored configuration must still enforce current rights, never
        # turn a previous denial into a cached positive authorization.
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            reader.read(user_token="synthetic-test-token", shop_id=shop, job_id=job)

    def test_untrusted_scoped_identifiers_cannot_construct_reader(self):
        factory = self.build()
        for shop, job in ((object(), str(uuid4())),
                          (str(uuid4()), object()),
                          ("not-a-uuid", str(uuid4())),
                          (str(uuid4()).upper(), str(uuid4()))):
            with self.assertRaises(ValueError):
                factory(shop, job)


    def test_scope_parser_denies_oversized_and_non_v4_ids_before_reader_io(self):
        """Hostile path input must not trigger JWT, RLS, or reader construction."""
        from unittest.mock import patch
        calls = []

        class UnexpectedReader:
            def __init__(self, **kwargs):
                calls.append("reader")
                raise AssertionError("private reader must not be constructed")

        factory = self.build()
        good = str(uuid4())
        bad_values = (
            "a" * 100000,
            good.upper(),
            good.replace("-", ""),
            "00000000-0000-0000-0000-000000000000",
            "00000000-0000-4000-8000-00000000000g",
        )
        with patch("feature3_private_png_runtime.Feature3RevocablePNGReader",
                   UnexpectedReader):
            for bad in bad_values:
                with self.subTest(bad_length=len(bad)):
                    for shop, job in ((bad, good), (good, bad)):
                        with self.assertRaises(ValueError):
                            factory(shop, job)
        self.assertEqual(calls, [])

    def test_scope_parser_accepts_canonical_uuid4_without_duplicate_parse(self):
        """The trusted reader still accepts normal route UUIDs."""
        shop, job = str(uuid4()), str(uuid4())
        factory = self.build()
        scoped = factory(shop, job)
        self.assertTrue(callable(scoped.read))


if __name__ == "__main__":
    unittest.main()
