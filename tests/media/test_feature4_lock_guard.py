"""Feature4 lock audit tests use original recovered CI lock when available.

A local synthetic file cannot masquerade as an audited 138-entry package lock.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine" / "hyperframes"))
from lock_guard import (verify_lock, DependencyLockError, PINNED_SHA256,
                        PRODUCER_VERSION, LOCK_PACKAGES)


class DependencyLockTests(unittest.TestCase):
    def test_frozen_reviewed_pin_format_and_count(self):
        self.assertEqual(len(PINNED_SHA256), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in PINNED_SHA256))
        self.assertEqual(PRODUCER_VERSION, "0.8.185")
        self.assertEqual(LOCK_PACKAGES, 138)

    def test_missing_or_modified_lock_fails_without_installing(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "package-lock.json"
            for content in (b"", b"{}", b'{"lockfileVersion":3}', b"x" * 200_001):
                path.write_bytes(content)
                with self.subTest(length=len(content)), self.assertRaises(DependencyLockError):
                    verify_lock(path)
            with self.assertRaises(FileNotFoundError):
                verify_lock(Path(root) / "missing.json")

    def test_correct_shape_but_wrong_sha_is_never_accepted(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "lock.json"
            path.write_text(json.dumps({"lockfileVersion": 3, "packages": {
                "": {"dependencies": {"@hyperframes/producer": "0.8.185"}}
            }}).ljust(1200))
            with self.assertRaisesRegex(DependencyLockError, "drifted"):
                verify_lock(path)

    def test_cannot_override_sha_with_user_or_runtime_environment(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "lock.json"
            path.write_bytes(b"x" * 1024)
            with patch.dict("os.environ", {"FEATURE4_LOCK_SHA256": hashlib.sha256(path.read_bytes()).hexdigest()}):
                with self.assertRaises(DependencyLockError):
                    verify_lock(path)

    def test_checked_in_lockfile_is_exact_frozen_audited_bytes(self):
        # A clean checkout must ship the same reviewed CI lock; no resolver step.
        lock = ROOT / "video-engine" / "hyperframes" / "package-lock.json"
        self.assertTrue(lock.is_file(), "Git-tracked dependency lock is required")
        self.assertEqual(hashlib.sha256(lock.read_bytes()).hexdigest(), PINNED_SHA256)
        result = verify_lock(lock)
        self.assertTrue(result["lockfile_committed_to_repository"])
        self.assertFalse(result["legal_signoff_for_commercial_saas"])
        self.assertEqual(result["package_entries_including_root"], LOCK_PACKAGES)


if __name__ == "__main__":
    unittest.main()
