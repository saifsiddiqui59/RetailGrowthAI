"""F3-08 synthetic HTTP adapter tests; no hosted auth or real media."""
import sys
import unittest
from pathlib import Path
from io import BytesIO
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_http_adapter import private_png_http_response
from feature3_private_png_reader import PrivateGeneratedDownloadDenied
from tenant_store import StorageUnavailable

SHOP = "11111111-1111-4111-8111-111111111111"
JOB = "22222222-2222-4222-8222-222222222222"
def synthetic_png():
    stream = BytesIO()
    Image.new("RGB", (256, 256), (25, 45, 70)).save(stream, format="PNG")
    return stream.getvalue()


PNG = synthetic_png()


class PrivatePNGHttpAdapterTests(unittest.TestCase):
    def test_success_returns_private_noncacheable_png(self):
        calls = []

        class Reader:
            def read(self, **kwargs):
                calls.append(kwargs)
                return PNG

        status, headers, body = private_png_http_response(
            reader_factory=lambda shop, job: Reader(), shop_id=SHOP,
            job_id=JOB, bearer_token="Bearer synthetic0.jwt.fixture")
        self.assertEqual(status, 200)
        self.assertEqual(body, PNG)
        self.assertEqual(headers["Content-Type"], "image/png")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("no-store", headers["Cache-Control"])
        self.assertEqual(calls, [{"user_token": "synthetic0.jwt.fixture", "shop_id": SHOP, "job_id": JOB}])

    def test_missing_or_malformed_bearer_never_calls_reader(self):
        calls = []
        def factory(*args):
            calls.append(args)
            raise AssertionError("Must not construct reader")
        for bearer in (None, "", "synthetic0.jwt.fixture", "Bearer ",
                       "Bearer  token", "Bearer token ", "bearer token"):
            with self.subTest(bearer=bearer):
                status, headers, body = private_png_http_response(
                    reader_factory=factory, shop_id=SHOP, job_id=JOB, bearer_token=bearer)
                self.assertEqual((status, body), (404, b""))
                self.assertIn("no-store", headers["Cache-Control"])
        self.assertEqual(calls, [])

    def test_supabase_api_keys_never_construct_private_reader(self):
        calls = []
        def factory(*args):
            calls.append(args)
            raise AssertionError("API key must never become a user JWT")
        for prefix in ("sb_secret_", "sb_publishable_"):
            with self.subTest(prefix=prefix):
                status, headers, body = private_png_http_response(
                    reader_factory=factory, shop_id=SHOP, job_id=JOB,
                    bearer_token="Bearer " + prefix + "synthetic.jwt.fixture")
                self.assertEqual((status, body), (404, b""))
                self.assertIn("no-store", headers["Cache-Control"])
        self.assertEqual(calls, [])

    def test_rights_denial_and_bad_bytes_never_escape(self):
        class Reader:
            def __init__(self, result):
                self.result = result
            def read(self, **kwargs):
                if isinstance(self.result, Exception):
                    raise self.result
                return self.result
        for result in (PrivateGeneratedDownloadDenied("foreign shop"),
                       bytearray(PNG), b"not a png" * 12, b"", PNG[:8],
                       b"\\\\x89PNG\\\\r\\\\n\\\\x1a\\\\n" + b"synthetic-fixture" * 8):
            with self.subTest(result=type(result).__name__):
                status, headers, body = private_png_http_response(
                    reader_factory=lambda shop, job: Reader(result),
                    shop_id=SHOP, job_id=JOB, bearer_token="Bearer synthetic0.jwt.fixture")
                self.assertEqual((status, body), (404, b""))
                self.assertNotIn("Content-Type", headers)

    def test_valid_signature_with_invalid_png_chunks_or_pixel_data_is_denied(self):
        # A forged reader may return bytes starting with a valid PNG magic
        # without a valid PNG; no such bytes may receive an HTTP 200.
        class Reader:
            def __init__(self, result):
                self.result = result

            def read(self, **kwargs):
                return self.result

        invalid = [
            PNG[:8] + b"synthetic-fixture" * 8,
            PNG + b"trailing-private-data",
            PNG[:-4] + b"FAIL",
        ]
        idat = PNG.index(b"IDAT")
        corrupt = bytearray(PNG)
        corrupt[idat + 4] ^= 0xFF
        invalid.append(bytes(corrupt))
        for payload in invalid:
            with self.subTest(payload_len=len(payload)):
                status, headers, body = private_png_http_response(
                    reader_factory=lambda shop, job: Reader(payload),
                    shop_id=SHOP, job_id=JOB,
                    bearer_token="Bearer synthetic0.jwt.fixture",
                )
                self.assertEqual((status, body), (404, b""))
                self.assertNotIn("Content-Type", headers)
        # All malformed attempts must leave a subsequent legitimate private
        # receipt readable, without a sticky fail-open or fail-closed state.
        status, headers, body = private_png_http_response(
            reader_factory=lambda shop, job: Reader(PNG),
            shop_id=SHOP, job_id=JOB,
            bearer_token="Bearer synthetic0.jwt.fixture",
        )
        self.assertEqual((status, body), (200, PNG))

    def test_oversized_png_and_untrusted_bearer_are_denied_before_delivery(self):
        calls = []
        class Reader:
            def read(self, **kwargs):
                calls.append(kwargs)
                return PNG[:8] + b"x" * (25 * 1024 * 1024)
        def factory(shop, job):
            calls.append((shop, job))
            return Reader()

        for token in ("Bearer synthetic0.jwt.fixture\\n", "Bearer synthetic,jwt.fixture",
                      "Bearer synthetic;jwt.fixture", "Bearer " + "x" * 8193,
                      "Bearer synthetic\\tjwt.fixture"):
            with self.subTest(token=token[:30]):
                status, headers, body = private_png_http_response(
                    reader_factory=factory, shop_id=SHOP, job_id=JOB, bearer_token=token)
                self.assertEqual((status, body), (404, b""))
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(calls, [])
        status, headers, body = private_png_http_response(
            reader_factory=factory, shop_id=SHOP, job_id=JOB,
            bearer_token="Bearer synthetic0.jwt.fixture")
        self.assertEqual((status, body), (404, b""))
        self.assertNotIn("Content-Type", headers)
        self.assertEqual(len(calls), 2)

    def test_noncanonical_scope_is_denied_before_reader_factory(self):
        calls = []
        def factory(*args):
            calls.append(args)
            raise AssertionError("Untrusted scope reached factory")

        for shop, job in (
            ("synthetic-shop", JOB),
            (SHOP, "synthetic-job"),
            ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa".upper(), JOB),
            ("11111111-1111-1111-8111-111111111111", JOB),
            (SHOP, "22222222-2222-4222-8222-22222222222z"),
            (None, JOB),
            (SHOP, object()),
        ):
            with self.subTest(shop=shop, job=job):
                status, headers, body = private_png_http_response(
                    reader_factory=factory, shop_id=shop, job_id=job,
                    bearer_token="Bearer synthetic0.jwt.fixture")
                self.assertEqual((status, body), (404, b""))
                self.assertNotIn("Content-Type", headers)
        self.assertEqual(calls, [])

    def test_invalid_compact_jws_never_constructs_private_reader(self):
        calls = []
        def factory(*args):
            calls.append(args)
            raise AssertionError("Malformed JWS must not reach scoped reader")

        for token in (
            "opaque-token-value",
            "a.b",
            "a.b.c.d",
            ".payload.signature",
            "header..signature",
            "header.payload.",
            "a.payload.signature",  # invalid base64url segment length
            "header.payload.sign+ature",
            "header.payload.sign/ature",
            "header.payload.sign=ature",
            "header.payload." + "x" * 2049,
        ):
            with self.subTest(token=token[:40]):
                status, headers, body = private_png_http_response(
                    reader_factory=factory, shop_id=SHOP, job_id=JOB,
                    bearer_token="Bearer " + token)
                self.assertEqual((status, body), (404, b""))
                self.assertIn("no-store", headers["Cache-Control"])
        self.assertEqual(calls, [])

    def test_backend_outage_returns_opaque_noncacheable_503(self):
        class Reader:
            def __init__(self, failure):
                self.failure = failure

            def read(self, **kwargs):
                raise self.failure

        for failure in (StorageUnavailable("synthetic backend secret"), OSError("synthetic network path")):
            with self.subTest(failure=type(failure).__name__):
                status, headers, body = private_png_http_response(
                    reader_factory=lambda shop, job: Reader(failure),
                    shop_id=SHOP, job_id=JOB,
                    bearer_token="Bearer synthetic0.jwt.fixture")
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Retry-After"], "5")
                self.assertIn("no-store", headers["Cache-Control"])
                self.assertNotIn("Content-Type", headers)

    def test_missing_trusted_factory_is_configuration_error(self):
        with self.assertRaises(ValueError):
            private_png_http_response(reader_factory=None, shop_id=SHOP,
                                      job_id=JOB, bearer_token="Bearer synthetic")


if __name__ == "__main__":
    unittest.main()
