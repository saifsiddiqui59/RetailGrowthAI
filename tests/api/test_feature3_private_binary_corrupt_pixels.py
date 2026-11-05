"""F3-08: CRC-valid PNG containers with corrupt compressed pixels are denied.

These synthetic fixtures are not hosted JWT or commercial-media evidence.
"""
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
        buffer = BytesIO()
        Image.new("RGB", (320, 320), "#112233").save(buffer, format="PNG")
        self.raw = buffer.getvalue()

    def read(self, *, user_token, shop_id, job_id):
        if (user_token, shop_id, job_id) != ("synthetic-reader-token", self.shop, self.job):
            raise PermissionError("synthetic access denied")
        return {
            "shop_id": self.shop, "job_id": self.job, "media_asset_id": self.asset,
            "image_sha256": sha256(self.raw).hexdigest(), "mime_type": "image/png",
            "image_bytes": self.raw, "private": True, "signed_url_issued": False,
            "approved_model": False, "publish_approved": False,
        }


def replace_idat(raw, payload):
    # Pillow's synthetic image is a simple IHDR / IDAT / IEND PNG.
    offset = 8
    chunks = []
    while offset < len(raw):
        size = int.from_bytes(raw[offset:offset + 4], "big")
        kind = raw[offset + 4:offset + 8]
        data = raw[offset + 8:offset + 8 + size]
        chunks.append(chunk(kind, payload if kind == b"IDAT" else data))
        offset += 12 + size
    return raw[:8] + b"".join(chunks)


class CorruptPixelTests(unittest.TestCase):
    def test_crc_correct_invalid_zlib_denied_and_valid_recovers(self):
        reader = SyntheticReader()
        adapter = Feature3PrivateBinaryHTTP(reader=reader)
        original = reader.raw

        def call():
            return adapter.handle(
                method="GET", authorization="Bearer synthetic-reader-token",
                shop_id=reader.shop, job_id=reader.job,
            )

        self.assertEqual(call()[0], 200)
        for payload in (b"not-a-zlib-stream", b"\\x78\\x9c" + b"\\x00" * 12):
            with self.subTest(payload=payload):
                reader.raw = replace_idat(original, payload)
                status, body, headers = call()
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
                self.assertNotIn("Content-Disposition", headers)
        reader.raw = original
        self.assertEqual(call()[0], 200)


if __name__ == "__main__":
    unittest.main()
