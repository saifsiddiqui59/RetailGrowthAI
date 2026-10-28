"""Guard Azure Feature5 alternative VM GPU inventory against paid cloud actions."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/retail-dev-feature5-gpu-vm-inventory.yml"


class TestFeature5AlternativeGpuInventory(unittest.TestCase):
    def test_only_existing_dev_oidc_and_main_ref(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("uses: azure/login@v3", source)
        self.assertIn("environment: dev", source)
        self.assertIn("github.ref == 'refs/heads/main'", source)
        self.assertIn("AZURE_SUBSCRIPTION_ID", source)
        self.assertIn("AZURE_CLIENT_ID", source)
        self.assertIn("AZURE_TENANT_ID", source)
        self.assertIn("rg-retailgrowth-dev", source)
        self.assertIn("centralindia eastus", source)

    def test_no_cloud_vm_or_quota_mutations(self):
        source = WORKFLOW.read_text()
        self.assertIn("az vm list-usage", source)
        self.assertIn("az vm list-skus", source)
        self.assertNotIn("az vm create", source)
        self.assertNotIn("az vm deallocate", source)
        self.assertNotIn("az vm start", source)
        self.assertNotIn("az provider register", source)
        self.assertNotIn("az deployment group create", source)
        self.assertNotIn("az quota", source)
        self.assertNotIn("az role assignment create", source)
        self.assertNotIn("az rest --method", source)
        self.assertNotIn("client-secret:", source)
        # Read-only calls occur in guarded "if az ..." branches, not
        # necessarily at the beginning of a shell line.
        self.assertRegex(source, r"\baz vm list-usage\b")
        self.assertRegex(source, r"\baz vm list-skus\b")


if __name__ == "__main__":
    unittest.main()
