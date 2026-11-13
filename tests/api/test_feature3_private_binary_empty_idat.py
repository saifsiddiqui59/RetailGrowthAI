"""F3-08: synthetic CRC-correct empty IDAT must never leave private binary route."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest
from uuid import uuid4
from zlib import crc32
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_binary_http import Feature3PrivateBinaryHTTP


def chunk(kind, payload):
    return (len(payload).to_bytes(4, "big") + kind + payload
            + (crc32(kind + payload) & 0xffffffff).to_bytes(4, "big"))


class SyntheticReader:
    def __init__(self):
        self.shop, self.job, self.asset = (str(uuid4()) for _ in range(3))
        stream = BytesIO()
        Image.new("RGB", (320, 320), "#123456").save(stream, format="PNG")
        self.raw = stream.getvalue()

    def read(self, *, user_token, shop_id, job_id):
        if (user_token, shop_id, job_id) != ("synthetic-reader-token", self.shop, self.job):
            raise PermissionError("mock denied")
        return {
            "shop_id": self.shop, "job_id": self.job, "media_asset_id": self.asset,
            "image_sha256": sha256(self.raw).hexdigest(), "mime_type": "image/png",
            "image_bytes": self.raw, "private": True, "signed_url_issued": False,
            "approved_model": False, "publish_approved": False,
        }


class EmptyIDATTests(unittest.TestCase):
    def test_empty_idat_streams_fail_closed_and_valid_image_recovers(self):
        reader = SyntheticReader()
        adapter = Feature3PrivateBinaryHTTP(reader=reader)
        original = reader.raw

        def call():
            return adapter.handle(method="GET", authorization="Bearer synthetic-reader-token",
                                  shop_id=reader.shop, job_id=reader.job)

        self.assertEqual(call()[0], 200)
        ihdr, iend = original[:33], original[-12:]
        # CRC-correct but pixel-less IDAT streams must be rejected, even if
        # the untrusted reader supplies a matching SHA for the forged image.
        for forged in (
            ihdr + chunk(b"IDAT", b"") + iend,
            ihdr + chunk(b"IDAT", b"") + chunk(b"IDAT", b"") + iend,
        ):
            with self.subTest(sha=sha256(forged).hexdigest()):
                reader.raw = forged
                status, body, headers = call()
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Vary"], "Authorization")
                self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
                self.assertNotIn("Content-Disposition", headers)
        reader.raw = original
        self.assertEqual(call()[0], 200)


if __name__ == "__main__":
    unittest.main()
