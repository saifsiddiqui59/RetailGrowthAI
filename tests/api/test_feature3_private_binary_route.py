"""F3-08 Azure boundary: synthetic two-shop denial, fail-closed injection."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_binary_route import private_png_response
from feature3_private_png_reader import PrivateGeneratedDownloadDenied
from test_feature3_private_binary_http import AuthorizedReader


class Request:
    method = "GET"
    headers = {"Authorization": "Bearer signed-retailer-test"}


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job = str(uuid4()), str(uuid4())
        self.reader = AuthorizedReader(self.shop, self.job)

    def invoke(self, factory=None, enabled=True, shop=None, job=None):
        return private_png_response(
            Request(), shop_id=shop or self.shop, job_id=job or self.job,
            reader_factory=factory, enabled=enabled)

    def test_disabled_or_unconfigured_never_reads_private_bytes(self):
        for enabled, factory, expected in (
            (False, lambda: self.reader, 404),
            (True, None, 503),
            (True, lambda: (_ for _ in ()).throw(RuntimeError("secret")), 503),
            (True, lambda: object(), 503),
        ):
            code, body, headers = self.invoke(factory, enabled)
            self.assertEqual((code, body), (expected, b""))
            self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
        self.assertEqual(self.reader.calls, [])

    def test_mock_current_rights_allow_and_foreign_tenant_denial(self):
        code, data, headers = self.invoke(lambda: self.reader)
        self.assertEqual(code, 200)
        self.assertEqual(data, self.reader.png)
        self.assertNotIn("Location", headers)
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        # The actual reader is required to deny foreign shop; this mock
        # intentionally simulates a current-rights failure, NOT hosted RLS.
        self.reader.fail = PrivateGeneratedDownloadDenied("foreign shop")
        code, data, headers = self.invoke(lambda: self.reader, shop=str(uuid4()))
        self.assertEqual((code, data), (404, b""))
        self.assertNotIn("object_path", str(headers).lower())

    def test_revoked_and_reader_outage_never_fall_back(self):
        self.reader.fail = PrivateGeneratedDownloadDenied("revoked")
        self.assertEqual(self.invoke(lambda: self.reader)[:2], (404, b""))
        self.reader.fail = TimeoutError("backend unavailable")
        self.assertEqual(self.invoke(lambda: self.reader)[:2], (503, b""))
        self.reader.fail = None
        self.assertEqual(self.invoke(lambda: self.reader)[0], 200)

    def test_bad_token_denied_before_reader(self):
        req = Request()
        req.headers = {"Authorization": "Bearer sb_secret_invalid"}
        code, body, _ = private_png_response(
            req, shop_id=self.shop, job_id=self.job,
            reader_factory=lambda: self.reader, enabled=True)
        self.assertEqual((code, body), (401, b""))
        self.assertEqual(self.reader.calls, [])


if __name__ == "__main__":
    unittest.main()
