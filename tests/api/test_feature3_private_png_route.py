"""Synthetic F3-08 route adapter tests. Not hosted JWT/RLS verification."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_route import handle_private_png_request


class Request:
    def __init__(self, shop, job, authorization):
        self.route_params = {"shop_id": shop, "job_id": job}
        self.headers = {"Authorization": authorization}


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

    def call(self, token):
        return handle_private_png_request(
            Request(self.shop, self.job, token),
            reader_factory=self.factory, response_type=Response,
        )

    def test_missing_token_denied_before_reader(self):
        response = self.call("")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.body, b"")
        self.assertEqual(self.calls, 0)
        self.assertIsNone(response.mimetype)
        self.assertEqual(response.headers["Content-Length"], "0")

    def test_backend_outage_never_leaks_exception(self):
        response = self.call("Bearer " + "x" * 30)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body, b"")
        self.assertEqual(self.calls, 1)
        self.assertNotIn("synthetic", repr(response.headers))
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_invalid_scope_denied_before_reader(self):
        request = Request("not-a-shop", self.job, "Bearer " + "x" * 30)
        response = handle_private_png_request(
            request, reader_factory=self.factory, response_type=Response)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.calls, 0)

    def test_missing_route_metadata_fails_closed(self):
        request = Request(self.shop, self.job, "")
        request.route_params = None
        with self.assertRaises(ValueError):
            handle_private_png_request(
                request, reader_factory=self.factory, response_type=Response)


if __name__ == "__main__":
    unittest.main()
