"""CPU-only, zero-cloud tests for shared Feature3/Feature5 Azure Files mount plan."""
import json
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
