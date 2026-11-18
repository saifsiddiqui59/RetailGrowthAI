"""F5-14 GPU-OFF regressions for existing mounted Wan weights only.

Tests create tiny synthetic files with test-only SHA overrides. They do NOT
validate actual model checkpoints, cloud mount permissions or commercial rights.
Consolidates protections proposed by existing draft PRs #771 and #746.
"""
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from feature5_motion.infra import wan22_local_weight_audit as audit
from feature5_motion.shared_model_mount import EXPECTED, PreflightError
from test_feature5_shared_model_mount import sample


class MountedWanIdentityIntegrationTests(unittest.TestCase):
    def _fake_mount(self, root):
        expected = dict(EXPECTED)
        for i, name in enumerate(audit.WAN_FILES):
            payload = (b"NON-WAN-FIXTURE-ONLY-" + bytes([i])) * 16
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            expected[name] = (len(payload), hashlib.sha256(payload).hexdigest(), EXPECTED[name][2])
        return expected

    def test_unchanged_three_file_mount_succeeds_without_gpu(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            expected = self._fake_mount(root)
            with patch.object(audit, "EXPECTED", expected):
                proof = audit.audit_full_wan_model_bytes(
                    mounted_share_root=root, trusted_private_manifest=sample())
            self.assertEqual(proof["checkpoint_count"], 3)
            self.assertEqual(proof["checkpoint_bytes_sha256_verified"],
                             sum(expected[name][0] for name in audit.WAN_FILES))
            self.assertFalse(proof["gpu_started"])
            self.assertFalse(proof["read_only_mount_proven"])
            self.assertFalse(proof["license_approved"])

    def test_path_replaced_with_same_hash_after_descriptor_open_denied(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "approved.safetensors"
            path.write_bytes(b"OFFLINE-ONLY-WEIGHT" * 12)
            replacement = Path(td) / "same-bytes-new-inode"
            replacement.write_bytes(path.read_bytes())
            actual_fstat = os.fstat
            calls = 0

            def swap_before_final_fstat(fd):
                nonlocal calls
                calls += 1
                if calls == 2:
                    replacement.replace(path)
                return actual_fstat(fd)

            with patch.object(audit.os, "fstat", side_effect=swap_before_final_fstat):
                # An atomic replacement can change the old open inode's ctime.
                # Both the descriptor-ctime denial and pathname-identity
                # denial are correct; require fail-closed behavior, not an
                # implementation-specific detection order.
                with self.assertRaisesRegex(
                        PreflightError, "modified during hashing|pathname changed"):
                    audit._actual_full_sha(
                        path, path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(calls, 2)

    def test_hardlink_created_mid_hash_denied(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "approved.safetensors"
            path.write_bytes(b"OFFLINE-ONLY-WEIGHT" * 12)
            size = path.stat().st_size
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            actual_fstat = os.fstat
            calls = 0

            def add_link_before_final_fstat(fd):
                nonlocal calls
                calls += 1
                if calls == 2:
                    os.link(path, Path(td) / "unexpected-hardlink")
                return actual_fstat(fd)

            with patch.object(audit.os, "fstat", side_effect=add_link_before_final_fstat):
                with self.assertRaisesRegex(PreflightError, "modified during hashing"):
                    audit._actual_full_sha(path, size, digest)
            self.assertEqual(calls, 2)

    def test_first_weight_swapped_after_its_hash_denied_at_final_readback(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            expected = self._fake_mount(root)
            first = root / audit.WAN_FILES[0]
            original = audit._actual_full_sha
            changed = []

            def swap_after_first_complete_sha(path, size, digest):
                count = original(path, size, digest)
                if Path(path) == first and not changed:
                    replacement = first.with_name(first.name + ".next")
                    replacement.write_bytes(first.read_bytes())
                    replacement.replace(first)
                    changed.append(True)
                return count

            with patch.object(audit, "EXPECTED", expected), patch.object(
                    audit, "_actual_full_sha", side_effect=swap_after_first_complete_sha):
                with self.assertRaisesRegex(PreflightError, "identity changed during full audit"):
                    audit.audit_full_wan_model_bytes(
                        mounted_share_root=root, trusted_private_manifest=sample())
            self.assertTrue(changed)


if __name__ == "__main__":
    unittest.main()
