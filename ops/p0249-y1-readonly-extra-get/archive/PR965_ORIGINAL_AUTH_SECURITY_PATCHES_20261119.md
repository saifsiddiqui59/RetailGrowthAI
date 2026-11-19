# #249 legacy PR #965 exact original JWT and PostgREST source patches (2026-11-19)

- Original historical PR: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/965, pinned head `63f5cbe4bbc3840b3ced6aeb60938976137782bc`, original 12 changed paths. Below are **all 12 exact original GitHub per-file patch hunks**. This file is inert source archaeology, not an auth module or deployed HTTP route.
- Original #965 is a large main-based shared security PR now stale relative to current JWT cache/Feature2 root/tenant code and was never independently approved. Its safe current-main source portions have been selectively ported to separate review-gated [#1018](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/1018): no-redirect tenant/service-role transport, sanitized JWKS dependency outage classification, current `cached_supabase_verifier` Feature2 builder NameError fix, and original negative tests. #1018 still requires independent affected-lead JWT/RLS/Functions approval and exact merged-main CI; do not count its code as accepted by this archive.
- Every remaining original #965 hunk is recoverable below; do NOT wholesale merge the older branch over modern JWT/RLS/storage contracts. Source retention and old PR retirement are PR hygiene, NOT resolution of original markerless Flex 503, authenticated hosted tenant acceptance or commercial release.
- No cloud configuration/deployment, Azure queues, secrets, paid AI, GPU/weights, PROD or WineShopPOS changes are authorized.

## azure-functions/campaign-api/admin_store.py

~~~~diff
@@ -7,12 +7,23 @@
 
 import json
 from urllib.error import HTTPError, URLError
-from urllib.parse import urlencode
-from urllib.request import Request, urlopen
+from urllib.parse import urlencode, urlsplit
+from urllib.request import HTTPRedirectHandler, Request, build_opener
 
 from tenant_store import StorageUnavailable, SubscriptionDenied, canonical_uuid
 
 
+class _DenyRedirects(HTTPRedirectHandler):
+    """A service-role secret must never be sent to any HTTP redirect target."""
+    def redirect_request(self, req, fp, code, msg, headers, newurl):
+        return None
+
+
+# Retain the historic injectable urlopen name for existing worker fixtures,
+# but default to an opener that never redirects a privileged API key or POST.
+urlopen = build_opener(_DenyRedirects()).open
+
+
 def backend_headers(secret):
     """Use opaque Supabase secret keys as API keys, not bearer tokens."""
     if isinstance(secret, str) and secret.startswith("sb_secret_"):
@@ -24,10 +35,25 @@ def backend_headers(secret):
 
 class AdminStore:
     def __init__(self, origin, service_role_key, transport=None):
-        if not origin.startswith("https://") or not service_role_key:
+        if (not isinstance(origin, str) or not isinstance(service_role_key, str)
+                or not service_role_key or
+                any(ord(ch) <= 32 or ord(ch) == 127 for ch in origin)
+                or "\\" in origin):
+            raise ValueError("worker-only Supabase HTTPS origin and secret key required")
+        try:
+            parsed = urlsplit(origin)
+            parsed.port  # reject malformed port before passing a secret to HTTP
+            valid = (origin.startswith("https://") and parsed.scheme == "https"
+                     and bool(parsed.hostname) and parsed.username is None
+                     and parsed.password is None and parsed.path in ("", "/")
+                     and not parsed.query and not parsed.fragment
+                     and parsed.geturl() == origin)
+        except ValueError:
+            valid = False
+        if not valid:
             raise ValueError("worker-only Supabase HTTPS origin and secret key required")
         self.origin, self.secret = origin.rstrip("/"), service_role_key
