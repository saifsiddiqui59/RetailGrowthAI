"""Source-only three-GET Y1 mirror: original JWT/RLS, no route mutators.

No Azure account, hosted Supabase identity, private fixture or network access.
"""
import ast
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "ops/p0249-y1-readonly-extra-get"
MODULE = BASE / "p0249_readonly_jobs.py"
SPEC = importlib.util.spec_from_file_location("p0249_y1_extra_get_shadow", MODULE)
shadow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shadow)

UID = "11111111-1111-4111-8111-111111111111"
CONFIG = {
    "RGAI_P0249_READONLY_SHADOW": "true",
    "RGAI_P0249_EXTRA_GET_SHADOW": "true",
    "RETAIL_SUPABASE_URL": "https://isolated-fixture.supabase.co",
    "RETAIL_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_mock_only",
}
ROUTES = {
    "render_job": ("render_job_read", "render-jobs/{job_id}", "/render-jobs/" + UID),
    "poster_job": ("poster_job_read", "poster-jobs/{job_id}", "/poster-jobs/" + UID),
    "poster_draft": ("poster_draft_read", "poster-drafts/{draft_id}", "/poster-drafts/" + UID),
}


class Y1ExtraGetSafetyTests(unittest.TestCase):
    def test_unauthed_rejected_without_config_auth_or_database_access(self):
        for kind in ROUTES:
            for authorization in ("", "Basic fake", "bearer invalid", "Bearer ",
                                  "Bearer " + "x" * 8193):
                with self.subTest(kind=kind, auth=authorization[:12]), \
                     patch.object(shadow, "_build_original_api",
                                  side_effect=AssertionError("must not reach JWT or SQL")):
                    self.assertEqual(
                        shadow.handle_get(kind, UID, authorization, environment={}),
                        (401, {"error": "UNAUTHORIZED"}),
                    )

    def test_both_enable_flags_and_public_settings_mandatory(self):
        missing_options = [
            {},
            {"RGAI_P0249_READONLY_SHADOW": "true"},
            {"RGAI_P0249_EXTRA_GET_SHADOW": "true"},
            dict(CONFIG, RGAI_P0249_EXTRA_GET_SHADOW="false"),
            {k: v for k, v in CONFIG.items() if k != "RETAIL_SUPABASE_URL"},
            {k: v for k, v in CONFIG.items()
             if k != "RETAIL_SUPABASE_PUBLISHABLE_KEY"},
        ]
        for config in missing_options:
            with self.subTest(config=set(config)), \
                 patch.object(shadow, "_build_original_api",
                              side_effect=AssertionError("must not access original API")):
                self.assertEqual(
                    shadow.handle_get("render_job", UID, "Bearer synthetic", environment=config),
                    (503, {"error": "SERVICE_NOT_CONFIGURED"}),
                )

    def test_only_exact_three_literal_routes_and_canonical_uuid(self):
        with patch.object(shadow, "_build_original_api",
                          side_effect=AssertionError("must not access original API")):
            self.assertEqual(shadow.handle_get("unregistered",
                                              UID, "Bearer synthetic", environment=CONFIG),
                             (404, {"error": "NOT_FOUND"}))
            for wrong in ("", "not-a-uuid", "11111111-1111-4111-8111-111111111111/extra",
                          UID.upper(), "%2f" + UID, UID.replace("-", "")):
                self.assertEqual(shadow.handle_get("poster_job", wrong, "Bearer synthetic",
                                                   environment=CONFIG),
                                 (400, {"error": "INVALID_REQUEST"}))

    def test_all_get_paths_delegate_to_original_httpapi_with_unmodified_bearer(self):
        api = MagicMock()
        api.handle.return_value = (404, {"error": "NOT_FOUND"})
        for kind, (_, _, path) in ROUTES.items():
            with self.subTest(kind=kind), \
                 patch.object(shadow, "_build_original_api", return_value=api) as factory:
                status, body = shadow.handle_get(kind, UID, "Bearer synthetic-only",
                                                  environment=CONFIG)
                self.assertEqual((status, body), (404, {"error": "NOT_FOUND"}))
                factory.assert_called_once_with(CONFIG["RETAIL_SUPABASE_URL"],
                                                CONFIG["RETAIL_SUPABASE_PUBLISHABLE_KEY"])
                api.handle.assert_called_with("GET", path, "Bearer synthetic-only")
        self.assertEqual(api.handle.call_count, 3)

    def test_builder_uses_existing_jwks_and_retailer_rls_not_privileged_admin(self):
        module_names = ("http_api", "security", "tenant_store", "render_api",
                        "poster_draft_api", "poster_render_api")
        module_types = {name: types.ModuleType(name) for name in module_names}
        token_verifier = object()
        stores = []
        def store(origin, key):
            result = types.SimpleNamespace(origin=origin, key=key)
            stores.append(result)
            return result
        module_types["security"].cached_supabase_verifier = lambda origin: token_verifier
        module_types["tenant_store"].TenantStore = store
        module_types["render_api"].RenderAPI = lambda user_store, admin, queue: (
            "read_render", user_store, admin, queue)
        module_types["poster_draft_api"].PosterDraftAPI = lambda user_store: (
            "read_poster_draft", user_store)
        module_types["poster_render_api"].PosterRenderAPI = lambda user_store: (
            "read_poster_job", user_store)
        def original_api(verifier, user_store, **kwargs):
            return types.SimpleNamespace(verifier=verifier, store=user_store, kwargs=kwargs)
        module_types["http_api"].HTTPAPI = original_api
        with patch.dict(sys.modules, module_types):
            built = shadow._build_original_api(CONFIG["RETAIL_SUPABASE_URL"],
                                              CONFIG["RETAIL_SUPABASE_PUBLISHABLE_KEY"])
        self.assertEqual(len(stores), 1)
        self.assertIs(built.verifier, token_verifier)
        self.assertIs(built.store, stores[0])
        self.assertEqual(built.kwargs["render_api"], ("read_render", stores[0], None, None))
        self.assertEqual(built.kwargs["poster_api"], ("read_poster_draft", stores[0]))
        self.assertEqual(built.kwargs["poster_render_api"], ("read_poster_job", stores[0]))
        self.assertIsNone(built.kwargs["planning_queue"])
        self.assertIsNone(built.kwargs["failure_store"])

    def test_python_v1_indexing_has_no_eager_jwt_rls_queue_or_paid_imports(self):
        tree = ast.parse(MODULE.read_text())
        top_imports = {n.module for n in tree.body if isinstance(n, ast.ImportFrom)}
        for name in ("http_api", "security", "tenant_store", "render_api",
                     "poster_render_api", "poster_draft_api", "admin_store",
                     "queue_adapter", "render_worker", "poster_worker"):
            self.assertNotIn(name, top_imports)
        builder = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                       and n.name == "_build_original_api")
        import_names = {n.module for n in ast.walk(builder)
                        if isinstance(n, ast.ImportFrom)}
        self.assertEqual(import_names, {"http_api", "security", "tenant_store",
                                         "render_api", "poster_draft_api",
                                         "poster_render_api"})

    def test_only_get_function_manifests_are_source_staged(self):
        found = []
        for kind, (dirname, route, _) in ROUTES.items():
            directory = BASE / dirname
            manifest = json.loads((directory / "function.json").read_text())
            self.assertEqual(manifest["entryPoint"], "main")
            self.assertEqual(manifest["scriptFile"], "__init__.py")
            trigger = [x for x in manifest["bindings"] if x["type"] == "httpTrigger"]
            self.assertEqual(len(trigger), 1)
            self.assertEqual(trigger[0]["authLevel"], "anonymous")
            self.assertEqual(trigger[0]["methods"], ["get"])
            self.assertEqual(trigger[0]["route"], route)
            self.assertEqual({x["type"] for x in manifest["bindings"]},
                             {"httpTrigger", "http"})
            source = (directory / "__init__.py").read_text()
            self.assertIn('serve(req, "' + kind + '")', source)
            self.assertNotIn("admin_store", source)
            found.append(directory.name)
        self.assertEqual(set(found), set(p[0] for p in ROUTES.values()))
        self.assertEqual(len(list(BASE.glob("*/function.json"))), 3)

    def test_explicit_only_get_entrypoint_returns_safe_errors_and_marker(self):
        from email.message import Message
        request = MagicMock()
        request.route_params = {"job_id": UID}
        request.headers = {"Authorization": "Bearer never-echo-this"}
        class FakeResponse:
            def __init__(self, payload, status_code, mimetype, headers):
                self.status_code = status_code
                self.body = payload
                self.headers = headers
        azure_module = types.ModuleType("azure")
        azure_module.__path__ = []
        functions = types.ModuleType("azure.functions")
        functions.HttpResponse = FakeResponse
        azure_module.functions = functions
        diagnostics = types.ModuleType("request_diagnostics")
        class Diagnostics:
            def __init__(self, method, path):
                self.method, self.path = method, path
            def complete(self, status, payload):
                return {"X-Request-ID": "synthetic-marker", "Cache-Control": "no-store"}
        diagnostics.RequestDiagnostics = Diagnostics
        with patch.dict(sys.modules, {"azure": azure_module,
                                      "azure.functions": functions,
                                      "request_diagnostics": diagnostics}):
            request.method = "POST"
            with patch.object(shadow, "handle_get",
                              side_effect=AssertionError("must not allow POST")):
                denied = shadow.serve(request, "render_job")
            self.assertEqual(denied.status_code, 405)
            request.method = "GET"
            with patch.object(shadow, "handle_get",
                              side_effect=RuntimeError("sensitive-jwt-or-private-path")):
                sanitized = shadow.serve(request, "render_job")
        self.assertEqual(sanitized.status_code, 500)
        self.assertEqual(json.loads(sanitized.body), {"error": "INTERNAL_ERROR"})
        self.assertEqual(sanitized.headers["X-Request-ID"], "synthetic-marker")
        self.assertNotIn("never-echo-this", str(sanitized.headers))
        self.assertNotIn("sensitive-jwt", sanitized.body)


if __name__ == "__main__":
    unittest.main()
