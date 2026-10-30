"""CPU-only, zero-cloud tests for shared Feature3/Feature5 Azure Files mount plan."""
from hashlib import sha256
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from feature5_motion import shared_model_mount as m


def sample():
    return {
        "gpu_started": False,
        "files": [
            {"path": name, "size": size, "sha256": digest, "source": repo, "revision": "a" * 40}
            for name, (size, digest, repo) in m.EXPECTED.items()
        ],
        "total_bytes": m.EXPECTED_BYTES,
    }


class SharedModelMountTests(unittest.TestCase):
    def test_exact_6_file_model_manifest(self):
        obj = sample()
        revisions = m.validate_manifest(obj)
        self.assertEqual(len(revisions), 3)
        self.assertEqual(sum(x["size"] for x in obj["files"]), 34277265757)
        self.assertEqual({x["path"] for x in obj["files"]}, set(m.EXPECTED))

    def test_rejects_corrupt_or_untrusted_metadata(self):
        for key, value in [("size", 1), ("sha256", "f" * 64), ("source", "unapproved/repo"), ("revision", "main")]:
            obj = sample()
            obj["files"][0][key] = value
            with self.subTest(key=key), self.assertRaises(m.PreflightError):
                m.validate_manifest(obj)
        obj = sample()
        obj["gpu_started"] = True
        with self.assertRaises(m.PreflightError):
            m.validate_manifest(obj)
        obj = sample()
        obj["total_bytes"] += 1
        with self.assertRaises(m.PreflightError):
            m.validate_manifest(obj)
        obj = sample()
        obj["files"][0] = obj["files"][1].copy()
        with self.assertRaises(m.PreflightError):
            m.validate_manifest(obj)

    def test_rejects_mixed_upstream_revisions(self):
        obj = sample()
        obj["files"][1]["revision"] = "b" * 40
        with self.assertRaises(m.PreflightError):
            m.validate_manifest(obj)

    def test_comfy_model_paths_are_share_relative_and_disjoint(self):
        config = m.comfy_extra_paths()
        self.assertIn("base_path: /mnt/retailgrowth-models/feature3", config)
        self.assertIn("base_path: /mnt/retailgrowth-models/feature5", config)
        for stem in ("diffusion_models", "text_encoders", "vae"):
            self.assertEqual(config.count("  " + stem + ": " + stem), 2)
        self.assertNotIn("wine", config.lower())

    def test_azure_file_volume_is_explicit_ro_no_gpu_actions(self):
        config = m.job_volume_fragment()
        self.assertEqual(config["environment_storage"]["storage_type"], "AzureFile")
        self.assertEqual(config["environment_storage"]["access_mode"], "ReadOnly")
        self.assertEqual(config["environment_storage"]["azure_file_share_name"], "retailgrowth-models")
        self.assertEqual(config["template_fragment"]["containers"][0]["volumeMounts"][0]["mountPath"], m.MOUNT_PATH)
        self.assertFalse(config["gpu_start_authorized"])
        self.assertFalse(config["executes_azure_commands"])
        self.assertNotIn("key", json.dumps(config).lower())

    def test_mounted_files_must_exist_and_not_be_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(m.PreflightError):
                m.check_mounted_files(temp)
            bad_root = Path(temp) / "linked"
            bad_root.symlink_to(temp, target_is_directory=True)
            with self.assertRaises(m.PreflightError):
                m.check_mounted_files(bad_root)


    def test_explicit_full_sha256_readback_of_small_local_fixture_only(self):
        """Never read the actual 34GB Azure share in automated tests."""
        relative = "feature5/vae/wan2.2_vae.safetensors"
        original = b"tiny CPU-only fixture, NOT real Wan weights"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / relative
            path.parent.mkdir(parents=True)
            path.write_bytes(original)
            expected = {relative: (len(original), sha256(original).hexdigest(), "fixture-only")}
            with patch.dict(m.EXPECTED, expected, clear=True):
                self.assertTrue(m.check_mounted_files(temp))
                self.assertEqual(m.verify_mounted_sha256(temp), {relative: sha256(original).hexdigest()})
                # Same byte count and metadata shape do not establish integrity.
                path.write_bytes(b"x" * len(original))
                self.assertTrue(m.check_mounted_files(temp))
                with self.assertRaisesRegex(m.PreflightError, "SHA-256 mismatch"):
                    m.verify_mounted_sha256(temp)

    def test_full_scan_rejects_parent_directory_symlinks(self):
        relative = "feature5/vae/wan2.2_vae.safetensors"
        payload = b"safe synthetic bytes"
        with tempfile.TemporaryDirectory() as temp:
            real = Path(temp) / "actual" / "vae"
            real.mkdir(parents=True)
            (real / "wan2.2_vae.safetensors").write_bytes(payload)
            (Path(temp) / "feature5").symlink_to(Path(temp) / "actual", target_is_directory=True)
            with patch.dict(m.EXPECTED, {relative: (len(payload), sha256(payload).hexdigest(), "fixture")}, clear=True):
                with self.assertRaises(m.PreflightError):
                    m.check_mounted_files(temp)
                with self.assertRaises(m.PreflightError):
                    m.verify_mounted_sha256(temp)

    def test_full_scan_never_runs_without_two_explicit_cli_flags(self):
        with tempfile.TemporaryDirectory() as temp:
            for args in (["--verify-sha256"], ["--verify-sha256", "--mounted-root", temp],
                         ["--confirm-full-scan", "--mounted-root", temp]):
                with self.subTest(args=args), self.assertRaises(SystemExit) as caught:
                    m.main(args)
                self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
