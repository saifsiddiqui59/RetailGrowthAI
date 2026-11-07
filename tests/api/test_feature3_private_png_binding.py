"""F3-08 offline composition tests: fixtures never establish hosted rights."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_binding import build_private_png_reader_factory


class SyntheticTenant:
    origin = "https://demo-project.supabase.co"
    key = "sb_publishable_" + "x" * 24

    def member(self, *args):
        return False

    def feature3_gpu_job(self, *args):
        return None

    def feature3_generated_asset(self, *args):
        return None


class PrivatePNGCompositionTests(unittest.TestCase):
    def setUp(self):
        self.tenant = SyntheticTenant()
        self.shop, self.job = str(uuid4()), str(uuid4())
        self.calls = []

    def make(self, rights=None, verifier=None, tenant=None):
        return build_private_png_reader_factory(
            origin=self.tenant.origin,
            publishable_key=self.tenant.key,
            tenant=self.tenant if tenant is None else tenant,
            verifier=(lambda token: str(uuid4())) if verifier is None else verifier,
            current_output_rights=rights,
        )

    def test_missing_rights_authority_is_configuration_error(self):
        for rights in (None, True, False, {}, "approved"):
            with self.subTest(rights=rights):
                with self.assertRaises(ValueError):
                    self.make(rights)

    def test_factory_rejects_invalid_route_scope(self):
        factory = self.make(lambda *args: False)
        for shop, job in (("forged", self.job), (self.shop, "forged")):
            with self.subTest(shop=shop, job=job):
                with self.assertRaises(ValueError):
                    factory(shop, job)

    def test_reader_uses_explicit_rights_authority_and_denies_fixture_membership(self):
        def rights(*args):
            self.calls.append(args)
            return False
        reader = self.make(rights)(self.shop, self.job)
        with self.assertRaises(PermissionError):
            reader.read(user_token="synthetic-token-not-hosted", shop_id=self.shop, job_id=self.job)
        # RLS denies before rights lookup; no storage bytes were fetched.
        self.assertEqual(self.calls, [])

    def test_bad_injected_tenant_and_verifier_fail_closed(self):
        with self.assertRaises(ValueError):
            self.make(lambda *args: False, tenant=object())
        with self.assertRaises(ValueError):
            self.make(lambda *args: False, verifier="not callable")

    def test_reader_rejects_service_key_and_non_https_origin(self):
        tenant = SyntheticTenant()
        tenant.key = "service-role-key"
        with self.assertRaises(ValueError):
            self.make(lambda *args: False, tenant=tenant)(self.shop, self.job)
        tenant = SyntheticTenant()
        tenant.origin = "http://demo-project.supabase.co"
        with self.assertRaises(ValueError):
            self.make(lambda *args: False, tenant=tenant)(self.shop, self.job)


if __name__ == "__main__":
    unittest.main()
