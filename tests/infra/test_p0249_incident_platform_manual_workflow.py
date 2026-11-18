"""Offline guardrails for #249 manual-only incident Azure workflow.

No Azure credentials, network, workflow dispatch or cloud operations.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/p0-249-incident-platform-readonly-manual.yml"


class P0249IncidentManualWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = WORKFLOW.read_text(encoding="utf-8")

    def test_strict_manual_trigger_only(self):
        self.assertIn("on:\n  workflow_dispatch:", self.content)
        for forbidden in ("push", "schedule", "pull_request", "workflow_run", "repository_dispatch"):
            with self.subTest(trigger=forbidden):
                self.assertIsNone(re.search(
                    r"(?m)^  " + re.escape(forbidden) + r":", self.content
                ))

    def test_exact_main_dev_and_short_timeout(self):
        self.assertIn("github.repository == 'saifsiddiqui59/RetailGrowthAI'", self.content)
        self.assertIn("github.ref == 'refs/heads/main'", self.content)
        self.assertIn("environment: dev", self.content)
        self.assertIn("timeout-minutes: 20", self.content)
        self.assertIn("cancel-in-progress: false", self.content)

    def test_oidc_permission_is_one_scoped_job_only(self):
        self.assertIn("permissions:\n  contents: read", self.content)
        self.assertEqual(self.content.count("id-token: write"), 1)
        self.assertIn("persist-credentials: false", self.content)
        self.assertIn("RGAI_DEV_EXPECTED_SUBSCRIPTION: ${{ secrets.AZURE_SUBSCRIPTION_ID }}", self.content)
        self.assertIn("azure/login@v3", self.content)
        self.assertIn("az logout", self.content)

    def test_original_collector_only_and_no_cloud_mutations(self):
        self.assertIn("p0_249_recent_http_platform_readonly.py", self.content)
        self.assertIn("P0249_IMMUTABLE_INCIDENT_SCOPE=PASS", self.content)
        for forbidden in (
            "az functionapp create", "az group create", "az resource create",
            "az functionapp config set", "az deployment group create",
            "az webapp deploy", "az storage blob upload",
            "curl -X POST", "curl --request POST", "wget ",
        ):
            with self.subTest(command=forbidden):
                self.assertNotIn(forbidden, self.content)


if __name__ == "__main__":
    unittest.main()
