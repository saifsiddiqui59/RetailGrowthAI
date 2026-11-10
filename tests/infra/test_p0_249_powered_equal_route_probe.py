"""Offline coverage for matched original Flex and SWA 20-sample GET reliability."""
from pathlib import Path
import runpy
import sys

OPS = Path(__file__).resolve().parents[2] / "ops"
sys.path.insert(0, str(OPS))
probe = runpy.run_path(str(OPS / "p0_249_powered_equal_route_probe.py"))


def response(backend, phase, route, status="401", marked=True, seconds=0.7):
    return {
        "backend": backend,
        "phase": phase,
        "route": route,
        "timestamp_utc": "2026-10-28T12:00:00+00:00",
        "http_status": status,
        "curl_exit": 0,
        "application_request_marker": marked,
        "category": "EXPECTED_401" if status=="401" else "HTTP_503_UNMARKED_OR_GATEWAY",
        "total_seconds": seconds,
        "dns_seconds":0.05,"tcp_seconds":0.1,"tls_seconds":0.2,
        "first_byte_seconds":seconds
    }


def test_exact_campaign_route_only_and_twenty_per_backend():
    assert probe["ROUTE"] == "campaign"
    assert probe["PER_BACKEND"] == 20
    assert probe["IDLE_SECONDS"] == 300
    assert probe["MAX_CONCURRENT_PER_BACKEND"] == 2
    assert sum(n for _,n in probe["PLAN"]) == 20
    called, slept = [], []
    def sender(backend, phase, route):
        called.append((backend, phase, route))
        return response(backend, phase, route)
    assert probe["run_powered"](sender=sender,sleeper=slept.append) == 0
    assert len(called) == 40
    assert slept == [300]
    assert set(route for _,_,route in called) == {"campaign"}
    assert sum(phase == "initial" for _,phase,_ in called) == 4
    assert sum(phase == "warm" for _,phase,_ in called) == 16
    assert sum(phase == "concurrent" for _,phase,_ in called) == 8
    assert sum(phase == "post_idle" for _,phase,_ in called) == 12


def test_p95_gate_and_p99_unavailable_for_twenty_samples():
    sample = [response(backend, "warm", "campaign", seconds=1.0+i)
              for backend in ("azure_flex_python","free_swa_node")
              for i in range(20)]
    result=probe["summarize_powered"](sample)
    for backend in result:
        assert result[backend]["attempts"] == 20
        assert result[backend]["p95_all_completed_http_seconds"] is not None
        assert result[backend]["p95_verified_401_seconds"] is not None
        assert result[backend]["p99_all_completed_http_seconds"] is None


def test_unmarked_python_handler_and_http503_fail_without_post_retry():
    def sender(backend, phase, route):
        if backend=="azure_flex_python":
            return response(backend, phase, route, status="503", marked=False, seconds=60.9)
        return response(backend, phase, route)
    assert probe["run_powered"](sender=sender,sleeper=lambda _:None,idle=0)==4
    observations=[response("azure_flex_python","warm","campaign",marked=False)]
    result=probe["summarize_powered"](observations)
    assert result["azure_flex_python"]["verified_expected_401"] == 0
    assert result["azure_flex_python"]["p95_verified_401_seconds"] is None


def test_wrong_backend_or_route_fails_closed():
    def sender(backend,phase,route):
        return response("production",phase,route)
    try:
        probe["safe_round"](sender,"warm",(1,))
    except ValueError:
        pass
    else:
        raise AssertionError("unapproved backend accepted")


def test_source_probe_uses_only_get_and_fixed_synthetic_ids():
    from p0_249_http_comparison_probe import ROUTES, ORIGINS
    assert ROUTES["campaign"].startswith("/api/campaigns/11111111-")
    assert all(value.startswith("https://") for value in ORIGINS.values())
    assert "production" not in ORIGINS
