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


if __name__ == "__main__":
    unittest.main()
