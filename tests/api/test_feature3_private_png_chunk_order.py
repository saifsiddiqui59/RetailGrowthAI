"""F3-08 synthetic PNG chunk-order negative tests; no hosted credentials or rights."""
from hashlib import sha256
from pathlib import Path
import sys
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_feature3_private_png_reader import RevocableReaderTests
from feature3_private_png_reader import PrivateGeneratedDownloadDenied


def chunks(data):
    offset = 8
    result = []
    while offset < len(data):
        size = int.from_bytes(data[offset:offset + 4], "big")
        end = offset + size + 12
        result.append((data[offset + 4:offset + 8], data[offset:end]))
        offset = end
    return result


class PrivatePNGChunkOrderTests(unittest.TestCase):
    def setUp(self):
        self.fixture = RevocableReaderTests(
            methodName="test_private_bytes_verified_twice_no_signed_link")
        self.fixture.setUp()

    def assert_rejected(self, altered):
        fixture = self.fixture
        fixture.binary = altered
        digest = sha256(altered).hexdigest()
        fixture.tenant.sha = digest
        fixture.tenant.path = (
            f"{fixture.shop}/feature3/gpu/{fixture.job}/{digest}.png")
        fixture.reader = fixture.build()
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            fixture.read()
        # Even a correctly SHA-named malicious object cannot be returned.
        self.assertEqual(fixture.calls.count("get"), 1)
        self.assertEqual(fixture.rights_called, 1)

    def test_many_tiny_ancillary_chunks_rejected_with_matching_digest(self):
        # A byte-size cap alone permits millions of tiny chunks and excessive
        # CPU work. This synthetic PNG has valid chunk CRCs and a matching SHA.
        original = self.fixture.png
        parts = chunks(original)
        name = b"tEXt"
        payload = b"x\\x00y"
        block = (len(payload).to_bytes(4, "big") + name + payload +
                 (zlib.crc32(name + payload) & 0xffffffff).to_bytes(4, "big"))
        self.assert_rejected(original[:8] + parts[0][1] +
                             block * 4097 +
                             b"".join(raw for _, raw in parts[1:]))

    def test_duplicate_ihdr_rejected_before_pillow(self):
        original = self.fixture.png
        parts = chunks(original)
        self.assertEqual(parts[0][0], b"IHDR")
        self.assert_rejected(original[:8] + parts[0][1] + parts[0][1] +
                             b"".join(raw for _, raw in parts[1:]))

    def test_missing_idat_rejected_even_with_matching_digest(self):
        original = self.fixture.png
        parts = chunks(original)
        self.assertTrue(any(name == b"IDAT" for name, _ in parts))
        self.assert_rejected(original[:8] + b"".join(
            raw for name, raw in parts if name != b"IDAT"))

    def test_ihdr_not_first_rejected(self):
        original = self.fixture.png
        parts = chunks(original)
        name = b"tEXt"
        payload = b"note\\x00fixture"
        block = (len(payload).to_bytes(4, "big") + name + payload +
                 (zlib.crc32(name + payload) & 0xffffffff).to_bytes(4, "big"))
        self.assert_rejected(original[:8] + block + original[8:])

    def test_unknown_critical_chunk_rejected_with_matching_digest(self):
        original = self.fixture.png
        parts = chunks(original)
        name = b"ABCD"
        payload = b"synthetic"
        block = (len(payload).to_bytes(4, "big") + name + payload +
                 (zlib.crc32(name + payload) & 0xffffffff).to_bytes(4, "big"))
        self.assert_rejected(original[:8] + parts[0][1] + block +
                             b"".join(raw for _, raw in parts[1:]))

    def test_noncontiguous_idat_rejected_with_matching_digest(self):
        original = self.fixture.png
        parts = chunks(original)
        idat_index = next(i for i, (name, _) in enumerate(parts)
                          if name == b"IDAT")
        name = b"tEXt"
        payload = b"note\\x00synthetic"
        block = (len(payload).to_bytes(4, "big") + name + payload +
                 (zlib.crc32(name + payload) & 0xffffffff).to_bytes(4, "big"))
        # Split one valid compressed IDAT payload across two adjacent IDAT
        # chunks, then insert a valid ancillary chunk between them.
        raw = parts[idat_index][1]
        size = int.from_bytes(raw[:4], "big")
        pixels = raw[8:8 + size]
        mid = len(pixels) // 2
        def idat(data):
            return (len(data).to_bytes(4, "big") + b"IDAT" + data +
                    (zlib.crc32(b"IDAT" + data) & 0xffffffff).to_bytes(4, "big"))
        altered = (original[:8] +
                   b"".join(part for _, part in parts[:idat_index]) +
                   idat(pixels[:mid]) + block + idat(pixels[mid:]) +
                   b"".join(part for _, part in parts[idat_index + 1:]))
        self.assert_rejected(altered)

    def test_late_palette_rejected_with_matching_digest(self):
        original = self.fixture.png
        parts = chunks(original)
        index = next(i for i, (name, _) in enumerate(parts)
                     if name == b"IDAT")
        name = b"PLTE"
        payload = bytes([0, 0, 0])
        block = (len(payload).to_bytes(4, "big") + name + payload +
                 (zlib.crc32(name + payload) & 0xffffffff).to_bytes(4, "big"))
        self.assert_rejected(original[:8] +
                             b"".join(part for _, part in parts[:index + 1]) +
                             block +
                             b"".join(part for _, part in parts[index + 1:]))



    def test_duplicate_palette_rejected_with_matching_digest(self):
        original = self.fixture.png
        parts = chunks(original)
        name = b"PLTE"
        payload = bytes([0, 0, 0])
        block = (len(payload).to_bytes(4, "big") + name + payload +
                 (zlib.crc32(name + payload) & 0xffffffff).to_bytes(4, "big"))
        self.assert_rejected(original[:8] + parts[0][1] + block + block +
                             b"".join(raw for _, raw in parts[1:]))

    def test_reserved_lowercase_chunk_name_rejected(self):
        original = self.fixture.png
        parts = chunks(original)
        name = b"abca"  # third byte is reserved and must be uppercase
        payload = b"synthetic"
        block = (len(payload).to_bytes(4, "big") + name + payload +
                 (zlib.crc32(name + payload) & 0xffffffff).to_bytes(4, "big"))
        self.assert_rejected(original[:8] + parts[0][1] + block +
                             b"".join(raw for _, raw in parts[1:]))

    def test_nonletter_chunk_name_rejected(self):
        original = self.fixture.png
        parts = chunks(original)
        name = b"ab1A"
        payload = b"synthetic"
        block = (len(payload).to_bytes(4, "big") + name + payload +
                 (zlib.crc32(name + payload) & 0xffffffff).to_bytes(4, "big"))
        self.assert_rejected(original[:8] + parts[0][1] + block +
                             b"".join(raw for _, raw in parts[1:]))

if __name__ == "__main__":
    unittest.main()
