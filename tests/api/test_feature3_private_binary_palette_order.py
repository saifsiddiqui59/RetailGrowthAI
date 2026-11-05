"""F3-08 synthetic PNG ordering regression: tRNS must follow optional PLTE."""
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


def chunk(kind, data):
    return len(data).to_bytes(4, "big") + kind + data + (crc32(kind + data) & 0xffffffff).to_bytes(4, "big")


def image_with_chunks(*ordered):
    stream = BytesIO()
    Image.new("RGB", (32, 32), "#112233").save(stream, format="PNG")
    raw = stream.getvalue()
    # Preserve IHDR and IDAT CRCs; inject syntactically valid chunks before IDAT.
    return raw[:33] + b"".join(chunk(k, v) for k, v in ordered) + raw[33:]


class Reader:
    def __init__(self):
        self.shop = str(uuid4())
        self.job = str(uuid4())
        self.media = str(uuid4())
        self.raw = image_with_chunks((b"PLTE", b"\\x00\\x00\\x00"), (b"tRNS", b"\\x00\\x11\\x00\\x22\\x00\\x33"))

    def read(self, *, user_token, shop_id, job_id):
        if (user_token, shop_id, job_id) != ("synthetic-only", self.shop, self.job):
            raise ValueError("synthetic authorization denied")
        return {
            "shop_id": self.shop, "job_id": self.job, "media_asset_id": self.media,
            "image_sha256": sha256(self.raw).hexdigest(), "mime_type": "image/png",
            "image_bytes": self.raw, "private": True, "signed_url_issued": False,
            "approved_model": False, "publish_approved": False,
        }


class TransparencyPaletteOrderingTests(unittest.TestCase):
    def test_valid_order_and_reversed_order(self):
        reader = Reader()
        adapter = Feature3PrivateBinaryHTTP(reader=reader)
        def get():
            return adapter.handle(method="GET", authorization="Bearer synthetic-only",
                                  shop_id=reader.shop, job_id=reader.job)
        status, body, headers = get()
        self.assertEqual(status, 200)
        self.assertEqual(body, reader.raw)
        self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
        # RGB allows an optional PLTE, but PNG requires PLTE to precede tRNS.
        reader.raw = image_with_chunks(
            (b"tRNS", b"\\x00\\x11\\x00\\x22\\x00\\x33"),
            (b"PLTE", b"\\x00\\x00\\x00"),
        )
        status, body, headers = get()
        self.assertEqual((status, body), (503, b""))
        self.assertEqual(headers["Vary"], "Authorization")
        self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")


if __name__ == "__main__":
    unittest.main()
