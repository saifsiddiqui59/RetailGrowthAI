"""Feature #5 model artifact integrity negative tests; no GPU or external weights."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from feature5_motion.artifact_lock import (
    ArtifactLock, construct_manifest, MAX_FILE_BYTES,
)
from feature5_motion.contracts import MotionError


class TestHunyuanModelArtifactLock(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="feature5-artifact-fixture-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.checkout = self.base / "checkout"
        self.weights = self.base / "licensed-weights"
        (self.checkout / "lib").mkdir(parents=True)
        (self.weights / "model").mkdir(parents=True)
        (self.checkout / "generate.py").write_text("print('synthetic stub, not official inference')\n")
        (self.checkout / "lib" / "pipeline.py").write_bytes(b"synthetic code bytes")
        (self.weights / "model" / "shard.bin").write_bytes(b"synthetic test weight bytes")
        self.lock = self.base / "reviewed-manifest.json"

    def seal(self):
        candidate = construct_manifest(self.checkout, self.weights)
        self.lock.write_bytes(candidate)
        return ArtifactLock(self.lock, hashlib.sha256(candidate).hexdigest())

    def test_reviewed_exact_manifest_checks_code_and_weights(self):
        approved = self.seal()
        self.assertEqual(approved.verify(checkout=self.checkout, weights=self.weights),
                         hashlib.sha256(self.lock.read_bytes()).hexdigest())
        manifest = json.loads(self.lock.read_bytes())
        self.assertEqual(manifest["version"], "feature5-artifacts-v1")
        self.assertEqual({r["scope"] for r in manifest["files"]}, {"checkout", "weights"})

    def test_same_bytes_different_tenant_checkout_is_no_change(self):
        lock = self.seal()
        self.assertEqual(len(lock.verify(checkout=self.checkout, weights=self.weights)), 64)

    def test_mutated_weight_or_runtime_code_fails(self):
        for relative, parent in (("model/shard.bin", self.weights),
                                 ("lib/pipeline.py", self.checkout),
                                 ("generate.py", self.checkout)):
            with self.subTest(relative=relative):
                lock = self.seal()
                target = parent / relative
                old = target.read_bytes()
                target.write_bytes(old + b"tampered")
                with self.assertRaises(MotionError):
                    lock.verify(checkout=self.checkout, weights=self.weights)
                target.write_bytes(old)

    def test_extra_or_removed_artifact_detected(self):
        lock = self.seal()
        extra = self.weights / "injected.pkl"
        extra.write_bytes(b"poison")
        with self.assertRaises(MotionError):
            lock.verify(checkout=self.checkout, weights=self.weights)
        extra.unlink()
        original = self.weights / "model" / "shard.bin"
        original.unlink()
        with self.assertRaises(MotionError):
            lock.verify(checkout=self.checkout, weights=self.weights)

    def test_self_declared_modified_manifest_without_reviewed_digest_rejected(self):
        approved = self.seal()
        parsed = json.loads(self.lock.read_bytes())
        parsed["files"][0]["sha256"] = "a" * 64
        self.lock.write_text(json.dumps(parsed))
        with self.assertRaisesRegex(MotionError, "differs from reviewed"):
            approved.verify(checkout=self.checkout, weights=self.weights)

    def test_forgeries_duplicates_traversal_and_invalid_hash(self):
        for bad in ("../escape.bin", "/etc/secret", "code\\injection.py", "one//two", "./bad", "a/.."):
            with self.subTest(bad=bad):
                baseline = json.loads(construct_manifest(self.checkout, self.weights))
                baseline["files"][0]["path"] = bad
                raw = json.dumps(baseline, sort_keys=True, separators=(",", ":")).encode()
                self.lock.write_bytes(raw)
                with self.assertRaises(MotionError):
                    ArtifactLock(self.lock, hashlib.sha256(raw).hexdigest()).verify(
                        checkout=self.checkout, weights=self.weights)
        baseline = json.loads(construct_manifest(self.checkout, self.weights))
        baseline["files"].append(dict(baseline["files"][0]))
        raw = json.dumps(baseline, sort_keys=True, separators=(",", ":")).encode()
        self.lock.write_bytes(raw)
        with self.assertRaisesRegex(MotionError, "Duplicate"):
            ArtifactLock(self.lock, hashlib.sha256(raw).hexdigest()).verify(
                checkout=self.checkout, weights=self.weights)

    def test_symlinks_and_dirty_git_checkout_fail_closed(self):
        lock = self.seal()
        weight = self.weights / "model" / "linked.bin"
        weight.symlink_to(self.weights / "model" / "shard.bin")
        with self.assertRaises(MotionError):
            lock.verify(checkout=self.checkout, weights=self.weights)
        weight.unlink()
        link_dir = self.weights / "extra"
        link_dir.symlink_to(self.weights / "model", target_is_directory=True)
        with self.assertRaises(MotionError):
            lock.verify(checkout=self.checkout, weights=self.weights)
        link_dir.unlink()
        (self.checkout / ".git").mkdir()
        with self.assertRaisesRegex(MotionError, "Git metadata"):
            construct_manifest(self.checkout, self.weights)

    def test_oversized_sparse_shard_rejected_before_hash(self):
        giant = self.weights / "model" / "huge.bin"
        with giant.open("wb") as handle:
            handle.truncate(MAX_FILE_BYTES + 1)
        with self.assertRaisesRegex(MotionError, "size outside"):
            construct_manifest(self.checkout, self.weights)


if __name__ == "__main__":
    unittest.main()
