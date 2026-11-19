"""Offline regression suite for #249 existing Y1 v1-indexed canary package."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "ops/p0249-y1-v1-canary"
WORKFLOW = ROOT / ".github/workflows/p0249-dev-y1-v1-index-recovery-once.yml"


class Y1V1CanaryRecoveryTests(unittest.TestCase):
    def test_function_json_is_single_explicit_http_get(self):
        manifest = json.loads((PACKAGE / "p0249_health/function.json").read_text())
        self.assertEqual(manifest["scriptFile"], "__init__.py")
        self.assertEqual(manifest["entryPoint"], "main")
        self.assertEqual(len(manifest["bindings"]), 2)
        request = next(x for x in manifest["bindings"] if x["type"] == "httpTrigger")
        self.assertEqual(request["name"], "req")
        self.assertEqual(request["route"], "p0249/health")
        self.assertEqual(request["authLevel"], "anonymous")
        self.assertEqual(request["methods"], ["get"])
        self.assertEqual(request["direction"], "in")
        response = next(x for x in manifest["bindings"] if x["type"] == "http")
        self.assertEqual(response["name"], "$return")
        self.assertEqual(response["direction"], "out")

    def test_python_script_explicit_main_without_queue_or_models(self):
        content = (PACKAGE / "p0249_health/__init__.py").read_text()
        tree = ast.parse(content)
        funcs = [x for x in tree.body if isinstance(x, ast.FunctionDef)]
        self.assertEqual([f.name for f in funcs], ["main"])
        self.assertEqual([x.arg for x in funcs[0].args.args], ["req"])
        self.assertIn("X-Request-ID", content)
        self.assertNotIn("queue_trigger", content)
        self.assertNotIn("timer_trigger", content)
        self.assertNotIn("Supabase", content)
        self.assertNotIn("storage_account", content)
        self.assertNotIn("MODEL", content)

    def test_minimal_package_no_v2_decorator(self):
        self.assertFalse((PACKAGE / "function_app.py").exists())
        self.assertTrue((PACKAGE / "host.json").exists())
        self.assertEqual(json.loads((PACKAGE / "host.json").read_text())["version"], "2.0")
        reqs = (PACKAGE / "requirements.txt").read_text().strip()
        self.assertEqual(reqs, "azure-functions==1.24.0")

    def test_workflow_exact_dev_oidc_and_identity_verification(self):
        content = WORKFLOW.read_text()
        for text in ("environment: dev", "id-token: write", "workflow_dispatch:",
                     "YES-Y1-ONLY-V1-RECOVERY", "refs/heads/main",
                     "p0249_y1_canary_guard.py verify", "setup-python@v6",
                     "python-version: '3.12'", "--build-remote false",
                     "P0249_Y1_V1_INDEXED_SUCCESS",
                     "p0249_y1_canary_guard.py probe"):
            with self.subTest(required=text):
                self.assertIn(text, content)

    def test_prohibit_infra_and_existing_flex_writes(self):
        content = WORKFLOW.read_text()
        for text in ("az deployment group create", "az resource delete",
                     "az group delete", "az functionapp create",
                     "az functionapp delete", "az functionapp config appsettings",
                     "az functionapp scale config always-ready set",
                     "az storage account delete", "rgai-dev-functions-d4e5ddbd"):
            with self.subTest(forbidden=text):
                self.assertNotIn(text, content)
        self.assertIn("-n rgai-dev-y1-p0249-d4e5ddbd", content)

    def test_package_only_v1_metadata_and_py_dependencies(self):
        content = WORKFLOW.read_text()
        self.assertIn("p0249_health/function.json", content)
        self.assertIn(".python_packages/lib/site-packages", content)
        self.assertIn("zip -qr", content)
        self.assertIn("exact_one={ok}", content)


if __name__ == "__main__":
    unittest.main()
