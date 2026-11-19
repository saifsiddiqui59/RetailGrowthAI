"""F3-08 synthetic private PNG backend failure isolation regressions.

No hosted credentials, real rights, or tenant authority are used here.
"""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_route import handle_private_png_request


class FakeResponse:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeRequest:
    def __init__(self):
        self.method = "GET"
        self.route_params = {"shop_id": str(uuid4()), "job_id": str(uuid4())}
        self.headers = {"Authorization": "Bearer synthetic-not-a-real-jwt"}
        self.params = {}
        self.body_reads = 0

    def get_body(self):
        self.body_reads += 1
        return b""


class BackendFailureIsolationTests(unittest.TestCase):
    def invoke(self, backend):
        request = FakeRequest()
        calls = []
        with patch("feature3_private_png_route.private_png_http", side_effect=lambda **kw: (calls.append(kw), backend)[1]):
            result = handle_private_png_request(
                request, reader_factory=lambda *args: None,
                response_type=FakeResponse)
        self.assertEqual(request.body_reads, 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["shop_id"], request.route_params["shop_id"])
        self.assertEqual(calls[0]["job_id"], request.route_params["job_id"])
        self.assertEqual(calls[0]["authorization"], request.headers["Authorization"])
        self.assertEqual(result.body, b"")
        self.assertEqual(result.headers["Content-Length"], "0")
        self.assertEqual(result.headers["Cache-Control"], "no-store, private")
        self.assertEqual(result.headers["Vary"], "Authorization")
        self.assertEqual(result.headers["X-Content-Type-Options"], "nosniff")
        self.assertNotIn("Location", result.headers)
        self.assertNotIn("Set-Cookie", result.headers)
        self.assertNotIn("X-Feature3-Shop-Id", result.headers)
        return result

    def test_backend_exceptions_are_opaque_and_never_leak_private_diagnostics(self):
        request = FakeRequest()
        calls = []
        def failing_backend(**kwargs):
            calls.append(kwargs)
            raise RuntimeError("synthetic-private-tenant-secret")
        with patch("feature3_private_png_route.private_png_http", side_effect=failing_backend):
            result = handle_private_png_request(
                request, reader_factory=lambda *args: None,
                response_type=FakeResponse)
        self.assertEqual(len(calls), 1)
        self.assertEqual(request.body_reads, 1)
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.body, b"")
        self.assertEqual(result.headers["Content-Length"], "0")
        self.assertEqual(result.headers["Cache-Control"], "no-store, private")
        self.assertNotIn("synthetic-private-tenant-secret", str(result.__dict__))

    def test_hostile_backend_response_properties_fail_closed(self):
        class HostileResponse:
            @property
            def status(self):
                raise RuntimeError("synthetic-private-diagnostic")
        self.assertEqual(self.invoke(HostileResponse()).status_code, 503)

    def test_success_with_missing_scope_receipts_is_never_released(self):
        # A synthetic PNG signature is not evidence of a real authorized asset.
        # Even a correctly declared byte count cannot replace backend attestation.
        png = bytes.fromhex("89504e470d0a1a0a") + b"synthetic-fixture"
        self.assertEqual(self.invoke(SimpleNamespace(
            status=200, body=png,
            headers={"Content-Type": "image/png",
                     "Content-Length": str(len(png)),
                     "Cache-Control": "no-store, private",
                     "Pragma": "no-cache",
                     "X-Content-Type-Options": "nosniff",
                     "Content-Security-Policy": "default-src 'none'",
                     "Vary": "Authorization"})).status_code, 503)

    def test_empty_canonical_denials_preserve_only_opaque_status(self):
        for status in (400, 401, 403, 404, 409, 410, 503):
            with self.subTest(status=status):
                result = self.invoke(SimpleNamespace(
                    status=status, body=b"", headers={
                        "Location": "https://synthetic.invalid/secret",
                        "Set-Cookie": "synthetic=secret",
                        "X-Feature3-Shop-Id": str(uuid4())}))
                self.assertEqual(result.status_code, status)

    def test_denials_with_body_never_expose_backend_diagnostics(self):
        for status in (400, 401, 403, 404, 409, 410, 503):
            with self.subTest(status=status):
                result = self.invoke(SimpleNamespace(
                    status=status, body=b"synthetic private diagnostic",
                    headers={"Content-Type": "text/plain"}))
                self.assertEqual(result.status_code, 503)

    def test_redirect_partial_cache_and_server_statuses_fail_closed(self):
        for status in (200.0, True, 201, 206, 301, 302, 304, 307, 308, 418, 429, 500, 502, 504):
            with self.subTest(status=status):
                result = self.invoke(SimpleNamespace(
                    status=status, body=b"", headers={
                        "Location": "https://synthetic.invalid/private"}))
                self.assertEqual(result.status_code, 503)

    def test_malformed_backend_envelopes_fail_closed(self):
        cases = (
            None,
            object(),
            SimpleNamespace(status=404, body="synthetic diagnostic", headers={}),
            SimpleNamespace(status=404, body=b"", headers=[]),
            SimpleNamespace(status=404, body=b""),
            SimpleNamespace(status=200, body=b"not a PNG", headers={}),
        )
        for backend in cases:
            with self.subTest(backend=repr(backend)):
                self.assertEqual(self.invoke(backend).status_code, 503)


if __name__ == "__main__":
    unittest.main()
