"""F3-08 synthetic backend security-header integrity checks (not hosted proof)."""
import hashlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
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

    def __init__(self):
        self.route_params = {"shop_id": str(uuid4()), "job_id": str(uuid4())}
        self.headers = {"Authorization": "Bearer synthetic-test-token"}

    def get_body(self):
        return b""


class PrivateResponseSecurityHeaders(unittest.TestCase):
    def test_missing_or_tampered_protection_fails_closed(self):
        req = Request()
        image = bytes.fromhex("89504e470d0a1a0a") + b"synthetic-only"
        headers = {
            "Content-Type": "image/png",
            "Content-Length": str(len(image)),
            "Cache-Control": "no-store, private, max-age=0",
            "X-Feature3-Shop-Id": req.route_params["shop_id"],
            "X-Feature3-Job-Id": req.route_params["job_id"],
            "X-Feature3-Media-Asset-Id": str(uuid4()),
            "X-Feature3-Image-Sha256": hashlib.sha256(image).hexdigest(),
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'",
            "Vary": "Authorization",
            "Content-Disposition": f'attachment; filename="feature3-{req.route_params["job_id"]}.png"',
        }
        for key in ("Pragma", "X-Content-Type-Options", "Content-Security-Policy",
                    "Vary", "Content-Disposition"):
            with self.subTest(missing=key):
                broken = dict(headers)
                del broken[key]
                with patch("feature3_private_png_route.private_png_http",
                           return_value=SimpleNamespace(status=200, body=image, headers=broken)):
                    result = handle_private_png_request(
                        req, reader_factory=lambda *args: None, response_type=Response)
                self.assertEqual(result.status_code, 503)
                self.assertEqual(result.body, b"")
        with patch("feature3_private_png_route.private_png_http",
                   return_value=SimpleNamespace(status=200, body=image, headers=headers)):
            result = handle_private_png_request(
                req, reader_factory=lambda *args: None, response_type=Response)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.body, image)


if __name__ == "__main__":
    unittest.main()
