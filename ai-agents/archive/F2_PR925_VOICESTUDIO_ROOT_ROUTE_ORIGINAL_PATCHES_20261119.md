# F2 stacked #925 original VoiceStudio root route source — historical archive, 2026-11-19

- Original #925 HEAD: `69a4edce42c3e7ed54c6984b9876a7bdd07d41f0`, DRAFT, base `feat/feature2-voicestudio-register-wav-20261111`, not main.
- Preserves exactly **3/3 complete original GitHub per-file patch hunks** verbatim below. Old branch `function_app.py` constructs `SupabaseJWTVerifier` per enabled route whereas newer main uses a bounded cached verifier; do NOT restore stale root imports or merge old parent wholesale.
- No source here is active runtime integration, and no license, human editor, JWT/RLS, commercial voice model, original key or private asset approval is implied. Route remains default OFF. Rebuild as a new latest-main review PR after independent affected auth/Functions/VoiceStudio review, with exact tenant-security tests and SQL #923 dependencies resolved.
- Existing Feature2 original 38 tasks and protected #920/#923 VoiceStudio work stay OPEN. No GPU, paid inference, DEV/PROD, SQL migration, model download or WineShopPOS changes.

## azure-functions/campaign-api/FEATURE2_VOICESTUDIO_ROUTE_REVIEW.md

~~~~diff
@@ -0,0 +1,38 @@
+# Feature2 VoiceStudio root Azure Function route — independent review REQUIRED
+
+**Source only; NOT deployed or enabled.** This stacked change adds one protected root Functions route,
+`POST /api/shops/{shop_id}/voicestudio-jobs`, using the existing `VoiceStudioSignedAPI`
+and the existing Supabase JWT verifier + `TenantStore.member(write=True)` on each
+request. Body accepts only trusted resource references
+`{campaign_id,request_id}`. Actor is always derived from the JWT; voice,
+language, script, commercial model, claim and media path come solely from
+server-side current approved SQL plan/asset readers.
+
+The route builds lazily and returns HTTP 503 unless **both**
+`RETAIL_VOICESTUDIO_HTTP_ENABLED=true` and
+`RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED=true`, all private
+backend credentials, and a 64-character exact model license-evidence digest
+are configured. A flag/digest is **not sufficient legal authorization by
+itself**. The SQL RPC must independently check an actual approved model
+revision, signed owner/editor, approved script, current membership and
+original-key lease; default OmniVoice CC-BY-NC weights remain OFF.
+
+Imports are lazy to avoid loading model or starting workers on Azure host
+indexing. No new billing, public signed audio, auto-publish, file download,
+GPU or model activation occurs in this source PR. The call is synchronous;
+the current PostgREST job claim blocks duplicate uncertain retries, but a
+durable queue/outbox is preferable before production because proxy timeouts
+can outlive the request. Neither the four RPCs (review-only PR #923)
+nor the human plan approval writer are deployed yet.
+
+This PR changes protected root `function_app.py`, so per
+`docs/FEATURE_SELF_MERGE_POLICY_20261031.md`, obtain independent review
+of all JWT/RLS, activation flags, provider network and async timeout gates
+before merging/DEV deployment. Do not bypass by green CI alone. No
+WineShopPOS changes.
+
+Tests: `tests/api/test_feature2_voicestudio_route_review.py` loads
+the exact Azure function definitions in isolation, proves default OFF,
+incomplete/forged flags DENIED, no model initialization or provider egress,
+and boundary status/error hygiene. Hosted two-shop tests require real
+DEV auth/migrations/approved commercial model; source tests are not those.
~~~~

## azure-functions/campaign-api/function_app.py

~~~~diff
@@ -473,3 +473,76 @@ def feature2_collect_india_trends(timer: func.TimerRequest):
         os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"],
     ))
     run_daily_collection(datetime.now(timezone.utc), store)
