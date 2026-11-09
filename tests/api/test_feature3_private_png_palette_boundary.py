"""F3-08 synthetic PNG palette/transparency validation; no hosted access."""
from hashlib import sha256
from pathlib import Path
import sys
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_feature3_private_png_reader import RevocableReaderTests
from feature3_private_png_reader import PrivateGeneratedDownloadDenied


def chunk(kind, payload):
    return (len(payload).to_bytes(4, "big") + kind + payload +
            (zlib.crc32(kind + payload) & 0xffffffff).to_bytes(4, "big"))


class PrivatePNGPaletteBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = RevocableReaderTests(
            methodName="test_private_bytes_verified_twice_no_signed_link")
        self.fixture.setUp()

    def rejected(self, data):
        fixture = self.fixture
        fixture.binary = data
        digest = sha256(data).hexdigest()
        fixture.tenant.sha = digest
        fixture.tenant.path = (
            f"{fixture.shop}/feature3/gpu/{fixture.job}/{digest}.png")
        fixture.reader = fixture.build()
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            fixture.read()
        self.assertEqual(fixture.calls.count("get"), 1)

    def test_zero_length_palette_rejected(self):
        original = self.fixture.png
        ihdr_end = 8 + 12 + 13
        self.rejected(original[:ihdr_end] + chunk(b"PLTE", b"") +
                      original[ihdr_end:])

    def test_palette_non_rgb_multiple_rejected(self):
        original = self.fixture.png
        ihdr_end = 8 + 12 + 13
        self.rejected(original[:ihdr_end] + chunk(b"PLTE", b"abcd") +
                      original[ihdr_end:])

    def test_oversized_palette_rejected(self):
        original = self.fixture.png
        ihdr_end = 8 + 12 + 13
        self.rejected(original[:ihdr_end] + chunk(b"PLTE", bytes([0]) * 771) +
                      original[ihdr_end:])

    def test_transparency_after_pixels_rejected(self):
        original = self.fixture.png
        iend_offset = original.rfind(b"IEND") - 4
        self.assertGreater(iend_offset, 8)
        self.rejected(original[:iend_offset] + chunk(b"tRNS", bytes([0])) +
                      original[iend_offset:])


if __name__ == "__main__":
    unittest.main()
