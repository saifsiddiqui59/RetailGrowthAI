"""Synthetic F3-08 HTTP adapter tests; not signed hosted E2E evidence."""
import sys
import unittest
import struct
import zlib
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_http import private_png_http
from feature3_private_png_reader import PrivateGeneratedDownloadDenied
from tenant_store import StorageUnavailable


def png_chunk(kind, payload):
    return (struct.pack(">I", len(payload)) + kind + payload +
            struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))


def synthetic_png():
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    pixels = zlib.compress(b"\x00\xff\x00\x00\xff")
    return (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) +
            png_chunk(b"tEXt", b"synthetic=" + b"a" * 50) +
            png_chunk(b"IDAT", pixels) + png_chunk(b"IEND", b""))


PNG = synthetic_png()


class Reader:
    def __init__(self, shop, job, *, fail=None, tamper=None):
        self.shop, self.job, self.fail, self.tamper = shop, job, fail, tamper
        self.calls = 0

    def read(self, **kwargs):
        self.calls += 1
        if self.fail:
            raise self.fail
        result = dict(shop_id=self.shop, job_id=self.job,
                      image_bytes=PNG, mime_type="image/png",
                      private=True, signed_url_issued=False)
        if self.tamper:
            result.update(self.tamper)
        return result


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job = str(uuid4()), str(uuid4())
        self.reader = Reader(self.shop, self.job)
        self.factories = []

    def factory(self, shop, job):
        self.factories.append((shop, job))
        return self.reader

    def call(self, **overrides):
        values = dict(authorization="Bearer " + "t" * 30,
                      shop_id=self.shop, job_id=self.job,
                      reader_factory=self.factory)
        values.update(overrides)
        return private_png_http(**values)

    def test_binary_success_no_url_no_cache(self):
        reply = self.call()
        self.assertEqual(reply.status, 200)
        self.assertEqual(reply.body, PNG)
        self.assertEqual(reply.headers["Content-Type"], "image/png")
        self.assertEqual(reply.headers["Content-Length"], str(len(PNG)))
        self.assertIn("no-store", reply.headers["Cache-Control"])
        self.assertEqual(self.factories, [(self.shop, self.job)])

    def test_invalid_scope_and_credentials_never_construct_reader(self):
        for changes in (dict(shop_id=str(uuid4()).upper()),
                        dict(job_id="not-uuid"),
                        dict(authorization=""),
                        dict(authorization="Bearer sb_secret_badsecret"),
                        dict(authorization="Bearer " + "t" * 9000),
                        dict(authorization="Bearer t\nother"),
                        dict(authorization=object())):
            with self.subTest(changes=repr(changes)):
                self.assertNotEqual(self.call(**changes).status, 200)
        self.assertEqual(self.factories, [])

    def test_denials_and_outages_never_return_private_bytes(self):
        for error, status in ((PrivateGeneratedDownloadDenied("secret"), 404),
                              (StorageUnavailable("secret"), 503),
                              (OSError("secret"), 503),
                              (RuntimeError("secret"), 503)):
            with self.subTest(error=type(error).__name__):
                self.reader.fail = error
                reply = self.call()
                self.assertEqual(reply.status, status)
                self.assertEqual(reply.body, b"")
                self.assertNotIn("secret", repr(reply))

    def test_corrupted_png_envelopes_never_leave_private_boundary(self):
        bad = (b"x" * len(PNG), PNG[:-1], PNG + b"trailing",
               PNG[:30] + bytes([PNG[30] ^ 1]) + PNG[31:],
               PNG.replace(b"IEND", b"IDAT"),
               PNG[:8] + PNG[8:33] + PNG[8:33] + PNG[33:])
        for value in bad:
            with self.subTest(length=len(value)):
                self.reader.tamper = {"image_bytes": value}
                response = self.call()
                self.assertEqual(response.status, 404)
                self.assertEqual(response.body, b"")
        self.reader.tamper = None
        self.assertEqual(self.call().status, 200)

    def test_png_rejects_invalid_headers_and_chunk_order(self):
        def build(ihdr, chunks):
            return (b"\x89PNG\r\n\x1a\n" +
                    png_chunk(b"IHDR", ihdr) +
                    b"".join(png_chunk(kind, data) for kind, data in chunks) +
                    png_chunk(b"IEND", b""))

        normal = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
        compressed = zlib.compress(b"\x00\xff\x00\x00\xff")
        cases = [
            build(struct.pack(">IIBBBBB", 16384, 16384, 8, 6, 0, 0, 0),
                  [(b"IDAT", compressed)]),
            build(struct.pack(">IIBBBBB", 1, 1, 4, 6, 0, 0, 0),
                  [(b"IDAT", compressed)]),
            build(struct.pack(">IIBBBBB", 1, 1, 8, 6, 1, 0, 0),
                  [(b"IDAT", compressed)]),
            build(normal, [(b"IDAT", compressed), (b"tEXt", b"x=y"),
                           (b"IDAT", compressed)]),
            build(normal, [(b"ABCD", b"unexpected"), (b"IDAT", compressed)]),
        ]
        for value in cases:
            with self.subTest(case=len(value)):
                self.reader.tamper = {"image_bytes": value}
                response = self.call()
                self.assertEqual(response.status, 404)
                self.assertEqual(response.body, b"")
        self.reader.tamper = None
        self.assertEqual(self.call().status, 200)

    def test_palette_order_and_indexed_color_requirements(self):
        def make(color_type, chunks):
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, color_type, 0, 0, 0)
            return (b"\x89PNG\r\n\x1a\n" +
                    png_chunk(b"IHDR", ihdr) +
                    b"".join(png_chunk(kind, data) for kind, data in chunks) +
                    png_chunk(b"IEND", b""))

        pixels = zlib.compress(b"\x00\x00\x00\x00\xff")
        palette = b"\x00\x00\x00"
        cases = [
            make(3, [(b"IDAT", pixels)]),
            make(3, [(b"IDAT", pixels), (b"PLTE", palette)]),
            make(3, [(b"PLTE", palette), (b"PLTE", palette), (b"IDAT", pixels)]),
            make(0, [(b"PLTE", palette), (b"IDAT", pixels)]),
            make(2, [(b"PLTE", b"ab"), (b"IDAT", pixels)]),
            make(2, [(b"PLTE", b"a" * 771), (b"IDAT", pixels)]),
        ]
        for value in cases:
            with self.subTest(case=value):
                self.reader.tamper = {"image_bytes": value}
                response = self.call()
                self.assertEqual(response.status, 404)
                self.assertEqual(response.body, b"")
        self.reader.tamper = None
        self.assertEqual(self.call().status, 200)

    def test_malformed_reader_result_is_denied(self):
        for tamper in (dict(shop_id=str(uuid4())),
                       dict(job_id=str(uuid4())),
                       dict(image_bytes="not bytes"),
                       dict(image_bytes=b"x"),
                       dict(private=False),
                       dict(signed_url_issued=True),
                       dict(mime_type="text/plain")):
            with self.subTest(tamper=repr(tamper)):
                self.reader.tamper = tamper
                reply = self.call()
                self.assertEqual(reply.status, 404)
                self.assertEqual(reply.body, b"")


if __name__ == "__main__":
    unittest.main()
