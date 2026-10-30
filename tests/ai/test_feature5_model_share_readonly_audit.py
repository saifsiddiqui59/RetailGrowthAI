"""Strict read-only Azure Files HEAD audit using fake in-memory metadata."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from feature5_motion import audit_shared_model_share_readonly as a
from feature5_motion.shared_model_mount import EXPECTED, EXPECTED_BYTES, PreflightError


class ReadOnlyAuditTests(unittest.TestCase):
    def setUp(self):
        self.items = [{"path": p, "size": size, "sha256": sha,
                       "source": source, "revision": "a" * 40}
                      for p, (size, sha, source) in EXPECTED.items()]
        self.blob = json.dumps({"gpu_started": False, "files": self.items,
                                "total_bytes": EXPECTED_BYTES}).encode()
        self.share = Mock()
        self.share.get_share_properties.return_value = SimpleNamespace(access_tier="Cool", quota=64)
        marker = Mock()
        marker.get_file_properties.return_value = SimpleNamespace(size=len(self.blob), etag='"fixture-v1"')
        marker.download_file.return_value.readall.return_value = self.blob
        self.model_clients = {}
        for proof in self.items:
            client = Mock()
            client.get_file_properties.return_value = SimpleNamespace(
                size=proof["size"],
                metadata={"complete":"true","sha256":proof["sha256"],"revision":proof["revision"]})
            self.model_clients[proof["path"]] = client
        self.share.get_file_client.side_effect = lambda path: (
            marker if path == a.MARKER else self.model_clients[path])

    def test_metadata_only_audit_checks_all_six_no_weight_download(self):
        result = a.audit_share(self.share)
        self.assertEqual(result["files_checked"], 6)
        self.assertEqual(result["total_bytes"], 34277265757)
        self.assertFalse(result["weight_bytes_rehashed"])
        marker = self.share.get_file_client(a.MARKER)
        marker.download_file.assert_called_once_with(
            offset=0, length=len(self.blob), max_concurrency=1)
        self.assertEqual(marker.get_file_properties.call_count, 2)
        for client in self.model_clients.values():
            client.download_file.assert_not_called()

    def test_corrupt_sha_or_revision_blocks(self):
        first = next(iter(self.model_clients.values()))
        first.get_file_properties.return_value.metadata["sha256"] = "b" * 64
        with self.assertRaises(PreflightError):
            a.audit_share(self.share)
        first.get_file_properties.return_value.metadata["sha256"] = self.items[0]["sha256"]
        first.get_file_properties.return_value.metadata["revision"] = "b" * 40
        with self.assertRaises(PreflightError):
            a.audit_share(self.share)

    def test_oversize_marker_is_denied_before_read(self):
        marker = self.share.get_file_client(a.MARKER)
        marker.get_file_properties.return_value.size = a.MANIFEST_MAX_BYTES + 1
        with self.assertRaises(PreflightError):
            a.audit_share(self.share)
        marker.download_file.assert_not_called()

    def test_wrong_tier_blocks(self):
        self.share.get_share_properties.return_value.access_tier = "Hot"
        with self.assertRaises(PreflightError):
            a.audit_share(self.share)

    def test_ambiguous_duplicate_root_or_nested_keys_are_denied(self):
        root_duplicate = self.blob.replace(
            b'"gpu_started": false',
            b'"gpu_started": true, "gpu_started": false', 1)
        nested_duplicate = self.blob.replace(
            b'"path": ', b'"path": "feature5/forged", "path": ', 1)
        for blob in (root_duplicate, nested_duplicate):
            with self.subTest(blob=blob[:100]):
                marker = self.share.get_file_client(a.MARKER)
                marker.get_file_properties.return_value = SimpleNamespace(
                    size=len(blob), etag='"fixture-v1"')
                marker.download_file.return_value.readall.return_value = blob
                with self.assertRaises(PreflightError):
                    a.audit_share(self.share)

    def test_nonfinite_recursive_or_nonobject_marker_denied(self):
        nonfinite = self.blob[:-1] + b', "ignored": NaN}'
        recursive = (self.blob[:-1] + b', "ignored": ' +
                     b'[' * 1500 + b'0' + b']' * 1500 + b'}')
        for blob in (nonfinite, recursive, b'[]', b'not-json'):
            with self.subTest(size=len(blob)):
                marker = self.share.get_file_client(a.MARKER)
                marker.get_file_properties.return_value = SimpleNamespace(
                    size=len(blob), etag='"fixture-v1"')
                marker.download_file.return_value.readall.return_value = blob
                with self.assertRaises(PreflightError):
                    a.audit_share(self.share)

    def test_changed_marker_size_or_etag_after_read_denied(self):
        marker = self.share.get_file_client(a.MARKER)
        for after in (
            SimpleNamespace(size=len(self.blob) + 1, etag='"fixture-v1"'),
            SimpleNamespace(size=len(self.blob), etag='"fixture-v2"'),
            SimpleNamespace(size=len(self.blob)),
        ):
            with self.subTest(after=after):
                marker.get_file_properties.side_effect = [
                    SimpleNamespace(size=len(self.blob), etag='"fixture-v1"'),
                    after,
                ]
                with self.assertRaises(PreflightError):
                    a.audit_share(self.share)
                self.assertEqual(marker.download_file.call_args.kwargs["length"],
                                 len(self.blob))
                marker.get_file_properties.reset_mock(side_effect=True)
                marker.download_file.reset_mock()

    def test_default_cli_is_entirely_offline(self):
        with patch.dict("os.environ", {}, clear=True), patch.object(a, "audit_share") as audit:
            self.assertEqual(a.main([]), 0)
            audit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
