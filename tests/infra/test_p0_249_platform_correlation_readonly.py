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
            assert "take 80" in text
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
                ("monitor", "log-analytics", "query")]) == 10
    assert all(c == "scoped" or c[:3] in (
        ("monitor", "log-analytics", "query"),
        ("monitor", "log-analytics", "workspace"),
    ) for c in calls)