-        self.transport = transport or urlopen
+        self.transport = transport if transport is not None else urlopen
 
     def request(self, path, *, query=None, data=None, method="GET", upsert=False):
         if path not in ("rpc/claim_campaign_job", "rpc/claim_render_job",
@@ -87,12 +113,16 @@ def request(self, path, *, query=None, data=None, method="GET", upsert=False):
                 return json.loads(raw.decode()) if raw else None
         except HTTPError as exc:
             try:
-                response_code = json.loads(exc.read(4096)).get("code")
-            except (ValueError, AttributeError, TypeError):
-                response_code = None
-            if response_code in ("RG001", "RG002", "RG003", "RG004"):
-                raise SubscriptionDenied(response_code) from exc
-            raise StorageUnavailable("worker database request failed") from exc
+                try:
+                    response_code = json.loads(exc.read(4096)).get("code")
+                except (ValueError, AttributeError, TypeError):
+                    response_code = None
+                if response_code in ("RG001", "RG002", "RG003", "RG004"):
+                    raise SubscriptionDenied(response_code) from exc
+                raise StorageUnavailable("worker database request failed") from exc
+            finally:
+                # Redirects and error responses retain the underlying socket.
+                exc.close()
         except (URLError, OSError, json.JSONDecodeError) as exc:
             raise StorageUnavailable("worker database request failed") from exc
 
~~~~

## azure-functions/campaign-api/feature2_adapter.py

~~~~diff
@@ -12,7 +12,7 @@
 from ai_agents.schemas import CampaignBrief, ContractError
 from ai_agents.providers import FoundryUnavailable
 from ai_agents.trend_intelligence import recommendations
-from security import AuthenticationError
+from security import AuthenticationError, SigningKeysUnavailable
 from tenant_store import StorageUnavailable, canonical_uuid
 
 
@@ -131,7 +131,7 @@ def handle(self, method: str, shop_id: str, authorization: str,
             return 400, {"error": "INVALID_REQUEST"}
         except PermissionError:
             return 403, {"error": "FORBIDDEN"}
-        except StorageUnavailable:
+        except (StorageUnavailable, SigningKeysUnavailable):
             return 503, {"error": "TREND_STORAGE_UNAVAILABLE"}
         except FoundryUnavailable:
             return 503, {"error": "AI_MODEL_UNAVAILABLE"}
@@ -188,7 +188,7 @@ def improve(self, shop_id: str, authorization: str,
             return 400, {"error": "INVALID_REQUEST"}
         except PermissionError:
             return 403, {"error": "FORBIDDEN"}
-        except StorageUnavailable:
+        except (StorageUnavailable, SigningKeysUnavailable):
             return 503, {"error": "PROFILE_UNAVAILABLE"}
         except FoundryUnavailable:
             return 503, {"error": "AI_MODEL_UNAVAILABLE"}
@@ -216,5 +216,5 @@ def list_drafts(self, shop_id: str, authorization: str) -> tuple[int, dict]:
             return 401, {"error": "UNAUTHORIZED"}
         except (ValueError, TypeError, KeyError):
             return 400, {"error": "INVALID_REQUEST"}
-        except StorageUnavailable:
+        except (StorageUnavailable, SigningKeysUnavailable):
             return 503, {"error": "CONTENT_DRAFT_READ_UNAVAILABLE"}
~~~~

## azure-functions/campaign-api/function_app.py

~~~~diff
@@ -379,7 +379,7 @@ def build_feature2_api():
                 # deterministic Feature2 endpoints. Paid AI continues OFF.
                 ai_service = None
     return TrendFeatureAdapter(
-        SupabaseJWTVerifier(origin), tenant,
+        cached_supabase_verifier(origin), tenant,
         profile_reader=authorized_profile_reader(tenant),
         snapshot_store=shared, draft_store=TenantDraftStore(admin, tenant),
         ai_service=ai_service,
~~~~

## azure-functions/campaign-api/http_api.py

~~~~diff
@@ -4,7 +4,7 @@
 from uuid import uuid4
 from ai_agents.schemas import CampaignBrief, ContractError, validate_campaign
 
-from security import AuthenticationError
+from security import AuthenticationError, SigningKeysUnavailable
 from tenant_store import StorageUnavailable, SubscriptionDenied, canonical_uuid
 from draft_api import DraftAPI
 
@@ -205,5 +205,5 @@ def handle(self, method, path, authorization, body=None):
             return 401, {"error": "UNAUTHORIZED"}
         except (ContractError, ValueError, TypeError, AttributeError):
             return 400, {"error": "INVALID_REQUEST"}
-        except (StorageUnavailable, KeyError):
+        except (StorageUnavailable, SigningKeysUnavailable, KeyError):
             return 503, {"error": "SERVICE_UNAVAILABLE"}
~~~~

## azure-functions/campaign-api/security.py

~~~~diff
@@ -7,12 +7,18 @@
 
 import jwt
 from jwt import PyJWKClient
+from jwt.exceptions import PyJWKClientConnectionError
 
 
 class AuthenticationError(ValueError):
     pass
 
 
+class SigningKeysUnavailable(RuntimeError):
+    """Project JWKS temporarily unreachable; never treat as invalid user JWT."""
+    pass
+
+
 class SupabaseJWTVerifier:
     def __init__(self, supabase_url: str, *, jwks_client=None):
         url = urlsplit(supabase_url)
@@ -40,6 +46,11 @@ def __call__(self, token: str) -> str:
             if claims.get("role") != "authenticated" or claims.get("is_anonymous") is True:
                 raise AuthenticationError("non-user token")
             return str(UUID(claims["sub"]))
+        except PyJWKClientConnectionError as exc:
+            # A failed project JWKS fetch is a dependency outage (503), not
+            # proof that the caller signed an invalid JWT (401). Do not leak
+            # the upstream exception or URL and never trust unsigned claims.
+            raise SigningKeysUnavailable("JWT signing keys unavailable") from exc
         except (jwt.PyJWTError, KeyError, ValueError, TypeError) as exc:
             raise AuthenticationError("invalid authentication token") from exc
 
~~~~

## azure-functions/campaign-api/tenant_store.py

~~~~diff
@@ -9,7 +9,7 @@
 import re
 from urllib.error import HTTPError, URLError
 from urllib.parse import urlencode, urlsplit
-from urllib.request import Request, urlopen
+from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
 from uuid import UUID
 
 from security import AuthenticationError
@@ -36,13 +36,45 @@ def canonical_uuid(value):
         raise ValueError("invalid UUID") from exc
 
 
+class _RejectRedirects(HTTPRedirectHandler):
+    """Never forward a verified user's JWT or Supabase API key to a redirect."""
+    def redirect_request(self, req, fp, code, msg, headers, newurl):
+        return None
+
+
+_NO_REDIRECT_OPENER = build_opener(_RejectRedirects())
+
+
 class TenantStore:
     def __init__(self, origin: str, publishable_key: str, transport=None):
-        if not origin.startswith("https://") or not publishable_key:
+        # The no-redirect transport protects *subsequent* hops; reject unsafe
+        # initial origins too, before a verified JWT can be sent over HTTP.
+        if (not isinstance(origin, str) or not isinstance(publishable_key, str)
+                or not publishable_key or
+                any(ord(ch) <= 32 or ord(ch) == 127 for ch in origin) or
+                "\\" in origin):
+            raise ValueError("Supabase HTTPS origin and publishable key required")
+        try:
+            parsed = urlsplit(origin)
+            # Accessing .port also validates malformed port syntax.
+            parsed.port
+            valid = (
+                origin.startswith("https://") and parsed.scheme == "https" and
+                bool(parsed.hostname) and parsed.username is None and
+                parsed.password is None and parsed.path in ("", "/") and
+                not parsed.query and not parsed.fragment and
+                parsed.geturl() == origin
+            )
+        except ValueError:
+            valid = False
+        if not valid:
             raise ValueError("Supabase HTTPS origin and publishable key required")
         self.origin = origin.rstrip("/")
         self.key = publishable_key
-        self.transport = transport or urlopen
+        # Public PostgREST uses the *user* Bearer token; default urlopen
+        # follows HTTP redirects, including to a different origin.
+        # Keep explicitly injected transports for isolated offline fixtures.
+        self.transport = transport if transport is not None else _NO_REDIRECT_OPENER.open
 
     def _request(self, table, token, *, query=None, method="GET", data=None):
         if table not in {"shop_memberships", "media_assets", "campaigns", "campaign_days", "render_jobs", "poster_drafts", "poster_jobs", "business_profiles", "shop_content_drafts", "feature3_gpu_jobs"}:
@@ -68,16 +100,21 @@ def _request(self, table, token, *, query=None, method="GET", data=None):
             with self.transport(request, timeout=8) as response:
                 return json.loads(response.read().decode("utf-8"))
         except HTTPError as exc:
-            if exc.code in (400, 402, 409, 429, 500):
-                try:
-                    response_code = json.loads(exc.read(4096)).get("code")
-                except (ValueError, AttributeError, TypeError):
-                    response_code = None
-                if response_code in ("RG001", "RG002"):
-                    raise SubscriptionDenied(response_code) from exc
-            if exc.code in (401, 403):
-                raise AuthenticationError("database denied user token") from exc
-            raise StorageUnavailable("database request rejected") from exc
+            try:
+                if exc.code in (400, 402, 409, 429, 500):
+                    try:
+                        response_code = json.loads(exc.read(4096)).get("code")
+                    except (ValueError, AttributeError, TypeError):
+                        response_code = None
+                    if response_code in ("RG001", "RG002"):
+                        raise SubscriptionDenied(response_code) from exc
+                if exc.code in (401, 403):
+                    raise AuthenticationError("database denied user token") from exc
+                raise StorageUnavailable("database request rejected") from exc
+            finally:
+                # HTTPError owns a response/socket even on denied redirects;
+                # close it on all error paths, including auth and quota.
+                exc.close()
         except (URLError, OSError, json.JSONDecodeError) as exc:
             raise StorageUnavailable("database unavailable") from exc
 
~~~~

## tests/infra/test_p0249_admin_store_redirects.py

~~~~diff
@@ -0,0 +1,153 @@
+"""#249: privileged original PostgREST worker transport denies off-origin redirects.
+
+Offline synthetic HTTPS and error bodies only. No Azure, Supabase, paid model,
+queue or customer data. Preserves the original AdminStore business RPCs.
+"""
+import io
+from email.message import Message
+from pathlib import Path
+import sys
+import unittest
+from unittest.mock import patch
+from urllib.error import HTTPError
+from urllib.request import HTTPSHandler, ProxyHandler, build_opener
+from urllib.response import addinfourl
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT / "azure-functions/campaign-api"))
+import admin_store  # noqa: E402
+from tenant_store import StorageUnavailable, SubscriptionDenied  # noqa: E402
+
+ORIGIN = "https://synthetic-p0249.supabase.co"
+OPAQUE_KEY = "sb_secret_testfixture_not_real"
+LEGACY_KEY = "eyJfake.header.not_a_signature"
+
+
+class SyntheticRedirectHTTPS(HTTPSHandler):
+    def __init__(self, status):
+        super().__init__()
+        self.status = status
+        self.sent = []
+        self.responses = []
+
+    def https_open(self, req):
+        self.sent.append((req.full_url, req.get_method(),
+                          req.get_header("Apikey"),
+                          req.get_header("Authorization")))
+        headers = Message()
+        headers["Location"] = "https://untrusted-p0249.invalid/collect"
+        response = addinfourl(io.BytesIO(b""), headers, req.full_url,
+                              self.status)
+        response.msg = "Redirect"
+        self.responses.append(response)
+        return response
+
+
+class JSONResponse:
+    def __enter__(self):
+        return self
+
+    def __exit__(self, *_args):
+        return False
+
+    def read(self):
+        return b"[]"
+
+
+class PrivilegedWorkerRedirectSafety(unittest.TestCase):
+    def test_default_transport_uses_the_no_redirect_opener(self):
+        store = admin_store.AdminStore(ORIGIN, OPAQUE_KEY)
+        self.assertIs(store.transport, admin_store.urlopen)
+        self.assertTrue(any(isinstance(handler, admin_store._DenyRedirects)
+                            for handler in admin_store.urlopen.__self__.handlers))
+
+    def test_admin_key_never_replays_get_or_mutating_rpc_on_redirect(self):
+        for secret, expected_bearer in (
+            (OPAQUE_KEY, None), (LEGACY_KEY, "Bearer " + LEGACY_KEY)
+        ):
+            for method, path, data in (
+                ("GET", "campaigns", None),
+                ("POST", "rpc/claim_campaign_job", {"p_id": "synthetic"}),
+            ):
+                for status in (301, 302, 303, 307, 308):
+                    with self.subTest(method=method, status=status,
+                                      key_class="opaque" if secret == OPAQUE_KEY else "legacy"):
+                        redirect = SyntheticRedirectHTTPS(status)
+                        opener = build_opener(ProxyHandler({}),
+                                              admin_store._DenyRedirects(), redirect)
+                        with patch.object(admin_store, "urlopen", opener.open):
+                            store = admin_store.AdminStore(ORIGIN, secret)
+                            with self.assertRaises(StorageUnavailable) as error:
+                                store.request(path, method=method, data=data)
+                        self.assertEqual(redirect.sent, [(
+                            ORIGIN + "/rest/v1/" + path, method, secret,
+                            expected_bearer
+                        )])
+                        self.assertEqual(len(redirect.responses), 1)
+                        self.assertTrue(redirect.responses[0].closed)
+                        self.assertNotIn(secret, str(error.exception))
+
+    def test_worker_rejects_untrusted_initial_origin_before_secret_use(self):
+        bad = (
+            "", "http://synthetic-p0249.supabase.co", "https://",
+            "https://admin:pass@synthetic-p0249.supabase.co",
+            "https://synthetic-p0249.supabase.co/rest/v1",
+            "https://synthetic-p0249.supabase.co/?key=leak",
+            "https://synthetic-p0249.supabase.co/#fragment",
+            "https://synthetic-p0249.supabase.co?",
+            "https://synthetic-p0249.supabase.co:bad",
+            "https://[not-an-ipv6", "https://synthetic-p0249.supabase.co\\\\@evil.invalid",
+            "https://synthetic-p0249.supabase.co\nX-Key: secret",
+            None, 42,
+        )
+        for origin in bad:
+            with self.subTest(origin=repr(origin)), self.assertRaises(ValueError):
+                admin_store.AdminStore(origin, OPAQUE_KEY)
+        for valid in (ORIGIN, ORIGIN + "/", ORIGIN + ":443"):
+            self.assertEqual(admin_store.AdminStore(valid, OPAQUE_KEY).origin,
+                             valid.rstrip("/"))
+        for secret in ("", None, 3):
+            with self.subTest(secret=repr(secret)), self.assertRaises(ValueError):
+                admin_store.AdminStore(ORIGIN, secret)
+
+    def test_injected_worker_transport_preserves_bounded_original_rpc(self):
+        calls = []
+
+        def fixture(req, timeout):
+            calls.append((req.full_url, req.get_method(), timeout,
+                          req.get_header("Apikey")))
+            return JSONResponse()
+
+        store = admin_store.AdminStore(ORIGIN, OPAQUE_KEY, transport=fixture)
+        self.assertEqual(store.request("campaigns"), [])
+        self.assertEqual(calls, [
+            (ORIGIN + "/rest/v1/campaigns", "GET", 10, OPAQUE_KEY)
+        ])
+
+    def test_quota_and_auth_http_errors_are_closed_without_exposing_keys(self):
+        for code, body, exception in (
+            (401, b'{"code":"PGRST301"}', StorageUnavailable),
+            (403, b'{"code":"PGRST301"}', StorageUnavailable),
+            (402, b'{"code":"RG001"}', SubscriptionDenied),
+        ):
+            with self.subTest(code=code):
+                handles = []
+
+                def denied(req, timeout):
+                    response = HTTPError(
+                        req.full_url, code, "synthetic failure",
+                        Message(), io.BytesIO(body)
+                    )
+                    handles.append(response)
+                    raise response
+
+                store = admin_store.AdminStore(ORIGIN, OPAQUE_KEY,
+                                               transport=denied)
+                with self.assertRaises(exception) as error:
+                    store.request("campaigns")
+                self.assertTrue(handles[0].closed)
+                self.assertNotIn(OPAQUE_KEY, str(error.exception))
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/infra/test_p0249_feature2_cached_verifier.py

~~~~diff
@@ -0,0 +1,107 @@
+"""#249 regression: original Flex Feature2 builds with the actually imported JWT verifier.
+
+Runs the unchanged build_feature2_api function body with synthetic dependencies.
+No Azure, Supabase network, signed tokens, customer credentials, or paid AI.
+"""
+import ast
+import os
+from pathlib import Path
+import sys
+import types
+import unittest
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[2]
+SOURCE = ROOT / "azure-functions/campaign-api/function_app.py"
+
+
+def load_builder(globals_for_test):
+    source = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
+    builders = [node for node in source.body
+                if isinstance(node, ast.FunctionDef) and node.name == "build_feature2_api"]
+    if len(builders) != 1:
+        raise AssertionError("Original Feature2 builder is missing or duplicated")
+    module = ast.fix_missing_locations(ast.Module(body=builders, type_ignores=[]))
+    namespace = dict(globals_for_test)
+    exec(compile(module, str(SOURCE), "exec"), namespace)
+    return namespace["build_feature2_api"]
+
+
+class Feature2OriginalVerifierConstructorTests(unittest.TestCase):
+    def test_actual_feature2_builder_uses_registered_bounded_verifier(self):
+        calls = []
+        verifier = object()
+        def cached_verifier(url):
+            calls.append(("verifier", url))
+            return verifier
+
+        class Store:
+            def __init__(self, url, key):
+                self.url = url
+                self.key = key
+
+        class Admin(Store):
+            pass
+
+        def feature_adapter(verify_token, tenant, **kwargs):
+            return types.SimpleNamespace(verify_token=verify_token, tenant=tenant,
+                                         kwargs=kwargs)
+
+        adapter = types.ModuleType("feature2_adapter")
+        adapter.TrendFeatureAdapter = feature_adapter
+        feature_store = types.ModuleType("feature2_store")
+        feature_store.TrendSnapshotStore = lambda admin: ("snapshots", admin)
+        feature_store.TenantDraftStore = lambda admin, tenant: ("drafts", admin, tenant)
+        feature_store.authorized_profile_reader = lambda tenant: ("profile", tenant)
+        env = {
+            "RETAIL_ENABLE_FEATURE2": "true",
+            "RETAIL_SUPABASE_URL": "https://synthetic-p0249.supabase.co",
+            "RETAIL_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_fixture_only",
+            "RETAIL_SUPABASE_SERVICE_ROLE_KEY": "TEST_ONLY_NEVER_NETWORK",
+            "RETAIL_FEATURE2_REAL_AI_ENABLED": "false",
+        }
+        builder = load_builder({
+            "os": os,
+            "cached_supabase_verifier": cached_verifier,
+            "TenantStore": Store,
+            "AdminStore": Admin,
+        })
+        with patch.dict(sys.modules, {
+            "feature2_adapter": adapter,
+            "feature2_store": feature_store,
+        }), patch.dict(os.environ, env):
+            instance = builder()
+        self.assertIs(instance.verify_token, verifier)
+        self.assertEqual(calls, [("verifier", env["RETAIL_SUPABASE_URL"])])
+        self.assertEqual(instance.tenant.url, env["RETAIL_SUPABASE_URL"])
+        self.assertIsNone(instance.kwargs["ai_service"])
+
+    def test_feature2_disabled_skips_all_auth_or_database_construction(self):
+        def deny(*_args, **_kwargs):
+            raise AssertionError("disabled Feature2 must not initialize JWT/tenant/store")
+        builder = load_builder({
+            "os": os,
+            "cached_supabase_verifier": deny,
+            "TenantStore": deny,
+            "AdminStore": deny,
+        })
+        with patch.dict(os.environ, {"RETAIL_ENABLE_FEATURE2": "false"}):
+            self.assertIsNone(builder())
+
+    def test_flex_http_and_feature2_reference_same_current_security_import(self):
+        source = ast.parse(SOURCE.read_text(encoding="utf-8"))
+        imported = {alias.asname or alias.name
+                    for node in source.body if isinstance(node, ast.ImportFrom)
+                    and node.module == "security" for alias in node.names}
+        self.assertIn("cached_supabase_verifier", imported)
+        for name in ("build_api", "build_feature2_api"):
+            node = next(n for n in source.body
+                        if isinstance(n, ast.FunctionDef) and n.name == name)
+            referenced = {call.func.id for call in ast.walk(node)
+                          if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)}
+            self.assertIn("cached_supabase_verifier", referenced, name)
+            self.assertNotIn("SupabaseJWTVerifier", referenced, name)
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/infra/test_p0249_jwks_outage_classification.py

~~~~diff
@@ -0,0 +1,107 @@
+"""#249: original JWT verifier distinguishes JWKS outage from forged JWT.
+
+Uses the actual project SupabaseJWTVerifier and original HTTPAPI. Entirely
+offline synthetic signing-key client; no Azure, Supabase, user or worker writes.
+"""
+from pathlib import Path
+import sys
+import unittest
+from unittest.mock import Mock
+
+import jwt
+from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT / "ai-agents/src"))
+sys.path.insert(0, str(ROOT / "azure-functions/campaign-api"))
+from http_api import HTTPAPI  # noqa: E402
+from feature2_adapter import TrendFeatureAdapter  # noqa: E402
+from security import (AuthenticationError, SigningKeysUnavailable,
+                      SupabaseJWTVerifier)  # noqa: E402
+
+ORIGIN = "https://synthetic-p0249.supabase.co"
+CAMPAIGN = "11111111-1111-4111-8111-111111111111"
+SYNTHETIC_TOKEN = "fake.header.signature"
+
+
+class NoTenantCalls:
+    def __getattr__(self, name):
+        raise AssertionError("JWT must be verified before database access: " + name)
+
+
+def api_with_error(error):
+    key_lookup = Mock(side_effect=error)
+    verifier = SupabaseJWTVerifier(
+        ORIGIN, jwks_client=Mock(get_signing_key_from_jwt=key_lookup))
+    return HTTPAPI(verifier, NoTenantCalls()), key_lookup
+
+
+class JWKSOutageClassificationTests(unittest.TestCase):
+    def test_temporary_jwks_connection_failure_returns_503_not_401(self):
+        api, lookup = api_with_error(
+            PyJWKClientConnectionError("fake upstream failure token=sensitive"))
+        status, payload = api.handle("GET", "/campaigns/" + CAMPAIGN,
+                                     "Bearer " + SYNTHETIC_TOKEN)
+        self.assertEqual((status, payload),
+                         (503, {"error": "SERVICE_UNAVAILABLE"}))
+        lookup.assert_called_once_with(SYNTHETIC_TOKEN)
+        self.assertNotIn("sensitive", str(payload))
+
+    def test_original_verifier_distinguishes_network_and_invalid_signature(self):
+        for error, kind in (
+            (PyJWKClientConnectionError("fake JWKS timeout"), SigningKeysUnavailable),
+            (PyJWKClientError("kid not found"), AuthenticationError),
+            (jwt.InvalidSignatureError("signature invalid"), AuthenticationError),
+        ):
+            with self.subTest(error=type(error).__name__):
+                client = Mock(get_signing_key_from_jwt=Mock(side_effect=error))
+                verifier = SupabaseJWTVerifier(ORIGIN, jwks_client=client)
+                with self.assertRaises(kind) as raised:
+                    verifier(SYNTHETIC_TOKEN)
+                self.assertNotIn("fake JWKS", str(raised.exception))
+
+    def test_feature2_all_original_jwt_routes_fail_closed_with_dependency_503(self):
+        shop = "33333333-3333-4333-8333-333333333333"
+        lookup = Mock(side_effect=PyJWKClientConnectionError(
+            "synthetic JWKS outage key=not-a-real-key"))
+        verifier = SupabaseJWTVerifier(
+            ORIGIN, jwks_client=Mock(get_signing_key_from_jwt=lookup))
+        adapter = TrendFeatureAdapter(verifier, NoTenantCalls())
+        expected = (
+            (adapter.handle, ("GET", shop, "Bearer " + SYNTHETIC_TOKEN),
+             (503, {"error": "TREND_STORAGE_UNAVAILABLE"})),
+            (adapter.improve, (shop, "Bearer " + SYNTHETIC_TOKEN, {}),
+             (503, {"error": "PROFILE_UNAVAILABLE"})),
+            (adapter.list_drafts, (shop, "Bearer " + SYNTHETIC_TOKEN),
+             (503, {"error": "CONTENT_DRAFT_READ_UNAVAILABLE"})),
+        )
+        for fn, args, output in expected:
+            with self.subTest(endpoint=fn.__name__):
+                status, body = fn(*args)
+                self.assertEqual((status, body), output)
+                self.assertNotIn("not-a-real-key", str(body))
+        self.assertEqual(lookup.call_count, 3)
+
+    def test_invalid_token_fails_before_jwks_and_returns_401(self):
+        api, lookup = api_with_error(
+            PyJWKClientConnectionError("unreachable JWKS"))
+        for authorization in ("", "Basic synthetic", "Bearer ",
+                              "Bearer " + "a" * 8193):
+            with self.subTest(authorization=authorization[:20]):
+                status, payload = api.handle("GET", "/campaigns/" + CAMPAIGN,
+                                             authorization)
+                self.assertEqual((status, payload),
+                                 (401, {"error": "UNAUTHORIZED"}))
+        lookup.assert_not_called()
+
+    def test_invalid_kid_stays_401_without_database_access(self):
+        api, lookup = api_with_error(PyJWKClientError("key id unavailable"))
+        self.assertEqual(
+            api.handle("GET", "/campaigns/" + CAMPAIGN,
+                       "Bearer " + SYNTHETIC_TOKEN),
+            (401, {"error": "UNAUTHORIZED"}))
+        lookup.assert_called_once()
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/infra/test_p0249_tenant_store_redirects.py

