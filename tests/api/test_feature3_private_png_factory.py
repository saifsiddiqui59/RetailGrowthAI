"""Synthetic F3-08 factory contract tests; not hosted JWT/RLS evidence."""
import sys
import base64
import json
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

    def test_malformed_jwt_segments_never_reach_verifier_or_store(self):
        calls = []
        class CountingStore(Store):
            def member(self, *args):
                calls.append("membership")
                raise AssertionError("unexpected tenant access")
        def verify(token):
            calls.append("verify")
            raise AssertionError("unexpected JWT verification")
        reader = TrustedPrivatePNGFactory(
            tenant_store=CountingStore(), verify_user_jwt=verify,
            current_output_rights=self.rights,
        )(self.shop, self.job)
        bad = (
            "abc", "a.b", "a.b.c.d", ".abc.def", "abc..def",
            "abc.def.", "abc.def.ghi=", "abc.def.ghi\\n",
            "abc.def.ghi xyz", "abc.def.ghi/", "abc.def.ghi+",
            "sb_secret_" + "a" * 30, "sb_publishable_" + "a" * 30,
            "a" * 4097 + ".bbb.ccc",
        )
        for token in bad:
            with self.subTest(token=token[:32]):
                with self.assertRaises(PrivateGeneratedDownloadDenied):
                    reader.read(user_token=token, shop_id=self.shop,
                                job_id=self.job)
        self.assertEqual(calls, [])

    def test_impossible_base64url_segment_lengths_denied_before_verifier(self):
        # A length modulo four of one is impossible for base64url-encoded
        # bytes, regardless of JWT signature or key. No tenant IO is allowed.
        calls = []
        class CountingStore(Store):
            def member(self, *args):
                calls.append("membership")
                raise AssertionError("unexpected RLS access")
        def verify(token):
            calls.append("verify")
            raise AssertionError("unexpected JWT verification")
        reader = TrustedPrivatePNGFactory(
            tenant_store=CountingStore(), verify_user_jwt=verify,
            current_output_rights=self.rights,
        )(self.shop, self.job)
        for token in ("abcde.bb.cc", "aa.abcde.cc", "aa.bb.abcde",
                      "a" * 4093 + ".bb.cc"):
            with self.subTest(token=token[:20]):
                with self.assertRaises(PrivateGeneratedDownloadDenied):
                    reader.read(user_token=token, shop_id=self.shop,
                                job_id=self.job)
        self.assertEqual(calls, [])

    def test_well_formed_synthetic_jwt_still_requires_real_verifier(self):
        calls = []
        def verify(token):
            calls.append(token)
            raise ValueError("synthetic token is not signed")
        reader = TrustedPrivatePNGFactory(
            tenant_store=Store(), verify_user_jwt=verify,
            current_output_rights=self.rights,
        )(self.shop, self.job)
        token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJmaXh0dXJlIn0.c2lnbmF0dXJl"
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            reader.read(user_token=token, shop_id=self.shop,
                        job_id=self.job)
        self.assertEqual(calls, [token])

    def test_untrusted_jose_header_rejected_without_verifier_or_tenant_io(self):
        calls = []
        class CountingStore(Store):
            def member(self, *args):
                calls.append("tenant")
                raise AssertionError("tenant access before signed verification")
        def verify(token):
            calls.append("verifier")
            raise AssertionError("unsigned/ambiguous JOSE must not reach verifier")
        reader = TrustedPrivatePNGFactory(
            tenant_store=CountingStore(), verify_user_jwt=verify,
            current_output_rights=self.rights,
        )(self.shop, self.job)
        headers = (
            '{"alg":"none"}',
            '{"alg":"HS256","alg":"none"}',
            '{"alg":"none","alg":"HS256"}',
            '{"alg":"HS512"}',
            '{"alg":123}',
            '{"alg":"HS256","crit":["exp"]}',
            '{"alg":"HS256","jku":"https://example.invalid/key"}',
            '{"alg":"HS256","jwk":{}}',
            '{"alg":"HS256","x5u":"https://example.invalid/cert"}',
            '{"alg":"HS256","x5c":[]}',
            '{"alg":"HS256","zip":"DEF"}',
            '[]', 'null', '{"typ":"JWT"}',
        )
        for header in headers:
            segment = base64.urlsafe_b64encode(header.encode()).decode().rstrip("=")
            token = segment + ".eyJzdWIiOiJmaXh0dXJlIn0.c2lnbmF0dXJl"
            with self.subTest(header=header):
                with self.assertRaises(PrivateGeneratedDownloadDenied):
                    reader.read(user_token=token, shop_id=self.shop, job_id=self.job)
        self.assertEqual(calls, [])

    def test_supported_jose_headers_still_require_cryptographic_verification(self):
        calls = []
        def verify(token):
            calls.append(token)
            raise ValueError("fixture is not cryptographically signed")
        reader = TrustedPrivatePNGFactory(
            tenant_store=Store(), verify_user_jwt=verify,
            current_output_rights=self.rights,
        )(self.shop, self.job)
        for algorithm in ("HS256", "RS256", "ES256"):
            segment = base64.urlsafe_b64encode(
                json.dumps({"alg": algorithm, "typ": "JWT"}).encode()
            ).decode().rstrip("=")
            token = segment + ".eyJzdWIiOiJmaXh0dXJlIn0.c2lnbmF0dXJl"
            with self.subTest(algorithm=algorithm):
                with self.assertRaises(PrivateGeneratedDownloadDenied):
                    reader.read(user_token=token, shop_id=self.shop, job_id=self.job)
            self.assertEqual(calls[-1], token)
        self.assertEqual(len(calls), 3)

    def test_ambiguous_payload_claims_denied_before_verifier_or_rls(self):
        calls = []
        class CountingStore(Store):
            def member(self, *args):
                calls.append("rls")
                raise AssertionError("tenant IO before verification")
        def verify(token):
            calls.append("jwt")
            raise AssertionError("ambiguous payload must not reach verifier")
        reader = TrustedPrivatePNGFactory(
            tenant_store=CountingStore(), verify_user_jwt=verify,
            current_output_rights=self.rights,
        )(self.shop, self.job)
        header = "eyJhbGciOiJIUzI1NiJ9"
        signature = "c2lnbmF0dXJl"
        for payload in (
            '{"sub":"one","sub":"two"}',
            '{"sub":null}', '{"sub":1}', '{"sub":""}',
            '[]', 'null', '{"role":"authenticated"}',
            '{"sub":"fixture","nested":{"x":1,"x":2}}',
            '{"sub":"fixture","nested":{"x":1,"x":2}}',
        ):
            segment = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
            with self.subTest(payload=payload):
                with self.assertRaises(PrivateGeneratedDownloadDenied):
                    reader.read(user_token=f"{header}.{segment}.{signature}",
                                shop_id=self.shop, job_id=self.job)
        self.assertEqual(calls, [])

    def test_valid_payload_still_requires_cryptographic_verification(self):
        calls = []
        def verify(token):
            calls.append(token)
            raise ValueError("unsigned synthetic fixture")
        reader = TrustedPrivatePNGFactory(
            tenant_store=Store(), verify_user_jwt=verify,
            current_output_rights=self.rights,
        )(self.shop, self.job)
        payload = base64.urlsafe_b64encode(
            b'{"sub":"fixture-user","role":"authenticated"}'
        ).decode().rstrip("=")
        token = f"eyJhbGciOiJIUzI1NiJ9.{payload}.c2lnbmF0dXJl"
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            reader.read(user_token=token, shop_id=self.shop, job_id=self.job)
        self.assertEqual(calls, [token])

    def test_valid_scope_reaches_real_reader_and_denies_fake_jwt(self):
        # No mocked success: the actual reader must reject the fixture token.
        reader = self.make()(self.shop, self.job)
        with self.assertRaises(Exception):
            reader.read(user_token="not-a-signed-jwt",
                        shop_id=self.shop, job_id=self.job)


if __name__ == "__main__":
    unittest.main()
