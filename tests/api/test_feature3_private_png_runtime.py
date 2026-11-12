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

    def test_untrusted_scoped_identifiers_cannot_construct_reader(self):
        factory = self.build()
        for shop, job in ((object(), str(uuid4())),
                          (str(uuid4()), object()),
                          ("not-a-uuid", str(uuid4())),
                          (str(uuid4()).upper(), str(uuid4()))):
            with self.assertRaises(ValueError):
                factory(shop, job)


if __name__ == "__main__":
    unittest.main()
