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


def test_azure_cli_row_list_is_preserved_only_as_allowlisted_aggregates(monkeypatch, capsys):
    monkeypatch.syspath_prepend(str(ROOT / "ops"))
    import flex_http_transport_correlation as diag
    raw = [{"bucket": "2026-10-25T08:10:00Z", "ResultCode": "401",
            "requests": 3, "p95_ms": 104.25,
            "Message": "SECRET SHOULD NEVER LEAK",
            "url": "https://private.invalid?token=DO_NOT_LOG"}]
    safe = diag.safe_aggregate_rows(raw)
    assert safe == [{"bucket": "2026-10-25T08:10:00Z",
                     "ResultCode": "401", "requests": 3, "p95_ms": 104.25}]
    assert "SECRET" not in repr(safe)

def test_rest_style_table_columns_rows_are_decoded_without_other_fields(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "ops"))
    import flex_http_transport_correlation as diag
    src = {"tables": [{"columns": [{"name": "bucket"}, {"name": "events"},
                                   {"name": "RawPrivateMessage"}],
                       "rows": [["2026-10-25T08:15:00Z", 7, "private body"]]}]}
    assert diag.safe_aggregate_rows(src) == [
        {"bucket": "2026-10-25T08:15:00Z", "events": 7}]

def test_proxy_marker_cannot_certify_original_flex_and_curl_error_is_failure(monkeypatch, capsys):
    monkeypatch.syspath_prepend(str(ROOT / "ops"))
    import flex_http_transport_correlation as diag

    def fake_run(argv, **kwargs):
        header = Path(argv[argv.index("--dump-header") + 1])
        header.write_text(
            "HTTP/1.1 200 Connection established\r\nX-Request-ID: proxy-only\r\n\r\n"
            "HTTP/2 401\r\nContent-Type: application/json\r\n\r\n"
        )
        class Result:
            stdout = "401|0.002|0.011|0.060|0.062|0.080|0.091"
            returncode = 0
        return Result()

    monkeypatch.setattr(diag.subprocess, "run", fake_run)
    assert diag.probe_once("campaign_auth_gate", "/api/campaigns/" + diag.UUID, 401, 1) is True
    output = capsys.readouterr().out
    assert '"app_marker_present":false' in output
    assert '"anomalous":true' in output
    assert "proxy-only" not in output

    def fake_failed(argv, **kwargs):
        header = Path(argv[argv.index("--dump-header") + 1])
        header.write_text("HTTP/2 401\r\nX-Request-ID: handler-only\r\n\r\n")
        class Result:
            stdout = "401|0.002|0.011|0.060|0.062|0.080|0.091"
            returncode = 28
        return Result()
    monkeypatch.setattr(diag.subprocess, "run", fake_failed)
    assert diag.probe_once("campaign_auth_gate", "/api/campaigns/" + diag.UUID, 401, 2) is True
    output = capsys.readouterr().out
    assert '"app_marker_present":true' in output
    assert '"transport":"curl_failure"' in output
    assert '"anomalous":true' in output
    assert "handler-only" not in output


def test_all_telemetry_queries_scope_to_original_flex_and_guard_sparse_percentiles(monkeypatch, capsys):
    monkeypatch.syspath_prepend(str(ROOT / "ops"))
    import flex_http_transport_correlation as diag
    calls = []
    def fake_azure(*args):
        calls.append(args)
        if args[:3] == ("monitor", "log-analytics", "workspace"):
            return {"customerId": "PRIVATE_WORKSPACE"}
        assert args[:3] == ("monitor", "log-analytics", "query")
        return [{"bucket": "2026-11-21T00:00:00Z", "requests": 4,
                 "p95_ms": None, "p99_ms": None, "ResultCode": "401",
                 "Message": "private JWT"}]

    monkeypatch.setattr(diag, "azure", fake_azure)
    diag.log_buckets()
    output = capsys.readouterr().out
    assert "PRIVATE_WORKSPACE" not in output
    assert "private JWT" not in output
    assert len(calls) == 5
    queries = [call[-1] for call in calls[1:]]
    for query in queries[:3]:
        assert diag._APP_FILTER in query
        assert query.startswith(("AppRequests ", "AppTraces ", "FunctionAppLogs "))
        assert query.endswith(" | take 18")
    assert "ResourceGroup =~ 'rg-retailgrowth-dev'" in queries[3]
    assert "endswith '/sites/rgai-dev-functions-d4e5ddbd'" in queries[3]
    assert "_ResourceId has" not in queries[3]
    assert "requests>=20" in queries[0]
    assert "requests>=100" in queries[0]
    assert "percentile(DurationMs,99)" in queries[0]


def test_telemetry_redactor_rejects_untrusted_status_class_time_and_nonfinite_values(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "ops"))
    import flex_http_transport_correlation as diag
    unsafe = [{"bucket": "2026-11-21T00:00:00Z bearer SECRET",
               "ResultCode": "401 SECRET",
               "class": "host_start PRIVATE",
               "Level": "Error;DROP",
               "ActivityStatusValue": "Succeeded LEAK",
               "requests": True,
               "events": -1,
               "p95_ms": float("nan"),
               "p99_ms": float("inf"),
               "UserId": "PRIVATE"}]
    assert diag.safe_aggregate_rows(unsafe) == []
    safe = [{"bucket": "2026-11-21T00:00:00.0000000Z", "ResultCode": "503",
             "p95_ms": 60123.98765, "p99_ms": 61000.12345,
             "class": "worker_exit", "requests": 125,
             "UserId": "PRIVATE"}]
    assert diag.safe_aggregate_rows(safe) == [{
        "bucket": "2026-11-21T00:00:00.0000000Z", "ResultCode": "503",
        "p95_ms": 60123.988, "p99_ms": 61000.123,
        "class": "worker_exit", "requests": 125,
    }]

def test_nonfinite_or_negative_transport_timings_never_certify_health(monkeypatch, capsys):
    monkeypatch.syspath_prepend(str(ROOT / "ops"))
    import flex_http_transport_correlation as diag

    for invalid in ("nan", "inf", "-0.1", "26"):
        def fake_run(argv, **kwargs):
            header = Path(argv[argv.index("--dump-header") + 1])
            header.write_text("HTTP/2 401\\r\\nX-Request-ID: handler-only\\r\\n\\r\\n".replace("\\r", "\r").replace("\\n", "\n"))
            class Result:
                stdout = "401|0.002|0.011|0.060|0.062|0.080|" + invalid
                returncode = 0
            return Result()
        monkeypatch.setattr(diag.subprocess, "run", fake_run)
        assert diag.probe_once("campaign_auth_gate", "/api/campaigns/" + diag.UUID, 401, 1) is True
        output = capsys.readouterr().out
        assert '"transport":"unavailable"' in output
        assert '"anomalous":true' in output
        assert "handler-only" not in output
