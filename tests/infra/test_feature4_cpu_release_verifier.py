"""Offline integrity negatives for the isolated Feature4 native release."""
import hashlib
import importlib.util
import json
import stat
import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts" / "deploy" / "verify_feature4_cpu_release.py"
spec = importlib.util.spec_from_file_location("f4_zip_verify", SOURCE)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def _sample(output, *, corrupt=None, extra=None, omit=None):
    required = release.REQUIRED | {
        ".python_packages/lib/site-packages/azure/functions/__init__.py",
        "hyperframes/node_modules/@hyperframes/producer/index.js",
        "puppeteer-cache/chrome-headless-shell/123/"
        "chrome-headless-shell-linux64/chrome-headless-shell",
    }
    body = {name: b"synthetic-reviewed-fixture-" + name.encode()
            for name in required - (omit or set())}
    body.update(extra or {})
    recorded = {name: hashlib.sha256(content).hexdigest() for name, content in body.items()}
    if corrupt:
        recorded[corrupt] = "0" * 64
    manifest = json.dumps({
        "schema": "retailgrowth-f4-native-worker-zip-v1",
        "cpu_only": True, "gpu_allowed": False,
        "contains_secrets": False, "file_sha256": recorded,
    }).encode()
    with ZipFile(output, "w") as z:
        for name, content in sorted(body.items()):
            info = ZipInfo(name)
            info.create_system = 3
            mode = (stat.S_IFREG | (0o755 if name.startswith("bin/") else 0o644))
            info.external_attr = mode << 16
            z.writestr(info, content)
        z.writestr("package_manifest.json", manifest)


class Feature4ReleaseIntegrityTests(unittest.TestCase):
    def test_approved_synthetic_zip_has_exact_checksum_proof(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "worker.zip"
            _sample(output)
            receipt = release.verify_release(output)
            self.assertEqual(receipt["files"], len(release.REQUIRED) + 3)
            self.assertEqual(len(receipt["verified_sha256"]), 64)

    def test_modified_bytes_cannot_reuse_sealed_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "worker.zip"
            _sample(output, corrupt="cpu_backend.py")
            with self.assertRaisesRegex(release.ReleaseIntegrityError, "sealed SHA-256"):
                release.verify_release(output)

    def test_missing_dependency_or_undocumented_member_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "worker.zip"
            _sample(output, omit={"cpu_backend.py"})
            with self.assertRaisesRegex(release.ReleaseIntegrityError, "Missing or unauthorized"):
                release.verify_release(output)
            _sample(output, extra={"http_api.py": b"unshipped legacy HTTP"})
            with self.assertRaisesRegex(release.ReleaseIntegrityError, "Missing or unauthorized"):
                release.verify_release(output)

    def test_unsafe_path_and_duplicate_member_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "worker.zip"
            _sample(output, extra={"../private.txt": b"bad"})
            with self.assertRaisesRegex(release.ReleaseIntegrityError, "Unsafe"):
                release.verify_release(output)
            _sample(output)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with ZipFile(output, "a") as z:
                    z.writestr("cpu_backend.py", b"duplicate")
            with self.assertRaisesRegex(release.ReleaseIntegrityError, "Duplicate"):
                release.verify_release(output)

    def test_symlinked_release_file_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "worker.zip"
            _sample(output)
            link = Path(root) / "current.zip"
            link.symlink_to(output)
            with self.assertRaisesRegex(release.ReleaseIntegrityError, "linked"):
                release.verify_release(link)
