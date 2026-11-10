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
        assert probe.classify(0, status, .6, .8, .85, marker=(status == "401"))["category"] == "EXPECTED_401_OR_404"

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
