"""Offline policy assertions: synthetic Node preview cannot replace live backend."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/p0-dev-free-swa-node-preview-once.yml"
NODE = ROOT / "experiments/wineshop-node-http-control/src/routes.mjs"

class SafePreviewPolicy(unittest.TestCase):
    def test_named_preview_is_mandatory_and_bounded(self):
        w = WORKFLOW.read_text()
        self.assertIn("deployment_environment: p0249node", w)
        self.assertIn("grep -iq '^x-p0-control: node-v4'", w)
        self.assertIn("production_branch: main", w)
        self.assertIn("app_location: experiments/wineshop-node-http-control/site", w)
        self.assertIn("skip_app_build: true", w)
        self.assertIn("p0-249-missing", (ROOT / "experiments/wineshop-node-http-control/src/index.mjs").read_text())
        self.assertIn("api_location: experiments/wineshop-node-http-control", w)
        self.assertIn("startsWith(github.event.head_commit.message", w)
        self.assertIn("github.ref == 'refs/heads/main'", w)
        self.assertIn("environment: dev", w)
        self.assertIn("retailgrowthai-dev-preview", w)
        self.assertIn("purple-dune-06b5da200.2.azurestaticapps.net", w)
        self.assertIn('"free"', w)
        self.assertNotIn("az functionapp create", w)
        self.assertNotIn("az functionapp scale", w)
        self.assertNotIn("az group create", w)
        self.assertNotIn("service_role", NODE.read_text().lower())

    def test_no_real_tenant_or_mutation_in_node_control(self):
        node=NODE.read_text()
        self.assertIn('status:401',node)
        self.assertIn('status:503',node)
        self.assertIn('status:404',node)
        self.assertNotIn('Supabase',node)
        self.assertNotIn('send_message',node)

if __name__ == "__main__":
    unittest.main()
