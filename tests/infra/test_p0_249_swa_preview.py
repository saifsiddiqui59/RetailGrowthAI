"""Offline safety and deployment isolation gates for P0 #249 Free SWA preview.

Must pass pytest AND Python unittest discovery. Nothing touches Azure.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "experiments/wineshop-node-http-control"
WORKFLOW = ROOT / ".github/workflows/p0-dev-free-swa-node-preview-once.yml"


class FreeSwaPreviewSafety(unittest.TestCase):
    def test_managed_node_runtime_and_static_control_only(self):
        config = json.loads((CONTROL / "site/staticwebapp.config.json").read_text())
        self.assertEqual(config["platform"]["apiRuntime"], "node:22")
        self.assertIn("noindex", config["globalHeaders"]["X-Robots-Tag"])
        page = (CONTROL / "site/index.html").read_text()
        self.assertIn("Not a customer application", page)
        self.assertNotIn("<script", page.lower())
        package = json.loads((CONTROL / "package.json").read_text())
        self.assertEqual(package["main"], "src/index.mjs")
        self.assertEqual(list(package["dependencies"]), ["@azure/functions"])

    def test_no_privileged_or_mutating_node_api(self):
        index = (CONTROL / "src/index.mjs").read_text()
        routes = (CONTROL / "src/routes.mjs").read_text()
        self.assertEqual(index.count("app.http("), 4)
        self.assertIn('route: "p0-health-lite"', index)
        self.assertIn('route: "campaigns/{campaignId}"', index)
        self.assertIn('route: "p0-249-missing"', index)
        self.assertIn('route: "p0-jwt-transport-lite"', index)
        self.assertIn('syntheticJwtTransport', index)
        self.assertIn('SYNTHETIC_HEADER_MISSING', routes)
        self.assertIn('CUSTOM_HEADER_DELIVERED_SYNTHETIC_ONLY', routes)
        self.assertNotIn('req.headers.get("authorization")', index)
        self.assertIn('"X-P0-Control": "node-v4"', index)
        self.assertNotIn('req.headers.get("authorization")', index)
        self.assertRegex(index, r'methods:\s*\["GET"\]')
        self.assertNotRegex(index, r'methods:\s*\["(?:POST|PUT|PATCH|DELETE)"\]')
        for source in (index, routes):
            self.assertNotRegex(source, r"(?i)service_role|sb_secret_|azure.*key|queueclient|createclient|cookie")
        self.assertIn("CONTROL_NO_TENANT_IMPLEMENTATION", routes)

    def test_named_preview_deployment_never_replaces_production(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("deployment_environment: p0249node", workflow)
        self.assertIn("production_branch: main", workflow)
        self.assertIn("skip_app_build: true", workflow)
        self.assertIn("app_location: experiments/wineshop-node-http-control/site", workflow)
        self.assertIn("api_location: experiments/wineshop-node-http-control", workflow)
        self.assertNotIn("app_location: frontend\n", workflow)
        self.assertIn("environment: dev", workflow)
        self.assertIn("rg-retailgrowth-dev", workflow)
        self.assertIn("retailgrowthai-dev-preview", workflow)
        self.assertIn("purple-dune-06b5da200.2.azurestaticapps.net", workflow)
        self.assertIn("purple-dune-06b5da200-p0249node.eastasia.2.azurestaticapps.net", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertNotIn("repo_token:", workflow)
        self.assertNotIn("api_location: ''", workflow)

    def test_credentialed_job_cannot_activate_outside_release_gate(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("startsWith(github.event.head_commit.message, 'experiment(dev): RetailGrowthAI P0 249 Free SWA Node preview')", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertNotIn("az functionapp deployment", workflow)
        self.assertNotIn("az staticwebapp create", workflow)
        self.assertNotIn("az group create", workflow)
        self.assertNotIn("alwaysReady", workflow)
        self.assertIn("P0_249_NODE_FREE_PREVIEW_ACCEPTED=true", workflow)

if __name__ == "__main__":
    unittest.main()
