"""Guard the one-time DEV Flex diagnostics against unsafe scopes or false health claims."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/p1-dev-flex-ingress-correlation-once.yml"
SOURCE = ROOT / "ops/flex_ingress_correlation.py"


def test_exact_protected_one_shot_dev_trigger():
    value = WORKFLOW.read_text()
    for marker in (
        "branches: [main]", "environment: dev",
        "saifsiddiqui59/RetailGrowthAI", "id-token: write",
        "audit(dev): correlate RetailGrowthAI Flex HTTP host and scale",
        "ops/flex_ingress_correlation.py",
    ):
        assert marker in value
    assert "workflow_dispatch" not in value
    assert "schedule:" not in value


def test_scope_telemetry_and_bounded_anonymous_fixed_probes():
    value = SOURCE.read_text()
    for marker in (
        "rg-retailgrowth-dev", "rgai-dev-functions-d4e5ddbd", "rgai-dev-law",
        "centralindia", "RGAI_DEV_EXPECTED_SUBSCRIPTION",
        "functionAppConfig", "scaleAndConcurrency", "instanceMemoryMB",
        "maximumInstanceCount", "alwaysReady", "perInstanceConcurrency",
        "InstanceCount", "Requests", "AlwaysReadyUnits", "CpuPercentage",
        "AverageMemoryWorkingSet", "AppRequests", "AppExceptions", "AppTraces",
        "bin(TimeGenerated,5m)", "urllib.request.urlopen(request, timeout=18)",
        "P0_HTTP_ANOMALIES=", "P0_OBSERVATION_SUCCESS_IS_NOT_HTTP_ACCEPTANCE=true",
    ):
        assert marker in value
    assert 'data=b"{}" if method == "POST" else None' in value
    assert '"X-Request-ID"' in value


def test_no_privileged_mutations_or_raw_logs():
    value = (SOURCE.read_text() + WORKFLOW.read_text()).lower()
    for forbidden in (
        "functionapp restart", "functionapp create", "functionapp delete",
        "functionapp config", "deployment source", "monitor metrics alert create",
        "group create", "storage queue create", "supabase db push",
        "service_role_key", "always-ready set", "static-web-apps-deploy",
        "response.read(", "print(error)", "print(app)", "curl -k",
    ):
        assert forbidden not in value
