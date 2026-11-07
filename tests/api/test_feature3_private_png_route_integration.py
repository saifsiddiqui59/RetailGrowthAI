"""F3-08 synthetic private PNG route integration: no hosted identity/rights claims."""
import io
import sys
import unittest
from pathlib import Path
from uuid import uuid4

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_route import handle_private_png_request


class Request:
    method = "GET"
    params = {}

    def __init__(self, shop, job, token):
        self.route_params = {"shop_id": shop, "job_id": job}
        self.headers = {"Authorization": "Bearer " + token}

    def get_body(self):
        return b""


class Response:
    def __init__(self, *, body, status_code, headers, mimetype):
        self.body, self.status_code = body, status_code
        self.headers, self.mimetype = headers, mimetype


def synthetic_png():
    image = Image.new("RGB", (256, 256))
    pixels = image.load()
    for y in range(256):
        for x in range(256):
            pixels[x, y] = (x, y, (x ^ y))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class PrivateRouteIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.png = synthetic_png()

    def setUp(self):
        self.shop, self.job = str(uuid4()), str(uuid4())
        self.token = "synthetic-nonprivileged-token-0001"
        self.calls = []

    def serve(self, *, reader_shop=None, reader_job=None, rights=True, bytes_override=None):
        shop, job = self.shop, self.job
        calls = self.calls
        png = self.png if bytes_override is None else bytes_override

        class Reader:
            def read(self, *, user_token, shop_id, job_id):
                calls.append((user_token, shop_id, job_id))
                if not rights:
                    from feature3_private_png_reader import PrivateGeneratedDownloadDenied
                    raise PrivateGeneratedDownloadDenied("synthetic revoked")
                return {
                    "shop_id": reader_shop or shop,
                    "job_id": reader_job or job,
                    "image_bytes": png,
                    "mime_type": "image/png",
                    "private": True,
                    "signed_url_issued": False,
                }

        def factory(shop_id, job_id):
            self.assertEqual((shop_id, job_id), (shop, job))
            return Reader()

        return handle_private_png_request(
            Request(shop, job, self.token),
            reader_factory=factory,
            response_type=Response,
        )

    def test_synthetic_positive_png_bytes_and_no_cache(self):
        reply = self.serve()
        self.assertEqual(reply.status_code, 200)
        self.assertEqual(reply.body, self.png)
        self.assertEqual(reply.mimetype, "image/png")
        self.assertEqual(reply.headers["Content-Length"], str(len(self.png)))
        self.assertIn("no-store", reply.headers["Cache-Control"])
        self.assertEqual(self.calls, [(self.token, self.shop, self.job)])

    def test_cross_shop_receipt_cannot_release_private_bytes(self):
        reply = self.serve(reader_shop=str(uuid4()))
        self.assertEqual(reply.status_code, 404)
        self.assertEqual(reply.body, b"")
        self.assertEqual(reply.headers["Content-Length"], "0")

    def test_cross_job_receipt_cannot_release_private_bytes(self):
        reply = self.serve(reader_job=str(uuid4()))
        self.assertEqual(reply.status_code, 404)
        self.assertEqual(reply.body, b"")

    def test_revoked_synthetic_rights_cannot_release_bytes(self):
        reply = self.serve(rights=False)
        self.assertEqual(reply.status_code, 404)
        self.assertEqual(reply.body, b"")

    def test_corrupted_png_cannot_release_bytes(self):
        reply = self.serve(bytes_override=self.png[:-4] + b"FAIL")
        self.assertEqual(reply.status_code, 404)
        self.assertEqual(reply.body, b"")


if __name__ == "__main__":
    unittest.main()
