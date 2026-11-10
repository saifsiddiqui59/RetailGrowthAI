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
        self.body = b""

    def get_body(self):
        return self.body


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
        self.assert_denied_without_reader(Request("not-a-shop", self.job, "Bearer " + "x" * 30), 400)

    def test_missing_route_metadata_fails_closed(self):
        request = Request(self.shop, self.job, "")
        request.route_params = None
        self.assert_denied_without_reader(request, 400)

    def test_non_get_methods_denied_before_reader(self):
        for method in ("POST", "HEAD", "OPTIONS", "DELETE"):
            with self.subTest(method=method):
                self.assert_denied_without_reader(Request(self.shop, self.job, "Bearer " + "x" * 30, method), 405)

    def test_spoofed_get_method_denied_before_reader(self):
        # A Python object can claim equality to GET without being an HTTP
        # method string. Never let it reach the rights reader.
        class EqualGet:
            def __eq__(self, other):
                return other == "GET"

        class SpoofedMethod(str):
            def __eq__(self, other):
                return True

        for method in (EqualGet(), SpoofedMethod("POST"), None, b"GET"):
            with self.subTest(method=type(method).__name__):
                request = Request(self.shop, self.job, "Bearer " + "x" * 30, method)
                self.assert_denied_without_reader(request, 405)

    def test_unexpected_route_identity_denied(self):
        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        request.route_params["asset_id"] = str(uuid4())
        self.assert_denied_without_reader(request, 400)

    def test_query_cannot_override_route_scope(self):
        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        request.params = {"shop_id": str(uuid4())}
        self.assert_denied_without_reader(request, 400)

    def test_get_with_nonempty_body_denied_before_reader(self):
        for body in (b'{"shop_id":"forged"}', b"token=forged", b"\\x00"):
            with self.subTest(body=body):
                request = Request(self.shop, self.job, "Bearer " + "x" * 30)
                request.body = body
                self.assert_denied_without_reader(request, 400)

    def test_unreadable_or_malformed_get_body_denied(self):
        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        request.get_body = lambda: "not bytes"
        self.assert_denied_without_reader(request, 400)
        request.get_body = lambda: (_ for _ in ()).throw(ValueError("synthetic"))
        self.assert_denied_without_reader(request, 400)

    def test_unavailable_factory_never_serves_bytes(self):
        response = self.call("Bearer " + "x" * 30, factory=False)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body, b"")
        self.assertEqual(self.calls, 0)

    def test_oversized_header_names_denied_before_body_or_reader(self):
        # A malicious adapter may expose a huge header key even when there
        # are only a few keys. Deny it before reading the body or rights.
        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        request.headers["X-" + "a" * 300] = "fixture"
        request.get_body = lambda: self.fail("GET body read before header denial")
        self.assert_denied_without_reader(request, 400)

    def test_header_name_limit_allows_normal_request_to_reach_reader(self):
        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        request.headers["X-" + "a" * 254] = "fixture"
        response = self.call("", request=request)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.calls, 1)

    def test_oversized_header_value_denied_before_body_and_reader(self):
        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        request.headers["X-Synthetic-Overflow"] = "x" * 20000
        request.get_body = lambda: self.fail("body read before oversized header denial")
        self.assert_denied_without_reader(request, 400)

    def test_cumulative_header_budget_denied_before_body_and_reader(self):
        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        for index in range(10):
            request.headers[f"X-Synthetic-{index}"] = "a" * 2000
        request.get_body = lambda: self.fail("body read before header budget denial")
        self.assert_denied_without_reader(request, 400)

    def test_header_budget_boundary_keeps_normal_auth_path(self):
        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        # Exactly 16384 total key+value characters is permitted.
        baseline = sum(len(k) + len(v) for k, v in request.headers.items())
        request.headers["X-Fixture"] = "a" * (16384 - baseline - len("X-Fixture"))
        response = self.call("", request=request)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.calls, 1)

    def test_stateful_authorization_mapping_is_read_only_once(self):
        # A synthetic proxy mapping swaps the bearer token on repeated reads.
        # The adapter must validate and pass one stable credential snapshot.
        class FlippingHeaders(dict):
            def __init__(self, initial):
                super().__init__(initial)
                self.auth_reads = 0

            def get(self, key, default=None):
                if key == "Authorization":
                    self.auth_reads += 1
                    if self.auth_reads > 1:
                        return "Bearer " + "z" * 30
                return super().get(key, default)

        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        request.headers = FlippingHeaders(request.headers)
        response = self.call("", request=request)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.calls, 1)
        self.assertEqual(request.headers.auth_reads, 1)

    def test_stateful_content_length_cannot_change_after_validation(self):
        class FlippingHeaders(dict):
            def __init__(self, initial):
                super().__init__(initial)
                self.length_reads = 0

            def get(self, key, default=None):
                if key == "Content-Length":
                    self.length_reads += 1
                    return "0" if self.length_reads == 1 else "99"
                return super().get(key, default)

        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        request.headers["Content-Length"] = "0"
        request.headers = FlippingHeaders(request.headers)
        response = self.call("", request=request)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.calls, 1)
        self.assertEqual(request.headers.length_reads, 1)

    def test_malformed_headers_denied(self):
        request = Request(self.shop, self.job, "Bearer " + "x" * 30)
        request.headers = None
        self.assert_denied_without_reader(request, 400)


if __name__ == "__main__":
    unittest.main()
