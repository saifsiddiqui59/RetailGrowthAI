"""Prompt-only hosted canary: offline contract tests, no cloud credentials required."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[2]
mod = runpy.run_path(str(ROOT / "tests/e2e/feature2_dev_live_canary.py"))

SHOP = "aa000000-0000-4000-8000-000000000021"
OTHER = "aa000000-0000-4000-8000-000000000022"
OWNER = "aa000000-0000-4000-8000-000000000023"
OUTSIDER = "aa000000-0000-4000-8000-000000000024"
ORIGINAL = "Create seven days of clothing styling ideas for my shop."
FORMATS = ["instagram_caption", "facebook_post", "linkedin_post",
           "youtube_shorts_description", "poster_brief", "reel_storyboard"]


def valid_result():
    return {
        "shop_id": SHOP, "original_prompt": ORIGINAL,
        "improved_prompt": "Only the original intent: " + ORIGINAL,
        "output_formats": FORMATS, "language": "en-IN",
        "review_status": "NEEDS_REVIEW", "provider_mode": "deterministic",
        "can_publish": False,
        "business_context_used": {
            "business_name": "RetailGrowthAI Test a", "city": "Nagpur",
            "products": [], "industry": "clothing",
        },
        "improvement_suggestions": ["Use authorized business context"],
        "usage": {"paid_inference_calls": 0, "estimated_paid_cost_usd": 0,
                  "provider": "local_templates"},
    }


def validate(obj):
    return mod["validated_prompt_preview"](
        obj, shop_id=SHOP, original_prompt=ORIGINAL, output_formats=FORMATS,
    )


def test_verified_nonpublishable_default_never_claims_paid_ai():
    assert validate(valid_result())["usage"]["paid_inference_calls"] == 0


@pytest.mark.parametrize("key,value", [
    ("shop_id", OTHER), ("original_prompt", "Different customer intent"),
    ("improved_prompt", "Deleted original user request"),
    ("output_formats", ["facebook_post"]), ("language", "mr-IN"),
    ("review_status", "APPROVED"), ("provider_mode", "approved_llm"),
    ("can_publish", True),
    ("business_context_used", {"city": "Mumbai", "business_name": "Imposter", "products": []}),
    ("improvement_suggestions", []),
    ("usage", {"paid_inference_calls": 1, "estimated_paid_cost_usd": 0.05,
               "provider": "approved_injected_llm"}),
])
def test_mismatched_tenant_intent_review_paid_calls_fail_closed(key, value):
    result = valid_result()
    result[key] = value
    with pytest.raises(RuntimeError):
        validate(result)


def test_rejects_unverified_products_and_excessive_prompt():
    result = valid_result()
    result["business_context_used"]["products"] = ["imaginary cotton sari"]
    with pytest.raises(RuntimeError):
        validate(result)
    result = valid_result()
    result["improved_prompt"] = ORIGINAL + " " + "x" * 1500
    with pytest.raises(RuntimeError):
        validate(result)


def test_signed_owner_viewer_editor_and_no_media_trend_or_draft():
    calls = []
    role = "NONMEMBER"

    def gateway(url, *, method="GET", payload=None, headers=None, expect=(200,), timeout=None):
        nonlocal role
        calls.append((url, method, deepcopy(payload), deepcopy(headers), expect))
        token = (headers or {}).get("Authorization", "")
        owner = token == "Bearer owner-token"
        outsider = token == "Bearer outsider-token"
        if "/rest/v1/business_profiles?" in url and method == "PATCH":
            assert owner and payload["category"] == "clothing"
            assert payload["city"] == "Nagpur"
            return 200, [{"shop_id": SHOP,
                          "business_name": "RetailGrowthAI Test a", "city": "Nagpur"}]
        if url.endswith("/improve-prompt"):
            assert method == "POST"
            if not owner and not outsider: return 401, {"error": "UNAUTHORIZED"}
            if outsider and role != "EDITOR": return 403, {"error": "FORBIDDEN"}
            if set(payload) != {"original_prompt", "language", "output_formats"}:
                return 400, {"error": "INVALID_REQUEST"}
            return 200, valid_result()
        if url.endswith("/content-drafts"):
            assert owner and method == "GET"
            return 200, {"shop_id": SHOP, "drafts": []}
        if url.endswith("/rest/v1/shop_memberships") and method == "POST":
            assert owner and payload["role"] == "VIEWER" and payload["user_id"] == OUTSIDER
            role = "VIEWER"
            return 201, [{"shop_id": SHOP, "user_id": OUTSIDER, "role": role}]
        if "/rest/v1/shop_memberships?" in url and method == "PATCH":
            assert owner and payload == {"role": "EDITOR"} and role == "VIEWER"
            assert "shop_id=eq."+SHOP in url and "user_id=eq."+OUTSIDER in url
            role = "EDITOR"
            return 200, [{"shop_id": SHOP, "user_id": OUTSIDER, "role": role}]
        raise AssertionError("unexpected canary call " + url)

    mod["run_live_feature2_prompt"](
        gateway, api="https://api.retailgrowth.test",
        supabase="https://supabase.retailgrowth.test",
        owner={"Authorization": "Bearer owner-token"},
        outsider={"Authorization": "Bearer outsider-token"},
        shops=[SHOP, OTHER],
        accounts=[(OWNER, {}), (OUTSIDER, {})],
    )
    assert role == "EDITOR"
    assert sum(url.endswith("/content-drafts") for url, *_ in calls) == 2
    assert all(method != "POST" for url, method, *_ in calls if url.endswith("/content-drafts"))
    assert not any("trend-recommendations" in url or "trend_snapshots" in url
                   or "storage" in url or "/campaigns" in url for url, *_ in calls)
    assert sum(url.endswith("/improve-prompt") and method == "POST"
               for url, method, *_ in calls) == 7


def test_protected_workflow_exposes_only_manual_no_gpu_prompt_canary():
    workflow = (ROOT / ".github/workflows/retail-dev-test-accounts-canary-once.yml").read_text()
    runner = (ROOT / "tests/e2e/retail_dev_canary_once.py").read_text()
    assert "workflow_dispatch:" in workflow
    assert "environment: dev" in workflow
    assert "inputs.approval_code == 'AUTHORIZED_RETAILGROWTHAI_DEV_ONLY'" in workflow
    assert "RGAI_DEV_FEATURE2_PROMPT_CANARY:" in workflow
    assert "          - feature2-prompt" in workflow
    assert "FEATURE2_PROMPT_ONLY=NO_FFMPEG_INSTALL_NO_VIDEO" in workflow
    assert "if prompt_only:" in runner
    assert "run_live_feature2_prompt" in runner
    assert "return  # Existing exact test-owned cleanup in finally." in runner
    assert "if full_feature2 or prompt_only:" in runner
    assert "shops.append(sid)" in runner and "finally:" in runner
    assert "if full_feature2:" in runner
    assert "preflight_live_source" in runner
    assert "preflight_dev_http_auth_routes(include_prompt=prompt_only)" in runner


def test_prompt_gateway_anonymous_preflight_runs_before_any_fixture():
    runner = runpy.run_path(str(ROOT / "tests/e2e/retail_dev_canary_once.py"))
    import urllib.error
    from email.message import Message
    from io import BytesIO

    calls = []
    headers = Message()
    headers["X-Request-ID"] = "test-request-id"

    def send(req, timeout):
        calls.append((req.get_method(), req.full_url, timeout))
        raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", headers, BytesIO(b""))

    step = iter(range(20))
    runner["preflight_dev_http_auth_routes"](
        transport=send, clock=lambda: next(step),
        include_prompt=True,
    )
    assert len(calls) == 5
    assert calls[-1][0] == "POST" and calls[-1][1].endswith("/improve-prompt")
    assert all("/auth/v1/admin/users" not in url for _, url, _ in calls)


def test_prompt_no_account_creation_when_anonymous_preflight_fails():
    runner = runpy.run_path(str(ROOT / "tests/e2e/retail_dev_canary_once.py"))
    from email.message import Message
    import urllib.error

    headers = Message()
    headers["X-Request-ID"] = "test-request-id"
    def send(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 503, "Service unavailable", headers, None)
    with pytest.raises(RuntimeError, match="DEV gateway preflight failed"):
        runner["preflight_dev_http_auth_routes"](
            transport=send, clock=lambda: 0.0, include_prompt=True,
        )
