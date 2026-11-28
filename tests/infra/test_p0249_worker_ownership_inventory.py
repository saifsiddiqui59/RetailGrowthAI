"""No-network regressions: worker flags are not queue drain proof."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops/p0249-y1-cutover"))
import inspect_worker_ownership as m

class WorkerInventoryTests(unittest.TestCase):
    def test_worker_setting_classifications(self):
        w = "render_campaign_reel"
        key = "AzureWebJobs." + w + ".Disabled"
        self.assertEqual(m.classify({w}, {}, w), "INDEXED_POTENTIAL_CONSUMER")
        self.assertEqual(m.classify({w}, {key: "true"}, w), "INDEXED_DISABLED_SETTING")
        self.assertEqual(m.classify(set(), {key: "false"}, w), "NOT_INDEXED")
        self.assertEqual(m.classify({w}, {key: "secret"}, w), "INVALID_FLAG")
        self.assertEqual(m.classify({w}, {key: "true", key.lower(): "false"}, w), "AMBIGUOUS")
    def test_nine_exact_workers(self):
        self.assertEqual(len(m.WORKERS), 9)
    def test_wrong_scope_never_reads(self):
        with self.assertRaisesRegex(RuntimeError, "SCOPE"):
            m.inventory(env={}, reader=lambda *_: self.fail("unexpected Azure read"))
    def test_exact_scope_inventory_is_never_handoff_permission(self):
        sub = "synthetic"
        def read(*args):
            if args == ("account", "show"): return {"id": sub}
            if args[:2] == ("group", "show"):
                return {"name": m.RG, "location": "centralindia", "tags": {"app":"RetailGrowthAI","environment":"dev"}}
            app = args[args.index("-n")+1]
            if args[:2] == ("resource", "show"):
                return {"name":app,"id":"/subscriptions/"+sub+"/resourceGroups/"+m.RG+"/providers/Microsoft.Web/sites/"+app,"properties":{"state":"Running"}}
            if args[:3] == ("functionapp","function","list"):
                names = m.ALL_HTTP_FUNCTIONS if app == m.Y1 else m.WORKERS
                return [{"name":app+"/"+n} for n in names]
            if args[:3] == ("functionapp","config","appsettings"):
                return [{"name":"RETAIL_STORAGE","value":"PRIVATE_SYNTHETIC"}]
            self.fail("unapproved command")
        env={"GITHUB_ACTIONS":"true","GITHUB_REPOSITORY":"saifsiddiqui59/RetailGrowthAI","GITHUB_REF":"refs/heads/main","AZURE_SUBSCRIPTION_ID":sub}
        result=m.inventory(env,read)
        self.assertTrue(result["y1_exact_http_only"])
        self.assertFalse(result["handoff_authorized"])
        self.assertFalse(result["drain_proven"])
        self.assertFalse(result["duplicate_potential_consumers"])
        self.assertNotIn("PRIVATE_SYNTHETIC", str(result))
