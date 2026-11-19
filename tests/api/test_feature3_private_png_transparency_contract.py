"""F3-08 synthetic transparency/color-type security tests; no hosted auth."""
from hashlib import sha256
from io import BytesIO
from PIL import Image
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


class TransparencyContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture = RevocableReaderTests(
            methodName="test_private_bytes_verified_twice_no_signed_link")
        self.fixture.setUp()

    def rejected(self, binary):
        f = self.fixture
        f.binary = binary
        digest = sha256(binary).hexdigest()
        f.tenant.sha = digest
        f.tenant.path = f"{f.shop}/feature3/gpu/{f.job}/{digest}.png"
        f.reader = f.build()
        # Subtests reuse the same fixture: assert one private read per
        # rejected candidate, not one read across the entire test method.
        previous_gets = f.calls.count("get")
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            f.read()
        self.assertEqual(f.calls.count("get") - previous_gets, 1)

    def inject(self, color_type, transparency, palette=b""):
        original = self.fixture.png
        # Rebuild IHDR with correct CRC, and insert synthetic metadata
        # before the first IDAT. The object digest is also recomputed.
        ihdr = bytearray(original[16:29])
        ihdr[9] = color_type
        header = chunk(b"IHDR", bytes(ihdr))
        return (original[:8] + header +
                (chunk(b"PLTE", palette) if palette else b"") +
                chunk(b"tRNS", transparency) + original[33:])

    def test_rgba_cannot_carry_trns(self):
        self.rejected(self.inject(6, b"\x00\x00"))

    def test_grayscale_requires_two_transparency_bytes(self):
        self.rejected(self.inject(0, b"\x00"))

    def test_rgb_requires_six_transparency_bytes(self):
        self.rejected(self.inject(2, b"\x00\x00"))

    def test_indexed_transparency_requires_palette(self):
        self.rejected(self.inject(3, b"\x00"))

    def test_indexed_transparency_cannot_exceed_palette(self):
        self.rejected(self.inject(3, b"\x00\x00",
                                  palette=b"\x00\x00\x00"))

    def test_indexed_palette_is_required_even_without_transparency(self):
        raw = self.fixture.png
        ihdr = bytearray(raw[16:29])
        ihdr[9] = 3
        self.rejected(raw[:8] + chunk(b"IHDR", bytes(ihdr)) + raw[33:])

    def test_grayscale_palette_is_rejected(self):
        # PNG spec forbids PLTE for grayscale even with a correct CRC.
        raw = self.fixture.png
        ihdr = bytearray(raw[16:29])
        ihdr[9] = 0
        binary = (raw[:8] + chunk(b"IHDR", bytes(ihdr)) +
                  chunk(b"PLTE", bytes([0, 0, 0])) + raw[33:])
        self.rejected(binary)

    def test_grayscale_alpha_palette_is_rejected(self):
        raw = self.fixture.png
        ihdr = bytearray(raw[16:29])
        ihdr[9] = 4
        binary = (raw[:8] + chunk(b"IHDR", bytes(ihdr)) +
                  chunk(b"PLTE", bytes([0, 0, 0])) + raw[33:])
        self.rejected(binary)

    def test_indexed_palette_cannot_exceed_bit_depth(self):
        raw = self.fixture.png
        ihdr = bytearray(raw[16:29])
        ihdr[8] = 1  # one-bit indexed PNG supports at most two entries
        ihdr[9] = 3
        palette = bytes([0, 0, 0, 128, 128, 128, 255, 255, 255])
        binary = (raw[:8] + chunk(b"IHDR", bytes(ihdr)) +
                  chunk(b"PLTE", palette) + raw[33:])
        self.rejected(binary)

    def test_invalid_ihdr_color_type_is_denied(self):
        raw = self.fixture.png
        ihdr = bytearray(raw[16:29])
        ihdr[9] = 5  # PNG color type 5 is reserved
        self.rejected(raw[:8] + chunk(b"IHDR", bytes(ihdr)) + raw[33:])

    def test_indexed_png_cannot_have_sixteen_bit_depth(self):
        raw = self.fixture.png
        ihdr = bytearray(raw[16:29])
        ihdr[8] = 16
        ihdr[9] = 3
        self.rejected(raw[:8] + chunk(b"IHDR", bytes(ihdr)) +
                      chunk(b"PLTE", bytes([0, 0, 0])) + raw[33:])

    def test_truecolor_png_cannot_have_one_bit_depth(self):
        raw = self.fixture.png
        ihdr = bytearray(raw[16:29])
        ihdr[8] = 1
        ihdr[9] = 2
        self.rejected(raw[:8] + chunk(b"IHDR", bytes(ihdr)) + raw[33:])

    def test_invalid_ihdr_encoding_methods_are_denied(self):
        # Synthetic PNGs retain correct chunk CRCs and immutable SHA values.
        # A decoder's tolerance must not relax the PNG format contract.
        raw = self.fixture.png
        for offset, value in ((10, 1), (11, 1), (12, 2), (12, 255)):
            with self.subTest(ihdr_offset=offset, value=value):
                ihdr = bytearray(raw[16:29])
                ihdr[offset] = value
                self.rejected(raw[:8] + chunk(b"IHDR", bytes(ihdr)) + raw[33:])

    def test_valid_indexed_png_with_transparency_is_accepted(self):
        image = Image.new("P", (320, 400), 0)
        image.putpalette([0, 0, 0, 255, 255, 255])
        image.info["transparency"] = bytes([0, 255])
        stream = BytesIO()
        image.save(stream, format="PNG")
        binary = stream.getvalue()
        f = self.fixture
        f.binary = binary
        digest = sha256(binary).hexdigest()
        f.tenant.sha = digest
        f.tenant.path = f"{f.shop}/feature3/gpu/{f.job}/{digest}.png"
        f.reader = f.build()
        self.assertEqual(f.read()["image_bytes"], binary)



if __name__ == "__main__":
    unittest.main()
