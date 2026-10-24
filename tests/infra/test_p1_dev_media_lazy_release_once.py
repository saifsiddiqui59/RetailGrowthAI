"""Protected DEV Functions code-only release must not mutate infra/config.

The live workflow is main-only and explicitly approval/commit gated. Ordinary
PR checks do not receive Azure identities, backend keys or DEV privileges.
"""
from pathlib import Path

SOURCE=(Path(__file__).resolve().parents[2]/
        ".github/workflows/p1-dev-media-lazy-release-once.yml")


def test_exact_retali_growth_dev_and_single_released_app():
    s=SOURCE.read_text(encoding="utf-8")
    for snippet in (
        "branches: [main]","environment: dev","RG: rg-retailgrowth-dev",
        "APP: rgai-dev-functions-d4e5ddbd","STORAGE: rgaid4e5ddbdf0d21d96",
        "jeearzffnjbvghwjjjrf.supabase.co",
        "release(dev): RetailGrowthAI P1 lazy media import",
        "az functionapp deployment source config-zip",
        "python3 scripts/deploy/package.py --verify-zip",
        "mwader/static-ffmpeg@sha256:",
        "SAFE_BACKEND_FLAGS_UNCHANGED=true",
        "SAFE_INDEXED_COUNT=",
        "AFTER_DEPLOY_ALL_THREE_AUTH_GATES_401_WITHIN_10S=true",
    ):
        assert snippet in s,snippet


def test_no_new_infra_cost_or_secret_or_db_writes_are_possible_in_release():
    s=SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "az group create", "az functionapp create",
        "az functionapp config appsettings set",
        "az functionapp plan create",
        "az storage account create",
        "az storage queue create",
        "always-ready", "alwaysReady",
        "az monitor log-analytics workspace create",
        "supabase db push", "apply_migration",
        "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
        "AzureWebJobs.render_campaign_poster.Disabled=true",
        "RETAIL_NOTIFICATIONS_ENABLED=true",
        "WineShopPOS",
    ):
        assert forbidden not in s,forbidden
    assert "RETAIL_NOTIFICATIONS_ENABLED" in s
    assert "RETAIL_ENABLE_POSTER_RENDERING" in s
    assert "RETAIL_ENABLE_POSTER_DRAFTS" in s
    assert "cancel-in-progress: false" in s
