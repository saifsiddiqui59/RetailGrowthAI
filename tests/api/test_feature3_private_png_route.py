"""Synthetic F3-08 route adapter tests. Not hosted JWT/RLS verification."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_route import handle_private_png_request


class Request:
    def __init__(self, shop, job, authorization, method="GET"):
        self.method = method
        self.route_params = {"shop_id": shop, "job_id": job}
        self.headers = {"Authorization": authorization}
        self.params = {}


class Response:
    def __init__(self, *, body, status_code, headers, mimetype):
        self.body = body
        self.status_code = status_code
        self.headers = headers
        self.mimetype = mimetype


class RouteAdapterTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job = str(uuid4()), str(uuid4())
        self.calls = 0

    def factory(self, shop, job):
        self.calls += 1
        raise RuntimeError("synthetic backend unavailable")

    def call(self, token, request=None, factory=None):
        return handle_private_png_request(
            request or Request(self.shop, self.job, token),
            reader_factory=self.factory if factory is None else factory,
            response_type=Response,
        )

    def assert_denied_without_reader(self, request, status):
        response = self.call("", request=request)
        self.assertEqual(response.status_code, status)
        self.assertEqual(response.body, b"")
        self.assertEqual(self.calls, 0)
        self.assertIsNone(response.mimetype)
        self.assertEqual(response.headers["Content-Length"], "0")
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_missing_token_denied_before_reader(self):
        self.assert_denied_without_reader(Request(self.shop, self.job, ""), 401)

    def test_backend_outage_never_leaks_exception(self):
        response = self.call("Bearer " + "x" * 30)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body, b"")
        self.assertEqual(self.calls, 1)
        self.assertNotIn("synthetic", repr(response.headers))

    def test_invalid_scope_denied_before_reader(self):
        self.assert_denied_without_reader(Request("not-a-shop", self.job, "Bearer " + "x" * 30), 404)

    def test_missing_route_metadata_fails_closed(self):
        request = Request(self.shop, self.job, "")
        request.route_params = None
        self.assert_denied_without_reader(request, 400)

    def test_non_get_methods_denied_before_reader(self):
        for method in ("POST", "HEAD", "OPTIONS", "DELETE"):
            with self.subTest(method=method):
                self.assert_denied_without_reader(Request(self.shop, self.job, "Bearer " + "x" * 30, method), 405)

    def test_unexpected_route_identity_denied(self):
        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        request.route_params["asset_id"] = str(uuid4())
        self.assert_denied_without_reader(request, 400)

    def test_query_cannot_override_route_scope(self):
        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        request.params = {"shop_id": str(uuid4())}
        self.assert_denied_without_reader(request, 400)

    def test_unavailable_factory_never_serves_bytes(self):
        response = self.call("Bearer " + "x" * 30, factory=False)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body, b"")
        self.assertEqual(self.calls, 0)

    def test_malformed_headers_denied(self):
        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        request.headers = None
        self.assert_denied_without_reader(request, 400)


if __name__ == "__main__":
    unittest.main()
