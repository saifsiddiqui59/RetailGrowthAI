"""Offline deployment package tests (no network, Azure or secrets)."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

module_path = Path(__file__).with_name("package.py")
spec = importlib.util.spec_from_file_location("rgai_packaging", module_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PackageTests(unittest.TestCase):
    def test_layout_and_safe_queue_concurrency(self):
        files = mod.source_files()
        self.assertIn("azure-functions/campaign-api/render_worker.py", files)
        self.assertIn("video-engine/render.py", files)
        self.assertIn("ai_agents/schemas.py", files)
        self.assertIn("function_app.py", files)
        host = json.loads(files["host.json"])
        self.assertEqual(host["extensions"]["queues"]["batchSize"], 1)
        self.assertEqual(host["extensions"]["queues"]["newBatchThreshold"], 0)
        self.assertEqual(host["extensions"]["queues"]["maxDequeueCount"], 3)
        self.assertEqual(host["functionTimeout"], "00:20:00")
        self.assertIn(b"sys.path.insert", files["function_app.py"])

    def test_budget_mismatch_fails_closed(self):
        host = {"functionTimeout": "00:20:00"}
        sql = (mod.ROOT / "supabase/migrations/20261022205000_p1_worker_execution_budget.sql").read_text()
        renderer = (mod.RENDER / "render.py").read_text()
        mod.verify_worker_budget(host, sql, renderer)
        with self.assertRaises(ValueError):
            mod.verify_worker_budget({"functionTimeout": "00:04:00"}, sql, renderer)
        with self.assertRaises(ValueError):
            mod.verify_worker_budget(host, sql.replace("25 minutes", "4 minutes"), renderer)
        with self.assertRaises(ValueError):
            mod.verify_worker_budget(host, sql, renderer.replace("timeout=780", "timeout=1500"))

    def test_binaries_must_be_verified_not_downloaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in ("ffmpeg", "ffprobe"):
                (folder / name).write_bytes(b"fake executable")
            (folder / "THIRD_PARTY_NOTICES.txt").write_text("Unverified")
            with self.assertRaises(ValueError):
                mod.ffmpeg_files(folder)

    def test_zip_reproducible_and_does_not_embed_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = mod.source_files()
            file = Path(tmp) / "functions.zip"
            mod.write_zip(file, entries)
            first = file.read_bytes()
            mod.write_zip(file, entries)
            self.assertEqual(first, file.read_bytes())
            with ZipFile(file) as archive:
                self.assertEqual(set(entries), set(archive.namelist()))
                self.assertNotIn("local.settings.json", archive.namelist())
                self.assertNotIn("bin/ffmpeg", archive.namelist())


if __name__ == "__main__":
    unittest.main()
