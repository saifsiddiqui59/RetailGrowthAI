"""Ensure F4 CPU Functions host provisioning stays disabled and DEV scoped."""
from pathlib import Path
import unittest

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/retail-dev-feature4-cpu-host-once.yml"


class Feature4CpuHostOneShotTests(unittest.TestCase):
    def test_protected_main_only_one_shot(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for expected in (
            "branches: [main]",
            "'.github/workflows/retail-dev-feature4-cpu-host-once.yml'",
            "github.repository == 'saifsiddiqui59/RetailGrowthAI'",
            "github.ref == 'refs/heads/main'",
            "environment: dev",
            "id-token: write",
            "cancel-in-progress: false",
            "persist-credentials: false",
            "secrets.AZURE_SUBSCRIPTION_ID",
            "uses: azure/login@v3",
        ):
            self.assertIn(expected, text)
        for forbidden in ("pull_request:", "schedule:", "az role assignment create"):
            self.assertNotIn(forbidden, text)

    def test_exact_worker_identity_queue_preflight_and_disabled_flags(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for expected in (
            "rg-retailgrowth-dev",
            "rgaid4e5ddbdf0d21d96",
            "rgai-dev-f4cpu-d4e5ddbd",
            "rgai-dev-f4cpu-plan",
            "retailgrowth-f4cpu-packages",
            "retail-feature4-cpu-render retail-feature4-cpu-render-poison",
            "--auth-mode login",
            "az bicep build",
            "az deployment group what-if",
            "az deployment group create",
            "if action not in ('NoChange','Ignore')",
            "if action not in ('Create','NoChange','Ignore')",
            "scale.get('maximumInstanceCount') != 1",
            "scale.get('instanceMemoryMB') != 2048",
            "str(flags.get('RETAIL_FEATURE4_CPU_WORKER_ENABLED','')).lower()!='false'",
            "str(flags.get('RETAIL_FEATURE4_CPU_RENDER_ENABLED','')).lower()!='false'",
        ):
            self.assertIn(expected, text)
        for forbidden in (
            "az storage queue create", "az storage queue delete",
            "az functionapp config appsettings set", "--auth-mode key",
            "RETAIL_FEATURE4_CPU_WORKER_ENABLED=true",
            "RETAIL_FEATURE4_CPU_RENDER_ENABLED=true",
            "RETAIL_SUPABASE_SERVICE_ROLE_KEY: ",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
