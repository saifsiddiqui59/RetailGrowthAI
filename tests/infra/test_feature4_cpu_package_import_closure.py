"""Keep real F4 FunctionApp imports closed inside the sealed worker ZIP."""
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from scripts.deploy import package_feature4_cpu as packager
from scripts.deploy.verify_feature4_cpu_release import REQUIRED

ROOT=Path(__file__).resolve().parents[2]


class F4WorkerCompleteImportTests(TestCase):
    def test_tenant_store_security_import_is_in_archived_source(self):
        src=packager.sources()
        self.assertIn("security.py",src)
        self.assertEqual(src["security.py"],packager.SERVICE/"security.py")
        self.assertIn("security.py",REQUIRED)
        self.assertIn("from security import AuthenticationError",
                      (packager.SERVICE/"tenant_store.py").read_text())

    def test_fails_closed_when_local_security_dependency_is_dropped(self):
        omitted=tuple(x for x in packager.SERVICE_MODULES if x!="security.py")
        with patch.object(packager,"SERVICE_MODULES",omitted):
            with self.assertRaisesRegex(ValueError,"Missing local F4 worker import: security"):
                packager.sources()

    def test_sealed_stage_runs_complete_source_and_artifact_checks(self):
        workflow=(ROOT/".github/workflows/retail-dev-feature4-cpu-zip-once.yml").read_text()
        self.assertIn("package_feature4_cpu.py --check",workflow)
        self.assertIn("verify_feature4_cpu_release.py",workflow)
        self.assertLess(workflow.index("verify_feature4_cpu_release.py"),
                        workflow.index("uses: Azure/functions-action@"))
        self.assertIn("RETAIL_FEATURE4_CPU_WORKER_ENABLED",workflow)
        self.assertIn("RETAIL_FEATURE4_CPU_RENDER_ENABLED",workflow)
        self.assertIn("protected worker credential remains after failed trigger rollback",workflow)
        self.assertIn("unexpected privileged worker secret after ZIP stage",workflow)
