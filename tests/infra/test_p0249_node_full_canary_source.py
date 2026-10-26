"""Offline gating: Node cloud E2E does not bypass ROOT, tenants or mutate PROD."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
E2E=ROOT/"tests/e2e/p0249_dev_node_full_canary_once.py"
ORIGINAL=ROOT/"tests/e2e/retail_dev_canary_once.py"
WORKFLOW=ROOT/".github/workflows/retail-dev-test-accounts-canary-once.yml"

class NodeFullCanarySafety(unittest.TestCase):
    def test_manual_root_approval_and_exact_node_target(self):
        src=E2E.read_text()
        original=ORIGINAL.read_text()
        self.assertIn("p0249writes.eastasia.2.azurestaticapps.net",src)
        self.assertIn('RGAI_DEV_CANARY_APPROVAL',src)
        self.assertIn('AUTHORIZED_RETAILGROWTHAI_DEV_ONLY',src)
        self.assertIn("ALLOWED_MODES = {\"node-poster-reel\",\"node-browser-reel\"}",src)
        self.assertIn('canary.main()',src)
        self.assertIn('canary.preflight_dev_http_auth_routes=node_preflight',src)
        self.assertIn('P0249_REAL_NODE_WRITE_API_PREFLIGHT_PASSED=true',src)
        self.assertIn('P0249_REAL_NODE_HTTP_TRANSACTION_UNCONFIRMED',src)
        self.assertIn('x-rgai-supabase-jwt',src)
        self.assertIn('canary.API=NODE_PREVIEW',src)
        self.assertNotIn('sb_secret_',src)
        self.assertNotIn('https://wineshop',src.lower())
        # Original canary unchanged and still demands real ROOT approval.
        self.assertIn('CANARY_WAITING_FOR_EXPLICIT_DEV_OPERATOR_APPROVAL=true',original)
        self.assertIn('preflight_dev_http_auth_routes()',original)
        self.assertIn('CANARY_PRIVATE_30S_H264_AAC_MP4_VERIFIED=true',original)
        self.assertIn('CANARY_POSTER_ONLY_LIVE_ACCEPTANCE=PASSED',original)
        self.assertIn('CANARY_TEMP_FIXTURES_CLEANUP=',original)

    def test_protected_workflow_never_auto_runs_or_swaps_default_api(self):
        workflow=WORKFLOW.read_text()
        self.assertIn('workflow_dispatch:',workflow)
        self.assertNotIn('on: push',workflow)
        self.assertIn("environment: dev",workflow)
        self.assertIn("inputs.approval_code == 'AUTHORIZED_RETAILGROWTHAI_DEV_ONLY'",workflow)
        self.assertIn('node-poster-reel',workflow)
        self.assertIn('node-browser-reel',workflow)
        self.assertIn('RGAI_DEV_NODE_PREVIEW_MODE',workflow)
        self.assertIn('python3 -u tests/e2e/p0249_dev_node_full_canary_once.py',workflow)
        self.assertIn('python3 tests/e2e/retail_dev_canary_once.py',workflow)
        self.assertIn('secrets.RETAIL_SUPABASE_SERVICE_ROLE_KEY',workflow)
        self.assertNotIn('azure/login',workflow)
        self.assertNotIn('static-web-apps-deploy',workflow)
        self.assertNotIn('az group create',workflow)
        self.assertNotIn('apply_migration',workflow)

if __name__=="__main__":
    unittest.main()
