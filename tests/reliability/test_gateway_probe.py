"""Offline tests for a no-token, non-mutating DEV gateway probe."""
import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ops import gateway_probe as probe


def observed(status, latency=100, trace=False, transport=None):
    return {"status": status, "latency_ms": latency,
            "request_id_header": trace, "transport": transport}


def test_fixed_dev_get_only_no_auth_headers(monkeypatch):
    seen = {}
    class Response:
        status = 401
        def getheader(self, name):
            return "trace" if name == "X-Request-ID" else None
    class Connection:
        def __init__(self, host, timeout):
            seen["host"] = host
            seen["timeout"] = timeout
        def request(self, method, path, headers):
            seen.update(method=method, path=path, headers=headers)
        def getresponse(self):
            return Response()
        def close(self):
            seen["closed"] = True
    monkeypatch.setattr(probe.http.client, "HTTPSConnection", Connection)
    result = probe.probe_once(probe.ROUTES[0][1], 7)
    assert result["status"] == 401 and result["request_id_header"]
    assert seen["host"] == probe.HOST and seen["method"] == "GET"
    assert seen["timeout"] == 7 and seen["closed"]
    assert "Authorization" not in seen["headers"] and "Cookie" not in seen["headers"]
    assert probe.SENTINEL in seen["path"]


def test_first_hit_gateway_failure_remains_visible():
    results = iter([
        observed(503, 9000), observed(401, 300, True),
        observed(401, 450, True), observed(504, 7500),
        observed(401, 110, True), observed(401, 115, True),
    ])
    pauses = []
    rows = probe.collect(3, 20, 5, request_fn=lambda *_: next(results),
                         sleep_fn=pauses.append)
    assert pauses == [5, 5]
    report = probe.summarize(rows)
    assert report["protected_routes_reached"]
    assert report["degraded"] and not report["healthy_all_samples_401"]
    assert report["routes"]["campaign_read"]["gateway_502_503_504"] == 1
    assert report["routes"]["campaign_read"]["first_latency_ms"] == 9000
    assert report["routes"]["campaign_read"]["subsequent_median_ms"] == 280
    assert report["routes"]["render_read"]["gateway_502_503_504"] == 1
    assert "not proof" in report["interpretation"]


def test_total_outage_and_bypass_never_pass():
    for code in (None, 200, 403):
        rows = [{"route": name, **observed(
            code, transport="timeout" if code is None else None)}
                for name, _ in probe.ROUTES]
        report = probe.summarize(rows)
        assert not report["protected_routes_reached"]
        assert report["degraded"]
        assert report["unexpected_responses"] == (code in (200, 403))
    with pytest.raises(ValueError):
        probe.summarize([])


def test_strict_limits_and_no_hidden_retry():
    for n, timeout, pause in (
        (0, 20, 5), (7, 20, 5), (2, 0, 5), (2, 31, 5),
        (2, 20, -1), (2, 20, 31),
    ):
        with pytest.raises(ValueError):
            probe.collect(n, timeout, pause, request_fn=lambda *_: observed(401))
    calls = []
    probe.collect(2, 2, 0, request_fn=lambda path, timeout: (
        calls.append((path, timeout)) or observed(502)
    ), sleep_fn=lambda _: None)
    assert len(calls) == 4 and all(t == 2 for _, t in calls)


def test_transport_exception_is_sanitized(monkeypatch):
    class Connection:
        def __init__(self, *args, **kwargs):
            pass
        def request(self, *args, **kwargs):
            raise TimeoutError("private API token must never appear")
        def close(self):
            pass
    monkeypatch.setattr(probe.http.client, "HTTPSConnection", Connection)
    row = probe.probe_once(probe.ROUTES[1][1], 2)
    assert row["transport"] == "timeout"
    assert "token" not in json.dumps(row)
