"""Zero-cost hosted smoke is a real signed JWT probe, not a paid bypass."""
import runpy
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT / "scripts/ops/feature2_free_signed_dev_canary.py"
WORKFLOW=ROOT / ".github/workflows/retail-dev-feature2-free-hosted-smoke.yml"

def test_original_synthetic_png_is_valid_and_not_a_licensed_external_photo():
    scope=runpy.run_path(str(SCRIPT))
    data=scope["png"]()
    assert data[:8]==b"\x89PNG\r\n\x1a\n"
    assert 100<len(data)<100000

def test_one_time_hosted_smoke_cannot_run_without_exact_operator_gate(monkeypatch):
    scope=runpy.run_path(str(SCRIPT))
    monkeypatch.delenv("RGAI_F2_FREE_DEV_ONCE",raising=False)
    with pytest.raises(RuntimeError,match="authorization"):
        scope["main"]()

def test_protected_workflow_has_no_azure_paid_inference_or_unprotected_pr():
    a=SCRIPT.read_text()
    w=WORKFLOW.read_text()
    assert "environment: dev" in w
    assert "github.ref == 'refs/heads/main'" in w
    assert "approval_code == 'AUTHORIZED_FEATURE2_DEV_FREE_MEDIA_NOT_AI'" in w
    assert "RETAIL_SUPABASE_SERVICE_ROLE_KEY" in w
    assert "workflow_dispatch:" in w
    assert "AzureFeature2PromptLLM" not in a
    assert "AzureFeature2ContentLLM" not in a
    assert "shop_ai_budget_controls" in a and '"enabled"] is False' in a
    assert "register_uploaded_image" in a
    assert "trend-recommendations" in a and "content-drafts" in a
    assert "NOT_AVAILABLE_FAIL_CLOSED" in a
    assert "TEST FIXTURE" in a
    assert "finally:" in a and "TEST_MEMBERSHIP_REVOKED" in a
    assert "RETAIL_FEATURE2_REAL_AI_ENABLED" not in w

def test_recover_existing_synthetic_media_only_with_exact_preflight():
    src=SCRIPT.read_text()
    assert 'len(existing)<=1' in src
    assert 'existing[0]["created_by"]==uid' in src
    assert 'existing[0]["object_path"]==PATH' in src
    assert 'existing[0]["mime_type"]=="image/png"' in src
    assert 'verify_existing_image(pub,token,image)' in src
    assert 'Previously registered private synthetic image unreadable' in src
    assert 'shop_content_drafts?select=id' in src
    assert 'FEATURE2_HOSTED_SIGNED_EXISTING_ORIGINAL_IMAGE_READBACK=PASS' in src


def test_safe_get_retries_only_503_no_post_or_unbounded_loop():
    probe=runpy.run_path(str(SCRIPT))["read_verified_trends"]
    retries=[]
    def temporary_503(url, *, apikey, bearer):
        retries.append(url)
        if len(retries)==1:
            raise RuntimeError("DEV endpoint returned 503 [GATEWAY_OR_UNKNOWN] for GET AZURE_API/path")
        return {"shop_id":"safe","recommendations":[]}
    probe.__globals__["request"]=temporary_503
    response=probe("https://rgai-dev-functions-d4e5ddbd.azurewebsites.net/api/shops/safe",
                   apikey="TEST_PUBLISHABLE",token="SIGNED_TEST",sleep=lambda seconds: None)
    assert response["shop_id"]=="safe"
    assert len(retries)==2
    assert all(url.endswith("/trend-recommendations") for url in retries)


def test_non_503_or_repeat_failure_does_not_mutate_or_continue():
    probe=runpy.run_path(str(SCRIPT))["read_verified_trends"]
    attempts=[]
    def denied(url, **kwargs):
        attempts.append(url)
        raise RuntimeError("DEV endpoint returned 403 [GATEWAY_OR_UNKNOWN] for GET")
    probe.__globals__["request"]=denied
    with pytest.raises(RuntimeError,match="403"):
        probe("https://dev.example.invalid",apikey="TEST",token="TEST",sleep=lambda _:None)
    assert len(attempts)==1
    attempts.clear()
    def outage(url, **kwargs):
        attempts.append(url)
        raise RuntimeError("DEV endpoint returned 503 [TREND_STORAGE_UNAVAILABLE] for GET")
    probe.__globals__["request"]=outage
    with pytest.raises(RuntimeError,match="503"):
        probe("https://dev.example.invalid",apikey="TEST",token="TEST",sleep=lambda _:None)
    assert len(attempts)==3

def test_ambiguous_membership_restore_still_arms_cleanup_first():
    source=SCRIPT.read_text()
    patch='updated=request(membership_url,method="PATCH",apikey=service,obj={"active":True})'
    arm='active=True'
    ensure='ensure(len(updated)==1 and updated[0]["active"] is True'
    assert source.index('    try:\n        # A lost PATCH acknowledgement') < source.index(arm,source.index('    try:\n        # A lost PATCH acknowledgement')) < source.index(patch)
    assert source.index(patch) < source.index(ensure)
    assert 'request(membership_url,method="PATCH",apikey=service,obj={"active":False})' in source


def test_absent_real_clothing_trend_skips_post_without_pretending_hosted_draft_saved():
    source=SCRIPT.read_text()
    start=source.index('        if not candidates:')
    end=source.index('        trend=candidates[0]',start)
    guard=source[start:end]
    assert 'FEATURE2_HOSTED_REAL_FASHION_TREND=NOT_AVAILABLE_FAIL_CLOSED' in guard
    assert 'FEATURE2_HOSTED_DRAFT_SAVE=BLOCKED_NO_RELEVANT_LIVE_TREND' in guard
    assert 'FEATURE2_HOSTED_UNVERIFIED_TREND_POST=SKIPPED_NO_FABRICATED_ID' in guard
    assert 'request(' not in guard
    assert 'return' in guard
    # Real positive branch remains present; a future source-backed fashion
    # recommendation is still required for signed DRAFT POST/GET.
    assert 'trend=candidates[0]' in source
    assert 'FEATURE2_HOSTED_REAL_TREND_SIGNED_DRAFT_SAVE_READBACK=PASS' in source
