"""F4-13: no network access or real customer media; private stock staging regression."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from feature4_stock_showcase import StockShowcaseError, retrieve_stock

URL = "https://videos.pexels.com/video-files/test/test-hd.mp4"
PAYLOAD = b"synthetic test fixture bytes" * 3000


class FakeResponse:
    url = URL
    headers = {"Content-Type": "video/mp4"}

    def __init__(self):
        self.sent = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _):
        if self.sent:
            return b""
        self.sent = True
        return PAYLOAD


class FakeOpener:
    def open(self, request, timeout):
        assert timeout == 55
        assert request.full_url == URL
        return FakeResponse()


class PrivateStockDownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.destination = self.root / "stock.mp4"

    def retrieve(self):
        with patch("feature4_stock_showcase.urllib.request.build_opener",
                   return_value=FakeOpener()):
            return retrieve_stock(self.destination, (URL,))

    def test_success_is_atomic_and_hashes_exact_fixture_bytes(self):
        receipt = self.retrieve()
        self.assertEqual(self.destination.read_bytes(), PAYLOAD)
        self.assertEqual(receipt["sha256"], hashlib.sha256(PAYLOAD).hexdigest())
        self.assertEqual(receipt["size_bytes"], len(PAYLOAD))
        self.assertEqual(list(self.root.glob(".feature4-stock-*")), [])

    def test_existing_private_media_cannot_be_overwritten(self):
        self.destination.write_bytes(b"keep-existing-private-media")
        with patch("feature4_stock_showcase.urllib.request.build_opener",
                   side_effect=AssertionError("network must not be attempted")):
            with self.assertRaisesRegex(StockShowcaseError, "overwrite"):
                retrieve_stock(self.destination, (URL,))
        self.assertEqual(self.destination.read_bytes(), b"keep-existing-private-media")

    def test_symlink_destination_cannot_redirect_private_download(self):
        protected = self.root / "protected.txt"
        protected.write_bytes(b"do-not-clobber")
        self.destination.symlink_to(protected)
        with self.assertRaisesRegex(StockShowcaseError, "overwrite"):
            self.retrieve()
        self.assertEqual(protected.read_bytes(), b"do-not-clobber")

    def test_concurrent_destination_creation_fails_closed_and_cleans_temp(self):
        def competing_writer(source, destination):
            Path(destination).write_bytes(b"newer-private-media")
            raise FileExistsError("another writer won")
        with patch("feature4_stock_showcase.os.link",
                   side_effect=competing_writer):
            with self.assertRaisesRegex(StockShowcaseError, "overwrite"):
                self.retrieve()
        self.assertEqual(self.destination.read_bytes(), b"newer-private-media")
        self.assertEqual(list(self.root.glob(".feature4-stock-*")), [])

    def test_invalid_media_type_leaves_no_private_temp_or_output(self):
        class WrongType(FakeResponse):
            headers = {"Content-Type": "text/html"}
        class BadOpener:
            def open(self, *_args, **_kwargs):
                return WrongType()
        with patch("feature4_stock_showcase.urllib.request.build_opener",
                   return_value=BadOpener()):
            with self.assertRaises(StockShowcaseError):
                retrieve_stock(self.destination, (URL,))
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.root.glob(".feature4-stock-*")), [])


if __name__ == "__main__":
    unittest.main()
