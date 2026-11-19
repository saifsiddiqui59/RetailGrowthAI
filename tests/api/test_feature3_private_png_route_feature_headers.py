"""Synthetic F3-08 rejection of untrusted Feature3 extension headers.

These fixtures do not represent signed hosted identities or commercial rights.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_route import handle_private_png_request


class Response:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Request:
    method = "GET"
    params = {}

    def __init__(self, extra):
        self.route_params = {"shop_id": str(uuid4()), "job_id": str(uuid4())}
        self.headers = {"Authorization": "Bearer synthetic-test-token-1234", **extra}
        self.body_reads = 0

    def get_body(self):
        self.body_reads += 1
        return b""


class FeatureHeaderIsolationTests(unittest.TestCase):
    def test_unknown_feature3_extension_headers_are_never_authority(self):
        for header in (
            "X-Feature3-Reviewer-Approved",
            "x-feature3-source-rights-v2",
            "X-Feature3-Worker-Lease",
            "X-Feature3-Download-Allowed",
            "X-Feature3-Future-Authorization",
        ):
            with self.subTest(header=header):
                request = Request({header: "true"})
                with patch("feature3_private_png_route.private_png_http") as backend:
                    response = handle_private_png_request(
                        request, reader_factory=lambda *args: None,
                        response_type=Response)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.body, b"")
                self.assertEqual(request.body_reads, 0)
                backend.assert_not_called()

    def test_alternate_proxy_credentials_never_reach_reader(self):
        for header in (
            "X-Api-Key", "X-Supabase-Auth", "X-User-JWT",
            "X-Forwarded-Access-Token", "X-Forwarded-Id-Token",
            "X-Original-Access-Token", "X-Original-Id-Token",
        ):
            with self.subTest(header=header):
                request = Request({header: "synthetic-credential-not-authority"})
                with patch("feature3_private_png_route.private_png_http") as backend:
                    response = handle_private_png_request(
                        request, reader_factory=lambda *args: None,
                        response_type=Response)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.body, b"")
                self.assertEqual(request.body_reads, 0)
                backend.assert_not_called()


    def test_future_proxy_identity_families_fail_before_body_and_backend(self):
        # Prefix-based denial prevents a future proxy extension from being
        # mistaken for verified JWT/RLS authority. Synthetic values only.
        for header in (
            "X-Forwarded-User-Email",
            "X-Forwarded-Identity-Claims",
            "X-Authenticated-Groups",
            "X-Remote-User-Roles",
            "X-Identity-Provider",
            "X-Supabase-Role",
            "X-JWT-Claims",
            "X-Access-Token-Subject",
        ):
            with self.subTest(header=header):
                request = Request({header: "synthetic-forged-authority"})
                with patch("feature3_private_png_route.private_png_http") as backend:
                    response = handle_private_png_request(
                        request, reader_factory=lambda *args: None,
                        response_type=Response)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.body, b"")
                self.assertEqual(request.body_reads, 0)
                backend.assert_not_called()


    def test_future_cloud_identity_header_suffixes_fail_closed(self):
        # Provider identity metadata is never an alternative to the verified
        # retailer bearer JWT, even when a proxy adds new header suffixes.
        for header in (
            "X-MS-CLIENT-PRINCIPAL-ROLES-V2",
            "X-AMZN-OIDC-CUSTOM-CLAIMS",
            "X-GOOG-AUTHENTICATED-USER-GROUPS",
            "CF-ACCESS-IDENTITY-CLAIMS",
        ):
            with self.subTest(header=header):
                request = Request({header: "synthetic-not-verified-authority"})
                with patch("feature3_private_png_route.private_png_http") as backend:
                    response = handle_private_png_request(
                        request, reader_factory=lambda *args: None,
                        response_type=Response)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.body, b"")
                self.assertEqual(request.body_reads, 0)
                backend.assert_not_called()


if __name__ == "__main__":
    unittest.main()