~~~~diff
@@ -0,0 +1,140 @@
+"""#249: original user-JWT PostgREST transport must never follow HTTP redirects.
+
+No real credentials, network, Azure deployment, database or customer records.
+"""
+import io
+from email.message import Message
+from pathlib import Path
+import sys
+import unittest
+from unittest.mock import patch
+from urllib.request import HTTPSHandler, ProxyHandler, build_opener
+from urllib.response import addinfourl
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT / "azure-functions/campaign-api"))
+import tenant_store  # noqa: E402
+
+ORIGIN = "https://synthetic-p0249.supabase.co"
+TOKEN = "synthetic.bearer.not-real"
+PUBLIC = "sb_publishable_synthetic_only"
+
+
+class RedirectingHTTPS(HTTPSHandler):
+    """A synthetic upstream 30x; no actual DNS/TLS request."""
+    def __init__(self, redirect_status):
+        super().__init__()
+        self.status = redirect_status
+        self.attempted = []
+        self.responses = []
+
+    def https_open(self, request):
+        self.attempted.append((
+            request.full_url, request.get_header("Authorization"),
+            request.get_header("Apikey"), request.get_method(),
+        ))
+        headers = Message()
+        headers["Location"] = "https://untrusted-p0249.invalid/collect"
+        response = addinfourl(io.BytesIO(b""), headers, request.full_url,
+                              self.status)
+        response.msg = "Redirect"
+        self.responses.append(response)
+        return response
+
+
+class JSONResponse:
+    def __enter__(self):
+        return self
+
+    def __exit__(self, *_args):
+        return False
+
+    def read(self):
+        return b"[]"
+
+
+class TenantStoreRedirectSafety(unittest.TestCase):
+    def test_real_default_transport_rejects_all_redirects_without_replaying_user_jwt(self):
+        for status in (301, 302, 303, 307, 308):
+            with self.subTest(status=status):
+                redirect = RedirectingHTTPS(status)
+                opener = build_opener(ProxyHandler({}),
+                                      tenant_store._RejectRedirects(), redirect)
+                with patch.object(tenant_store, "_NO_REDIRECT_OPENER", opener):
+                    store = tenant_store.TenantStore(ORIGIN, PUBLIC)
+                    self.assertIs(store.transport.__self__, opener)
+                    with self.assertRaises(tenant_store.StorageUnavailable) as error:
+                        store._request("campaigns", TOKEN, query={"select": "id"})
+                self.assertEqual(len(redirect.attempted), 1)
+                self.assertEqual(len(redirect.responses), 1)
+                self.assertTrue(redirect.responses[0].closed)
+                path, auth, public, method = redirect.attempted[0]
+                self.assertEqual(path, ORIGIN + "/rest/v1/campaigns?select=id")
+                self.assertEqual(auth, "Bearer " + TOKEN)
+                self.assertEqual(public, PUBLIC)
+                self.assertEqual(method, "GET")
+                self.assertNotIn(TOKEN, str(error.exception))
+
+    def test_redirect_cannot_replay_post_mutation_or_forward_credentials(self):
+        for status in (302, 307, 308):
+            with self.subTest(status=status):
+                redirect = RedirectingHTTPS(status)
+                opener = build_opener(ProxyHandler({}),
+                                      tenant_store._RejectRedirects(), redirect)
+                with patch.object(tenant_store, "_NO_REDIRECT_OPENER", opener):
+                    store = tenant_store.TenantStore(ORIGIN, PUBLIC)
+                    with self.assertRaises(tenant_store.StorageUnavailable):
+                        store._request("campaigns", TOKEN, method="POST",
+                                       data={"id": "synthetic-only"})
+                self.assertEqual(len(redirect.attempted), 1)
+                self.assertEqual(len(redirect.responses), 1)
+                self.assertTrue(redirect.responses[0].closed)
+                url, auth, pub, method = redirect.attempted[0]
+                self.assertEqual(url, ORIGIN + "/rest/v1/campaigns")
+                self.assertEqual(auth, "Bearer " + TOKEN)
+                self.assertEqual(pub, PUBLIC)
+                self.assertEqual(method, "POST")
+
+    def test_initial_origin_is_pinned_to_https_authority_before_jwt_transport(self):
+        bad = (
+            "", "http://synthetic-p0249.supabase.co",
+            "https://", "https://name:password@synthetic-p0249.supabase.co",
+            "https://synthetic-p0249.supabase.co/rest/v1",
+            "https://synthetic-p0249.supabase.co/?token=leak",
+            "https://synthetic-p0249.supabase.co/#fragment",
+            "https://synthetic-p0249.supabase.co?",
+            "https://synthetic-p0249.supabase.co#",
+            "https://synthetic-p0249.supabase.co:bad",
+            "https://[not-an-ipv6",
+            "https://synthetic-p0249.supabase.co\\\\@untrusted.invalid",
+            "https://synthetic-p0249.supabase.co\nExtra: yes",
+            None, 42,
+        )
+        for origin in bad:
+            with self.subTest(origin=repr(origin)), self.assertRaises(ValueError):
+                tenant_store.TenantStore(origin, PUBLIC)
+        for origin in (ORIGIN, ORIGIN + "/", ORIGIN + ":443"):
+            with self.subTest(origin=origin):
+                store = tenant_store.TenantStore(origin, PUBLIC)
+                self.assertEqual(store.origin, origin.rstrip("/"))
+        for key in (None, "", 5):
+            with self.subTest(key=key), self.assertRaises(ValueError):
+                tenant_store.TenantStore(ORIGIN, key)
+
+    def test_explicit_test_transport_remains_injectable(self):
+        seen = []
+
+        def fixture(request, timeout):
+            seen.append((request.full_url, request.get_header("Authorization"),
+                         request.get_method(), timeout))
+            return JSONResponse()
+
+        store = tenant_store.TenantStore(ORIGIN, PUBLIC, transport=fixture)
+        self.assertEqual(store._request("campaigns", TOKEN), [])
+        self.assertEqual(seen, [
+            (ORIGIN + "/rest/v1/campaigns", "Bearer " + TOKEN, "GET", 8)
+        ])
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

