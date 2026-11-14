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
                return b"synthetic-only"

        with patch("feature3_private_png_runtime.TenantStore") as store, patch(
                "feature3_private_png_runtime.Feature3RevocablePNGReader",
                CountingReader):
            store.return_value.origin = ORIGIN
            store.return_value.key = KEY
            shop, job = str(uuid4()), str(uuid4())
            scoped = compose(jwt_verifier=verifier)(shop, job)
            for token in ("synthetic-test-token", "abc.def", "abc..def",
                          ".abc.def", "abc.def.", "abc.def.ghi.jkl",
                          "abc.def.ghi=", "abc.def.ghi+", "abc.def.ghi/"):
                with self.subTest(token=token):
                    with self.assertRaises(PrivateGeneratedDownloadDenied):
                        scoped.read(user_token=token, shop_id=shop, job_id=job)
            self.assertEqual(calls, ["construct"])
            # Framing alone never authorizes bytes; the real verifier and
            # downstream reader still own cryptographic/tenant checks.
            self.assertEqual(scoped.read(user_token="abc.def.ghi",
                                         shop_id=shop, job_id=job), b"synthetic-only")
            self.assertEqual(calls, ["construct", "read"])

    def test_injected_isolated_store_retains_synthetic_fixture_support(self):
        class Store:
            origin = ORIGIN
            key = KEY
        factory = compose(
            tenant_store=Store(), jwt_verifier=lambda token: "synthetic-only")
        self.assertTrue(callable(factory))


if __name__ == "__main__":
    unittest.main()
