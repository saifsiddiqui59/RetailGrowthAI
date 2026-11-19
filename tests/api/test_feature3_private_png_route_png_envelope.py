"""F3-08 synthetic Azure PNG envelope truncation checks (not hosted authorization)."""
import hashlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_route import handle_private_png_request

PNG_SIGNATURE = bytes.fromhex("89504e470d0a1a0a")
PNG_IEND = bytes.fromhex("0000000049454e44ae426082")


class Response:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Request:
    method = "GET"
    params = {}
    headers = {"Authorization": "Bearer synthetic-not-a-real-jwt"}

    def __init__(self):
        self.route_params = {"shop_id": str(uuid4()), "job_id": str(uuid4())}

    def get_body(self):
        return b""


class PNGEnvelopeBoundaryTests(unittest.TestCase):
    def run_case(self, png):
        req = Request()
        headers = {
            "Content-Type": "image/png",
            "Content-Length": str(len(png)),
            "Cache-Control": "no-store, private, max-age=0",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'",
            "Vary": "Authorization",
            "Content-Disposition": f'attachment; filename="feature3-{req.route_params["job_id"]}.png"',
            "X-Feature3-Shop-Id": req.route_params["shop_id"],
            "X-Feature3-Job-Id": req.route_params["job_id"],
            "X-Feature3-Media-Asset-Id": str(uuid4()),
            "X-Feature3-Image-Sha256": hashlib.sha256(png).hexdigest(),
        }
        fake = SimpleNamespace(status=200, body=png, headers=headers)
        with patch("feature3_private_png_route.private_png_http", return_value=fake):
            return handle_private_png_request(
                req, reader_factory=lambda *_: None, response_type=Response)

    def test_signature_only_is_not_a_png_download(self):
        for png in (PNG_SIGNATURE, PNG_SIGNATURE + b"synthetic",
                    PNG_SIGNATURE + b"0" * 48):
            with self.subTest(length=len(png)):
                result = self.run_case(png)
                self.assertEqual(result.status_code, 503)
                self.assertEqual(result.body, b"")

    def test_complete_envelope_can_pass_adapter_with_synthetic_receipts(self):
        # Boundary-only fixture; the canonical private reader performs full
        # PNG validation and authorization in production.
        png = PNG_SIGNATURE + b"synthetic-payload" * 3 + PNG_IEND
        result = self.run_case(png)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.body, png)
        self.assertEqual(result.headers["Cache-Control"], "no-store, private")


if __name__ == "__main__":
    unittest.main()
