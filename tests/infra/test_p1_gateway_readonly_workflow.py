"""Guard one-shot P0 Azure diagnostic workflow against privileged side effects.

Ordinary CI checks the checked-in workflow source WITHOUT accessing Azure.
Actual Azure read-only evidence requires separate protected DEV execution.
"""
from pathlib import Path

WORKFLOW = (Path(__file__).resolve().parents[2] /
            ".github/workflows/p1-dev-gateway-readonly-diagnostics-once.yml")


def test_gate_is_exact_dev_only_and_main_push_only():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "environment: dev" in source
    assert "branches: [main]" in source
    assert "saifsiddiqui59/RetailGrowthAI" in source
    assert "rg-retailgrowth-dev" in source
    assert "rgai-dev-functions-d4e5ddbd" in source
    assert "jeearzffnjbvghwjjjrf.supabase.co" in source
    assert "audit(dev): observe RetailGrowthAI Azure gateway" in source
    assert "cancel-in-progress: false" in source
    assert "id-token: write" in source


def test_queries_are_aggregated_and_no_privileged_operation_is_present():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert source.count("az monitor log-analytics query") == 1
    assert "summarize" in source
    assert "AppRequests" in source and "AppExceptions" in source
    assert "AppDependencies" in source and "AppTraces" in source
    assert 'print("P0_GATEWAY_ANOMALY_OBSERVED="' in source
    blocked = (
        "az functionapp config appsettings set",
        "az functionapp deployment",
        "az functionapp stop",
        "az functionapp start",
        "az group create",
        "az monitor log-analytics workspace create",
        "az monitor app-insights component create",
        "supabase db push",
        "apply_migration",
        "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
        "RETAIL_NOTIFICATIONS_ENABLED=true",
        "github.event.pull_request",
    )
    for forbidden in blocked:
        assert forbidden not in source
    assert "az group show" in source
    assert "az functionapp show" in source
    assert "az functionapp function list" in source
    assert "curl" in source
    assert "No credentials" in source
