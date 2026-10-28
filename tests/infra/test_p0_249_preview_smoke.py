"""Offline checks for a read-only, bounded HTTP observation of the Node preview."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMOKE = ROOT / ".github/workflows/p0-dev-node-preview-readonly-smoke-once.yml"
DEPLOY = ROOT / ".github/workflows/p0-dev-free-swa-node-preview-once.yml"


class NodePreviewSmokePolicy(unittest.TestCase):
    def test_exact_hostname_from_actual_azure_publish(self):
        host = "purple-dune-06b5da200-p0249node.eastasia.2.azurestaticapps.net"
        self.assertIn(host, SMOKE.read_text())
        self.assertIn('p.hostname=="' + host + '"', DEPLOY.read_text())

    def test_read_only_and_no_azure_upload_or_customer_identifiers(self):
        text = SMOKE.read_text()
        self.assertIn("P0_249_FREE_NODE_PREVIEW_READONLY_HTTP_ACCEPTANCE=PASSED", text)
        self.assertIn("github.ref == 'refs/heads/main'", text)
        self.assertIn("environment: dev", text)
        self.assertIn("rg-retailgrowth-dev", text)
        self.assertIn('defaultHostname', text)
        self.assertIn('lower()=="free"', text)
        self.assertIn("id-token: write", text)
        self.assertIn("--max-time 15", text)
        self.assertIn("x-p0-control: node-v4", text)
        self.assertIn("'p0-health-lite:200'", text)
        self.assertIn("'p0-249-missing:404'", text)
        self.assertNotIn("azure_static_web_apps_api_token", text)
        self.assertNotIn("action: upload", text)
        self.assertNotIn("deployment_environment:", text)
        self.assertNotIn("curl -X POST", text)
        self.assertNotIn("service_role", text)
        self.assertNotIn("createClient", text)

if __name__ == "__main__":
    unittest.main()
