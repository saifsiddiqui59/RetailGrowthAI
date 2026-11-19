"""#249 regression: original Flex Feature2 builds with the actually imported JWT verifier.

Runs the unchanged build_feature2_api function body with synthetic dependencies.
No Azure, Supabase network, signed tokens, customer credentials, or paid AI.
"""
import ast
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "azure-functions/campaign-api/function_app.py"


def load_builder(globals_for_test):
    source = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    builders = [node for node in source.body
                if isinstance(node, ast.FunctionDef) and node.name == "build_feature2_api"]
    if len(builders) != 1:
        raise AssertionError("Original Feature2 builder is missing or duplicated")
    module = ast.fix_missing_locations(ast.Module(body=builders, type_ignores=[]))
    namespace = dict(globals_for_test)
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["build_feature2_api"]


class Feature2OriginalVerifierConstructorTests(unittest.TestCase):
    def test_actual_feature2_builder_uses_registered_bounded_verifier(self):
        calls = []
        verifier = object()
        def cached_verifier(url):
            calls.append(("verifier", url))
            return verifier

        class Store:
            def __init__(self, url, key):
                self.url = url
                self.key = key

        class Admin(Store):
            pass

        def feature_adapter(verify_token, tenant, **kwargs):
            return types.SimpleNamespace(verify_token=verify_token, tenant=tenant,
                                         kwargs=kwargs)

        adapter = types.ModuleType("feature2_adapter")
        adapter.TrendFeatureAdapter = feature_adapter
        feature_store = types.ModuleType("feature2_store")
        feature_store.TrendSnapshotStore = lambda admin: ("snapshots", admin)
        feature_store.TenantDraftStore = lambda admin, tenant: ("drafts", admin, tenant)
        feature_store.authorized_profile_reader = lambda tenant: ("profile", tenant)
        env = {
            "RETAIL_ENABLE_FEATURE2": "true",
            "RETAIL_SUPABASE_URL": "https://synthetic-p0249.supabase.co",
            "RETAIL_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_fixture_only",
            "RETAIL_SUPABASE_SERVICE_ROLE_KEY": "TEST_ONLY_NEVER_NETWORK",
            "RETAIL_FEATURE2_REAL_AI_ENABLED": "false",
        }
        builder = load_builder({
            "os": os,
            "cached_supabase_verifier": cached_verifier,
            "TenantStore": Store,
            "AdminStore": Admin,
        })
        with patch.dict(sys.modules, {
            "feature2_adapter": adapter,
            "feature2_store": feature_store,
        }), patch.dict(os.environ, env):
            instance = builder()
        self.assertIs(instance.verify_token, verifier)
        self.assertEqual(calls, [("verifier", env["RETAIL_SUPABASE_URL"])])
        self.assertEqual(instance.tenant.url, env["RETAIL_SUPABASE_URL"])
        self.assertIsNone(instance.kwargs["ai_service"])

    def test_feature2_disabled_skips_all_auth_or_database_construction(self):
        def deny(*_args, **_kwargs):
            raise AssertionError("disabled Feature2 must not initialize JWT/tenant/store")
        builder = load_builder({
            "os": os,
            "cached_supabase_verifier": deny,
            "TenantStore": deny,
            "AdminStore": deny,
        })
        with patch.dict(os.environ, {"RETAIL_ENABLE_FEATURE2": "false"}):
            self.assertIsNone(builder())

    def test_flex_http_and_feature2_reference_same_current_security_import(self):
        source = ast.parse(SOURCE.read_text(encoding="utf-8"))
        imported = {alias.asname or alias.name
                    for node in source.body if isinstance(node, ast.ImportFrom)
                    and node.module == "security" for alias in node.names}
        self.assertIn("cached_supabase_verifier", imported)
        for name in ("build_api", "build_feature2_api"):
            node = next(n for n in source.body
                        if isinstance(n, ast.FunctionDef) and n.name == name)
            referenced = {call.func.id for call in ast.walk(node)
                          if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)}
            self.assertIn("cached_supabase_verifier", referenced, name)
            self.assertNotIn("SupabaseJWTVerifier", referenced, name)


if __name__ == "__main__":
    unittest.main()
