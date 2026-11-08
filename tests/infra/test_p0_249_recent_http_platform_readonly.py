"""Offline safety and evidence tests for recent #249 Azure Flex host correlation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops"))
import p0_249_recent_http_platform_readonly as incident


def test_queries_are_fixed_to_approved_dev_app_and_exact_incidents():
    assert len(incident.WINDOWS) == 4
    for label, start, end in incident.WINDOWS:
        for kind in incident.KINDS:
            q = incident.build_query(label, kind)
            assert start in q and end in q
            assert q.count(" | take 80") == 1
            assert "rgai-dev-functions-d4e5ddbd" in q
            if kind == "activity":
                assert "AzureActivity" in q and "rg-retailgrowth-dev" in q
            else:
                assert incident.APP_SCOPE in q
                assert "instance=" in q
                assert " | where " in q
            assert "Authorization" not in q and "token" not in q
    host = incident.build_query("nov08_1755", "host")
    for signal in ("drainmode", "worker process exited", "worker process started",
                   "pendingitem.ontimeout", "specializeasync"):
        assert signal in host
    for bad in ("", "tomorrow", "nov08_1755;print('secret')"):
        with pytest.raises(ValueError):
            incident.build_query(bad, "host")
    for bad in ("", "AppTraces | project Message", "secrets"):
        with pytest.raises(ValueError):
            incident.build_query("nov08_1755", bad)


def test_sanitizer_retains_only_allowlisted_utc_minute_counts_and_hashed_instance():
    raw = {"bucket": "2026-11-08T17:55:00.0000000Z", "events": "3",
           "event": "drain_mode", "instance": "private-platform-worker-id",
           "Message": "JWT: PRIVATE_TOKEN", "Url": "https://secret.invalid/a",
           "tenant_id": "private-shop"}
    rows = incident.safe_rows([raw], window="nov08_1755", kind="host")
    assert len(rows) == 1
    row = rows[0]
    assert row["events"] == 3 and row["event"] == "drain_mode"
    assert len(row["host_hash"]) == 12
    assert row["bucket"] == raw["bucket"]
    assert "private-" not in json.dumps(row)
    assert "PRIVATE_TOKEN" not in json.dumps(row)
    assert "Url" not in row and "tenant_id" not in row
    assert incident.safe_rows([raw], window="nov06_1952", kind="host") == []
    assert incident.safe_rows([dict(raw, event=["unhashable"])],
                              window="nov08_1755", kind="host") == []


@pytest.mark.parametrize("bad_bucket", [
    "2026-11-08T17:55:01Z", "2026-11-08T17:55:00.0000001Z",
    "2026-11-08T17:55:00.00000000Z", "2026-11-08T17:55:00+01:00",
    "2026-11-08T19:55:00Z", "2026-11-09T17:55:00Z",
    "2026-11-08T17:55:00Z JWT=PRIVATE", None, {}, [],
])
def test_date_parser_rejects_wrong_or_untrusted_bucket(bad_bucket):
    assert incident.safe_rows([{"bucket": bad_bucket, "events": 1, "event": "worker_start"}],
                              window="nov08_1755", kind="host") == []


def test_count_validation_and_no_worker_identity_leaks():
    baseline = {"bucket": "2026-11-08T17:55:00Z", "events": "2",
                "app_401": "1", "reported_503": "0",
                "internal_or_missing": "1", "instance": "raw-PROTECTED-abc"}
    out = incident.safe_rows({"value": [baseline]}, window="nov08_1755",
                             kind="requests")
    assert out[0]["app_401"] == 1 and out[0]["reported_503"] == 0
    assert "raw-PROTECTED" not in json.dumps(out)
    for bad in (True, -1, 1.5, "Infinity", "99999999", ["x"]):
        bad_record = dict(baseline, events=bad)
        assert incident.safe_rows([bad_record], window="nov08_1755",
                                  kind="requests") == []
    with pytest.raises(ValueError):
        incident.safe_rows([baseline], window="invalid", kind="requests")


def test_collect_only_reads_existing_dev_and_never_prints_raw_azure(monkeypatch, capsys):
    calls = []
    scope_checks = []
    def fake_scope():
        scope_checks.append(True)
        return "/validated/DEV/resource"
    def fake_azure(*args):
        calls.append(args)
        if args[2:5] == ("workspace", "show", "-g"):
            return {"customerId": "private-workspace-id"}
        assert args[:3] == ("monitor", "log-analytics", "query")
        query = args[-1]
        window = next((w for w in incident.WINDOWS if w[1] in query), None)
        assert window is not None
        bucket = window[1]
        if query.startswith("AppTraces"):
            return [{"bucket": bucket, "events": "1",
                     "event": "drain_mode", "instance": "PRIVATE_INSTANCE",
                     "Message": "SECRET_JWT", "Url": "https://private.invalid"}]
        if query.startswith("AppRequests"):
            return [{"bucket": bucket, "events": "2",
                     "app_401": "1", "reported_503": "0",
                     "internal_or_missing": "1", "instance": "PRIVATE_INSTANCE",
                     "Message": "SECRET_JWT"}]
        assert query.startswith("AzureActivity")
        return [{"bucket": bucket, "events": "1", "operation": "PRIVATE_RESOURCE"}]
    monkeypatch.setattr(incident, "audit_scope", fake_scope)
    monkeypatch.setattr(incident, "azure", fake_azure)
    assert incident.collect() == 0
    text = capsys.readouterr().out
    assert len(scope_checks) == 1
    assert len(calls) == 1 + len(incident.WINDOWS) * len(incident.KINDS)
    assert text.count("P0249_INCIDENT=") == 12
    for secret in ("PRIVATE_INSTANCE", "SECRET_JWT", "PRIVATE_RESOURCE",
                   "private-workspace-id", "PRIVATE_RESOURCE"):
        assert secret not in text
    assert "P0249_NO_HTTP_REQUEST_TO_INSTANCE_CAUSAL_PROOF=true" in text
    assert "P0249_READ_ONLY_NO_CONFIG_WRITES_NO_NEW_RESOURCES=true" in text
