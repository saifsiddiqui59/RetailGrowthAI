"""Owner-triggered cloud Reel workflow is one-time, gated, and cleanup-bound."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/p1-dev-owner-cloud-reel-acceptance-once.yml"

def test_only_exact_owner_gate_can_execute_user_creating_job():
    s=WF.read_text(encoding="utf-8")
    for x in ("branches: [main]", "environment: dev",
              "github.repository == 'saifsiddiqui59/RetailGrowthAI'",
              "test(dev): owner approves one REAL RetailGrowthAI cloud Reel acceptance",
              "RGAI_DEV_PLAYWRIGHT_UPLOAD: '1'",
              "RGAI_DEV_CANARY_APPROVAL: AUTHORIZED_RETAILGROWTHAI_DEV_ONLY",
              "preflight_dev_http_auth_routes()",
              "ONE_SHOT_DEV_GATEWAY_BEFORE_FIXTURES_PASSED=true",
              "rgai-dev-live-canary",
              "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
              "CANARY_TEMP_FIXTURES_CLEANUP=",
              "retailgrowthai-real-dev-cloud-30s-reel-owner-accepted"):
        assert x in s,x

def test_no_root_gate_bypass_or_prod_or_wineshop_or_paid_deployment():
    s=WF.read_text(encoding="utf-8")
    for forbidden in ("onboarding_gate set", "enforce_approval=false",
                      "az functionapp deployment", "az staticwebapp create",
                      "supabase db push", "apply_migration",
                      "WineShopPOS", "RETAIL_NOTIFICATIONS_ENABLED=true",
                      "wan_video", "always-ready"):
        assert forbidden not in s,forbidden
    assert "python3 -u tests/e2e/retail_dev_canary_once.py" in s
    assert "if-no-files-found: warn" in s
