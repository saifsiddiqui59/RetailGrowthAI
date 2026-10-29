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


def test_final_response_marker_is_trusted_only_when_exact():
    parse = probe.response_handler_markers
    python, node = parse("HTTP/2 401\r\nX-Request-ID: server-only-id\r\n\r\n")
    assert python and not node
    python, node = parse("HTTP/2 401\r\nX-RGAI-Secure-Adapter: candidate-v1\r\n\r\n")
    assert node and not python
    # CONNECT intermediary markers must not be misread as final app responses.
    python, node = parse(
        "HTTP/1.1 200 Connection established\r\n"
        "X-Request-ID: proxy-id\r\n"
        "X-RGAI-Secure-Adapter: candidate-v1\r\n\r\n"
        "HTTP/2 401\r\ncontent-length: 0\r\n\r\n"
    )
    assert not python and not node
    assert parse("HTTP/2 401\r\nX-RGAI-Secure-Adapter: other-v1\r\n\r\n") == (False, False)
    assert parse("HTTP/2 401\r\nX-RGAI-Secure-Adapter: candidate-v1-extra\r\n\r\n") == (False, False)
    assert parse("HTTP/2 401\r\nX-Request-ID:   \r\n\r\n") == (False, False)
    assert parse("X-RGAI-Secure-Adapter: candidate-v1") == (False, False)


def test_node_plain_401_fails_classification_not_backend_proof():
    assert probe.classify(0, "401", False, "free_swa_node") == "UNMARKED_401_NOT_PROVEN_HANDLER"
    assert probe.classify(0, "401", True, "free_swa_node") == "EXPECTED_401"
    assert probe.classify(0, "503", False, "free_swa_node") == "HTTP_503_UNMARKED_OR_GATEWAY"
    assert probe.classify(0, "503", True, "free_swa_node") == "HTTP_503_APP_MARKED"


def test_actual_curl_sample_uses_final_response_handler_markers_only():
    """Mock the real curl-to-temporary-header pipeline, not just its parser."""
    from types import SimpleNamespace

    def sample(backend, header_blob):
        def fake_run(command, **kwargs):
            assert kwargs["capture_output"] is True
            assert command[command.index("--request") + 1] == "GET"
            assert "--location" not in command and "-L" not in command
            assert all("Authorization" not in x and "Cookie" not in x
                       for x in command)
            path = command[command.index("--dump-header") + 1]
            Path(path).write_text(header_blob)
            return SimpleNamespace(returncode=0,
                                   stdout="401 0.001 0.002 0.003 0.004 0.005")
        with patch.object(probe.subprocess, "run", fake_run):
            return probe.sample(backend, "initial", "campaign")

    ok = sample("free_swa_node",
                "HTTP/2 401\r\nX-RGAI-Secure-Adapter: candidate-v1\r\n\r\n")
    assert ok["node_adapter_marker"] is True
    assert ok["application_request_marker"] is False
    assert ok["category"] == "EXPECTED_401"
    assert not any("candidate-v1" in str(v) for v in ok.values())

    fake = sample("free_swa_node",
                  "HTTP/1.1 200 Connection established\r\n"
                  "X-RGAI-Secure-Adapter: candidate-v1\r\n\r\n"
                  "HTTP/2 401\r\nContent-Length: 0\r\n\r\n")
    assert fake["node_adapter_marker"] is False
    assert fake["category"] == "UNMARKED_401_NOT_PROVEN_HANDLER"

    python = sample("azure_flex_python", "HTTP/2 401\r\nX-Request-ID: private-opaque\r\n\r\n")
    assert python["application_request_marker"] is True
    assert python["node_adapter_marker"] is False
    assert python["category"] == "EXPECTED_401"
    assert "private-opaque" not in str(python)


def test_percentile_gates_prevent_unsupported_p99_claim():
    rows = [{"backend": b, "curl_exit": 0, "http_status": "401",
             "category": "EXPECTED_401", "total_seconds": 0.8}
            for b in probe.ORIGINS for _ in range(8)]
    summary = probe.summarize(rows)
    assert summary["azure_flex_python"]["p50_completed_http_seconds"] == .8
    assert summary["azure_flex_python"]["p95_completed_http_seconds"] is None
    assert summary["free_swa_node"]["p99_completed_http_seconds"] is None


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


def test_azure_metric_definitions_both_cli_shapes():
    rows = [{"name": {"value": "Http5xx"}}, {"name": "Requests"},
            {"name": {"value": "CpuPercentage"}}]
    assert probe.sanitized_metric_names(rows) == ["Http5xx", "Requests"]
    assert probe.sanitized_metric_names({"value": rows}) == ["Http5xx", "Requests"]
    assert probe.sanitized_metric_names(None) == []


def test_all_http_median_name_includes_503_without_mislabeling_success():
    data = []
    for backend in probe.ORIGINS:
        for code, sec in (("401", 1.0), ("503", 61.0)):
            data.append({"backend": backend, "curl_exit": 0,
                         "http_status": code, "category": "EXPECTED_401" if code == "401" else "HTTP_503_UNMARKED_OR_GATEWAY",
                         "total_seconds": sec})
    s = probe.summarize(data)
    assert s["azure_flex_python"]["p50_completed_http_seconds"] == 31.0
    assert s["azure_flex_python"]["http_503"] == 1
