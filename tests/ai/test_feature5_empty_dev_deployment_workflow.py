"""Fail-closed release contract for one-time empty Feature5 GPU-quota environment."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "infra/azure/feature5-empty-env-dev.json"
WORKFLOW = ROOT / ".github/workflows/retail-dev-feature5-empty-env-once.yml"


class TestFeature5EmptyEnvDeploymentPolicy(unittest.TestCase):
    def test_exact_one_environment_with_no_active_compute_or_logging(self):
        d = json.loads(TEMPLATE.read_text())
        self.assertEqual(len(d.get("resources", [])), 1)
        r = d["resources"][0]
        self.assertEqual(r, {
            "type": "Microsoft.App/managedEnvironments",
            "apiVersion": "2024-03-01",
            "name": "rgai-f5-gpu-canary-eastus",
            "location": "eastus",
            "tags": {
                "app": "RetailGrowthAI", "environment": "dev",
                "feature": "feature5", "purpose": "zero-compute-gpu-quota-probe",
            },
            "properties": {
                "appLogsConfiguration": {},
                "workloadProfiles": [{"name": "Consumption", "workloadProfileType": "Consumption"}],
            },
        })
        self.assertNotIn("parameters", d)
        self.assertNotIn("Microsoft.Compute", json.dumps(d))

    def test_workflow_main_only_once_without_manual_dispatch(self):
        w = WORKFLOW.read_text()
        self.assertIn("branches: [main]", w)
        self.assertIn("github.ref == 'refs/heads/main'", w)
        self.assertIn("environment: dev", w)
        self.assertIn("id-token: write", w)
        self.assertNotIn("workflow_dispatch:", w)
        self.assertNotIn("schedule:", w)
        self.assertIn("retail-dev-feature5-empty-env-once.yml", w)
        self.assertIn("azure/login@v3", w)
        self.assertIn("--template-file \"$TEMPLATE\"", w)

    def test_only_single_azure_create_command_and_strict_what_if(self):
        w = WORKFLOW.read_text()
        actual = re.findall(r"^\s*az\s+deployment\s+group\s+create\b", w, re.M)
        self.assertEqual(len(actual), 1)
        self.assertIn("what-if", w)
        self.assertIn("from scripts.ci.feature5_arm_whatif_policy import validate_what_if", w)
        self.assertIn("result=validate_what_if(data,sys.argv[2],sys.argv[3],sys.argv[4])", w)
        self.assertIn("rgai-f5-empty-env-20261026", w)
        for phrase in ("az containerapp job create", "az containerapp create", "az containerapp env create",
                       "az role assignment create", "az provider register", "az deployment group delete",
                       "az vm create", "az acr create"):
            self.assertNotIn(phrase, w)


if __name__ == "__main__":
    unittest.main()
