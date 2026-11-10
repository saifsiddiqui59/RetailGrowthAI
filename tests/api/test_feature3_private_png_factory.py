"""Synthetic F3-08 factory contract tests; not hosted JWT/RLS evidence."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_factory import TrustedPrivatePNGFactory
from feature3_private_png_reader import PrivateGeneratedDownloadDenied


class Store:
    origin = "https://fixture.supabase.co"
    key = "sb_publishable_" + "x" * 12

    def member(self, *args):
        return False

    def feature3_gpu_job(self, *args):
        return None

    def feature3_generated_asset(self, *args):
        return None


class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job = str(uuid4()), str(uuid4())
        self.verify = lambda token: None
        self.rights = lambda shop, job, asset: False

    def make(self, store=None):
        return TrustedPrivatePNGFactory(
            tenant_store=Store() if store is None else store,
            verify_user_jwt=self.verify,
            current_output_rights=self.rights,
        )

    def test_reject_missing_security_dependencies(self):
        for kwargs in (
            {"verify_user_jwt": None},
            {"current_output_rights": None},
            {"tenant_store": object()},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                values = dict(tenant_store=Store(), verify_user_jwt=self.verify,
                              current_output_rights=self.rights)
                values.update(kwargs)
                TrustedPrivatePNGFactory(**values)

    def test_service_role_key_is_not_accepted(self):
        store = Store()
        store.key = "service_role_test_secret"
        with self.assertRaises(ValueError):
            self.make(store)

    def test_invalid_scopes_denied_before_read(self):
        factory = self.make()
        for shop, job in ((self.shop.upper(), self.job), ("not-uuid", self.job),
                          (self.shop, None), (self.shop, str(uuid4()).upper())):
            with self.subTest(shop=shop, job=job), self.assertRaises(ValueError):
                factory(shop, job)

    def test_scoped_reader_denies_cross_shop_and_job(self):
        factory = self.make()
        reader = factory(self.shop, self.job)
        for shop, job in ((str(uuid4()), self.job),
                          (self.shop, str(uuid4()))):
            with self.subTest(shop=shop, job=job):
                with self.assertRaises(PrivateGeneratedDownloadDenied):
                    reader.read(user_token="synthetic", shop_id=shop, job_id=job)

    def test_malformed_tokens_denied_before_verifier(self):
        calls = []
        def verify(token):
            calls.append(token)
            raise AssertionError("verifier should not be called")
        factory = TrustedPrivatePNGFactory(
            tenant_store=Store(), verify_user_jwt=verify,
            current_output_rights=self.rights,
        )
        reader = factory(self.shop, self.job)
        bad = (None, b"token", 42, "", "a" * 8193, "a b",
               "a\\n", "a\\r", "a\\t", "\\x00", "\\x7f")
        for token in bad:
            with self.subTest(token=repr(token)), self.assertRaises(PrivateGeneratedDownloadDenied):
                reader.read(user_token=token, shop_id=self.shop, job_id=self.job)
        self.assertEqual(calls, [])

    def test_token_string_subclass_denied(self):
        class Token(str):
            pass
        reader = self.make()(self.shop, self.job)
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            reader.read(user_token=Token("synthetic"), shop_id=self.shop, job_id=self.job)

    def test_valid_scope_reaches_real_reader_and_denies_fake_jwt(self):
        # No mocked success: the actual reader must reject the fixture token.
        reader = self.make()(self.shop, self.job)
        with self.assertRaises(Exception):
            reader.read(user_token="not-a-signed-jwt",
                        shop_id=self.shop, job_id=self.job)


if __name__ == "__main__":
    unittest.main()
