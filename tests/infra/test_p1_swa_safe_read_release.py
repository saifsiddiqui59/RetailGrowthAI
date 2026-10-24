"""Guard single existing-Free-SWA frontend-only release."""
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[2]/".github/workflows/p1-dev-swa-safe-read-release-once.yml"


def test_one_time_dev_only_and_existing_free_swa_only():
    s=SOURCE.read_text()
    for required in (
        "branches: [main]","environment: dev",
        "release(dev): RetailGrowthAI safe GET 503 UX",
        "rg-retailgrowth-dev","retailgrowthai-dev-preview",
        "purple-dune-06b5da200.2.azurestaticapps.net",
        "s['defaultHostname']", "'free'",
        "VITE_CAMPAIGN_GENERATION_MODE: foundry",
        "const READ_TIMEOUT_MS = 12000",
        "const READ_ATTEMPTS = 2",
        "Azure/static-web-apps-deploy@",
        "DEV_SAFE_GET_RETRY_ASSET_LIVE=true",
    ):
        assert required in s,required


def test_no_backend_or_cost_modification():
    s=SOURCE.read_text()
    for forbidden in (
        "az functionapp config appsettings set",
        "az functionapp deployment",
        "az functionapp create",
        "az group create",
        "az staticwebapp create",
        "az monitor log-analytics workspace create",
        "supabase db push",
        "apply_migration",
        "RETAIL_NOTIFICATIONS_ENABLED=true",
        "always-ready set",
    ):
        assert forbidden not in s,forbidden
    assert "id-token: write" in s
    assert "contents: read" in s
    assert "grep -REq 'sb_secret_" in s
