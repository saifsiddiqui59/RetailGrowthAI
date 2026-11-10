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


def test_metric_data_is_numeric_and_finite_window_only():
    payload = {"value":[{"timeseries":[{"data":[
        {"timeStamp":"2026-10-28T10:27:00Z", "average":1.5,
         "resourceId":"secret"},
        {"timeStamp":"2026-10-27T10:27:00Z", "average":2.0},
        {"timeStamp":"2026-10-28T10:28:00Z", "average":"not numeric"}]}]}]}
    assert mod.safe_metric_points(payload, "Average", "InstanceCount") == [
        {"bucket":"2026-10-28T10:27:00Z", "metric":"InstanceCount", "value":1.5}]
