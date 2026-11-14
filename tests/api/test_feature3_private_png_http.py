"""Synthetic F3-08 HTTP adapter tests; not signed hosted E2E evidence."""
import sys
import unittest
import struct
import zlib
from hashlib import sha256
from io import BytesIO
from PIL import Image
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_http import private_png_http
from feature3_private_png_reader import PrivateGeneratedDownloadDenied
from tenant_store import StorageUnavailable


def png_chunk(kind, payload):
    return (struct.pack(">I", len(payload)) + kind + payload +
            struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))


def synthetic_png():
    out = BytesIO()
    image = Image.new("RGB", (256, 256), "#124578")
    image.save(out, format="PNG")
    return out.getvalue()


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
                      media_asset_id=str(uuid4()),
                      image_sha256=sha256(PNG).hexdigest(),
                      image_bytes=PNG, mime_type="image/png",
                      private=True, signed_url_issued=False,
                      approved_model=False, publish_approved=False)
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

    def test_outer_boundary_rejects_success_header_or_digest_drift(self):
        # Synthetic canonical-handler fault injection. Even a status 200
        # must not forward a public cache policy, redirect or corrupt digest.
        good = self.call()
        self.assertEqual(good.status, 200)
        cases = (
            {"Cache-Control": "public, max-age=3600"},
            {"Location": "https://example.invalid/private"},
            {"Set-Cookie": "session=leaked"},
            {"Content-Length": "1"},
            {"X-Feature3-Image-Sha256": "0" * 64},
            {"X-Feature3-Shop-Id": str(uuid4())},
            {"X-Feature3-Media-Asset-Id": "not-a-uuid"},
            {"Content-Disposition": "inline"},
            {"Vary": "*"},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                headers = dict(good.headers)
                headers.update(changes)
                with patch("feature3_private_png_http.Feature3PrivateBinaryHTTP.handle",
                           return_value=(200, PNG, headers)):
                    result = self.call()
                self.assertEqual(result.status, 503)
                self.assertEqual(result.body, b"")
                self.assertNotIn("Location", result.headers)
                self.assertNotIn("Set-Cookie", result.headers)
        with patch("feature3_private_png_http.Feature3PrivateBinaryHTTP.handle",
                   return_value=(200, PNG + b"x", dict(good.headers))):
            self.assertEqual(self.call().status, 503)
        self.assertEqual(self.call().status, 200)

    def test_outer_headers_reject_spoofed_keys_before_equality(self):
        # A compromised inner adapter can return a dict with hostile keys.
        # Validate key types before set comparison or dictionary lookup.
        class SpoofedKey:
            def __hash__(self):
                return hash("Content-Type")

            def __eq__(self, other):
                raise AssertionError("untrusted header equality executed")

        good = self.call()
        self.assertEqual(good.status, 200)
        headers = dict(good.headers)
        headers.pop("Content-Type")
        headers[SpoofedKey()] = "image/png"
        with patch("feature3_private_png_http.Feature3PrivateBinaryHTTP.handle",
                   return_value=(200, PNG, headers)):
            reply = self.call()
        self.assertEqual(reply.status, 503)
        self.assertEqual(reply.body, b"")
        self.assertNotIn("Content-Type", reply.headers)

    def test_invalid_scope_and_credentials_never_construct_reader(self):
        for changes in (dict(shop_id=str(uuid4()).upper()),
                        dict(job_id="not-uuid"),
                        dict(authorization=""),
                        dict(authorization="Bearer sb_secret_badsecret"),
                        dict(authorization="Bearer " + "t" * 9000),
                        dict(authorization="Bearer t\nother"),
                        dict(authorization="Bearer " + "t" * 20 + ",other"),
                        dict(authorization="Bearer " + "t" * 20 + ";other"),
                        dict(authorization="Bearer " + "t" * 20 + " extra"),
                        dict(authorization="Bearer Bearer " + "t" * 30),
                        dict(authorization="Bearer " + "t" * 20 + "\tother"),
                        dict(authorization='Bearer ' + 't' * 20 + '"other'),
                        dict(authorization="Bearer " + "t" * 20 + "\\other"),
                        dict(authorization=object())):
            with self.subTest(changes=repr(changes)):
                self.assertNotEqual(self.call(**changes).status, 200)
        self.assertEqual(self.factories, [])

    def test_oversized_and_noncanonical_scope_is_rejected_before_reader_io(self):
        # Direct HTTP callers must not trigger UUID parsing or backend IO on
        # oversized path input, even if the Azure route adapter was bypassed.
        class ForgedUUID(str):
            def __eq__(self, other):
                return True

        invalid = (
            dict(shop_id="a" * 100000),
            dict(job_id="b" * 100000),
            dict(shop_id=ForgedUUID(self.shop)),
            dict(job_id=ForgedUUID(self.job)),
            dict(shop_id=self.shop.upper()),
            dict(job_id=self.job.replace("-", "")),
        )
        for changes in invalid:
            with self.subTest(field=next(iter(changes))):
                reply = self.call(**changes)
                self.assertEqual(reply.status, 404)
                self.assertEqual(reply.body, b"")
        self.assertEqual(self.factories, [])
        self.assertEqual(self.reader.calls, 0)

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
                self.assertEqual(response.status, 503)
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
                self.assertEqual(response.status, 503)
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
                self.assertEqual(response.status, 503)
                self.assertEqual(response.body, b"")
        self.reader.tamper = None
        self.assertEqual(self.call().status, 200)

    def test_rejects_invalid_chunk_names_and_oversized_indexed_palette(self):
        def assemble(color_type, depth, chunks):
            header = struct.pack(">IIBBBBB", 1, 1, depth, color_type, 0, 0, 0)
            return (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header) +
                    b"".join(png_chunk(kind, payload) for kind, payload in chunks) +
                    png_chunk(b"IEND", b""))

        pixel = zlib.compress(b"\x00\x00")
        cases = [
            assemble(0, 8, [(b"ab1d", b"x"), (b"IDAT", pixel)]),
            assemble(0, 8, [(b"abcd", b"x"), (b"IDAT", pixel)]),
            assemble(3, 1, [(b"PLTE", b"\x00\x00\x00" * 3),
                            (b"IDAT", pixel)]),
            assemble(0, 8, [(b"tEXt", b"x")]*4096 + [(b"IDAT", pixel)]),
        ]
        for value in cases:
            with self.subTest(length=len(value)):
                self.reader.tamper = {"image_bytes": value}
                self.assertEqual(self.call().status, 503)
        self.reader.tamper = None
        self.assertEqual(self.call().status, 200)

    def test_negative_fixture_uses_canonical_png_signature(self):
        """Negative cases must reach chunk validation, not fail at signature."""
        def chunk(kind, payload):
            return png_chunk(kind, payload)

        header = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
        pixels = zlib.compress(b"\x00\xff\x00\x00\xff")
        prefix = b"\x89PNG\r\n\x1a\n"
        valid = PNG
        self.assertTrue(valid.startswith(prefix))
        self.reader.tamper = {"image_bytes": valid}
        self.assertEqual(self.call().status, 200)
        # Inject an invalid chunk with valid CRC into an otherwise normal
        # production-size PNG. This must reach PNG framing validation.
        invalid = valid[:33] + chunk(b"ab1d", b"bad-chunk-name") + valid[33:]
        self.assertTrue(invalid.startswith(prefix))
        self.reader.tamper = {"image_bytes": invalid}
        self.assertEqual(self.call().status, 503)
        self.reader.tamper = None


    def test_untrusted_result_identity_cannot_spoof_equality(self):
        """An injected adapter cannot grant foreign-shop bytes via __eq__."""
        class AlwaysEqual:
            def __eq__(self, other):
                return True

        for field in ("shop_id", "job_id"):
            with self.subTest(field=field):
                self.reader.tamper = {field: AlwaysEqual()}
                reply = self.call()
                self.assertEqual(reply.status, 404)
                self.assertEqual(reply.body, b"")
        # A str subclass can also spoof equality; actual output scope must
        # be a plain canonical string, never an overloaded custom value.
        class ForgedString(str):
            def __eq__(self, other):
                return True
        for field in ("shop_id", "job_id"):
            self.reader.tamper = {field: ForgedString("different-scope")}
            self.assertEqual(self.call().status, 404)
        self.reader.tamper = None
        self.assertEqual(self.call().status, 200)

    def test_spoofed_mapping_keys_never_release_private_bytes(self):
        # A backend adapter may return a real dict with hostile key objects.
        # No equality/hash spoof may substitute for literal protocol keys.
        class SpoofedKey:
            def __init__(self, name):
                self.name = name

            def __hash__(self):
                return hash(self.name)

            def __eq__(self, other):
                return other == self.name

        class SpoofingReader:
            def read(self, **kwargs):
                return {
                    SpoofedKey("shop_id"): self_shop,
                    SpoofedKey("job_id"): self_job,
                    "media_asset_id": str(uuid4()),
                    "image_sha256": sha256(PNG).hexdigest(),
                    "image_bytes": PNG,
                    "mime_type": "image/png",
                    "private": True,
                    "signed_url_issued": False,
                    "approved_model": False,
                    "publish_approved": False,
                }

        self_shop, self_job = self.shop, self.job
        reply = self.call(reader_factory=lambda shop, job: SpoofingReader())
        self.assertEqual(reply.status, 404)
        self.assertEqual(reply.body, b"")

    def test_non_dictionary_reader_result_never_releases_bytes(self):
        class InvalidReader:
            def read(self, **kwargs):
                return [("image_bytes", PNG)]
        reply = self.call(reader_factory=lambda shop, job: InvalidReader())
        self.assertEqual(reply.status, 404)
        self.assertEqual(reply.body, b"")

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
                # Foreign scope is an opaque 404. Other malformed internal
                # receipts are opaque 503 errors from the canonical validator.
                expected = 404 if "shop_id" in tamper or "job_id" in tamper else 503
                self.assertEqual(reply.status, expected)
                self.assertEqual(reply.body, b"")
                self.assertEqual(reply.body, b"")


if __name__ == "__main__":
    unittest.main()
