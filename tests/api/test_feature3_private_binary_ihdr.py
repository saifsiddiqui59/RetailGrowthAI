"""F3-08: deterministic malformed private PNG header denials (synthetic only)."""
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


def png():
    out = BytesIO()
    Image.new("RGB", (64, 64), "#776655").save(out, format="PNG")
    return out.getvalue()


def mutate_ihdr(source, start, replacement):
    raw = bytearray(source)
    raw[start:start + len(replacement)] = replacement
    raw[29:33] = (crc32(raw[12:29]) & 0xffffffff).to_bytes(4, "big")
    return bytes(raw)


class FakeReader:
    def __init__(self, shop, job):
        self.shop, self.job = shop, job
        self.media = str(uuid4())
        self.raw = png()
        self.calls = 0

    def read(self, *, user_token, shop_id, job_id):
        self.calls += 1
        if user_token != "synthetic-token" or shop_id != self.shop or job_id != self.job:
            raise ValueError("foreign shop or job")
        return {
            "shop_id": self.shop, "job_id": self.job,
            "media_asset_id": self.media, "image_sha256": sha256(self.raw).hexdigest(),
            "mime_type": "image/png", "image_bytes": self.raw,
            "private": True, "signed_url_issued": False,
            "approved_model": False, "publish_approved": False,
        }


class PrivateIHDRBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job = str(uuid4()), str(uuid4())
        self.reader = FakeReader(self.shop, self.job)
        self.adapter = Feature3PrivateBinaryHTTP(reader=self.reader)

    def response(self):
        return self.adapter.handle(
            method="GET", authorization="Bearer synthetic-token",
            shop_id=self.shop, job_id=self.job)

    def test_valid_synthetic_png_returns_exact_private_bytes(self):
        status, body, headers = self.response()
        self.assertEqual(status, 200)
        self.assertEqual(body, self.reader.raw)
        self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")

    def test_self_consistent_digest_cannot_authorize_invalid_ihdr(self):
        original = self.reader.raw
        variants = [
            mutate_ihdr(original, 16, (0).to_bytes(4, "big")),
            mutate_ihdr(original, 20, (0).to_bytes(4, "big")),
            mutate_ihdr(original, 16, (16385).to_bytes(4, "big")),
            # Both dimensions together exceed the 16,777,216-pixel cap.
            mutate_ihdr(mutate_ihdr(original, 16, (8192).to_bytes(4, "big")),
                        20, (8192).to_bytes(4, "big")),
            mutate_ihdr(mutate_ihdr(original, 16, (4096).to_bytes(4, "big")),
                        20, (8192).to_bytes(4, "big")),
            mutate_ihdr(original, 24, b"\x01"),  # RGB cannot have 1-bit depth
            mutate_ihdr(original, 25, bytes((5,))),  # invalid colour type
            mutate_ihdr(original, 26, b"\x01"),  # compression
            mutate_ihdr(original, 27, b"\x01"),  # filter
            mutate_ihdr(original, 28, b"\x02"),  # interlace
        ]
        for forged in variants:
            self.reader.raw = forged
            with self.subTest(header=forged[16:29].hex()):
                status, body, headers = self.response()
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
        self.reader.raw = original
        self.assertEqual(self.response()[0], 200)

    def test_two_shop_and_invalid_bearer_denials_never_return_private_bytes(self):
        foreign_shop = str(uuid4())
        cases = [
            {"authorization": "Bearer synthetic-token", "shop_id": foreign_shop},
            {"authorization": "Bearer synthetic-token", "job_id": str(uuid4())},
            {"authorization": "Bearer sb_secret_fake"},
            {"authorization": "Bearer sb_publishable_fake"},
            {"authorization": "Basic synthetic-token"},
            {"authorization": "Bearer "},
        ]
        for overrides in cases:
            request = {
                "method": "GET", "authorization": "Bearer synthetic-token",
                "shop_id": self.shop, "job_id": self.job,
            }
            request.update(overrides)
            with self.subTest(request=overrides):
                status, body, headers = self.adapter.handle(**request)
                self.assertIn(status, (401, 404))
                self.assertEqual(body, b"")
                self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
        self.assertEqual(self.response()[0], 200)

    def test_reader_failure_and_forged_receipt_fail_closed(self):
        original_read = self.reader.read
        def unavailable(**kwargs):
            raise RuntimeError("synthetic rights store unavailable")
        self.reader.read = unavailable
        status, body, headers = self.response()
        self.assertEqual((status, body), (503, b""))
        self.assertEqual(headers["Vary"], "Authorization")
        self.reader.read = original_read
        original = self.reader.raw
        self.reader.raw = original + b"trailing-forged-bytes"
        self.assertEqual(self.response()[:2], (503, b""))
        self.reader.raw = original
        self.assertEqual(self.response()[0], 200)

    def test_transparency_chunk_order_and_size_are_fail_closed(self):
        original = self.reader.raw

        def chunk(kind, payload):
            return (len(payload).to_bytes(4, "big") + kind + payload
                    + (crc32(kind + payload) & 0xffffffff).to_bytes(4, "big"))

        # The RGB synthetic fixture permits one six-byte tRNS before IDAT.
        valid = chunk(b"tRNS", bytes((0, 1, 0, 2, 0, 3)))
        self.reader.raw = original[:33] + valid + original[33:]
        self.assertEqual(self.response()[0], 200)

        invalid = [
            original[:33] + valid + valid + original[33:],
            original[:-12] + valid + original[-12:],
            original[:33] + chunk(b"tRNS", bytes((0, 1))) + original[33:],
            original[:33] + chunk(b"tRNS", b"") + original[33:],
            # Indexed transparency without a palette cannot be authorized.
            mutate_ihdr(original, 25, bytes((3,)))[:33] + valid +
            mutate_ihdr(original, 25, bytes((3,)))[33:],
        ]
        for forged in invalid:
            self.reader.raw = forged
            with self.subTest(length=len(forged), digest=sha256(forged).hexdigest()):
                status, body, headers = self.response()
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Vary"], "Authorization")
        self.reader.raw = original
        self.assertEqual(self.response()[0], 200)

    def test_reserved_chunk_bit_denied_even_with_valid_crc_and_sha(self):
        original = self.reader.raw
        kind = b"texT"  # third letter lowercase: reserved PNG chunk bit
        payload = b"note\\x00synthetic"
        chunk = (len(payload).to_bytes(4, "big") + kind + payload
                 + (crc32(kind + payload) & 0xffffffff).to_bytes(4, "big"))
        self.reader.raw = original[:33] + chunk + original[33:]
        self.assertEqual(self.response()[:2], (503, b""))
        self.reader.raw = original
        self.assertEqual(self.response()[0], 200)


if __name__ == "__main__":
    unittest.main()