+
+# VoiceStudio integration route — SOURCE ONLY, independent security review
+# required before merging this root Functions registration or enabling DEV.
+# Default is OFF; no model is downloaded or started during function indexing.
+def build_feature2_voicestudio_api():
+    import re
+    if (
+        os.environ.get("RETAIL_VOICESTUDIO_HTTP_ENABLED") != "true"
+        or os.environ.get("RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED") != "true"
+    ):
+        return None
+    required = (
+        "RETAIL_SUPABASE_URL",
+        "RETAIL_SUPABASE_PUBLISHABLE_KEY",
+        "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
+        "RETAIL_VOICESTUDIO_UPSTREAM_URL",
+        "RETAIL_VOICESTUDIO_UPSTREAM_API_KEY",
+        "RETAIL_VOICESTUDIO_MODEL_LICENSE_EVIDENCE_SHA256",
+    )
+    if not all(os.environ.get(k) for k in required):
+        return None
+    if not re.fullmatch(
+        r"[0-9a-f]{64}", os.environ["RETAIL_VOICESTUDIO_MODEL_LICENSE_EVIDENCE_SHA256"]
+    ):
+        return None
+    # This operator configuration is never a legal licence by itself. The
+    # original-key SQL plan RPC must independently require actual reviewed
+    # model/actor/script evidence and live RLS membership.
+    from feature2_voicestudio_http import VoiceStudioSignedAPI
+    from feature2_voicestudio_sql import VoiceStudioSqlStore
+    from feature2_voicestudio_storage import VoiceStudioPrivateStorage
+
+    origin = os.environ["RETAIL_SUPABASE_URL"]
+    secret = os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]
+    return VoiceStudioSignedAPI(
+        SupabaseJWTVerifier(origin),
+        TenantStore(origin, os.environ["RETAIL_SUPABASE_PUBLISHABLE_KEY"]),
+        lambda verified_actor: VoiceStudioSqlStore(origin, secret, verified_actor),
+        VoiceStudioPrivateStorage(origin, secret),
+        base_url=os.environ["RETAIL_VOICESTUDIO_UPSTREAM_URL"],
+        api_key=os.environ["RETAIL_VOICESTUDIO_UPSTREAM_API_KEY"],
+        enabled=True, commercial_model_verified=True,
+    )
+
+
+@app.route(route="shops/{shop_id}/voicestudio-jobs", methods=["POST"])
+def create_private_voicestudio_job(req: func.HttpRequest) -> func.HttpResponse:
+    # A synchronous source-only handler; no deployed production queue route.
+    # Original request ID is one-shot and must never be blindly retried
+    # after HTTP/SQL/Storage uncertainty.
+    path = "/shops/{shop_id}/voicestudio-jobs"
+    diagnostics = RequestDiagnostics("POST", path)
+    try:
+        handler = build_feature2_voicestudio_api()
+        if handler is None:
+            code, result = 503, {"error": "VOICESTUDIO_DISABLED"}
+        else:
+            try:
+                payload = req.get_json()
+            except ValueError:
+                code, result = 400, {"error": "INVALID_REQUEST"}
+            else:
+                code, result = handler.generate(
+                    req.route_params["shop_id"],
+                    req.headers.get("Authorization", ""),
+                    payload,
+                )
+    except (KeyError, ValueError, TypeError, RuntimeError):
+        code, result = 503, {"error": "VOICE_STUDIO_UNAVAILABLE"}
+    return func.HttpResponse(
+        json.dumps(result), status_code=code, mimetype="application/json",
+        headers=diagnostics.complete(code, result),
+    )
~~~~

## tests/api/test_feature2_voicestudio_route_review.py

