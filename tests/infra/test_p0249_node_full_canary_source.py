"""Offline gating: Node cloud E2E does not bypass ROOT, tenants or mutate PROD."""
from pathlib import Path
import ast
import time
import types
import unittest
import urllib.error

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
        self.assertIn('CANARY_WAITING_FOR_TWO_EXPLICIT_DEV_OPERATOR_APPROVALS=true',original)
        self.assertIn('CANARY_BOTH_OPERATOR_APPROVALS_VERIFIED=true',original)
        self.assertLess(
            original.index('wait_for_both_root_approvals(accounts)'),
            original.index('call(SUPABASE+"/rest/v1/shops",'))
        self.assertIn('preflight_dev_http_auth_routes(',original)
        self.assertIn('CANARY_PRIVATE_30S_H264_AAC_MP4_VERIFIED=true',original)
        self.assertIn('CANARY_POSTER_ONLY_LIVE_ACCEPTANCE=PASSED',original)
        self.assertIn('CANARY_TEMP_FIXTURES_CLEANUP=',original)


    def test_parent_keyword_contract_and_real_preflight_without_network(self):
        """Regression for hosted run #40828856951: parent's include_prompt kwarg."""
        source = E2E.read_text()
        parent = ORIGINAL.read_text()
        self.assertIn("preflight_dev_http_auth_routes(include_prompt=prompt_only)", parent)
        module = ast.parse(source)
        preflight = next(n for n in module.body
                         if isinstance(n, ast.FunctionDef) and n.name == "node_preflight")
        # Only compile the callback: importing the hosted canary here could
        # bring secrets/network configuration into offline CI.
        self.assertEqual([n.arg for n in preflight.args.kwonlyargs], ["include_prompt"])
        self.assertEqual(len(preflight.args.kw_defaults), 1)
        self.assertIs(preflight.args.kw_defaults[0].value, False)
        calls = []
        origin = "https://purple-dune-06b5da200-p0249writes.eastasia.2.azurestaticapps.net"

        class Response:
            status = 200
            headers = {"X-P0249-Secure-Preview": "real-jwks-rls-dev-write-v1"}
            def __enter__(self):
                return self
            def __exit__(self, *_):
                return False

        def request(url, **kwargs):
            return types.SimpleNamespace(url=url, method=kwargs.get("method", "GET"))

        def urlopen(req, *, timeout):
            self.assertEqual(timeout, 12)
            self.assertTrue(req.url.startswith(origin + "/api/"))
            calls.append(req.url)
            if req.url.endswith("/api/p0-secure-health"):
                return Response()
            # No real remote requests or tokens: model only required
            # app-origin 401+marker behavior.
            raise urllib.error.HTTPError(
                req.url, 401, "Unauthorized",
                {"X-RGAI-Secure-Adapter": "candidate-v1"}, None)

        scope = {
            "urllib": types.SimpleNamespace(
                request=types.SimpleNamespace(Request=request, urlopen=urlopen),
                error=types.SimpleNamespace(HTTPError=urllib.error.HTTPError)),
            "NODE_PREVIEW": origin,
            "time": time,
        }
        exec(compile(ast.Module(body=[preflight], type_ignores=[]),
                     str(E2E), "exec"), scope)
        scope["node_preflight"](include_prompt=False)
        self.assertEqual(len(calls), 6)  # health + five protected routes
        with self.assertRaisesRegex(RuntimeError, "PROMPT_MODE_NOT_SUPPORTED"):
            scope["node_preflight"](include_prompt=True)
        # Unsupported mode is rejected BEFORE any network request.
        self.assertEqual(len(calls), 6)

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
