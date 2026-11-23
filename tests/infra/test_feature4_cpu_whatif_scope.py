"""ARM Ignore requires an independently inventoried exact DEV ID."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts.deploy.feature4_cpu_whatif_scope import load_existing_dev_ids, is_existing_ignore

SCOPE = "/subscriptions/11111111-1111-1111-1111-111111111111/resourcegroups/rg-retailgrowth-dev"
ID = SCOPE + "/providers/microsoft.web/staticsites/existing-web"
WORKFLOW = Path(__file__).resolve().parents[2]/".github/workflows/retail-dev-feature4-cpu-host-once.yml"


class F4IgnoreScopeTests(unittest.TestCase):
    def load(self, entries):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"ids.json"
            p.write_text(json.dumps(entries), encoding="utf-8")
            return load_existing_dev_ids(p, SCOPE)

    def test_ignore_only_for_existing_exact_id(self):
        ids=self.load([ID])
        self.assertTrue(is_existing_ignore(ID, "Ignore", ids, SCOPE))
        for act in ("Create", "Modify", "Delete", "NoChange", "Deploy"):
            self.assertFalse(is_existing_ignore(ID, act, ids, SCOPE))
        self.assertFalse(is_existing_ignore(ID+"/config/web", "Ignore", ids, SCOPE))
        self.assertFalse(is_existing_ignore(ID.replace("/resourcegroups/rg-retailgrowth-dev", "/resourcegroups/foreign"), "Ignore", ids, SCOPE))
        self.assertFalse(is_existing_ignore(ID.replace("/subscriptions/11111111", "/subscriptions/22222222"), "Ignore", ids, SCOPE))

    def test_missing_foreign_duplicate_and_invalid_inventory_fails_closed(self):
        bad=[[],[ID,ID],["unscoped"],[ID+"?private=secret"],[ID.replace("rg-retailgrowth-dev","foreign")],[ID,5],list(range(501))]
        for candidate in bad:
            with self.subTest(size=len(candidate)):
                with self.assertRaises(ValueError):
                    self.load(candidate)

    def test_workflow_preserves_safe_host_gate(self):
        x=WORKFLOW.read_text()
        for needed in (
            "environment: dev",
            "az resource list --resource-group",
            "--query '[].id' -o json",
            "inventoried=load_existing_dev_ids(",
            "if is_existing_ignore(rid, action, inventoried, scope):",
            "if rid not in allowed:",
            "if action not in ('Create','NoChange','Ignore')",
            "if allowed[0] not in created or allowed[1] not in observed or allowed[2] not in observed",
        ):
            self.assertIn(needed,x)
        self.assertLess(x.index("az resource list --resource-group"),x.index("az deployment group what-if"))
        self.assertNotIn("if action=='Ignore':\n                  continue", x)
        self.assertNotIn("az role assignment create",x)


if __name__=="__main__":
    unittest.main()
