"""P0 DEV HTTP timing workflow tests: must never widen access or claim acceptance."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "ops/flex_http_transport_correlation.py"
WF = ROOT / ".github/workflows/p1-dev-flex-http-transport-once.yml"

def test_one_shot_main_protected_dev_only():
    s = WF.read_text()
    for fragment in (
        "branches: [main]", "environment: dev", "id-token: write",
        "github.repository == 'saifsiddiqui59/RetailGrowthAI'",
        "audit(dev): RetailGrowthAI Flex HTTP transport correlation",
        "RGAI_DEV_EXPECTED_SUBSCRIPTION", "ops/flex_http_transport_correlation.py",
    ):
        assert fragment in s
    for prohibited in ("workflow_dispatch", "schedule:", "pull_request_target",
                       "static-web-apps-deploy", "az functionapp config", "az deployment"):
        assert prohibited not in s

def test_safe_get_only_fixed_resource_and_timing():
    s = SRC.read_text()
    for fragment in (
        "from flex_ingress_correlation import", "audit_scope()", "PHASE_FORMAT",
        "time_namelookup", "time_connect", "time_appconnect", "time_starttransfer",
        "time_total", "--max-time", "--connect-timeout", "app_marker_present",
        "P0_READ_ONLY_OBSERVATION_NOT_PROOF_OF_ROOT_CAUSE_OR_FIX",
        "AppRequests", "AppTraces", "FunctionAppLogs", "AzureActivity",
        "rg-retailgrowth-dev", "rgai-dev-functions-d4e5ddbd",
    ):
        assert fragment in s
    for unsafe in ("service_role", "access_token", "--data", "--request",
                   "Authorization:", "--location", "Bearer ", "set always-ready",
                   "az functionapp restart", "functionapp config", "supabase db push",
                   "APPINSIGHTS_INSTRUMENTATIONKEY", "print(result.stderr)",
                   "print(result.stdout)", "headers.read_text()", "WineShopPOS"):
        assert unsafe not in s
    assert "HOST + path" in s

def test_transport_phases_without_header_contents(monkeypatch, capsys):
    monkeypatch.syspath_prepend(str(ROOT / "ops"))
    import flex_http_transport_correlation as diag

    def run_ok(argv, **kwargs):
        assert argv[0] == "curl"
        assert "--max-time" in argv and "--noproxy" in argv
        assert "Authorization:" not in " ".join(argv)
        header = Path(argv[argv.index("--dump-header")+1])
        header.write_text("HTTP/1.1 401 Unauthorized\nX-Request-ID: confidential-marker\n")
        class Result:
            stdout = "401|0.003|0.020|0.080|0.082|0.110|0.112"
            returncode = 0
        return Result()

    monkeypatch.setattr(diag.subprocess, "run", run_ok)
    assert diag.probe_once("campaign_auth_gate", "/api/campaigns/" + diag.UUID, 401, 1) is False
    output = capsys.readouterr().out
    assert '"status":401' in output
    assert '"app_marker_present":true' in output
    assert '"tls_s":0.08' in output
    assert "confidential-marker" not in output

def test_transport_timeout_not_mislabeled_http503(monkeypatch, capsys):
    monkeypatch.syspath_prepend(str(ROOT / "ops"))
    import flex_http_transport_correlation as diag
    def no_response(argv, **kwargs):
        class Result:
            stdout = "000|0.002|0.011|0.060|0.062|0.000|20.000"
            returncode = 28
        return Result()
    monkeypatch.setattr(diag.subprocess, "run", no_response)
    assert diag.probe_once("unknown_route", "/api/p0-route-that-does-not-exist", 404, 2)
    output = capsys.readouterr().out
    assert '"status":0' in output and '"transport":"curl_failure"' in output
    assert '"anomalous":true' in output
