"""The owner-approved existing Free DEV release cannot alter cloud backend/RLS."""
from pathlib import Path
W=Path(__file__).resolve().parents[2]/".github/workflows/p1-dev-reel-read-rls-release-once.yml"
def test_only_exact_main_release_to_existing_tagged_free_dev_swa():
    s=W.read_text(encoding="utf-8")
    for required in (
        "branches: [main]","environment: dev",
        "startsWith(github.event.head_commit.message, 'release(dev): RetailGrowthAI signed Reel reads via tenant RLS')",
        "rg-retailgrowth-dev","retailgrowthai-dev-preview",
        "purple-dune-06b5da200.2.azurestaticapps.net",
        "'free'","frontend","npm test","npm run build",
        "reel-rls-fallback.test.mjs",
        "DEV_PRIVATE_REEL_RLS_READ_FALLBACK_JS_LIVE=true",
        "Private video status is temporarily unavailable. Please retry.",
    ):
        assert required in s,required
    for forbidden in ("az functionapp deployment","az functionapp config",
        "az staticwebapp create","supabase db push",
        "RETAIL_NOTIFICATIONS_ENABLED=true","WineShopPOS","alwaysReady",
        "apply_migration"):
        assert forbidden not in s,forbidden

def test_frontend_only_is_still_authenticated_and_no_unsafe_write_retry():
    s=W.read_text(encoding="utf-8")
    for x in (
        "const attempts = method === 'GET' ? READ_ATTEMPTS : 1",
        "if (error?.status !== 503 || !statusFallback) throw error",
        "const token=await tokenProvider()",
        "'/rest/v1/media_assets?'",
        "'/rest/v1/render_jobs?'",
        "expiresIn:60",
    ):
        assert x in s,x
