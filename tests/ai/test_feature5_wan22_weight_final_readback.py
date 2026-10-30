"""GPU-OFF regression: a full SHA pass must not accept swapped model paths.

Tiny synthetic fixture bytes only; no actual Wan checkpoints or Azure access.
"""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from feature5_motion.infra import wan22_local_weight_audit as audit
from feature5_motion.shared_model_mount import EXPECTED, PreflightError
from test_feature5_shared_model_mount import sample


class FinalMountReadbackTests(unittest.TestCase):
    def test_swapped_identical_bytes_after_first_hash_are_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            expected = dict(EXPECTED)
            for i, name in enumerate(audit.WAN_FILES):
                payload = (b"OFFLINE-NOT-A-MODEL-" + bytes([i])) * 16
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                expected[name] = (
                    len(payload), hashlib.sha256(payload).hexdigest(),
                    EXPECTED[name][2],
                )
            with patch.object(audit, "EXPECTED", expected):
                ok = audit.audit_full_wan_model_bytes(
                    mounted_share_root=root, trusted_private_manifest=sample())
                self.assertEqual(ok["checkpoint_count"], 3)
                original = audit._actual_full_sha
                first = root / audit.WAN_FILES[0]
                changed = [False]

                def swap_after_hash(path, size, digest):
                    result = original(path, size, digest)
                    if Path(path) == first and not changed[0]:
                        # Same size and SHA but a different inode at the path.
                        replacement = first.with_name(first.name + ".new")
                        replacement.write_bytes(first.read_bytes())
                        replacement.replace(first)
                        changed[0] = True
                    return result

                with patch.object(audit, "_actual_full_sha",
                                  side_effect=swap_after_hash):
                    with self.assertRaisesRegex(
                            PreflightError, "identity changed"):
                        audit.audit_full_wan_model_bytes(
                            mounted_share_root=root,
                            trusted_private_manifest=sample())
                self.assertTrue(changed[0])


if __name__ == "__main__":
    unittest.main()
