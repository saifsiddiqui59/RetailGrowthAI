"""CPU-only private model manifest ancestor denial regression."""
import tempfile
import unittest
from pathlib import Path
from feature5_motion import shared_model_mount as m

class ManifestParentGuardTests(unittest.TestCase):
    def test_symlinked_parent_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "real"
            real.mkdir()
            (real / "manifest.json").write_text('{"gpu_started":false,"files":[]}', encoding="utf-8")
            alias = root / "alias"
            alias.symlink_to(real, target_is_directory=True)
            with self.assertRaises(m.PreflightError):
                m.read_private_manifest(alias / "manifest.json")
            self.assertFalse(m.read_private_manifest(real / "manifest.json")["gpu_started"])

if __name__ == "__main__":
    unittest.main()
