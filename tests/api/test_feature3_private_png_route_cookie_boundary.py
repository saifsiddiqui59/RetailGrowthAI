"""F3-08: synthetic bearer-only route must not accept ambient cookies.

These fixtures are not hosted signed-user or tenant-isolation evidence.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_route import handle_private_png_request


class Response:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Request:
    method = "GET"
    params = {}

    def __init__(self, headers):
        self.route_params = {"shop_id": str(uuid4()), "job_id": str(uuid4())}
        self.headers = headers
        self.body_reads = 0

    def get_body(self):
        self.body_reads += 1
        return b""


class CookieBoundaryTests(unittest.TestCase):
    def test_cookie_headers_fail_before_body_or_private_reader(self):
        for key in ("Cookie", "cookie", "COOKIE", "Cookie2", "Set-Cookie"):
            with self.subTest(header=key):
                req = Request({
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    key: "session=synthetic-test-only",
                })
                with patch("feature3_private_png_route.private_png_http") as backend:
                    result = handle_private_png_request(
                        req, reader_factory=lambda: None, response_type=Response
                    )
                self.assertEqual(result.status_code, 400)
                self.assertEqual(result.body, b"")
                self.assertEqual(result.headers["Cache-Control"], "no-store, private")
                self.assertEqual(req.body_reads, 0)
                backend.assert_not_called()

    def test_proxy_identity_header_families_fail_before_body_or_reader(self):
        # Synthetic identity metadata is never proof of a signed user.
        for key in (
            "X-Auth-Request-User", "x-auth-request-email",
            "X-MS-TOKEN-AAD-ACCESS-TOKEN", "X-Client-Cert-Subject",
            "X-Forwarded-Client-Cert", "X-SSL-Client-Verify",
            "X-User-Role", "x-user-tenant",
        ):
            with self.subTest(header=key):
                req = Request({
                    "Authorization": "Bearer synthetic-not-a-real-jwt",
                    key: "synthetic-proxy-identity",
                })
                with patch("feature3_private_png_route.private_png_http") as backend:
                    result = handle_private_png_request(
                        req, reader_factory=lambda: None, response_type=Response
                    )
                self.assertEqual(result.status_code, 400)
                self.assertEqual(result.body, b"")
                self.assertEqual(req.body_reads, 0)
                backend.assert_not_called()

    def test_bearer_without_cookie_reaches_canonical_adapter(self):
        req = Request({"Authorization": "Bearer synthetic-not-a-real-jwt"})
        with patch(
            "feature3_private_png_route.private_png_http",
            return_value=SimpleNamespace(status=404, body=b"", headers={}),
        ) as backend:
            result = handle_private_png_request(
                req, reader_factory=lambda: None, response_type=Response
            )
        self.assertEqual(result.status_code, 404)
        self.assertEqual(req.body_reads, 1)
        backend.assert_called_once()


if __name__ == "__main__":
    unittest.main()
