"""Safeguards against widening the P0 DEV health diagnostic scope."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "ops/p1_dev_resource_health_once.py"
WF = ROOT / ".github/workflows/p1-dev-resource-health-once.yml"

def test_oidc_workflow_is_exact_one_shot_main():
    data = WF.read_text()
    for item in ("branches: [main]", "environment: dev", "id-token: write",
                 "github.repository == 'saifsiddiqui59/RetailGrowthAI'",
                 "audit(dev): RetailGrowthAI resource health",
                 "RGAI_DEV_EXPECTED_SUBSCRIPTION",
                 "ops/p1_dev_resource_health_once.py"):
        assert item in data
    for item in ("workflow_dispatch:", "schedule:", "pull_request_target:",
                 "azure/webapps-deploy", "az deployment", "az functionapp restart"):
        assert item not in data

def test_readonly_azure_paths_and_no_raw_secret_logging():
    data = SRC.read_text()
    for item in ("audit_scope()", "Microsoft.ResourceHealth",
                 "availabilityStatuses/current", "events?api-version=",
                 '"--method", "get"', "RGAI_DEV_EXPECTED_SUBSCRIPTION",
                 "P0_READ_ONLY_NO_PROVISION_OR_COST_CHANGE"):
        # Protected variable is wired through the workflow.
        assert item in data or item in WF.read_text()
    for item in ("--method post", "Authorization:", "Bearer ",
                 "print(result)", "print(result.stdout)", "print(result.stderr)",
                 "service_role", "az deployment", "functionapp config set",
                 "WineShopPOS", "az rest --method post"):
        assert item not in data

def test_resource_identity_and_redacted_health(monkeypatch, capsys):
    import sys
    monkeypatch.syspath_prepend(str(ROOT / "ops"))
    import p1_dev_resource_health_once as health
    appid = ("/subscriptions/AAAA/resourceGroups/rg-retailgrowth-dev/"
             "providers/Microsoft.Web/sites/rgai-dev-functions-d4e5ddbd")
    health._fixed_resource_id(appid, "AAAA")
    import pytest
    with pytest.raises(RuntimeError):
        health._fixed_resource_id(appid.replace("rg-retailgrowth-dev", "prod"), "AAAA")
    with pytest.raises(RuntimeError):
        health._fixed_resource_id(appid, "BBBB")
    calls = []
    def fake_get(url):
        calls.append(url)
        if "availabilityStatuses" in url:
            return {"properties":{"availabilityState":"Degraded", "reason":"PRIVATE-URL"}}
        return {"value":[
            {"properties":{"status":"Active","impact":[{"impactedRegions":[{"impactedRegion":"Central India"}]}],
                           "title":"SECRET-INCIDENT"}},
            {"properties":{"status":"Resolved","impact":[]}},
            {"properties":{"status":"Active","impact":[]}}
        ], "nextLink":"private-link"}
    monkeypatch.setattr(health, "_get", fake_get)
    health._health(appid)
    health._events("RESOURCE_EVENTS","https://management.azure.com/subscriptions/AAAA/providers/Microsoft.ResourceHealth/events?api-version=2025-05-01")
    s = capsys.readouterr().out
    assert "P0_RESOURCE_HEALTH_STATUS=Degraded" in s
    assert '"active_central_india_impact_first_page":1' in s
    assert '"active_without_region_first_page":1' in s
    assert '"next_page_exists":true' in s
    assert "SECRET-" not in s and "AAAA" not in s and "private-link" not in s

def test_disallow_non_read_health_url(monkeypatch):
    import pytest
    monkeypatch.syspath_prepend(str(ROOT / "ops"))
    import p1_dev_resource_health_once as health
    with pytest.raises(RuntimeError):
        health._get("https://management.azure.com/subscriptions/AAAA/providers/Microsoft.Web/sites/foo?api-version=2025-05-01")
    with pytest.raises(RuntimeError):
        health._get("https://evil.example/subscriptions/AAAA/providers/Microsoft.ResourceHealth/events?api-version=2025-05-01")
