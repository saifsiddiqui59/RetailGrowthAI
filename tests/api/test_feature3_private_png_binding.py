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

    def test_factory_rejects_noncanonical_uuid_spellings_before_reader_io(self):
        from unittest.mock import patch

        factory = self.make(lambda *args: False)
        # UUID parser accepts alternate spellings, but a route reader must
        # have a single canonical scope for rights, storage and audit checks.
        variants = (
            (self.shop.upper(), self.job),
            (self.shop, self.job.upper()),
            (self.shop.replace("-", ""), self.job),
            (self.shop, "{" + self.job + "}"),
        )
        with patch("feature3_private_png_binding.Feature3RevocablePNGReader") as reader:
            for shop, job in variants:
                with self.subTest(shop=shop, job=job):
                    with self.assertRaisesRegex(ValueError, "canonical UUID"):
                        factory(shop, job)
            reader.assert_not_called()

    def test_factory_rejects_spoofed_scope_before_reader_construction(self):
        from unittest.mock import patch

        class SpoofedUUID(str):
            def __eq__(self, other):
                return True

        factory = self.make(lambda *args: False)
        with patch("feature3_private_png_binding.Feature3RevocablePNGReader") as reader:
            for shop, job in (
                (SpoofedUUID(self.shop), self.job),
                (self.shop, SpoofedUUID(self.job)),
                (object(), self.job),
                (self.shop, object()),
            ):
                with self.subTest(shop_type=type(shop).__name__, job_type=type(job).__name__):
                    with self.assertRaises(ValueError):
                        factory(shop, job)
            reader.assert_not_called()
        # Exact UUID strings still enter the ordinary secure reader path.
        reader = factory(self.shop, self.job)
        with self.assertRaises(PermissionError):
            reader.read(user_token="synthetic-not-hosted", shop_id=self.shop, job_id=self.job)

    def test_reader_uses_explicit_rights_authority_and_denies_fixture_membership(self):
        def rights(*args):
            self.calls.append(args)
            return False
        reader = self.make(rights)(self.shop, self.job)
        with self.assertRaises(PermissionError):
            reader.read(user_token="synthetic-token-not-hosted", shop_id=self.shop, job_id=self.job)
        # RLS denies before rights lookup; no storage bytes were fetched.
        self.assertEqual(self.calls, [])

    def test_factory_reader_rejects_cross_scope_before_jwt_or_rls(self):
        from feature3_private_png_reader import PrivateGeneratedDownloadDenied

        calls = []
        class GuardTenant(SyntheticTenant):
            def member(self, *args):
                calls.append("member")
                return False

        tenant = GuardTenant()
        def verifier(token):
            calls.append("verify")
            return str(uuid4())

        reader = self.make(lambda *args: False, verifier=verifier,
                           tenant=tenant)(self.shop, self.job)
        foreign_shop, foreign_job = str(uuid4()), str(uuid4())
        class Spoofed(str):
            def __eq__(self, other):
                return True
        for shop, job in (
            (foreign_shop, self.job),
            (self.shop, foreign_job),
            (Spoofed(self.shop), self.job),
            (self.shop, Spoofed(self.job)),
            (object(), self.job),
        ):
            with self.subTest(shop=shop, job=job):
                with self.assertRaises(PrivateGeneratedDownloadDenied):
                    reader.read(user_token="synthetic-not-hosted-token",
                                shop_id=shop, job_id=job)
        self.assertEqual(calls, [])
        # Same-scope request proceeds into normal JWT/RLS checks and denies
        # the synthetic tenant; scope guard must not grant access.
        with self.assertRaises(PermissionError):
            reader.read(user_token="synthetic-not-hosted-token",
                        shop_id=self.shop, job_id=self.job)
        self.assertIn("verify", calls)
        self.assertIn("member", calls)

    def test_bad_injected_tenant_and_verifier_fail_closed(self):
        with self.assertRaises(ValueError):
            self.make(lambda *args: False, tenant=object())
        with self.assertRaises(ValueError):
            self.make(lambda *args: False, verifier="not callable")

    def test_cross_project_tenant_binding_is_rejected_before_reader_creation(self):
        # Synthetic project/key mismatches are never a hosted auth assertion.
        for field, value in (
            ("origin", "https://foreign-project.supabase.co"),
            ("key", "sb_publishable_" + "z" * 24),
            ("origin", None),
            ("key", object()),
        ):
            with self.subTest(field=field, value=value):
                tenant = SyntheticTenant()
                setattr(tenant, field, value)
                with self.assertRaisesRegex(ValueError, "Tenant store must match"):
                    self.make(lambda *args: True, tenant=tenant)

    def test_matching_project_tenant_still_denies_without_rls_membership(self):
        reader = self.make(lambda *args: True)(self.shop, self.job)
        with self.assertRaises(PermissionError):
            reader.read(user_token="synthetic-unprivileged",
                        shop_id=self.shop, job_id=self.job)

    def test_rotated_project_denied_at_factory_and_cached_reader(self):
        from feature3_private_png_reader import PrivateGeneratedDownloadDenied

        for field, replacement in (
            ("origin", "https://foreign-project.supabase.co"),
            ("key", "sb_publishable_" + "z" * 24),
            ("origin", object()),
            ("key", object()),
        ):
            with self.subTest(field=field, replacement_type=type(replacement).__name__):
                tenant = SyntheticTenant()
                calls = []
                def verifier(token):
                    calls.append("jwt")
                    return str(uuid4())
                factory = self.make(lambda *args: calls.append("rights"),
                                    verifier=verifier, tenant=tenant)
                cached = factory(self.shop, self.job)
                setattr(tenant, field, replacement)
                with self.assertRaises(ValueError):
                    factory(self.shop, self.job)
                with self.assertRaises(PrivateGeneratedDownloadDenied):
                    cached.read(user_token="synthetic-unprivileged",
                                shop_id=self.shop, job_id=self.job)
                self.assertEqual(calls, [])

    def test_rotation_during_reader_construction_fails_before_reader_is_returned(self):
        from unittest.mock import patch

        for field, replacement in (
            ("origin", "https://other-project.supabase.co"),
            ("key", "sb_publishable_" + "z" * 24),
        ):
            with self.subTest(field=field):
                tenant = SyntheticTenant()
                calls = []

                class RotatingReader:
                    def __init__(self, **kwargs):
                        calls.append("construct")
                        setattr(tenant, field, replacement)

                    def read(self, **kwargs):
                        calls.append("read")
                        return b"synthetic-private-bytes"

                with patch("feature3_private_png_binding.Feature3RevocablePNGReader",
                           RotatingReader):
                    factory = self.make(
                        lambda *args: calls.append("rights"),
                        verifier=lambda token: calls.append("jwt"),
                        tenant=tenant,
                    )
                    with self.assertRaisesRegex(ValueError, "during reader construction"):
                        factory(self.shop, self.job)
                self.assertEqual(calls, ["construct"])

    def test_project_rotation_during_byte_read_denies_returned_bytes(self):
        from unittest.mock import patch
        from feature3_private_png_reader import PrivateGeneratedDownloadDenied

        for field, replacement in (
            ("origin", "https://foreign-project.supabase.co"),
            ("key", "sb_publishable_" + "z" * 24),
        ):
            with self.subTest(field=field):
                tenant = SyntheticTenant()
                class SimulatedReader:
                    def __init__(self, **kwargs):
                        pass

                    def read(self, **kwargs):
                        setattr(tenant, field, replacement)
                        return b"synthetic-private-png-bytes"

                with patch("feature3_private_png_binding.Feature3RevocablePNGReader", SimulatedReader):
                    reader = self.make(lambda *args: True, tenant=tenant)(self.shop, self.job)
                    with self.assertRaises(PrivateGeneratedDownloadDenied):
                        reader.read(user_token="synthetic-not-hosted",
                                    shop_id=self.shop, job_id=self.job)

    def test_project_config_read_outage_denies_cached_reader_before_jwt(self):
        from feature3_private_png_reader import PrivateGeneratedDownloadDenied

        class FlakyTenant(SyntheticTenant):
            def __init__(self):
                self.fail = False

            @property
            def origin(self):
                if self.fail:
                    raise RuntimeError("synthetic project configuration outage")
                return SyntheticTenant.origin

            @property
            def key(self):
                if self.fail:
                    raise RuntimeError("synthetic project key outage")
                return SyntheticTenant.key

        tenant = FlakyTenant()
        observed = []
        factory = self.make(
            lambda *args: observed.append("rights"),
            verifier=lambda token: observed.append("jwt"),
            tenant=tenant,
        )
        cached = factory(self.shop, self.job)
        tenant.fail = True
        with self.assertRaises(ValueError):
            factory(self.shop, self.job)
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            cached.read(user_token="synthetic-not-hosted",
                        shop_id=self.shop, job_id=self.job)
        self.assertEqual(observed, [])

    def test_side_effecting_key_getter_rotates_origin_and_denies_reader(self):
        from unittest.mock import patch
        from feature3_private_png_reader import PrivateGeneratedDownloadDenied

        class RotatingTenant(SyntheticTenant):
            def __init__(self):
                self.current_origin = SyntheticTenant.origin
                self.rotate = False
                self.key_reads = 0

            @property
            def origin(self):
                return self.current_origin

            @property
            def key(self):
                self.key_reads += 1
                if self.rotate:
                    self.current_origin = "https://foreign-project.supabase.co"
                return SyntheticTenant.key

        tenant = RotatingTenant()
        calls = []
        class SyntheticReader:
            def __init__(self, **kwargs):
                calls.append("construct")
            def read(self, **kwargs):
                calls.append("bytes")
                return b"synthetic-bytes"

        with patch("feature3_private_png_binding.Feature3RevocablePNGReader",
                   SyntheticReader):
            factory = self.make(lambda *args: calls.append("rights"),
                                verifier=lambda token: calls.append("jwt"),
                                tenant=tenant)
            cached = factory(self.shop, self.job)
            tenant.rotate = True
            with self.assertRaises(ValueError):
                factory(self.shop, self.job)
            with self.assertRaises(PrivateGeneratedDownloadDenied):
                cached.read(user_token="synthetic-not-hosted",
                            shop_id=self.shop, job_id=self.job)
        self.assertEqual(calls, ["construct"])

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
