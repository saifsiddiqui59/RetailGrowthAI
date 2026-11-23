"""Only verified exact DEV partial resources may be reused without Azure changes."""
import unittest
from scripts.deploy.feature4_cpu_whatif_scope import (
    verify_tagged_partial_plan, verify_private_existing_container, required_reuse_action,
)
from pathlib import Path
W=Path(__file__).resolve().parents[2]/".github/workflows/retail-dev-feature4-cpu-host-once.yml"
SCOPE="/subscriptions/11111111-2222-3333-4444-555555555555/resourcegroups/rg-retailgrowth-dev"
PLAN=SCOPE+"/providers/microsoft.web/serverfarms/rgai-dev-f4cpu-plan"
class F4PartialReuseTests(unittest.TestCase):
    def plan(self):
        return dict(id=PLAN,location="centralindia",sku=dict(name="FC1",tier="FlexConsumption"),
                    tags=dict(app="RetailGrowthAI",environment="dev",purpose="feature4-cpu-private-worker"))
    def test_absence_and_exact_verified_existing_plan(self):
        self.assertFalse(verify_tagged_partial_plan([],None,SCOPE))
        self.assertTrue(verify_tagged_partial_plan([dict(id=PLAN)],self.plan(),SCOPE))
        for field,wrong in (("id",PLAN.replace("rg-retailgrowth-dev","foreign")),
                            ("location","eastus"),("sku",dict(name="B1",tier="Basic")),
                            ("tags",dict(app="unknown",environment="dev",purpose="feature4-cpu-private-worker"))):
            p=self.plan()
            p[field]=wrong
            with self.subTest(field=field),self.assertRaises(ValueError):
                verify_tagged_partial_plan([dict(id=PLAN)],p,SCOPE)
        with self.assertRaises(ValueError):
            verify_tagged_partial_plan([dict(id=PLAN),dict(id=PLAN)],self.plan(),SCOPE)
        with self.assertRaises(ValueError):
            verify_tagged_partial_plan([],self.plan(),SCOPE)
    def test_private_container_only(self):
        self.assertFalse(verify_private_existing_container(dict(exists=False),None))
        self.assertTrue(verify_private_existing_container(dict(exists=True),
                            dict(name="retailgrowth-f4cpu-packages",publicAccess=None)))
        for props in (dict(name="retailgrowth-f4cpu-packages",publicAccess="Blob"),
                      dict(name="customer-media",publicAccess=None),None):
            with self.subTest(props=props),self.assertRaises(ValueError):
                verify_private_existing_container(dict(exists=True),props)
        with self.assertRaises(ValueError):
            verify_private_existing_container(dict(exists="true"),None)
    def test_whatif_action_matrix_no_mutations(self):
        for present,success in ((True,"NoChange"),(False,"Create")):
            for action in ("NoChange","Create","Modify","Delete","Ignore","Deploy",None):
                self.assertEqual(required_reuse_action(action,present),action==success)
        self.assertFalse(required_reuse_action("NoChange","true"))
    def test_guard_preserves_customer_flags_and_no_wildcards(self):
        w=W.read_text()
        for phrase in ("verify_tagged_partial_plan","verify_private_existing_container",
                       "f4cpu-partial-safe-state.json","required_reuse_action(action,previously_present)",
                       "if allowed[0] not in created or allowed[1] not in observed",
                       "RETAIL_FEATURE4_CPU_WORKER_ENABLED","RETAIL_FEATURE4_CPU_RENDER_ENABLED",
                       "if rid not in allowed:"):
            self.assertIn(phrase,w)
        self.assertNotIn("az resource delete",w)
        self.assertNotIn("az storage container delete",w)
        self.assertNotIn("az role assignment create",w)
if __name__=="__main__":
    unittest.main()
