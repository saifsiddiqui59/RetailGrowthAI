"""Coordinator guard: Feature5 DEV Azure OIDC diagnostic must remain read-only.

This test checks the installed workflow source, rather than trying to
authenticate to or mutate Azure in the Python/uv CI job.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / ".github/workflows/retail-dev-feature5-azure-reconcile.yml"


class Feature5AzureReconcileWorkflowSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contents = PATH.read_text(encoding="utf-8")

    def test_scoped_main_and_manual_dispatch(self):
        w = self.contents
        self.assertIn("workflow_dispatch:", w)
        self.assertIn("branches: [main]", w)
        self.assertIn("paths:", w)
        self.assertIn("retail-dev-feature5-azure-reconcile.yml", w)
        self.assertIn("github.ref == 'refs/heads/main'", w)
        self.assertIn("environment: dev", w)

    def test_oidc_limited_permission_existing_dev_secret_names(self):
        w = self.contents
        self.assertIn("uses: azure/login@v3", w)
        self.assertIn("id-token: write", w)
        self.assertIn("contents: read", w)
        for secret in ("AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION_ID"):
            self.assertIn("secrets." + secret, w)
        self.assertNotIn("client-secret:", w)

    def test_no_azure_write_commands(self):
        w = self.contents
        # Extract actual shell commands, not prose or printed headings.
        bad = re.compile(
            r"^\s*az\s+(?:group|resource|deployment|containerapp|provider|role|vm|acr|account)\s+"
            r".*\b(create|delete|update|register|assign|start|apply|deploy|set)\b",
            re.MULTILINE,
        )
        self.assertIsNone(bad.search(w), "Azure write operation found")
        self.assertNotIn("az rest --method POST", w)
        self.assertNotIn("az rest --method PUT", w)
        self.assertNotIn("az rest --method DELETE", w)
        self.assertNotIn("az deployment group create", w)

    def test_exact_scope_and_original_deployment(self):
        w = self.contents
        for value in ("rg-retailgrowth-dev", "rgai-f5-gpu-canary-eastus",
                      "CustomDeployment-20261026093554",
                      "Microsoft.App/managedEnvironments"):
            self.assertIn(value, w)
        self.assertIn("tags.environment", w)
        self.assertIn("tags.app", w)
        self.assertIn("quota UNKNOWN", w)


if __name__ == "__main__":
    unittest.main()
