"""Review-only root Azure route safety; no live model, JWT or Supabase."""
import ast
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "azure-functions" / "campaign-api" / "function_app.py"


def isolated():
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    targets = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in ("build_feature2_voicestudio_api", "create_private_voicestudio_job")
    ]
    assert {x.name for x in targets} == {
        "build_feature2_voicestudio_api", "create_private_voicestudio_job",
    }
    assert "shops/{shop_id}/voicestudio-jobs" in APP.read_text(encoding="utf-8")
    for node in targets:
        node.decorator_list = []
    module = ast.fix_missing_locations(ast.Module(body=targets, type_ignores=[]))

    class Response:
        def __init__(self, text, status_code, mimetype, headers):
            self.status_code = status_code
            self.text = text
            self.mimetype = mimetype
            self.headers = headers

    class Diagnostics:
        def __init__(self, *_):
            pass
        def complete(self, code, result):
            return {"X-Synthetic-Result": "safe"}

    namespace = {
        "os": os, "json": json,
        "func": SimpleNamespace(HttpRequest=object, HttpResponse=Response),
        "RequestDiagnostics": Diagnostics,
    }
    exec(compile(module, str(APP), "exec"), namespace)
    return namespace


def request(*, payload=None, auth="Bearer fixture", invalid_json=False):
    def get_json():
        if invalid_json:
            raise ValueError("invalid")
        return payload or {"campaign_id": "not-a-real-campaign", "request_id": "not-a-real-request"}
    return SimpleNamespace(
        route_params={"shop_id": "synthetic-shop"},
        headers={"Authorization": auth},
        get_json=get_json,
    )


def test_voice_http_route_is_off_with_no_configuration(monkeypatch):
    monkeypatch.delenv("RETAIL_VOICESTUDIO_HTTP_ENABLED", raising=False)
    monkeypatch.delenv("RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED", raising=False)
    namespace = isolated()
    assert namespace["build_feature2_voicestudio_api"]() is None
    response = namespace["create_private_voicestudio_job"](request())
    assert response.status_code == 503
    assert json.loads(response.text) == {"error": "VOICESTUDIO_DISABLED"}


@pytest.mark.parametrize("settings", [
    {"RETAIL_VOICESTUDIO_HTTP_ENABLED": "true"},
    {"RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED": "true"},
    {"RETAIL_VOICESTUDIO_HTTP_ENABLED": "false",
     "RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED": "true"},
])
def test_no_partial_boolean_flag_enables_private_voice(monkeypatch, settings):
    for key in ("RETAIL_VOICESTUDIO_HTTP_ENABLED",
                "RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED"):
        monkeypatch.delenv(key, raising=False)
    for key, value in settings.items():
        monkeypatch.setenv(key, value)
    assert isolated()["build_feature2_voicestudio_api"]() is None


def test_missing_real_license_evidence_denies_even_when_flags_set(monkeypatch):
    for key in ("RETAIL_VOICESTUDIO_HTTP_ENABLED",
                "RETAIL_VOICESTUDIO_COMMERCIAL_MODEL_APPROVED"):
        monkeypatch.setenv(key, "true")
    for key in ("RETAIL_SUPABASE_URL",
                "RETAIL_SUPABASE_PUBLISHABLE_KEY",
                "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
                "RETAIL_VOICESTUDIO_UPSTREAM_URL",
                "RETAIL_VOICESTUDIO_UPSTREAM_API_KEY"):
        monkeypatch.setenv(key, "source-only-not-a-real-credential")
    monkeypatch.setenv("RETAIL_VOICESTUDIO_MODEL_LICENSE_EVIDENCE_SHA256", "not-a-sha")
    assert isolated()["build_feature2_voicestudio_api"]() is None


def test_route_passes_only_bearer_and_body_to_trusted_api():
    namespace = isolated()
    calls = []
    class Handler:
        def generate(self, shop, authorization, payload):
            calls.append((shop, authorization, payload))
            return 202, {"review_status": "NEEDS_REVIEW", "approved": False}
    namespace["build_feature2_voicestudio_api"] = lambda: Handler()
    data = {"campaign_id": "campaign", "request_id": "job"}
    result = namespace["create_private_voicestudio_job"](
        request(payload=data, auth="Bearer synthetic-token")
    )
    assert result.status_code == 202
    assert calls == [("synthetic-shop", "Bearer synthetic-token", data)]
    assert json.loads(result.text)["approved"] is False


def test_malformed_body_returns_400_without_job_inference():
    namespace = isolated()
    calls = []
    namespace["build_feature2_voicestudio_api"] = lambda: SimpleNamespace(
        generate=lambda *args: calls.append(args)
    )
    response = namespace["create_private_voicestudio_job"](
        request(invalid_json=True)
    )
    assert response.status_code == 400
    assert calls == []
