"""Offline safety and result-classification regression for Issue #249."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[2] / "ops" / "p0_249_http_comparison_probe.py"
spec = importlib.util.spec_from_file_location("p0_extended", FILE)
import sys
sys.path.insert(0, str(FILE.parent))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_read_only_fixed_paths_and_hosts():
    assert len(probe.ORIGINS) == 2
    assert all(url.startswith("https://") for url in probe.ORIGINS.values())
    assert len(probe.ROUTES) == 2
    assert all("11111111-" in path or "nonexistent-path" in path for path in probe.ROUTES.values())
    assert probe.DEADLINE_SECONDS >= 70
    for backend in ("production", "wine"):
        try:
            probe.sample(backend, "initial", "campaign")
        except ValueError:
            pass
        else:
            raise AssertionError("unexpected backend was accepted")


def test_503_and_post_tls_timeout_distinguished():
    assert probe.classify(0, "503", False, "azure_flex_python") == "HTTP_503_UNMARKED_OR_GATEWAY"
    assert probe.classify(0, "503", True, "azure_flex_python") == "HTTP_503_APP_MARKED"
    assert probe.classify(28, "000", False, "azure_flex_python") == "CLIENT_TIMEOUT"
    assert probe.classify(0, "401", False, "azure_flex_python") == "UNMARKED_401_NOT_PROVEN_HANDLER"


def test_percentile_gates_prevent_unsupported_p99_claim():
    rows = [{"backend": b, "curl_exit": 0, "http_status": "401",
             "category": "EXPECTED_401", "total_seconds": 0.8}
            for b in probe.ORIGINS for _ in range(8)]
    summary = probe.summarize(rows)
    assert summary["azure_flex_python"]["p50_success_seconds"] == .8
    assert summary["azure_flex_python"]["p95_success_seconds"] is None
    assert summary["free_swa_node"]["p99_success_seconds"] is None


def test_series_sends_16_fixed_get_observations_and_one_five_minute_idle():
    calls, slept = [], []
    def fake_sender(backend, phase, route):
        calls.append((backend, phase, route))
        return {"backend": backend, "curl_exit": 0, "http_status": "401",
                "category": "EXPECTED_401", "total_seconds": 0.3}
    assert probe.run_series(sender=fake_sender, sleeper=slept.append) == 0
    assert len(calls) == 16
    assert slept == [300]
    assert len([c for c in calls if c[1] == "post-idle"]) == 4
    assert len([c for c in calls if c[1].startswith("concurrent-")]) == 4


def test_failed_503_fails_test_without_automatic_retry():
    def fake_sender(backend, phase, route):
        code = "503" if backend == "azure_flex_python" and phase == "initial" else "401"
        return {"backend": backend, "curl_exit": 0, "http_status": code,
                "category": "HTTP_503_UNMARKED_OR_GATEWAY" if code == "503" else "EXPECTED_401",
                "total_seconds": 60.9 if code == "503" else 0.5}
    assert probe.run_series(sender=fake_sender, sleeper=lambda _: None, idle=0) == 4
