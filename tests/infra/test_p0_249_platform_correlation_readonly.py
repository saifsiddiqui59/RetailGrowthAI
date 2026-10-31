"""Security and safety regression for Azure #249 historical causal lookup."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "ops"
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))
spec = importlib.util.spec_from_file_location(
    "p0249_platform_for_tests", OPS / "p0_249_platform_correlation_readonly.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_scope_has_only_fixed_failed_canary_and_postrollback_windows():
    assert module.WINDOWS == (
        ("failed_canary", "2026-10-28T19:35:00Z", "2026-10-28T19:51:00Z"),
        ("post_rollback", "2026-10-28T19:59:00Z", "2026-10-28T20:02:00Z"),
    )
    for _, start, end in module.WINDOWS:
        q = module.queries(start, end)
        assert set(q) == module.STATES
        for label, text in q.items():
            assert "rgai-dev-functions-d4e5ddbd" in text
            assert "TimeGenerated between" in text
            assert "summarize events=count()" in text
            assert ("take 25" if label in ("host_timeline", "request_status_timeline", "startup_401_link") else "take 80") in text
            # Join must project only timestamp + transient host-instance key;
            # never project the original raw log message or URL to output.
            if label == "startup_401_link":
                assert text.count("| project start_time=TimeGenerated, instance") == 1
                assert text.count("| project request_time=TimeGenerated, instance") == 1
                assert "| project Message" not in text
                assert "| project Url" not in text
            else:
                assert "project " not in text
            assert "raw" not in text.lower()
            if label != "activity":
                assert "AppRoleName" in text
    try:
        module.queries("2026-10-27T00:00:00Z", "2026-10-28T22:00:00Z")
        assert False, "Unexpected custom time range accepted"
    except ValueError:
        pass


def test_kusto_classifies_host_specialization_and_worker_errors():
    q = module.queries(*module.WINDOWS[0][1:])
    for group in ("traces", "exceptions", "function_logs"):
        assert 'SpecializeAsync' in q[group]
        assert 'PendingItem.OnTimeout' in q[group]
        assert 'StartStream' in q[group]
        assert 'RpcException' in q[group]
        assert 'Worker process started' in q[group]
        assert '| where category != "other"' in q[group]


def test_sanitization_never_exposes_raw_instance_or_log_message():
    raw = [
        {"bucket": "2026-10-28T19:49:00Z", "category": "worker_startstream",
         "events": 4, "instance": "sensitive-internal-host-instance", "Message": "jwt secret"},
        {"bucket": "2026-10-28T19:49:00+00:00", "status": "503",
         "events": 1, "instance": "sensitive-internal-host-instance", "ResourceId": "private"},
        {"bucket": "2026-10-28T19:40:00Z", "category": "untrusted-secret",
         "events": 8, "instance": "different-instance", "raw": "do not emit"},
        {"bucket": "bad-date", "category": "rpc_exception", "events": 2},
        {"bucket": "2026-10-28T19:40:00Z", "category": "worker_exit",
         "events": -1, "instance": "another-instance"},
    ]
    sanitized = module.safe_rows(raw)
    assert len(sanitized) == 3
    assert sanitized[0]["category"] == "worker_startstream"
    assert sanitized[0]["events"] == 4
    assert sanitized[0]["host_hash"] == sanitized[1]["host_hash"]
    assert sanitized[1]["status"] == "503"
    assert "category" not in sanitized[2]
    assert all("Message" not in item and "instance" not in item for item in sanitized)
    assert "secret" not in repr(sanitized) and "private" not in repr(sanitized)


def test_kusto_aggregate_counts_accept_bounded_decimal_strings():
    rows = [
        {"bucket": "2026-10-28T19:40:00Z", "events": "17",
         "category": "worker_start", "instance": "same-host"},
        {"bucket": "2026-10-28T19:41:00Z", "events": 2.0,
         "category": "grpc_pending_timeout"},
        {"bucket": "2026-10-28T19:42:00Z", "events": "1e5",
         "category": "worker_startstream"},
        {"bucket": "2026-10-28T19:43:00Z", "events": "90000000000000",
         "category": "rpc_exception"},
        {"bucket": "2026-10-28T19:44:00Z", "events": False,
         "category": "worker_exit"},
    ]
    cleaned = module.safe_rows(rows)
    assert len(cleaned) == 2
    assert [r["events"] for r in cleaned] == [17, 2]
    assert all("instance" not in r for r in cleaned)


def test_full_window_timeline_separates_routine_initialization_from_timeouts():
    q = module.queries(*module.WINDOWS[0][1:])["host_timeline"]
    assert "by bucket=bin(TimeGenerated,1m)" in q
    assert "AppRoleInstance" not in q
    assert 'worker_start=countif(' in q
    assert 'host_initialization=countif(' in q
    assert 'grpc_pending_timeout=countif(' in q
    assert 'worker_exit=countif(' in q
    assert 'take 25' in q
    source = module.queries(*module.WINDOWS[0][1:])["traces"]
    assert '"host_initialization"' in source
    assert '"host_error"' not in source
    sample = [
        {"bucket": "2026-10-28T19:40:00Z", "events": "12",
         "worker_start": "4", "host_initialization": "3",
         "grpc_pending_timeout": "0", "worker_exit": 2.0,
         "Message": "untrusted message with sensitive identifiers"},
    ]
    result = module.safe_rows(sample)
    assert result == [{"bucket": "2026-10-28T19:40:00Z", "events": 12,
                       "worker_start": 4, "host_initialization": 3,
                       "grpc_pending_timeout": 0, "worker_exit": 2}]
    assert module._safe_count("-1") is None
    assert module._safe_count(True) is None


def test_http_scale_group_link_is_only_401_evidence_not_a_503_claim():
    q = module.queries(*module.WINDOWS[0][1:])
    request = q["request_status_timeline"]
    assert 'result=="503"' in request and 'result=="401"' in request
    assert 'missing_or_zero=countif(' in request
    assert 'by bucket=bin(TimeGenerated,1m)' in request
    assert 'url' not in request.lower() and 'jwt' not in request.lower()
    link = q["startup_401_link"]
    assert 'let starts = AppTraces' in link
    assert 'let authenticated = AppRequests' in link
    assert 'join kind=leftouter authenticated on instance' in link
    assert 'linked_401=countif(' in link
    assert 'unlinked=countif(' in link
    assert 'ResultCode' in link and '"401"' in link
    assert '"503"' not in link
    # Correlate a startup only with 401 logs on the same instance AFTER
    # startup and within two minutes. A whole-window instance match was a
    # false-positive hint; even this bounded link is NOT request-level proof.
    assert "request_time >= start_time" in link
    assert "request_time <= start_time + 2m" in link
    assert "nearby_401=max(iff(isnotnull(request_time)" in link
    assert "by start_time, instance" in link
    assert "by bucket=bin(start_time,1m)" in link
    assert "app_401=count() by instance" not in link
    assert "| project Message" not in link and "| project Url" not in link
    for _, start, end in module.WINDOWS:
        each_link = module.queries(start, end)["startup_401_link"]
        assert start in each_link and end in each_link
        assert "2026-10-27" not in each_link


def test_safe_http_and_startup_link_counts_no_sensitive_fields():
    raw = [
        {"bucket": "2026-10-28T19:40:00Z", "events": "8",
         "app_401": "3", "reported_503": "0", "missing_or_zero": "5",
         "other_5xx": 0, "url": "https://private/api/shop/jwt"},
        {"bucket": "2026-10-28T19:41:00Z", "events": 4,
         "linked_401": 2, "unlinked": 2, "instance": "raw-host-worker-guid"},
    ]
    out = module.safe_rows(raw)
    assert out[0] == {"bucket": "2026-10-28T19:40:00Z", "events": 8,
                      "app_401": 3, "reported_503": 0,
                      "missing_or_zero": 5, "other_5xx": 0}
    assert out[1]["linked_401"] == 2
    assert out[1]["unlinked"] == 2
    assert "host_hash" in out[1]
    assert "raw-host-worker-guid" not in repr(out)
    assert "private" not in repr(out)



def test_azure_minute_bucket_zero_fraction_is_retained_without_private_suffixes():
    # Azure Log Analytics can serialize bin(TimeGenerated, 1m) with seven
    # zero fractional digits. Previously all such rows were silently dropped.
    accepted = (
        "2026-10-28T19:40:00Z",
        "2026-10-28T19:40:00.0Z",
        "2026-10-28T19:40:00.0000000Z",
        "2026-10-28T19:40:00.0000000+00:00",
        "2026-10-28T20:01:00.000Z",
    )
    for stamp in accepted:
        assert module.safe_rows([{"bucket": stamp, "events": 2}]) == [
            {"bucket": stamp, "events": 2}
        ]
    rejected = (
        "2026-10-28T19:40:00.0000001Z",  # not a whole minute
        "2026-10-28T19:40:00.00000000Z", # overprecise/unreviewed
        "2026-10-28T19:40:00.000Z/private-jwt",
        "2026-10-28T19:40:00.000Z;set-cookie",
        "2026-10-28T19:40:00.000+01:00",
        "2026-10-29T19:40:00.0000000Z",
        "2026-10-28T19:40:01.0000000Z",
    )
    for stamp in rejected:
        assert module.safe_rows([{"bucket": stamp, "events": 2}]) == []



def test_historical_platform_diagnostic_preserves_rows_31_to_80():
    # 80 is the reviewed Kusto query limit, NOT an authority to log raw data.
    rows = [
        {"bucket": "2026-10-28T19:40:00Z", "events": 1,
         "category": "worker_exit" if i == 79 else "worker_start",
         "instance": "private-host-ident-" + str(i),
         "Message": "private token string must never be printed"}
        for i in range(90)
    ]
    for payload in (rows, {"value": rows}):
        raw = module.platform_aggregate_rows(payload)
        assert len(raw) == 80
        assert raw[79]["category"] == "worker_exit"
        assert module.safe_rows(payload)[79]["category"] == "worker_exit"
        assert len(module.safe_rows(payload)) == 80
        assert "private-host-ident" not in str(module.safe_rows(payload))
        assert "private token" not in str(module.safe_rows(payload))
    # Nested table output from Azure CLI is subject to the same 80-row cap.
    payload = {"tables": [
        {"columns": [{"name": name} for name in
                     ("bucket", "events", "category", "instance", "Message")],
         "rows": [[r[name] for name in
                   ("bucket", "events", "category", "instance", "Message")]
                  for r in rows[:65]]},
        {"columns": [{"name": name} for name in
                     ("bucket", "events", "category", "instance", "Message")],
         "rows": [[r[name] for name in
                   ("bucket", "events", "category", "instance", "Message")]
                  for r in rows[65:]]},
    ]}
    assert len(module.platform_aggregate_rows(payload)) == 80
    sanitized = module.safe_rows(payload)
    assert len(sanitized) == 80
    assert sanitized[79]["category"] == "worker_exit"
    assert "instance" not in sanitized[79]
    assert "Message" not in sanitized[79]


def test_historical_decoder_rejects_bad_shapes_and_untrusted_columns():
    assert module.platform_aggregate_rows(None) == []
    assert module.platform_aggregate_rows({"tables": "not a list"}) == []
    assert module.platform_aggregate_rows({"tables": [
        {"columns": [{"name": "events"}, {"name": "events"}],
         "rows": [[1, 2]]},
        {"columns": [{"name": "events"}], "rows": ["not a row"]},
    ]}) == []
    assert module.safe_rows({"value": [
        {"events": 99, "bucket": "untrusted date", "Message": "private"}
    ]}) == []


def test_only_aggregate_read_operations_reachable():
    calls = []
    module.audit_scope = lambda: calls.append("scoped")
    def fake_azure(*args):
        calls.append(args)
        if args[:3] == ("monitor", "log-analytics", "workspace"):
            return {"customerId": "existing-workspace-identifier"}
        if args[:3] == ("monitor", "log-analytics", "query"):
            return [{"bucket": "2026-10-28T19:40:00Z", "events": 2,
                     "category": "grpc_pending_timeout", "instance": "worker-a"}]
        raise AssertionError(f"Unexpected Azure operation: {args}")
    module.azure = fake_azure
    assert module.collect() == 0
    assert calls[0] == "scoped"
    assert len([c for c in calls if isinstance(c, tuple) and c[:3] ==
                ("monitor", "log-analytics", "query")]) == 16
    assert all(c == "scoped" or c[:3] in (
        ("monitor", "log-analytics", "query"),
        ("monitor", "log-analytics", "workspace"),
    ) for c in calls)
