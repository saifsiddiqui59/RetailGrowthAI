"""Y1 shadow GET must reuse original verified JWT/RLS with NO new side effects."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai-agents/src"))
sys.path.insert(0, str(ROOT / "azure-functions/campaign-api"))
SOURCE = ROOT / "ops/p0249-y1-readonly-campaign/campaign_read/__init__.py"
spec = importlib.util.spec_from_file_location("p0249_y1_campaign_read_shadow", SOURCE)
shadow = importlib.util.module_from_spec(spec)
try:
    import azure.functions  # noqa: F401; installed in real Linux deploy workflow
except ModuleNotFoundError:
    # The full repo's Python CI intentionally does not install azure-functions.
    # Supply only the transport shape while importing the real auth/RLS logic;
    # real Azure Functions import is exercised separately in the deploy job.
    functions = types.ModuleType("azure.functions")
    class LocalResponse:
        def __init__(self, body, *, status_code, mimetype, headers):
            self.status_code = status_code
            self.headers = headers
            self._body = body.encode("utf-8")
        def get_body(self):
            return self._body
    functions.HttpResponse = LocalResponse
    package = types.ModuleType("azure")
    package.__path__ = []
    package.functions = functions
    with patch.dict(sys.modules, {"azure": package, "azure.functions": functions}):
        spec.loader.exec_module(shadow)
else:
    spec.loader.exec_module(shadow)
UUID = "11111111-1111-4111-8111-111111111111"
ENV = {
    "RGAI_P0249_READONLY_SHADOW": "true",
    "RETAIL_SUPABASE_URL": "https://synthetic.supabase.co",
    "RETAIL_SUPABASE_PUBLISHABLE_KEY": "synthetic-publishable-only",
}


class Y1ReadOnlyCampaignShadowTests(unittest.TestCase):
    def test_denies_no_bearer_without_creating_auth_or_store(self):
        for auth in ("", "garbage", "bearer token", "Basic anything",
                     "Bearer ", "Bearer " + "x" * 8193):
            with self.subTest(auth=auth[:10]), \
                 patch.object(shadow, "HTTPAPI",
                              side_effect=AssertionError("must never access store")):
                self.assertEqual(
                    shadow.handle_campaign_get(auth, UUID, environment={}),
                    (401, {"error": "UNAUTHORIZED"}),
                )

    def test_feature_off_denies_before_any_sql_or_jwks(self):
        with patch.object(shadow, "SupabaseJWTVerifier",
                          side_effect=AssertionError("no JWT verification")), \
             patch.object(shadow, "TenantStore",
                          side_effect=AssertionError("no SQL")):
            self.assertEqual(
                shadow.handle_campaign_get("Bearer suspect", UUID, environment={}),
                (503, {"error": "SERVICE_NOT_CONFIGURED"}),
            )

    def test_missing_public_config_fails_closed(self):
        for env in ({"RGAI_P0249_READONLY_SHADOW": "true"},
                    {"RGAI_P0249_READONLY_SHADOW": "true",
                     "RETAIL_SUPABASE_URL": ENV["RETAIL_SUPABASE_URL"]}):
            with patch.object(shadow, "HTTPAPI",
                              side_effect=AssertionError("no API")):
                self.assertEqual(
                    shadow.handle_campaign_get("Bearer invalid", UUID, environment=env),
                    (503, {"error": "SERVICE_NOT_CONFIGURED"}),
                )

    def test_signed_get_delegates_exactly_to_original_httpapi(self):
        api = MagicMock()
        api.handle.return_value = (404, {"error": "NOT_FOUND"})
        with patch.object(shadow, "SupabaseJWTVerifier") as verify, \
             patch.object(shadow, "TenantStore") as store, \
             patch.object(shadow, "HTTPAPI", return_value=api) as api_type:
            output = shadow.handle_campaign_get("Bearer synthetic-jwt", UUID,
                                                 environment=ENV)
        self.assertEqual(output, (404, {"error": "NOT_FOUND"}))
        verify.assert_called_once_with(ENV["RETAIL_SUPABASE_URL"])
        store.assert_called_once_with(ENV["RETAIL_SUPABASE_URL"],
                                      ENV["RETAIL_SUPABASE_PUBLISHABLE_KEY"])
        api_type.assert_called_once_with(verify.return_value, store.return_value)
        api.handle.assert_called_once_with(
            "GET", "/campaigns/" + UUID, "Bearer synthetic-jwt",
        )

    def test_main_preserves_denial_headers_without_token_leak(self):
        request = MagicMock()
        request.route_params = {"campaign_id": UUID}
        request.headers = {"Authorization": "Bearer sensitive-token-do-not-echo"}
        with patch.object(shadow, "handle_campaign_get",
                          return_value=(401, {"error": "UNAUTHORIZED"})):
            response = shadow.main(request)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.get_body()), {"error": "UNAUTHORIZED"})
        self.assertTrue(response.headers["X-Request-ID"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertNotIn("sensitive-token", str(response.headers))
        self.assertNotIn("sensitive-token", response.get_body().decode())

    def test_main_returns_sanitized_response_on_runtime_failure(self):
        request = MagicMock()
        request.route_params = {"campaign_id": UUID}
        request.headers = {}
        with patch.object(shadow, "handle_campaign_get", side_effect=RuntimeError("secret")):
            response = shadow.main(request)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.get_body()), {"error": "INTERNAL_ERROR"})
        self.assertNotIn("secret", response.get_body().decode())

    def test_v1_manifest_only_get_never_write_or_queue(self):
        folder = SOURCE.parent
        manifest = json.loads((folder / "function.json").read_text())
        self.assertEqual(manifest["scriptFile"], "__init__.py")
        self.assertEqual(manifest["entryPoint"], "main")
        trigger, output = manifest["bindings"]
        self.assertEqual(trigger["type"], "httpTrigger")
        self.assertEqual(trigger["authLevel"], "anonymous")
        self.assertEqual(trigger["methods"], ["get"])
        self.assertEqual(trigger["route"], "campaigns/{campaign_id}")
        self.assertEqual(output["type"], "http")
        self.assertEqual(output["name"], "$return")
        self.assertNotIn("@app.queue_trigger", SOURCE.read_text())
        self.assertNotIn("@app.timer_trigger", SOURCE.read_text())

    def test_package_excludes_privileged_auth_and_provider_dependencies(self):
        req=(ROOT / "ops/p0249-y1-readonly-campaign/requirements.txt").read_text()
        self.assertIn("PyJWT[crypto]==2.10.1", req)
        self.assertNotIn("azure-storage-queue", req)
        self.assertNotIn("Pillow", req)
        src = SOURCE.read_text()
        self.assertIn("from http_api import HTTPAPI", src)
        self.assertIn("from security import SupabaseJWTVerifier", src)
        self.assertIn("from tenant_store import TenantStore", src)
        self.assertNotIn("SERVICE_ROLE", src)
        self.assertNotIn("AzurePlanningQueue", src)

    def test_no_route_on_poster_model_or_mutating_api(self):
        txt = SOURCE.read_text()
        manifest = (SOURCE.parent / "function.json").read_text()
        for forbidden in ("POST", "PATCH", "DELETE", "admin_key",
                          "render_queue", "planning_queue", "feature3_gpu",
                          "retail-campaign-planning", "az deployment group create"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, manifest)


if __name__ == "__main__":
    unittest.main()
