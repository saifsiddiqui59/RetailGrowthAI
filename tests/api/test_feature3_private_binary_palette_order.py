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
        self.raw = image_with_chunks((b"PLTE", bytes((0,0,0))), (b"tRNS", bytes((0,17,0,34,0,51))))

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
    def test_non_ascii_bearer_never_reaches_private_reader(self):
        class FailIfCalled:
            def read(self, **kwargs):
                raise AssertionError("untrusted bearer reached private rights reader")

        adapter = Feature3PrivateBinaryHTTP(reader=FailIfCalled())
        shop, job = str(uuid4()), str(uuid4())
        for token in ("Bearer synthetic-\u00e9", "Bearer synthetic-\u200b",
                      "Bearer synthetic-\uff21", "Bearer synthetic-\u007f",
                      "Bearer synthetic-\n"):
            with self.subTest(token=repr(token)):
                status, body, headers = adapter.handle(
                    method="GET", authorization=token, shop_id=shop, job_id=job)
                self.assertEqual((status, body), (401, b""))
                self.assertEqual(headers["Vary"], "Authorization")
                self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")

    def test_rgb_transparency_sample_depth_is_enforced(self):
        reader = Reader()
        adapter = Feature3PrivateBinaryHTTP(reader=reader)
        def get():
            return adapter.handle(method="GET", authorization="Bearer synthetic-only",
                                  shop_id=reader.shop, job_id=reader.job)
        # RGB fixture is 8-bit: tRNS stores 16-bit values but each
        # transparent sample must fit the image's declared bit depth.
        for values, expected in (
            ((0, 0, 0), 200),
            ((255, 17, 34), 200),
            ((256, 17, 34), 503),
            ((17, 256, 34), 503),
            ((17, 34, 65535), 503),
        ):
            payload = b"".join(v.to_bytes(2, "big") for v in values)
            reader.raw = image_with_chunks((b"tRNS", payload))
            with self.subTest(values=values):
                status, body, headers = get()
                self.assertEqual(status, expected)
                self.assertEqual(headers["Vary"], "Authorization")
                if expected != 200:
                    self.assertEqual(body, b"")
                    self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
        reader.raw = image_with_chunks((b"tRNS", bytes((0, 255, 0, 17, 0, 34))))
        self.assertEqual(get()[0], 200)

    def test_private_png_metadata_chunks_are_denied_without_leakage(self):
        reader = Reader()
        adapter = Feature3PrivateBinaryHTTP(reader=reader)
        original = reader.raw
        # All receipts have matching synthetic SHA/CRC; content must still
        # fail closed rather than expose embedded customer metadata.
        for kind, payload in (
            (b"tEXt", b"customer\\x00synthetic-private-note"),
            (b"zTXt", b"prompt\\x00\\x00compressed"),
            (b"iTXt", b"prompt\\x00\\x00\\x00\\x00\\x00synthetic"),
            (b"eXIf", b"Exif\\x00\\x00synthetic"),
        ):
            with self.subTest(kind=kind):
                reader.raw = image_with_chunks((kind, payload))
                status, body, headers = adapter.handle(
                    method="GET", authorization="Bearer synthetic-only",
                    shop_id=reader.shop, job_id=reader.job)
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
                self.assertNotIn("Content-Disposition", headers)
        reader.raw = original
        self.assertEqual(adapter.handle(
            method="GET", authorization="Bearer synthetic-only",
            shop_id=reader.shop, job_id=reader.job)[0], 200)

    def test_unknown_ancillary_chunks_cannot_smuggle_private_metadata(self):
        reader = Reader()
        adapter = Feature3PrivateBinaryHTTP(reader=reader)
        def get():
            return adapter.handle(method="GET", authorization="Bearer synthetic-only",
                                  shop_id=reader.shop, job_id=reader.job)
        # These chunks are CRC-valid and the synthetic receipt SHA matches.
        # PNG's safe-to-copy bit is not permission to disclose metadata.
        for kind, payload in (
            (b"iCCP", b"customer-profile\\x00\\x00hidden"),
            (b"sPLT", b"private-palette\\x00\\x08"),
            (b"tIME", bytes((7, 234, 1, 1, 0, 0, 0))),
            (b"vpAg", b"synthetic-secret"),
            (b"aaAa", b"synthetic-secret"),
        ):
            with self.subTest(kind=kind):
                reader.raw = image_with_chunks((kind, payload))
                status, body, headers = get()
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Vary"], "Authorization")
                self.assertNotIn("Content-Disposition", headers)
        # Standard colour-space metadata remains supported.
        reader.raw = image_with_chunks((b"sRGB", bytes((0,))))
        status, body, headers = get()
        self.assertEqual(status, 200)
        self.assertEqual(body, reader.raw)
        self.assertEqual(headers["Content-Type"], "image/png")
        reader.raw = image_with_chunks()
        self.assertEqual(get()[0], 200)

    def test_permitted_color_metadata_requires_valid_wire_payloads(self):
        reader = Reader()
        adapter = Feature3PrivateBinaryHTTP(reader=reader)
        def get():
            return adapter.handle(method="GET", authorization="Bearer synthetic-only",
                                  shop_id=reader.shop, job_id=reader.job)
        invalid = (
            (b"sRGB", b""),
            (b"sRGB", bytes((4,))),
            (b"sRGB", b"\\\\x00"),
            (b"gAMA", bytes((0, 0, 0, 0))),
            (b"gAMA", bytes((0, 1))),
            (b"cHRM", bytes(31)),
            (b"pHYs", bytes(8)),
            (b"pHYs", bytes(8) + bytes((2,))),
        )
        for kind, payload in invalid:
            with self.subTest(kind=kind, payload=payload):
                reader.raw = image_with_chunks((kind, payload))
                status, body, headers = get()
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Vary"], "Authorization")
                self.assertNotIn("Content-Disposition", headers)
        for kind, payload in (
            (b"sRGB", bytes((0,))),
            (b"gAMA", bytes((0, 0, 177, 143))),
            (b"cHRM", bytes(32)),
            (b"pHYs", bytes((0, 0, 11, 19, 0, 0, 11, 19, 1))),
        ):
            with self.subTest(valid=kind):
                reader.raw = image_with_chunks((kind, payload))
                self.assertEqual(get()[0], 200)
        reader.raw = image_with_chunks()
        self.assertEqual(get()[0], 200)

    def test_duplicate_and_post_idat_color_metadata_denied(self):
        reader = Reader()
        adapter = Feature3PrivateBinaryHTTP(reader=reader)
        def get():
            return adapter.handle(method="GET", authorization="Bearer synthetic-only",
                                  shop_id=reader.shop, job_id=reader.job)
        # A valid colour-space hint is not permission to duplicate metadata.
        for kind, payload in ((b"sRGB", bytes((0,))),
                              (b"gAMA", bytes((0, 0, 177, 143))),
                              (b"pHYs", bytes((0, 0, 11, 19, 0, 0, 11, 19, 1)))):
            with self.subTest(kind=kind, placement="duplicate"):
                reader.raw = image_with_chunks((kind, payload), (kind, payload))
                status, body, headers = get()
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Vary"], "Authorization")
                self.assertNotIn("Content-Disposition", headers)
            with self.subTest(kind=kind, placement="after-idat"):
                # Insert a CRC-valid metadata chunk immediately before IEND.
                base = image_with_chunks()
                reader.raw = base[:-12] + chunk(kind, payload) + base[-12:]
                status, body, headers = get()
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
        # Rejected metadata must not affect subsequent valid private bytes.
        reader.raw = image_with_chunks()
        self.assertEqual(get()[0], 200)

    def test_color_profile_chunks_must_precede_palette(self):
        reader = Reader()
        adapter = Feature3PrivateBinaryHTTP(reader=reader)
        def get():
            return adapter.handle(method="GET", authorization="Bearer synthetic-only",
                                  shop_id=reader.shop, job_id=reader.job)
        palette = (b"PLTE", bytes((0, 0, 0)))
        for kind, payload in (
            (b"sRGB", bytes((0,))),
            (b"gAMA", bytes((0, 0, 177, 143))),
            (b"cHRM", bytes(32)),
        ):
            with self.subTest(kind=kind, placement="after-palette"):
                reader.raw = image_with_chunks(palette, (kind, payload))
                status, body, headers = get()
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Vary"], "Authorization")
                self.assertNotIn("Content-Disposition", headers)
            with self.subTest(kind=kind, placement="before-palette"):
                reader.raw = image_with_chunks((kind, payload), palette)
                status, body, headers = get()
                self.assertEqual(status, 200)
                self.assertEqual(body, reader.raw)
                self.assertEqual(headers["Content-Type"], "image/png")
        reader.raw = image_with_chunks()
        self.assertEqual(get()[0], 200)

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
            (b"tRNS", bytes((0,17,0,34,0,51))),
            (b"PLTE", bytes((0,0,0))),
        )
        status, body, headers = get()
        self.assertEqual((status, body), (503, b""))
        self.assertEqual(headers["Vary"], "Authorization")
        self.assertEqual(headers["Cache-Control"], "no-store, private, max-age=0")
        # A self-consistent SHA and CRC never excuse duplicate/invalid tRNS.
        for chunks in (
            ((b"PLTE", bytes((0, 0, 0))), (b"tRNS", bytes((0, 1, 0, 2, 0, 3))),
             (b"tRNS", bytes((0, 1, 0, 2, 0, 3)))),
            ((b"PLTE", bytes((0, 0, 0))), (b"tRNS", bytes((0, 1)))),
            ((b"tRNS", b""),),
        ):
            with self.subTest(chunks=chunks):
                reader.raw = image_with_chunks(*chunks)
                status, body, headers = get()
                self.assertEqual((status, body), (503, b""))
                self.assertEqual(headers["Vary"], "Authorization")
        # Denial cannot poison a later valid private response.
        reader.raw = image_with_chunks(
            (b"PLTE", bytes((0, 0, 0))),
            (b"tRNS", bytes((0, 17, 0, 34, 0, 51))),
        )
        self.assertEqual(get()[0], 200)


if __name__ == "__main__":
    unittest.main()
