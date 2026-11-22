"""Contract tests for inert, isolated Feature4 CPU Flex DEV infrastructure."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "infra" / "azure" / "feature4-cpu-worker-dev.bicep"


class Feature4HostSourceSafetyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf8")

    def test_fixed_approved_dev_target_only(self):
        s = self.source
        self.assertIn("@allowed(['centralindia'])", s)
        self.assertIn("@allowed(['dev'])", s)
        self.assertIn("@allowed(['rgaid4e5ddbdf0d21d96'])", s)
        self.assertIn("@allowed(['rgai-dev-f4cpu-d4e5ddbd'])", s)
        self.assertIn("@allowed(['rgai-dev-f4cpu-plan'])", s)
        self.assertIn("resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing", s)

    def test_isolated_scale_to_zero_cpu_no_gpu_or_other_app(self):
        s = self.source
        self.assertIn("tier: 'FlexConsumption'", s)
        self.assertIn("maximumInstanceCount: 1", s)
        self.assertIn("instanceMemoryMB: 2048", s)
        self.assertNotIn("alwaysReady:", s)
        self.assertNotIn("rgai-dev-functions-d4e5ddbd", s)
        self.assertNotIn("rgai-dev-y1-p0249", s)
        self.assertNotIn("A100", s)
        self.assertNotIn("WineShopPOS", s.split("resource workerPlan")[1])

    def test_no_public_worker_http_or_credential_leak(self):
        s = self.source
        self.assertIn("publicAccess: 'None'", s)
        self.assertIn("retailgrowth-f4cpu-packages", s)
        self.assertIn("functionapp,linux", s)
        self.assertIn("version: '3.11'", s)
        self.assertIn("{ name: 'RETAIL_FEATURE4_CPU_WORKER_ENABLED', value: 'false' }", s)
        self.assertIn("{ name: 'RETAIL_FEATURE4_CPU_RENDER_ENABLED', value: 'false' }", s)
        self.assertNotIn("RETAIL_SUPABASE_SERVICE_ROLE_KEY", s)
        self.assertNotIn("RETAIL_SUPABASE_URL', value", s)
        self.assertNotIn("WEBSITE_RUN_FROM_PACKAGE", s)
        self.assertNotIn("AzureWebJobs.feature4", s)


if __name__ == "__main__":
    unittest.main()
