"""Guard exact F4 DEV original API review staging; no hosted mutation in tests."""
from copy import deepcopy
from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts/deploy/feature4_cpu_original_api_readiness.py"
WF = ROOT / ".github/workflows/retail-dev-feature4-api-review-once.yml"
spec = importlib.util.spec_from_file_location("f4_original_api_guard", MODULE)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
SUB = "11111111-2222-3333-4444-555555555555"
SECRET = "sb_secret_" + "x"*40


def fixture():
    def site(name, purpose=None):
        tags = {"app": "retailgrowthai", "environment": "dev"}
        if purpose:
            tags["purpose"] = purpose
        data = {"id": f"/subscriptions/{SUB}/resourceGroups/{guard.DEV_RG}/providers/Microsoft.Web/sites/{name}",
                "name": name, "tags": tags, "properties": {}}
        if purpose:
            data["properties"]["functionAppConfig"] = {
                "runtime": {"name": "python", "version": "3.11"},
                "scaleAndConcurrency": {"maximumInstanceCount": 1, "instanceMemoryMB": 2048}}
        return data

    common = [
        {"name": "RETAIL_SUPABASE_URL", "value": guard.DEV_URL},
        {"name": "RETAIL_SUPABASE_SERVICE_ROLE_KEY", "value": SECRET},
        {"name": "RETAIL_STORAGE", "value": "same-private-dev-storage"},
        {"name": "AzureWebJobsStorage", "value": "separate-app-storage"},
    ]
    return {
        "worker_app": site(guard.WORKER, "feature4-cpu-private-worker"),
        "api_app": site(guard.API),
        "worker_settings": deepcopy(common) + [
            {"name": "RETAIL_FEATURE4_CPU_WORKER_ENABLED", "value": "true"},
            {"name": "RETAIL_FEATURE4_CPU_RENDER_ENABLED", "value": "false"}],
        "api_settings": common + [
            {"name": "RETAIL_SUPABASE_PUBLISHABLE_KEY", "value": "sb_publishable_test"},
            *({"name": name, "value": "false"} for name in guard.API_FLAGS)],
        "worker_functions": [{"name": guard.WORKER+"/"+f}
                             for f in sorted(guard.WORKER_FUNCTIONS)],
        "api_functions": [{"name": guard.API+"/"+f} for f in sorted(guard.API_FUNCTIONS)] +
                         [{"name": guard.API+"/existing_v1_http"}],
        "queue_render": {"exists": True},
        "queue_poison": {"exists": True},
        "f4_jobs_empty": True,
    }


class OriginalApiReadiness(unittest.TestCase):
    def test_valid_readonly_stage(self):
        self.assertTrue(guard.verify(fixture(), SUB, SECRET))

    def test_reject_foreign_identity_flags_and_unproved_packages(self):
        changes = [
            lambda x: x["api_app"].update(id="wrong"),
            lambda x: x["worker_app"]["tags"].update(environment="prod"),
            lambda x: x["worker_app"]["properties"]["functionAppConfig"]["scaleAndConcurrency"].update(maximumInstanceCount=2),
            lambda x: x["worker_settings"].append({"name":"RETAIL_FEATURE4_CPU_WORKER_ENABLED","value":"true"}),
            lambda x: next(a for a in x["worker_settings"] if a["name"]=="RETAIL_STORAGE").update(value="foreign"),
            lambda x: next(a for a in x["api_settings"] if a["name"]=="RETAIL_SUPABASE_URL").update(value="https://not-dev.supabase.co"),
            lambda x: next(a for a in x["api_settings"] if a["name"]=="RETAIL_FEATURE4_CPU_RENDER_ENABLED").update(value="true"),
            lambda x: next(a for a in x["api_settings"] if a["name"]=="RETAIL_FEATURE4_PLAN_REVIEW_ENABLED").update(value="true"),
            lambda x: next(a for a in x["worker_settings"] if a["name"]=="RETAIL_FEATURE4_CPU_WORKER_ENABLED").update(value="false"),
            lambda x: next(a for a in x["worker_settings"] if a["name"]=="RETAIL_SUPABASE_SERVICE_ROLE_KEY").update(value="sb_secret_wrong"),
            lambda x: x["worker_functions"].pop(),
            lambda x: x["api_functions"].pop(0),
            lambda x: x["queue_render"].update(exists=False),
            lambda x: x.update(f4_jobs_empty=False),
            lambda x: x.update(api_functions=[{"name":"foreign"}]),
        ]
        for change in changes:
            with self.subTest(change=str(change)):
                x=fixture()
                change(x)
                with self.assertRaises(guard.NotReady):
                    guard.verify(x, SUB, SECRET)

    def test_reject_untrusted_service_identity_and_bad_input(self):
        for wrong in ("", "sb_secret_short", "fake-dev-secret", "eyJ.abc"):
            with self.subTest(wrong=wrong):
                with self.assertRaises(guard.NotReady):
                    guard.verify(fixture(), SUB, wrong)
        with self.assertRaises(guard.NotReady):
            guard.verify({}, SUB, SECRET)
        with self.assertRaises(guard.NotReady):
            guard.verify(fixture(), "invalid-sub", SECRET)

    def test_protected_review_only_workflow_retains_real_hosted_gates(self):
        w=WF.read_text(encoding="utf-8")
        self.assertIn("environment: dev", w)
        self.assertIn("if: github.repository == 'saifsiddiqui59/RetailGrowthAI'",w)
        self.assertIn("id-token: write",w)
        self.assertIn("feature4_cpu_rest_schema_guard.py",w)
        self.assertIn("feature4_cpu_original_api_readiness.py",w)
        self.assertIn("az functionapp function list -g",w)
        self.assertIn("az storage queue exists --name retail-feature4-cpu-render",w)
        self.assertIn("trap restore EXIT",w)
        self.assertIn("RETAIL_FEATURE4_PLAN_ISSUE_ENABLED=true",w)
        self.assertIn("RETAIL_FEATURE4_PLAN_REVIEW_ENABLED=true",w)
        self.assertIn("RETAIL_FEATURE4_CPU_WORKER_ENABLED=true",w)
        self.assertIn("RETAIL_FEATURE4_CPU_RENDER_ENABLED=false",w)
        self.assertNotIn("RETAIL_FEATURE4_CPU_RENDER_ENABLED=true",w)
        self.assertNotIn("az functionapp restart",w)
        self.assertNotIn("az role assignment create",w)
        self.assertLess(w.index("feature4_cpu_original_api_readiness.py"),
                        w.index("Activate ONLY original API plan issue/review"))
        self.assertNotIn("pull_request_target",w)


if __name__ == "__main__":
    unittest.main()
