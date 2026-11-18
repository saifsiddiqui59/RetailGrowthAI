"""No-network release/rollback source parity for alternate Issue #249 Y1."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "ops/p0249-y1-readonly-extra-get"
sys.path.insert(0, str(DIR))
from build_five_get_release import FIVE_FILES, TWO_FILES, MODES, stage_release


class Y1FiveRouteReleaseSourceTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        from stage_five_get_sources import SOURCES
        for relative in SOURCES.values():
            src = ROOT / relative
            dst = self.repo / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)

    def stage(self, mode):
        output = self.root / ("staged-" + mode)
        self.assertEqual(stage_release(self.repo, output, mode), output)
        return output

    def test_five_get_originals_only(self):
        stage = self.stage("five")
        actual = {str(p.relative_to(stage)) for p in stage.rglob("*") if p.is_file()}
        self.assertEqual(actual, FIVE_FILES)
        self.assertEqual(set(p.parent.name for p in stage.glob("*/function.json")),
                         {"p0249_health", "campaign_read", "render_job_read",
                          "poster_job_read", "poster_draft_read"})
        self.assertNotIn("function_app.py", actual)

    def test_rollback_two_retains_exact_original_routes(self):
        stage = self.stage("rollback-two")
        actual = {str(p.relative_to(stage)) for p in stage.rglob("*") if p.is_file()}
        self.assertEqual(actual, TWO_FILES)
        self.assertEqual(set(p.parent.name for p in stage.glob("*/function.json")),
                         {"p0249_health", "campaign_read"})
        self.assertFalse((stage / "p0249_readonly_jobs.py").exists())
        self.assertFalse((stage / "poster_job_read").exists())

    def test_both_modes_use_verbatim_original_bytes(self):
        for mode in MODES:
            stage = self.stage(mode)
            from stage_five_get_sources import SOURCES
            for relative in MODES[mode][1]:
                with self.subTest(mode=mode, path=relative):
                    self.assertEqual((stage / relative).read_bytes(),
                                     (self.repo / SOURCES[relative]).read_bytes())

    def test_unknown_mode_denied_before_any_write(self):
        target = self.root / "unknown"
        with self.assertRaisesRegex(ValueError, "unapproved"):
            stage_release(self.repo, target, "six")
        self.assertFalse(target.exists())

    def test_deployable_package_is_not_implicitly_built(self):
        for mode in MODES:
            stage = self.stage(mode)
            self.assertFalse((stage / ".python_packages").exists())
            self.assertFalse((stage / "function_app.py").exists())
            self.assertFalse(any(p.suffix == ".zip" for p in stage.rglob("*")))

    def test_unvendored_original_http_dependency_rejected_before_stage(self):
        source = self.repo / "azure-functions/campaign-api/http_api.py"
        source.write_text(source.read_text() + "\nimport requests\n")
        with self.assertRaisesRegex(ValueError, "unvendored Y1 Python import"):
            stage_release(self.repo, self.root / "no-unpinned-import", "five")
        self.assertFalse((self.root / "no-unpinned-import").exists())

    def test_privileged_worker_dependency_rejected_before_stage(self):
        source = self.repo / "azure-functions/campaign-api/render_api.py"
        source.write_text(source.read_text() + "\nfrom admin_store import AdminStore\n")
        with self.assertRaisesRegex(ValueError, "unvendored Y1 Python import"):
            stage_release(self.repo, self.root / "no-admin-store", "five")
        self.assertFalse((self.root / "no-admin-store").exists())

    def test_unpinned_azure_storage_import_rejected_before_stage(self):
        source = self.repo / "ops/p0249-y1-readonly-extra-get/p0249_readonly_jobs.py"
        source.write_text(source.read_text() + "\nfrom azure.storage.queue import QueueClient\n")
        with self.assertRaisesRegex(ValueError, "unvendored Azure SDK import"):
            stage_release(self.repo, self.root / "no-azure-queue", "five")
        self.assertFalse((self.root / "no-azure-queue").exists())

    def test_relative_import_rejected_before_stage(self):
        source = self.repo / "azure-functions/campaign-api/http_api.py"
        source.write_text(source.read_text() + "\nfrom .unsafe import anything\n")
        with self.assertRaisesRegex(ValueError, "unreviewed relative Y1 import"):
            stage_release(self.repo, self.root / "no-relative-import", "rollback-two")
        self.assertFalse((self.root / "no-relative-import").exists())

    def test_no_http_write_or_worker_route_in_either_mode(self):
        for mode in MODES:
            stage = self.stage(mode)
            for manifest in stage.glob("*/function.json"):
                with self.subTest(mode=mode, manifest=manifest):
                    bindings = json.loads(manifest.read_text())["bindings"]
                    self.assertEqual(len(bindings), 2)
                    self.assertEqual([b["type"] for b in bindings],
                                     ["httpTrigger", "http"])
                    self.assertEqual(bindings[0]["methods"], ["get"])


if __name__ == "__main__":
    unittest.main()