~~~~diff
@@ -0,0 +1,143 @@
+"""Review-only root Azure route safety; no live model, JWT or Supabase."""
+import ast
+import json
+import os
+from pathlib import Path
+from types import SimpleNamespace
+
+import pytest
+
+
+ROOT = Path(__file__).resolve().parents[2]
+APP = ROOT / "azure-functions" / "campaign-api" / "function_app.py"
+
+
+def isolated():
+    tree = ast.parse(APP.read_text(encoding="utf-8"))
+    targets = [
+        node for node in tree.body
+        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
+        and node.name in ("build_feature2_voicestudio_api", "create_private_voicestudio_job")
+    ]
+    assert {x.name for x in targets} == {
+        "build_feature2_voicestudio_api", "create_private_voicestudio_job",
+    }
+    assert "shops/{shop_id}/voicestudio-jobs" in APP.read_text(encoding="utf-8")
+    for node in targets:
+        node.decorator_list = []
+    module = ast.fix_missing_locations(ast.Module(body=targets, type_ignores=[]))
+
+    class Response:
+        def __init__(self, text, status_code, mimetype, headers):
+            self.status_code = status_code
+            self.text = text
+            self.mimetype = mimetype
+            self.headers = headers
+
+    class Diagnostics:
+        def __init__(self, *_):
+            pass
+        def complete(self, code, result):
+            return {"X-Synthetic-Result": "safe"}
+
+    namespace = {
+        "os": os, "json": json,
+        "func": SimpleNamespace(HttpRequest=object, HttpResponse=Response),
+        "RequestDiagnostics": Diagnostics,
+    }
+    exec(compile(module, str(APP), "exec"), namespace)
+    return namespace
+
+
+def request(*, payload=None, auth="Bearer fixture", invalid_json=False):
+    def get_json():
+        if invalid_json:
+            raise ValueError("invalid")
+        return payload or {"campaign_id": "not-a-real-campaign", "request_id": "not-a-real-request"}
+    return SimpleNamespace(
+        route_params={"shop_id": "synthetic-shop"},
+        headers={"Authorization": auth},
+        get_json=get_json,
+    )
+
+
+def test_voice_http_route_is_off_with_no_configuration(monkeypatch):
+    monkeypatch.delenv("RETAIL_VOICESTUDIO_HTTP_ENABLED", raising=False)
+    monkeypatch.delenv("RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED", raising=False)
+    namespace = isolated()
+    assert namespace["build_feature2_voicestudio_api"]() is None
+    response = namespace["create_private_voicestudio_job"](request())
+    assert response.status_code == 503
+    assert json.loads(response.text) == {"error": "VOICESTUDIO_DISABLED"}
+
+
+@pytest.mark.parametrize("settings", [
+    {"RETAIL_VOICESTUDIO_HTTP_ENABLED": "true"},
+    {"RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED": "true"},
+    {"RETAIL_VOICESTUDIO_HTTP_ENABLED": "false",
+     "RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED": "true"},
+])
+def test_no_partial_boolean_flag_enables_private_voice(monkeypatch, settings):
+    for key in ("RETAIL_VOICESTUDIO_HTTP_ENABLED",
+                "RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED"):
+        monkeypatch.delenv(key, raising=False)
+    for key, value in settings.items():
+        monkeypatch.setenv(key, value)
+    assert isolated()["build_feature2_voicestudio_api"]() is None
+
+
+def test_missing_real_license_evidence_denies_even_when_flags_set(monkeypatch):
+    for key in ("RETAIL_VOICESTUDIO_HTTP_ENABLED",
+                "RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED"):
+        monkeypatch.setenv(key, "true")
+    for key in ("RETAIL_SUPABASE_URL",
+                "RETAIL_SUPABASE_PUBLISHABLE_KEY",
+                "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
+                "RETAIL_VOICESTUDIO_UPSTREAM_URL",
+                "RETAIL_VOICESTUDIO_UPSTREAM_API_KEY"):
+        monkeypatch.setenv(key, "source-only-not-a-real-credential")
+    monkeypatch.setenv("RETAIL_VOICESTUDIO_MODEL_LICENSE_EVIDENCE_SHA256", "not-a-sha")
+    assert isolated()["build_feature2_voicestudio_api"]() is None
+
+
+def test_route_passes_only_bearer_and_body_to_trusted_api():
+    namespace = isolated()
+    calls = []
+    class Handler:
+        def generate(self, shop, authorization, payload):
+            calls.append((shop, authorization, payload))
+            return 202, {"review_status": "NEEDS_REVIEW", "approved": False}
+    namespace["build_feature2_voicestudio_api"] = lambda: Handler()
+    data = {"campaign_id": "campaign", "request_id": "job"}
+    result = namespace["create_private_voicestudio_job"](
+        request(payload=data, auth="Bearer synthetic-token")
+    )
+    assert result.status_code == 202
+    assert calls == [("synthetic-shop", "Bearer synthetic-token", data)]
+    assert json.loads(result.text)["approved"] is False
+
+
+def test_malformed_body_returns_400_without_job_inference():
+    namespace = isolated()
+    calls = []
+    namespace["build_feature2_voicestudio_api"] = lambda: SimpleNamespace(
+        generate=lambda *args: calls.append(args)
+    )
+    response = namespace["create_private_voicestudio_job"](
+        request(invalid_json=True)
+    )
+    assert response.status_code == 400
+    assert calls == []
+
+
+def test_handler_runtime_failure_is_generic_and_does_not_leak_private_details():
+    """An unexpected one-shot backend failure must not disclose credentials or paths."""
+    namespace = isolated()
+    def fail(*_args):
+        raise RuntimeError("private service key and original WAV path must stay secret")
+    namespace["build_feature2_voicestudio_api"] = lambda: SimpleNamespace(generate=fail)
+    response = namespace["create_private_voicestudio_job"](request())
+    assert response.status_code == 503
+    assert json.loads(response.text) == {"error": "VOICE_STUDIO_UNAVAILABLE"}
+    assert "private service key" not in response.text
+    assert "original WAV path" not in response.text
~~~~

