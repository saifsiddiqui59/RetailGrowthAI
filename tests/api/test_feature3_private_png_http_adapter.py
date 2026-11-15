"""F3-08 synthetic HTTP adapter tests; no hosted auth or real media."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_http_adapter import private_png_http_response
from feature3_private_png_reader import PrivateGeneratedDownloadDenied

SHOP = "synthetic-shop"
JOB = "synthetic-job"
PNG = bytes((137, 80, 78, 71, 13, 10, 26, 10)) + b"synthetic-fixture" * 8


class PrivatePNGHttpAdapterTests(unittest.TestCase):
    def test_success_returns_private_noncacheable_png(self):
        calls = []

        class Reader:
            def read(self, **kwargs):
                calls.append(kwargs)
                return PNG

        status, headers, body = private_png_http_response(
            reader_factory=lambda shop, job: Reader(), shop_id=SHOP,
            job_id=JOB, bearer_token="Bearer synthetic.jwt.fixture")
        self.assertEqual(status, 200)
        self.assertEqual(body, PNG)
        self.assertEqual(headers["Content-Type"], "image/png")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("no-store", headers["Cache-Control"])
        self.assertEqual(calls, [{"user_token": "synthetic.jwt.fixture", "shop_id": SHOP, "job_id": JOB}])

    def test_missing_or_malformed_bearer_never_calls_reader(self):
        calls = []
        def factory(*args):
            calls.append(args)
            raise AssertionError("Must not construct reader")
        for bearer in (None, "", "synthetic.jwt.fixture", "Bearer ",
                       "Bearer  token", "Bearer token ", "bearer token"):
            with self.subTest(bearer=bearer):
                status, headers, body = private_png_http_response(
                    reader_factory=factory, shop_id=SHOP, job_id=JOB, bearer_token=bearer)
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
                       bytearray(PNG), b"not a png" * 12, b"", PNG[:8],\n                       b"\\\\x89PNG\\\\r\\\\n\\\\x1a\\\\n" + b"synthetic-fixture" * 8):
            with self.subTest(result=type(result).__name__):
                status, headers, body = private_png_http_response(
                    reader_factory=lambda shop, job: Reader(result),
                    shop_id=SHOP, job_id=JOB, bearer_token="Bearer synthetic")
                self.assertEqual((status, body), (404, b""))
                self.assertNotIn("Content-Type", headers)

    def test_missing_trusted_factory_is_configuration_error(self):
        with self.assertRaises(ValueError):
            private_png_http_response(reader_factory=None, shop_id=SHOP,
                                      job_id=JOB, bearer_token="Bearer synthetic")


if __name__ == "__main__":
    unittest.main()
