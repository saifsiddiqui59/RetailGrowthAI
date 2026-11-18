"""Offline negative cases; executed by existing Python CI tests/infra."""
import importlib.util
from pathlib import Path

import unittest

FILE = Path(__file__).resolve().parents[2] / "ops/p0_249_cold_warm_http_probe.py"
spec = importlib.util.spec_from_file_location("p0_probe", FILE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

def test_000_after_tls_is_not_confirmed_503():
    sample = probe.classify(28, "000", .6, 0, 12)
    assert sample["category"] == "CLIENT_TIMEOUT_OR_NETWORK_ERROR"
    assert sample["post_tls_no_first_byte"]

def test_actual_503_distinct():
    sample = probe.classify(0, "503", .6, 60.9, 60.95)
    assert sample["category"] == "CONFIRMED_HTTP_503"

def test_expected_statuses():
    for status in ("401", "404"):
        route = "campaign" if status == "401" else "unknown"
        assert probe.classify(0, status, .6, .8, .85,
                              marker=(status == "401"), route=route)["category"] == "EXPECTED_401_OR_404"

def test_campaign_and_unknown_routes_cannot_swap_authentication_status():
    assert probe.classify(0, "401", .4, .6, .8, marker=True,
                          route="campaign")["category"] == "EXPECTED_401_OR_404"
    assert probe.classify(0, "404", .4, .6, .8, route="unknown")["category"] == "EXPECTED_401_OR_404"
    for route, status, marker in [
        ("campaign", "404", True),
        ("campaign", "401", False),
        ("unknown", "401", True),
        ("unknown", "401", False),
        (None, "401", True),
        (None, "404", False),
    ]:
        assert probe.classify(0, status, .4, .6, .8,
                              marker=marker, route=route)["category"] == "OTHER_UNEXPECTED"


def test_final_header_marker_not_a_proxy_or_empty_value():
    a = ("HTTP/1.1 200 Connection established\r\n"
         "X-Request-ID: proxy-only\r\n\r\n"
         "HTTP/2 401\r\ncontent-type: application/json\r\n\r\n")
    assert not probe.final_app_request_marker(a)
    b = "HTTP/2 401\r\nX-Request-ID: \r\n\r\n"
    assert not probe.final_app_request_marker(b)
    c = a + "HTTP/2 401\r\nx-request-id: app-present\r\n\r\n"
    assert probe.final_app_request_marker(c)


def test_mocked_curl_six_gets_fail_closed_on_wrong_route_even_with_marker():
    from types import SimpleNamespace
    from unittest.mock import patch

    def make(headers, code):
        def sender(args, **kwargs):
            from pathlib import Path
            Path(args[args.index("-D") + 1]).write_text(headers)
            return SimpleNamespace(
                returncode=0, stdout=f"{code} 0.1 0.3 0.8",
            )
        return sender

    campaign = dict(probe.ROUTES)["campaign"]
    unknown = dict(probe.ROUTES)["unknown"]
    with patch.object(probe.subprocess, "run", make(
            "HTTP/2 404\r\nx-request-id: any\r\n\r\n", "404")):
        assert probe.probe("initial-campaign", campaign)["category"] == "OTHER_UNEXPECTED"
        assert probe.probe("initial-unknown", unknown)["category"] == "EXPECTED_401_OR_404"
    with patch.object(probe.subprocess, "run", make(
            "HTTP/2 401\r\nX-Request-ID: app-valid\r\n\r\n", "401")):
        assert probe.probe("initial-campaign", campaign)["category"] == "EXPECTED_401_OR_404"
        assert probe.probe("initial-unknown", unknown)["category"] == "OTHER_UNEXPECTED"


def test_sends_exactly_six_read_only_requests_and_one_idle():
    calls, idle = [], []
    def sender(label, path):
        calls.append((label,path))
        return {"category": "EXPECTED_401_OR_404"}
    assert probe.run_probe(sender=sender,sleeper=idle.append) == 0
    assert len(calls) == 6
    assert idle == [300]
    assert set(path for _, path in calls) == set(path for _, path in probe.ROUTES)

def test_anomaly_fails_diagnostic_acceptance():
    calls = []
    def sender(label,path):
        calls.append(label)
        return {"category": "CLIENT_TIMEOUT_OR_NETWORK_ERROR"
                if len(calls) == 5 else "EXPECTED_401_OR_404"}
    assert probe.run_probe(sender=sender,sleeper=lambda _:None) == 4

def test_rejects_arbitrary_customer_route():
    with unittest.TestCase().assertRaises(ValueError):
        probe.probe("fake", "/api/shop/real-id")

def test_anonymous_401_without_application_marker_is_not_healthy():
    assert probe.classify(0, "401", .6, .8, .85)["category"] == "OTHER_UNEXPECTED"
