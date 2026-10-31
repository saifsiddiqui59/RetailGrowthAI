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
        marker.get_file_properties.return_value = SimpleNamespace(size=len(self.blob))
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

    def test_ambiguous_nonfinite_or_recursive_marker_denied_without_model_heads(self):
        marker = self.share.get_file_client(a.MARKER)
        original = json.loads(self.blob)
        cases = (
            self.blob.replace(b'"gpu_started": false',
                              b'"gpu_started": true, "gpu_started": false', 1),
            self.blob.replace(b'"size":', b'"size": 1, "size":', 1),
            self.blob.replace(b'"total_bytes":', b'"extra": NaN, "total_bytes":', 1),
            self.blob.replace(b'"total_bytes":', b'"extra": Infinity, "total_bytes":', 1),
            b'[' * 2000 + b'0' + b']' * 2000,
            b'null', b'[]',
            b'{"gpu_started": false, "files": []} trailing',
        )
        for data in cases:
            with self.subTest(prefix=data[:50]):
                marker.get_file_properties.return_value.size = len(data)
                marker.download_file.return_value.readall.return_value = data
                for client in self.model_clients.values():
                    client.get_file_properties.reset_mock()
                with self.assertRaises(PreflightError):
                    a.audit_share(self.share)
                for client in self.model_clients.values():
                    client.get_file_properties.assert_not_called()
        self.assertEqual(original["total_bytes"], EXPECTED_BYTES)

    def test_marker_replacement_and_oversized_sdk_payload_denied(self):
        marker = self.share.get_file_client(a.MARKER)
        baseline = SimpleNamespace(size=len(self.blob), etag='"generation-a"')
        changed = SimpleNamespace(size=len(self.blob), etag='"generation-b"')
        marker.get_file_properties.side_effect = [baseline, changed]
        with self.assertRaisesRegex(PreflightError, "changed during"):
            a.audit_share(self.share)
        marker.get_file_properties.side_effect = None
        marker.get_file_properties.return_value = baseline
        marker.download_file.return_value.readall.return_value = self.blob + b"Z"
        with self.assertRaisesRegex(PreflightError, "readback size"):
            a.audit_share(self.share)
        marker.download_file.assert_called_with(
            offset=0, length=len(self.blob), max_concurrency=1)

    def test_wrong_tier_blocks(self):
        self.share.get_share_properties.return_value.access_tier = "Hot"
        with self.assertRaises(PreflightError):
            a.audit_share(self.share)

    def test_default_cli_is_entirely_offline(self):
        with patch.dict("os.environ", {}, clear=True), patch.object(a, "audit_share") as audit:
            self.assertEqual(a.main([]), 0)
            audit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
