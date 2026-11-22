"""Isolated F4 CPU host must never batch multiple long CPU renders."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
FILE = ROOT / "scripts" / "deploy" / "package_feature4_cpu.py"
spec = importlib.util.spec_from_file_location("f4_cpu_packager_concurrency", FILE)
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)


class Feature4CpuSingleRenderHostTests(unittest.TestCase):
    def test_isolated_host_is_used_and_original_stays_untouched(self):
        sources = pack.sources()
        self.assertEqual(sources["host.json"], pack.ISOLATED / "host.json")
        worker = json.loads(sources["host.json"].read_text())
        legacy = json.loads((pack.SERVICE / "host.json").read_text())
        self.assertEqual(worker["functionTimeout"], "00:20:00")
        self.assertEqual(worker["extensions"]["queues"]["batchSize"], 1)
        self.assertEqual(worker["extensions"]["queues"]["newBatchThreshold"], 0)
        self.assertIs(worker["concurrency"]["dynamicConcurrencyEnabled"], False)
        self.assertNotIn("batchSize", legacy["extensions"]["queues"])
        self.assertNotIn("newBatchThreshold", legacy["extensions"]["queues"])

    def test_package_rejects_multiple_render_queue_messages(self):
        with tempfile.TemporaryDirectory() as directory:
            staging = Path(directory)
            for name in ("host.json", "function_app.py", "cpu_backend.py"):
                shutil.copy2(pack.ISOLATED / name, staging / name)
            edited = json.loads((staging / "host.json").read_text())
            edited["extensions"]["queues"]["batchSize"] = 16
            (staging / "host.json").write_text(json.dumps(edited))
            with patch.object(pack, "ISOLATED", staging):
                with self.assertRaisesRegex(ValueError, "isolated F4 CPU queue concurrency"):
                    pack.sources()

    def test_package_rejects_dynamic_concurrency_override(self):
        with tempfile.TemporaryDirectory() as directory:
            staging = Path(directory)
            for name in ("host.json", "function_app.py", "cpu_backend.py"):
                shutil.copy2(pack.ISOLATED / name, staging / name)
            edited = json.loads((staging / "host.json").read_text())
            edited["concurrency"]["dynamicConcurrencyEnabled"] = True
            (staging / "host.json").write_text(json.dumps(edited))
            with patch.object(pack, "ISOLATED", staging):
                with self.assertRaisesRegex(ValueError, "isolated F4 CPU queue concurrency"):
                    pack.sources()


if __name__ == "__main__":
    unittest.main()
