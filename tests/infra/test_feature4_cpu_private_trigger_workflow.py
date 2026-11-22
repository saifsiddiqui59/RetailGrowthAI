"""Never allow protected F4 private-worker activation to enable customer API."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/retail-dev-feature4-cpu-trigger-once.yml"


class Feature4PrivateWorkerTriggerActivationTests(unittest.TestCase):
    def test_exact_dev_main_only_and_existing_oidc(self):
        x=WF.read_text()
        for token in (
            "branches: [main]",
            "'.github/workflows/retail-dev-feature4-cpu-trigger-once.yml'",
            "github.repository == 'saifsiddiqui59/RetailGrowthAI'",
            "github.ref == 'refs/heads/main'",
            "environment: dev",
            "id-token: write",
            "uses: azure/login@v3",
            "rg-retailgrowth-dev",
            "rgai-dev-f4cpu-d4e5ddbd",
            "rgaid4e5ddbdf0d21d96",
            "secrets.RETAIL_SUPABASE_SERVICE_ROLE_KEY",
            "scripts/deploy/feature4_cpu_rest_schema_guard.py",
        ):
            self.assertIn(token,x)
        self.assertNotIn("pull_request:",x)
        self.assertNotIn("schedule:",x)
        self.assertNotIn("az role assignment create",x)
        self.assertNotIn("--auth-mode key",x)

    def test_only_worker_privately_indexed_and_original_off(self):
        x=WF.read_text()
        for token in (
            "retail-feature4-cpu-render retail-feature4-cpu-render-poison",
            "ORIGINAL: rgai-dev-functions-d4e5ddbd",
            "str(original.get('RETAIL_FEATURE4_CPU_RENDER_ENABLED','')).lower()=='true'",
            "str(original.get('RETAIL_FEATURE4_CPU_WORKER_ENABLED','')).lower()=='true'",
            "str(settings.get('RETAIL_FEATURE4_CPU_WORKER_ENABLED','')).lower()!='false'",
            "str(settings.get('RETAIL_FEATURE4_CPU_RENDER_ENABLED','')).lower()!='false'",
            "'RETAIL_FEATURE4_CPU_WORKER_ENABLED': 'true'",
            "'RETAIL_FEATURE4_CPU_RENDER_ENABLED': 'false'",
            "feature4_cpu_render_message",
            "feature4_cpu_poison_message",
            "feature4_cpu_dispatch_timer",
            "if names!=expected",
            "trap rollback EXIT",
            "RET AIL",
        ):
            if token == "RET AIL":
                continue
            self.assertIn(token,x)
        self.assertNotIn("'RETAIL_FEATURE4_CPU_RENDER_ENABLED': 'true'",x)
        self.assertNotIn("AZURE_STORAGE_KEY",x)

    def test_failure_restores_off_and_cleans_new_secret(self):
        x=WF.read_text()
        self.assertIn("if [ \"$rc\" -ne 0 ]; then",x)
        self.assertIn("--settings RETAIL_FEATURE4_CPU_WORKER_ENABLED=false RETAIL_FEATURE4_CPU_RENDER_ENABLED=false",x)
        self.assertIn("--setting-names RETAIL_SUPABASE_SERVICE_ROLE_KEY",x)
        self.assertIn("rm -f \"$settings_file\"",x)
        self.assertIn("os.O_CREAT|os.O_EXCL|os.O_WRONLY",x)
        self.assertIn("0o600",x)


if __name__=="__main__":
    unittest.main()
