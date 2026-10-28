"""F4-08 no-network tests for HyperFrames producer execution requirements."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine" / "hyperframes"))
from qualify_runtime import node_version, chromium_binary


class RuntimePreflightTests(unittest.TestCase):
    def test_puppeteer_node_22_12_minimum(self):
        self.assertEqual(node_version("v22.12.0"), (22, 12, 0))
        self.assertEqual(node_version("v24.0.0"), (24, 0, 0))
        for item in ("v22.11.0", "v20.19.1", "bad", "22", "v22.9.9"):
            with self.subTest(value=item), self.assertRaises(ValueError):
                node_version(item)

    def test_chromium_cache_must_have_expected_local_executable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertIsNone(chromium_binary(root))
            exe = (root / "chrome-headless-shell" / "linux-156.0" /
                   "chrome-headless-shell-linux64" / "chrome-headless-shell")
            exe.parent.mkdir(parents=True)
            exe.write_text("synthetic binary fixture", encoding="utf-8")
            self.assertIsNone(chromium_binary(root), "Non-executable must fail")
            exe.chmod(0o755)
            self.assertEqual(chromium_binary(root), exe)


if __name__ == "__main__":
    unittest.main()
