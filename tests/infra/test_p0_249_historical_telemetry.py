"""No Azure access: verify #249 fixed-window and no-PII aggregation contract."""
import importlib.util
from pathlib import Path
import sys

FILE = Path(__file__).resolve().parents[2] / "ops" / "p0_249_historical_telemetry.py"
sys.path.insert(0, str(FILE.parent))
spec = importlib.util.spec_from_file_location("p0249_telemetry", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_fixed_original_flex_scope_and_windows_only():
    assert mod.APP == "rgai-dev-functions-d4e5ddbd"
    assert mod.RG == "rg-retailgrowth-dev"
    assert len(mod.WINDOWS) == 3
    try:
        mod.build_queries("2026-10-28T00:00:00Z", "2026-10-29T00:00:00Z")
    except ValueError:
        pass
    else:
        raise AssertionError("unreviewed window allowed")
    for _, begin, end in mod.WINDOWS:
        assert begin.startswith("2026-10-28T")
        assert begin < end
        for label, query in mod.build_queries(begin, end):
            assert "TimeGenerated between" in query
            assert label in ("requests", "worker_traces", "exceptions", "dependencies", "activity")
            assert "rgai-dev-functions-d4e5ddbd" in query


def test_azure_cli_list_and_table_output_both_sanitize():
    rows = [{"bucket":"2026-10-28T10:27:00Z", "events":2, "status":"503",
             "RequestUri":"https://secret", "Message":"SECRET", "OperationId":"TOKEN",
             "category":"worker_exit"}]
    expected = [{"bucket":"2026-10-28T10:27:00Z", "events":2,
                 "status":"503", "category":"worker_exit"}]
    assert mod.safe_aggregate_rows(rows) == expected
    assert mod.safe_aggregate_rows({"value":rows}) == expected
    table = {"tables":[{"columns":[{"name":x} for x in rows[0]],
                        "rows":[list(rows[0].values())]}]}
    assert mod.safe_aggregate_rows(table) == expected
    assert mod.safe_aggregate_rows([]) == []


def test_reject_dynamic_status_category_and_unknown_sensitive_fields():
    data = [{"bucket":"2026-10-27T00:00:00Z",
             "status":"user@example.com", "category":"customer payload",
             "events":3, "token":"SECRET", "p95_ms":61000.0}]
    assert mod.safe_aggregate_rows(data) == [{"events":3, "p95_ms":61000.0}]


def test_dependency_success_and_numeric_telemetry_fail_closed():
    import math
    # Dependency query returns tostring(Success); retain only bool outcome.
    values = [
        {"bucket": "2026-10-28T10:27:00Z", "events": 1,
         "success": "true", "p95_ms": 61000.12345},
        {"bucket": "2026-10-28T10:28:00+00:00", "events": 2,
         "success": "FALSE", "value": 0.125},
    ]
    assert mod.safe_aggregate_rows(values) == [
        {"bucket": "2026-10-28T10:27:00Z", "events": 1,
         "success": True, "p95_ms": 61000.123},
        {"bucket": "2026-10-28T10:28:00+00:00", "events": 2,
         "success": False, "value": 0.125},
    ]
    untrusted = [
        {"bucket": "2026-10-28Tfake-private-id", "events": -2,
         "p95_ms": float("nan"), "success": "token-secret"},
        {"bucket": "2026-10-28T10:27:00Z;customer@example.com",
         "events": True, "p95_ms": float("inf"), "value": -4},
        {"bucket": "2026-10-28T10:27:00Z", "events": 1.3,
         "p95_ms": -0.1, "value": float("-inf")},
    ]
    assert mod.safe_aggregate_rows(untrusted) == [
        {"bucket": "2026-10-28T10:27:00Z"}
    ]
    assert mod.public_utc_stamp("2026-10-28T24:28:00Z") is False
    assert mod.public_utc_stamp("2026-10-28T10:27:00Z") is True


def test_metric_series_denies_nonfinite_outside_date_and_private_suffix():
    payload = {"value": [{"timeseries": [{"data": [
        {"timeStamp": "2026-10-28T10:27:00Z", "average": 1.25},
        {"timeStamp": "2026-10-28T10:27:00Z/private-id", "average": 2.0},
        {"timeStamp": "2026-10-28T10:28:00Z", "average": float("inf")},
        {"timeStamp": "2026-10-28T10:29:00Z", "average": float("nan")},
        {"timeStamp": "2026-10-28T10:30:00Z", "average": True},
        {"timeStamp": "2026-10-28T10:31:00Z", "average": -1.0},
    ]}]}]}
    assert mod.safe_metric_points(payload, "Average", "InstanceCount") == [
        {"bucket": "2026-10-28T10:27:00Z",
         "metric": "InstanceCount", "value": 1.25}]
    assert mod.safe_metric_points(payload, "Average", "untrusted-private-label") == []


def test_metric_data_is_numeric_and_finite_window_only():
    payload = {"value":[{"timeseries":[{"data":[
        {"timeStamp":"2026-10-28T10:27:00Z", "average":1.5,
         "resourceId":"secret"},
        {"timeStamp":"2026-10-27T10:27:00Z", "average":2.0},
        {"timeStamp":"2026-10-28T10:28:00Z", "average":"not numeric"}]}]}]}
    assert mod.safe_metric_points(payload, "Average", "InstanceCount") == [
        {"bucket":"2026-10-28T10:27:00Z", "metric":"InstanceCount", "value":1.5}]
