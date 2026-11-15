"""F3-08: live reader composition must not accept test-only JWT authority.

All inputs are synthetic; these tests do not create real users or fetch JWKS.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_runtime import build_private_png_reader_factory
from security import SupabaseJWTVerifier

ORIGIN = "https://synthetic-dev-project.supabase.co"
KEY = "sb_publishable_synthetic_test_only_12345"


def compose(**kwargs):
    return build_private_png_reader_factory(
        supabase_origin=ORIGIN,
        publishable_key=KEY,
        authoritative_rights_read=lambda *args: None,
        **kwargs,
    )


class LiveVerifierBoundaryTests(unittest.TestCase):
    def test_rejects_malformed_project_config_before_any_adapter_creation(self):
        # No JWT/JWKS client or TenantStore may be constructed from a
        # caller-supplied project URL or privileged/invalid API key.
        origins = (
            "http://synthetic-dev-project.supabase.co",
            "https://synthetic-dev-project.supabase.co.evil.test",
            "https://synthetic-dev-project.supabase.co/path",
            "https://synthetic-dev-project.supabase.co\\n",
            "https://user@synthetic-dev-project.supabase.co",
            "https://synthetic-dev-project.supabase.co:444",
        )
        with patch("feature3_private_png_runtime.TenantStore") as store, patch(
                "feature3_private_png_runtime.SupabaseJWTVerifier") as verifier:
            for origin in origins:
                with self.subTest(origin=repr(origin)):
                    with self.assertRaisesRegex(ValueError, "project configuration"):
                        build_private_png_reader_factory(
                            supabase_origin=origin,
                            publishable_key=KEY,
                            authoritative_rights_read=lambda *args: True,
                        )
            for key in ("service_role_secret", "sb_secret_test123456",
                        "sb_publishable_short", KEY + "\\n", ""):
                with self.subTest(key=repr(key)):
                    with self.assertRaisesRegex(ValueError, "project configuration"):
                        build_private_png_reader_factory(
                            supabase_origin=ORIGIN,
                            publishable_key=key,
                            authoritative_rights_read=lambda *args: True,
                        )
            store.assert_not_called()
            verifier.assert_not_called()

    def test_runtime_module_compiles_before_security_tests(self):
        # Guard against malformed source escaping in generated security fixes.
        import ast
        source = (Path(__file__).resolve().parents[2] / "azure-functions" /
                  "campaign-api" / "feature3_private_png_runtime.py").read_text()
        ast.parse(source, filename="feature3_private_png_runtime.py")

    def test_live_path_rejects_callable_fixture_without_reading_rights(self):
        calls = []
        with patch("feature3_private_png_runtime.TenantStore") as store:
            store.return_value.origin = ORIGIN
            store.return_value.key = KEY
            with self.assertRaisesRegex(ValueError, "trusted JWT/JWKS"):
                compose(jwt_verifier=lambda token: calls.append(token))
        self.assertEqual(calls, [])

    def test_live_path_rejects_real_verifier_with_fake_jwks_client(self):
        from types import SimpleNamespace
        verifier = object.__new__(SupabaseJWTVerifier)
        verifier.issuer = ORIGIN + "/auth/v1"
        verifier.client = SimpleNamespace(
            uri=ORIGIN + "/auth/v1/.well-known/jwks.json")
        with patch("feature3_private_png_runtime.TenantStore") as store:
            store.return_value.origin = ORIGIN
            store.return_value.key = KEY
            with self.assertRaisesRegex(ValueError, "trusted JWT/JWKS"):
                compose(jwt_verifier=verifier)

    def test_live_path_accepts_concrete_verifier_without_network(self):
        verifier = SupabaseJWTVerifier(ORIGIN)
        with patch("feature3_private_png_runtime.TenantStore") as store:
            store.return_value.origin = ORIGIN
            store.return_value.key = KEY
            factory = compose(jwt_verifier=verifier)
        self.assertTrue(callable(factory))

    def test_live_reader_rejects_jwks_client_replaced_after_composition(self):
        from types import SimpleNamespace
        from uuid import uuid4
        verifier = SupabaseJWTVerifier(ORIGIN)
        with patch("feature3_private_png_runtime.TenantStore") as store:
            store.return_value.origin = ORIGIN
            store.return_value.key = KEY
            factory = compose(jwt_verifier=verifier)
            verifier.client = SimpleNamespace(
                uri=ORIGIN + "/auth/v1/.well-known/jwks.json")
            with self.assertRaisesRegex(ValueError, "project changed"):
                factory(str(uuid4()), str(uuid4()))
            store.return_value.member.assert_not_called()
            store.return_value.feature3_gpu_job.assert_not_called()

    def test_live_reader_rejects_same_uri_jwks_client_replacement(self):
        from jwt import PyJWKClient
        from uuid import uuid4
        from feature3_private_png_reader import PrivateGeneratedDownloadDenied
        verifier = SupabaseJWTVerifier(ORIGIN)
        with patch("feature3_private_png_runtime.TenantStore") as store:
            store.return_value.origin = ORIGIN
            store.return_value.key = KEY
            factory = compose(jwt_verifier=verifier)
            shop, job = str(uuid4()), str(uuid4())
            scoped = factory(shop, job)
            verifier.client = PyJWKClient(
                ORIGIN + "/auth/v1/.well-known/jwks.json")
            with self.assertRaises(PrivateGeneratedDownloadDenied):
                scoped.read(user_token="abc.def.ghi", shop_id=shop, job_id=job)
            store.return_value.member.assert_not_called()
            store.return_value.feature3_gpu_job.assert_not_called()

    def test_live_route_rejects_malformed_compact_jws_before_backend_io(self):
        from uuid import uuid4
        from feature3_private_png_reader import PrivateGeneratedDownloadDenied
        verifier = SupabaseJWTVerifier(ORIGIN)
        calls = []

        class CountingReader:
            def __init__(self, **kwargs):
                calls.append("construct")

            def read(self, **kwargs):
                calls.append("read")
                return b"synthetic-only" * 10

        with patch("feature3_private_png_runtime.TenantStore") as store, patch(
                "feature3_private_png_runtime.Feature3RevocablePNGReader",
                CountingReader):
            store.return_value.origin = ORIGIN
            store.return_value.key = KEY
            shop, job = str(uuid4()), str(uuid4())
            scoped = compose(jwt_verifier=verifier)(shop, job)
            for token in ("synthetic-test-token", "abc.def", "abc..def",
                          ".abc.def", "abc.def.", "abc.def.ghi.jkl",
                          "abc.def.ghi=", "abc.def.ghi+", "abc.def.ghi/",
                          "a.def.ghi", "abc.d.ghi", "abc.def.g", "ab.def.ghi", "abc.de.ghi",
                          "a" * 2049 + ".def.ghi",
                          "abc." + "b" * 6145 + ".ghi",
                          "abc.def." + "c" * 2049):
                with self.subTest(token=token):
                    with self.assertRaises(PrivateGeneratedDownloadDenied):
                        scoped.read(user_token=token, shop_id=shop, job_id=job)
            self.assertEqual(calls, ["construct"])
            # Framing alone never authorizes bytes; the real verifier and
            # downstream reader still own cryptographic/tenant checks.
            self.assertEqual(scoped.read(user_token="abc.deQ.ghg",
                                         shop_id=shop, job_id=job), b"synthetic-only" * 10)
            self.assertEqual(calls, ["construct", "read"])

    def test_live_reader_rejects_lazy_mutable_or_custom_download_bodies(self):
        # A streamed/lazy body could be consumed after the final rights and
        # project checks; only an immutable concrete bytes value may escape.
        from uuid import uuid4
        from feature3_private_png_reader import PrivateGeneratedDownloadDenied
        verifier = SupabaseJWTVerifier(ORIGIN)
        calls = []

        class CountingReader:
            def __init__(self, **kwargs):
                pass

            def read(self, **kwargs):
                calls.append("read")
                return candidate[0]

        class BytesSubclass(bytes):
            pass

        with patch("feature3_private_png_runtime.TenantStore") as store, patch(
                "feature3_private_png_runtime.Feature3RevocablePNGReader",
                CountingReader):
            store.return_value.origin = ORIGIN
            store.return_value.key = KEY
            shop, job = str(uuid4()), str(uuid4())
            scoped = compose(jwt_verifier=verifier)(shop, job)
            candidate = [None]
            for value in (None, bytearray(b"png"), memoryview(b"png"),
                          BytesSubclass(b"png"), iter([b"png"]), "png"):
                candidate[0] = value
                with self.subTest(type=type(value).__name__):
                    with self.assertRaises(PrivateGeneratedDownloadDenied):
                        scoped.read(user_token="abc.deQ.ghg", shop_id=shop,
                                    job_id=job)
            candidate[0] = b"synthetic-only" * 10
            self.assertEqual(
                scoped.read(user_token="abc.deQ.ghg", shop_id=shop, job_id=job),
                b"synthetic-only" * 10)
        self.assertEqual(len(calls), 7)

    def test_live_reader_denies_bytes_if_store_rotates_during_backend_read(self):
        # Even a successfully returned immutable payload must be discarded if
        # tenant authority changes while the private reader is performing IO.
        from uuid import uuid4
        from feature3_private_png_reader import PrivateGeneratedDownloadDenied
        verifier = SupabaseJWTVerifier(ORIGIN)
        calls = []

        class MutableStore:
            origin = ORIGIN
            key = KEY

        store = MutableStore()

        class MutatingReader:
            def __init__(self, **kwargs):
                calls.append("construct")

            def read(self, **kwargs):
                calls.append("read")
                store.origin = "https://foreign-project.supabase.co"
                return b"synthetic-private-png-bytes" * 5

        with patch("feature3_private_png_runtime.TenantStore", return_value=store), patch(
                "feature3_private_png_runtime.Feature3RevocablePNGReader",
                MutatingReader):
            shop, job = str(uuid4()), str(uuid4())
            scoped = compose(jwt_verifier=verifier)(shop, job)
            with self.assertRaises(PrivateGeneratedDownloadDenied):
                scoped.read(user_token="abc.deQ.ghg", shop_id=shop, job_id=job)
        self.assertEqual(calls, ["construct", "read"])

    def test_live_reader_denies_when_jwks_client_rotates_during_backend_read(self):
        # A same-URL replacement during IO cannot authorize returned bytes.
        from uuid import uuid4
        from jwt import PyJWKClient
        from feature3_private_png_reader import PrivateGeneratedDownloadDenied
        verifier = SupabaseJWTVerifier(ORIGIN)
        calls = []

        class CountingReader:
            def __init__(self, **kwargs):
                pass

            def read(self, **kwargs):
                calls.append("read")
                verifier.client = PyJWKClient(
                    ORIGIN + "/auth/v1/.well-known/jwks.json")
                return b"synthetic-private-png-bytes"

        with patch("feature3_private_png_runtime.TenantStore") as store, patch(
                "feature3_private_png_runtime.Feature3RevocablePNGReader",
                CountingReader):
            store.return_value.origin = ORIGIN
            store.return_value.key = KEY
            shop, job = str(uuid4()), str(uuid4())
            scoped = compose(jwt_verifier=verifier)(shop, job)
            with self.assertRaises(PrivateGeneratedDownloadDenied):
                scoped.read(user_token="abc.deQ.ghg", shop_id=shop, job_id=job)
        self.assertEqual(calls, ["read"])

    def test_scoped_adapter_rejects_empty_short_and_oversized_private_payloads(self):
        # The scoped HTTP-facing adapter must enforce the same byte bounds as
        # the private Storage reader even if an injected backend misbehaves.
        from uuid import uuid4
        from feature3_private_png_reader import PrivateGeneratedDownloadDenied
        verifier = SupabaseJWTVerifier(ORIGIN)
        payload = [b""]

        class StubReader:
            def __init__(self, **kwargs):
                pass

            def read(self, **kwargs):
                return payload[0]

        with patch("feature3_private_png_runtime.TenantStore") as store, patch(
                "feature3_private_png_runtime.Feature3RevocablePNGReader",
                StubReader):
            store.return_value.origin = ORIGIN
            store.return_value.key = KEY
            shop, job = str(uuid4()), str(uuid4())
            scoped = compose(jwt_verifier=verifier)(shop, job)
            for size in (0, 1, 99, 25 * 1024 * 1024 + 1):
                payload[0] = b"x" * size
                with self.subTest(size=size):
                    with self.assertRaises(PrivateGeneratedDownloadDenied):
                        scoped.read(user_token="abc.deQ.ghg",
                                    shop_id=shop, job_id=job)
            for size in (100, 25 * 1024 * 1024):
                payload[0] = b"x" * size
                with self.subTest(size=size):
                    self.assertEqual(
                        len(scoped.read(user_token="abc.deQ.ghg",
                                        shop_id=shop, job_id=job)), size)

    def test_injected_isolated_store_retains_synthetic_fixture_support(self):
        class Store:
            origin = ORIGIN
            key = KEY
        factory = compose(
            tenant_store=Store(), jwt_verifier=lambda token: "synthetic-only")
        self.assertTrue(callable(factory))


if __name__ == "__main__":
    unittest.main()
