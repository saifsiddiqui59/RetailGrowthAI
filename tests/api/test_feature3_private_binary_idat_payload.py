"""F3-08 synthetic IDAT integrity regression; no hosted rights claims."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest
from uuid import uuid4
from zlib import compress, crc32, decompress

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_binary_http import Feature3PrivateBinaryHTTP


def _chunk(kind, payload):
    return (len(payload).to_bytes(4, "big") + kind + payload
            + (crc32(kind + payload) & 0xffffffff).to_bytes(4, "big"))


def _single_idat(source):
    position = 8
    found = []
    while position < len(source):
        size = int.from_bytes(source[position:position + 4], "big")
        kind = source[position + 4:position + 8]
        if kind == b"IDAT":
            found.append((position, position + 12 + size,
                          source[position + 8:position + 8 + size]))
        position += 12 + size
    assert len(found) == 1, "synthetic source fixture must have one IDAT"
    return found[0]


def _replace_idat(source, replacement):
    start, end, _ = _single_idat(source)
    return source[:start] + _chunk(b"IDAT", replacement) + source[end:]


class SyntheticReader:
    def __init__(self):
        self.shop, self.job, self.asset = (str(uuid4()) for _ in range(3))
        buffer = BytesIO()
        Image.new("RGB", (256, 256), "#124578").save(buffer, format="PNG")
        self.raw = buffer.getvalue()

    def read(self, *, user_token, shop_id, job_id):
        if (user_token, shop_id, job_id) != (
                "synthetic-idat-token", self.shop, self.job):
            raise ValueError("synthetic user or tenant denied")
        return {
            "shop_id": self.shop, "job_id": self.job,
            "media_asset_id": self.asset,
            "image_sha256": sha256(self.raw).hexdigest(),
            "mime_type": "image/png", "image_bytes": self.raw,
            "private": True, "signed_url_issued": False,
            "approved_model": False, "publish_approved": False,
        }


class PrivateIDATPayloadTests(unittest.TestCase):
    def test_extra_idat_data_is_never_released_even_with_valid_crc_sha_and_pixels(self):
        reader = SyntheticReader()
        http = Feature3PrivateBinaryHTTP(reader=reader)
        original = reader.raw
        compressed = _single_idat(original)[2]
        pixels = decompress(compressed)

        def call():
            return http.handle(
                method="GET", authorization="Bearer synthetic-idat-token",
                shop_id=reader.shop, job_id=reader.job)

        self.assertEqual(call()[0], 200)
        # All payloads have valid outer PNG CRC and matching full-byte SHA.
        # Pillow may silently display the first image while ignoring covert
        # bytes after zlib EOF or after the expected final filtered scanline.
        bad_payloads = (
            compressed + b"hidden-private-payload",
            compressed + compress(b"another-hidden-zlib-stream"),
            compress(pixels + b"hidden-decompressed-payload"),
            compressed[:-3],  # truncated Adler-32, despite valid PNG CRC
        )
        for candidate in bad_payloads:
            with self.subTest(candidate_length=len(candidate)):
                reader.raw = _replace_idat(original, candidate)
                status, body, headers = call()
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
                self.assertNotIn("Content-Disposition", headers)
        reader.raw = original
        self.assertEqual(call()[0], 200)

    def test_valid_rgba_and_grayscale_pixels_survive_the_integrity_gate(self):
        reader = SyntheticReader()
        http = Feature3PrivateBinaryHTTP(reader=reader)
        for mode in ("RGB", "RGBA", "L", "LA", "P", "1", "I;16"):
            with self.subTest(mode=mode):
                output = BytesIO()
                image = Image.new(mode, (256, 256))
                if mode == "1":
                    # An all-zero 1-bit PNG compresses below the private
                    # output's existing 100-byte minimum; use real varied
                    # pixels to exercise the valid 1-bit decode path.
                    for y in range(256):
                        for x in range(256):
                            image.putpixel((x, y), ((x * 17 + y * 29 + x * y) % 37) & 1)
                image.save(output, format="PNG")
                reader.raw = output.getvalue()
                self.assertGreaterEqual(len(reader.raw), 100)
                status, body, headers = http.handle(
                    method="GET", authorization="Bearer synthetic-idat-token",
                    shop_id=reader.shop, job_id=reader.job)
                self.assertEqual(status, 200)
                self.assertEqual(body, reader.raw)
                self.assertEqual(headers["Content-Type"], "image/png")

    def test_foreign_shop_cannot_reuse_valid_png(self):
        reader = SyntheticReader()
        status, body, headers = Feature3PrivateBinaryHTTP(reader=reader).handle(
            method="GET", authorization="Bearer synthetic-idat-token",
            shop_id=str(uuid4()), job_id=reader.job)
        self.assertEqual((status, body), (404, b""))
        self.assertEqual(headers["Vary"], "Authorization")


if __name__ == "__main__":
    unittest.main()
