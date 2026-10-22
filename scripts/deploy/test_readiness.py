"""Offline Azure Functions DEV resource and approval invariants; no cloud access."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]


class FlexReadinessTests(unittest.TestCase):
    def test_python_v2_runtime_region_and_cost_limits(self):
        bicep = (ROOT / "infra/azure/main.bicep").read_text()
        for setting in (
            "runtime: { name: 'python', version: '3.12' }",
            "instanceMemoryMB: instanceMemoryMB",
            "maximumInstanceCount: maxInstances", "tier: 'FlexConsumption'",
            "@allowed(['centralindia'])",
            "allowBlobPublicAccess: false", "supportsHttpsTrafficOnly: true",
        ):
            self.assertIn(setting, bicep)
        self.assertIn("@allowed([1, 2])\nparam maxInstances int = 1", bicep)
        self.assertIn("@allowed([2048])\nparam instanceMemoryMB int = 2048", bicep)
        self.assertNotIn("FUNCTIONS_WORKER_RUNTIME", bicep)
        self.assertNotIn("FUNCTIONS_EXTENSION_VERSION", bicep)
        self.assertNotIn("alwaysReady", bicep)
        self.assertNotIn("WEBSITE_RUN_FROM_PACKAGE", bicep)

    def test_example_only_dev_placeholders(self):
        data = json.loads((ROOT / "infra/azure/dev.parameters.example.json").read_text())
        values = {key: entry["value"] for key, entry in data["parameters"].items()}
        self.assertEqual(values["environmentName"], "dev")
        self.assertEqual(values["location"], "centralindia")
        self.assertTrue(values["frontendOrigin"].startswith("https://"))
        self.assertNotIn("secret", str(values).lower())
        self.assertNotIn("password", str(values).lower())

    def test_deployment_scripts_require_approval_and_verified_zip(self):
        for name in ("apply-infra.sh", "deploy-code.sh"):
            script = (ROOT / "scripts/deploy" / name).read_text()
            self.assertIn("RETAIL_AZURE_DEPLOY_APPROVED=YES", script)
            self.assertIn('"$RETAIL_AZURE_SUBSCRIPTION_ID"', script)
            self.assertIn('case "$RETAIL_AZURE_DEV_RG"', script)
            self.assertIn('if [ "$#" -ne 2 ]', script)
        code = (ROOT / "scripts/deploy/deploy-code.sh").read_text()
        self.assertIn("--verify-zip", code)
        self.assertIn("--build-remote true", code)


if __name__ == "__main__":
    unittest.main()
