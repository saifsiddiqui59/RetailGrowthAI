"""Offline source-only gates for the five-route Y1 #249 package staging.

NO Azure access, ZIP deployment, Supabase users or network calls.
"""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ops/p0249-y1-readonly-extra-get/stage_five_get_sources.py"
SPEC = importlib.util.spec_from_file_location("p0249_stage_five_get", SCRIPT)
stage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage)


class Y1FiveGetSourceStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.repo = self.home / "repo"
        self.repo.mkdir()
        for relative in stage.SOURCES.values():
            src = ROOT / relative
            target = self.repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
        self.target = self.home / "stage"

    def test_exact_five_get_only_and_verbatim_original_modules(self):
        actual = stage.stage_sources(self.repo, self.target)
        self.assertEqual(actual, self.target)
        self.assertEqual(
            {p.parent.name for p in actual.glob("*/function.json")},
            set(stage.ROUTES),
        )
        self.assertEqual(
            {str(p.relative_to(actual)) for p in actual.rglob("*") if p.is_file()},
            set(stage.SOURCES),
        )
        for dest, relative in stage.SOURCES.items():
            with self.subTest(dest=dest):
                self.assertEqual((actual / dest).read_bytes(),
                                 (self.repo / relative).read_bytes())
        self.assertFalse((actual / "function_app.py").exists())
        self.assertFalse((actual / ".python_packages").exists())
        self.assertFalse(any("queue" in p.name.lower() or "timer" in p.name.lower()
                             for p in actual.rglob("function.json")))

    def test_reject_post_trigger_before_writing(self):
        source = self.repo / stage.SOURCES["poster_job_read/function.json"]
        manifest = json.loads(source.read_text())
        manifest["bindings"][0]["methods"] = ["get", "post"]
        source.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "GET routes"):
            stage.stage_sources(self.repo, self.target)
        self.assertFalse(self.target.exists())

    def test_reject_altered_route_before_writing(self):
        source = self.repo / stage.SOURCES["render_job_read/function.json"]
        manifest = json.loads(source.read_text())
        manifest["bindings"][0]["route"] = "admin/{anything}"
        source.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "GET routes"):
            stage.stage_sources(self.repo, self.target)
        self.assertFalse(self.target.exists())

    def test_reject_additional_binding(self):
        source = self.repo / stage.SOURCES["campaign_read/function.json"]
        manifest = json.loads(source.read_text())
        manifest["bindings"].append({"type": "queueTrigger", "name": "q"})
        source.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            stage.stage_sources(self.repo, self.target)
        self.assertFalse(self.target.exists())

    def test_reject_missing_original_dependency(self):
        (self.repo / stage.SOURCES["render_api.py"]).unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            stage.stage_sources(self.repo, self.target)
        self.assertFalse(self.target.exists())

    def test_reject_symlink_to_any_source(self):
        source = self.repo / stage.SOURCES["security.py"]
        source.unlink()
        source.symlink_to(ROOT / stage.SOURCES["security.py"])
        with self.assertRaisesRegex(ValueError, "symlinked"):
            stage.stage_sources(self.repo, self.target)
        self.assertFalse(self.target.exists())

    def test_reject_changed_dependency_versions(self):
        source = self.repo / stage.SOURCES["requirements.txt"]
        source.write_text("azure-functions\nPyJWT\n")
        with self.assertRaisesRegex(ValueError, "requirements changed"):
            stage.stage_sources(self.repo, self.target)
        self.assertFalse(self.target.exists())

    def test_reject_manifest_that_changes_auth_level(self):
        source = self.repo / stage.SOURCES["poster_draft_read/function.json"]
        manifest = json.loads(source.read_text())
        manifest["bindings"][0]["authLevel"] = "admin"
        source.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "GET routes"):
            stage.stage_sources(self.repo, self.target)
        self.assertFalse(self.target.exists())

    def test_reject_modified_host_version(self):
        source = self.repo / stage.SOURCES["host.json"]
        source.write_text(json.dumps({"version": "3.0"}))
        with self.assertRaisesRegex(ValueError, "host version"):
            stage.stage_sources(self.repo, self.target)
        self.assertFalse(self.target.exists())

    def test_reject_preexisting_directory_and_existing_symlink(self):
        self.target.mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"):
            stage.stage_sources(self.repo, self.target)
        self.target.rmdir()
        self.target.symlink_to(self.repo, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "already exists"):
            stage.stage_sources(self.repo, self.target)

    def test_reject_staging_under_original_repo(self):
        with self.assertRaisesRegex(ValueError, "overlaps"):
            stage.stage_sources(self.repo, self.repo / "tmp-package")
        self.assertFalse((self.repo / "tmp-package").exists())


if __name__ == "__main__":
    unittest.main()