## tests/infra/test_p0249_y1_signed_two_shop_transport.py

~~~~diff
@@ -158,7 +158,7 @@ def setUp(self):
             patch("security.PyJWKClient", return_value=SimpleNamespace(
                 get_signing_key_from_jwt=lambda _t: SimpleNamespace(key=RSA_KEY.public_key())
             )),
-            patch("tenant_store.urlopen", side_effect=self.backend),
+            patch("tenant_store._NO_REDIRECT_OPENER.open", side_effect=self.backend),
         )
         for p in self.patches:
             p.start()
@@ -215,6 +215,36 @@ def test_invalid_signed_claims_and_forged_signatures_denied_before_store(self):
                 self.assertEqual(len(self.backend.requests), before,
                                  "rejected JWT must not reach PostgREST")
 
+    def test_actual_y1_handler_marks_jwks_dependency_503_without_db_or_token(self):
+        from jwt.exceptions import PyJWKClientConnectionError
+        from security import cached_supabase_verifier
+
+        token = make_token(A_USER)
+        request = SimpleNamespace(
+            route_params={"campaign_id": A_CAMPAIGN},
+            headers={"Authorization": "Bearer " + token},
+        )
+
+        def no_keys(_token):
+            raise PyJWKClientConnectionError("synthetic JWKS outage secret=fixture")
+
+        cached_supabase_verifier.cache_clear()
+        try:
+            with patch("security.PyJWKClient", return_value=SimpleNamespace(
+                    get_signing_key_from_jwt=no_keys)):
+                with patch.dict("os.environ", ENV):
+                    response = shadow.main(request)
+            self.assertEqual(response.status_code, 503)
+            self.assertEqual(json.loads(response.get_body()),
+                             {"error": "SERVICE_UNAVAILABLE"})
+            self.assertTrue(response.headers.get("X-Request-ID"))
+            self.assertEqual(response.headers.get("Cache-Control"), "no-store")
+            self.assertNotIn(token, response.get_body().decode("utf-8"))
+            self.assertNotIn("secret=fixture", response.get_body().decode("utf-8"))
+            self.assertEqual(self.backend.requests, [])
+        finally:
+            cached_supabase_verifier.cache_clear()
+
     def test_y1_reuses_only_bounded_jwks_verifier_not_current_tenant_store(self):
         from security import cached_supabase_verifier
 
~~~~

## tests/reliability/test_media_lazy_import_boundaries.py

~~~~diff
@@ -59,4 +59,8 @@ def test_public_http_adapter_still_declared_and_jwt_path_not_removed():
     assert {"build_api","dispatch","create_campaign","read_campaign",
             "request_poster_render","select_poster_banner",
             "render_campaign_reel","render_campaign_poster","dispatch_pending_posters"} <= names
-    assert "SupabaseJWTVerifier" in SOURCE.read_text(encoding="utf-8")
+    security_imports={alias.asname or alias.name
+                      for node in TREE.body if isinstance(node,ast.ImportFrom)
+                      and node.module=="security" for alias in node.names}
+    assert "cached_supabase_verifier" in security_imports
+
~~~~

