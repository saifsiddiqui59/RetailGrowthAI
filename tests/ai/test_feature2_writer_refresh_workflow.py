"""Static invariants for main-only, strictly one-shot Feature2 existing-DEV refresh."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / ".github/workflows/retail-dev-feature2-writer-refresh-once.yml"


def test_refresh_is_only_one_push_and_never_mints_paid_infrastructure():
    text = SOURCE.read_text(encoding="utf-8")
    assert "workflow_dispatch:" not in text and "pull_request:" not in text
    assert "branches: [main]" in text and "paths:" in text
    assert "startsWith(github.event.head_commit.message, 'release(dev): refresh reviewed RetailGrowthAI Feature2 writer')" in text
    assert "environment: dev" in text
    assert "id-token: write" in text and "persist-credentials: false" in text
    assert "rg-retailgrowth-dev" in text
    assert "rgai-dev-functions-d4e5ddbd" in text
    assert "rgaid4e5ddbdf0d21d96" in text
    assert "https://jeearzffnjbvghwjjjrf.supabase.co" in text
    assert "python3 scripts/deploy/package.py --verify-zip" in text
    assert "az functionapp deployment source config-zip" in text
    assert "az functionapp function list" in text
    assert "FEATURE2_SOURCE_REFRESH_DEPLOYMENT=PASS" in text
    for forbidden in ("az group create", "az containerapp", "az vm create",
                      "az functionapp create", "az functionapp config appsettings set",
                      "az storage account create", "supabase db push",
                      "retail-dev-test-accounts-canary-once.yml"):
        assert forbidden not in text


def test_no_additional_paid_models_or_public_credentials():
    text = SOURCE.read_text(encoding="utf-8")
    assert "RETAIL_TRENDS_YOUTUBE_ENABLED" in text
    assert "get_retailer_trends" in text and "create_retailer_trend_draft" in text
    assert "FEATURE2_REFRESH_ANONYMOUS_DENIAL=UNVERIFIED" in text
    assert "no config changed" in text
    assert "secrets.AZURE_SUBSCRIPTION_ID" in text
