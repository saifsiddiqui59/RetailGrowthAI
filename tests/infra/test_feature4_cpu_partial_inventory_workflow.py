"""Protected DEV host inventory after partial Azure deployment is read-only."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/retail-dev-feature4-cpu-inventory-once.yml"
class F4PartialInventoryWorkflowTests(unittest.TestCase):
    def test_protected_read_only_exact_scope(self):
        w=WF.read_text()
        for term in ("branches: [main]","environment: dev","id-token: write",
                     "github.repository == 'saifsiddiqui59/RetailGrowthAI'",
                     "RG: rg-retailgrowth-dev","STORAGE: rgaid4e5ddbdf0d21d96",
                     "APP: rgai-dev-f4cpu-d4e5ddbd","PLAN: rgai-dev-f4cpu-plan",
                     "CONTAINER: retailgrowth-f4cpu-packages",
                     "az resource list -g","az storage container exists",
                     "az resource show -g","az functionapp config appsettings list",
                     "sku.get('name')!='FC1'","runtime.get('name')!='python'",
                     "RETAIL_FEATURE4_CPU_WORKER_ENABLED","GITHUB_STEP_SUMMARY"):
            self.assertIn(term,w)
        for forbidden in ("az deployment group create","az resource create","az resource delete",
                          "az role assignment create","az functionapp config appsettings set",
                          "az storage queue create","az storage container create",
                          "az functionapp deploy","--auth-mode key"):
            self.assertNotIn(forbidden,w)
        self.assertNotIn("workflow_dispatch:",w)
        self.assertNotIn("schedule:",w)
        self.assertLess(w.index("Validate exact DEV RG"),w.index("Inventory target worker app"))
    def test_no_secret_or_resource_id_reporting(self):
        w=WF.read_text()
        self.assertIn("Read-only DEV F4 target inventory",w)
        self.assertIn("no changes made",w)
        self.assertIn("DEV F4 plan invariant booleans:",w)
        self.assertIn("DEV F4 container access metadata:",w)
        self.assertIn("str(v).lower() for k,v in sorted(bits.items())",w)
        self.assertNotIn("print(settings)",w)
        self.assertNotIn("print(app)",w)
        self.assertNotIn("print(plan)",w)
        self.assertNotIn("print(scope)",w)
        self.assertNotIn("echo $AZURE_SUBSCRIPTION_ID",w)
if __name__=="__main__":
    unittest.main()
