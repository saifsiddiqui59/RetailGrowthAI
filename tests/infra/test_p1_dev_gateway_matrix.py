"""Fail closed if DEV gateway diagnostics change production resources."""
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[2] /
          ".github/workflows/p1-dev-get-503-route-matrix-once.yml")


def test_protected_main_only_exact_resource_scope():
    text=SOURCE.read_text()
    for marker in (
        "branches: [main]", "environment: dev",
        "saifsiddiqui59/RetailGrowthAI", "rg-retailgrowth-dev",
        "rgai-dev-functions-d4e5ddbd", "rgai-dev-law",
        "audit(dev): isolate RetailGrowthAI HTTP GET 503",
        "P0_MATRIX_DEV_SCOPE_VERIFIED=true",
        "P0_MATRIX_HTTP_FUNCTIONS_INDEXED=true",
        "cancel-in-progress: false",
        "id-token: write",
    ):
        assert marker in text


def test_method_matrix_records_real_gateway_status_and_handler_header():
    text=SOURCE.read_text()
    assert "P0_MATRIX_ANOMALY_COUNT=" in text
    assert "x-request-id:" in text
    assert "time_starttransfer" in text
    assert "P0_SAFE_AGGREGATE_" in text
    for path in ("/api/campaigns","/api/poster-drafts/","/api/poster-jobs/",
                 "/api/render-jobs/","/api/p0-route-that-does-not-exist"):
        assert path in text


def test_no_writes_or_secrets_or_automatic_customer_account_canary():
    text=SOURCE.read_text()
    for forbidden in ("config appsettings set", "deployment source config-zip",
                      "az functionapp restart", "az functionapp create",
                      "az monitor log-analytics workspace create",
                      "az storage queue create", "supabase db push", "apply_migration",
                      "RETAIL_SUPABASE_SERVICE_ROLE_KEY", "RGAI_DEV_SERVICE_KEY",
                      "authorization: bearer", "retail-dev-test-accounts-canary-once.yml",
                      "workflow_dispatch", "always-ready set"):
        assert forbidden not in text
    assert "P0_RAW_LOGS_TENANT_IDS_JWT_PAYLOADS_NOT_QUERIED=true" in text
