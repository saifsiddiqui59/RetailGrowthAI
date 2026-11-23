"""Exact verified partial-Flex recovery creates only a new disabled worker app."""
from pathlib import Path
import unittest
P=Path(__file__).resolve().parents[2]
B=P/"infra/azure/feature4-cpu-worker-dev-resume.bicep"
W=P/".github/workflows/retail-dev-feature4-cpu-resume-once.yml"

class F4PartialResumeTests(unittest.TestCase):
    def test_plan_and_container_existing_only(self):
        x=B.read_text()
        self.assertIn("resource workerPlan 'Microsoft.Web/serverfarms@2024-04-01' existing",x)
        self.assertIn("resource privatePackages 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' existing",x)
        self.assertIn("resource workerApp 'Microsoft.Web/sites@2024-11-01' = {",x)
        self.assertNotIn("FUNCTIONS_WORKER_RUNTIME', value:",x)
        self.assertNotIn("FUNCTIONS_EXTENSION_VERSION', value:",x)
        self.assertNotIn("ftpsState:",x)
        self.assertIn("name: 'python'",x)
        self.assertIn("version: '3.11'",x)
        self.assertIn("maximumInstanceCount: 1",x)
        self.assertIn("instanceMemoryMB: 2048",x)
        self.assertIn("RETAIL_FEATURE4_CPU_WORKER_ENABLED', value: 'false'",x)
        self.assertIn("RETAIL_FEATURE4_CPU_RENDER_ENABLED', value: 'false'",x)

    def test_readonly_proofs_and_strict_whatif_precede_any_create(self):
        x=W.read_text()
        for key in ("environment: dev","branches: [main]",
                    "F4 worker app already exists","existing FC1 plan identity unverified",
                    "existing package container privacy unverified",
                    "az storage container show","--auth-mode login",
                    "az resource list --resource-group",
                    "if is_existing_ignore(rid, action, inventoried, scope):",
                    "if action not in ('NoChange','Ignore')",
                    "if allowed[0] not in created:",
                    "feature4-cpu-worker-dev-resume.bicep",
                    "rgai-f4cpu-private-worker-resume"):
            self.assertIn(key,x)
        self.assertLess(x.index("Verify absent site and exact existing FC1"),
                        x.index("az deployment group what-if"))
        self.assertLess(x.index("az deployment group what-if"),x.index("az deployment group create"))
        self.assertNotIn("az storage container create",x)
        self.assertNotIn("az role assignment create",x)
        self.assertNotIn("az functionapp config appsettings set",x)

if __name__=="__main__":
    unittest.main()
