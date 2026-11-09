"""F3-08 synthetic current-rights outage vs denial regression (no hosted calls)."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_feature3_private_png_reader import RevocableReaderTests
from feature3_private_png_reader import PrivateGeneratedDownloadDenied
from tenant_store import StorageUnavailable


class CurrentRightsOutageTests(unittest.TestCase):
    def setUp(self):
        self.fixture = RevocableReaderTests(methodName="test_private_bytes_verified_twice_no_signed_link")
        self.fixture.setUp()

    def test_transport_oserror_preserved_not_misclassified_as_rights_denial(self):
        def rights(*_args):
            raise OSError("SYNTHETIC_RIGHTS_NETWORK_DOWN")
        self.fixture.rights = rights
        self.fixture.reader = self.fixture.build()
        with self.assertRaises(OSError):
            self.fixture.read()
        self.assertEqual(self.fixture.calls, ["verify"])
        self.assertEqual(self.fixture.tenant.calls, ["member", "job", "asset"])

    def test_backend_storage_outage_preserved_before_private_get(self):
        def rights(*_args):
            raise StorageUnavailable("synthetic current rights backend unavailable")
        self.fixture.rights = rights
        self.fixture.reader = self.fixture.build()
        with self.assertRaises(StorageUnavailable):
            self.fixture.read()
        self.assertEqual(self.fixture.calls, ["verify"])

    def test_explicit_rights_denial_still_opaque(self):
        self.fixture.rights = lambda *_args: False
        self.fixture.reader = self.fixture.build()
        with self.assertRaises(PrivateGeneratedDownloadDenied) as caught:
            self.fixture.read()
        self.assertNotIn("SYNTHETIC", str(caught.exception))
        self.assertEqual(self.fixture.calls, ["verify"])


if __name__ == "__main__":
    unittest.main()
