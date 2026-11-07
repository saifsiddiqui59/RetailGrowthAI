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
        "application_request_marker": marked if backend=="azure_flex_python" else False,
        "node_adapter_marker": marked if backend=="free_swa_node" else False,
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


def test_node_generic_401_no_longer_counts_as_handler_success():
    unmarked = response("free_swa_node", "warm", "campaign", marked=False)
    assert probe["accepted"](unmarked) is False
    s = probe["summarize_powered"]([unmarked])
    assert s["free_swa_node"]["verified_expected_401"] == 0
    assert s["free_swa_node"]["p95_verified_401_seconds"] is None

    # Even if all 20 Node responses are syntactically 401, none is verified
    # unless the *final* Node secure-adapter header was present.
    samples = [response("free_swa_node", "warm", "campaign", marked=False)
               for _ in range(20)]
    summary = probe["summarize_powered"](samples)
    assert summary["free_swa_node"]["completed_http"] == 20
    assert summary["free_swa_node"]["verified_expected_401"] == 0
    assert summary["free_swa_node"]["p95_verified_401_seconds"] is None


def test_wrong_backend_or_route_fails_closed():
    def sender(backend,phase,route):
        return response("production",phase,route)
    try:
        probe["safe_round"](sender,"warm",(1,))
    except ValueError:
        pass
    else:
        raise AssertionError("unapproved backend accepted")


def test_mismatched_phase_is_never_counted_as_after_idle_evidence():
    def wrong_phase(backend, phase, route):
        return response(backend, "warm" if phase == "post_idle" else phase, route)
    try:
        probe["run_powered"](sender=wrong_phase, sleeper=lambda _: None, idle=0)
    except ValueError as error:
        assert "phase" in str(error)
    else:
        raise AssertionError("stale warm request misclassified as post-idle acceptance")


def test_handler_code_and_classification_must_agree():
    fake = response("free_swa_node", "warm", "campaign")
    fake["category"] = "UNMARKED_401_NOT_PROVEN_HANDLER"
    assert probe["accepted"](fake) is False
    fake["category"] = "EXPECTED_401"
    fake["route"] = "unknown"
    assert probe["accepted"](fake) is False
    fake["route"] = "campaign"
    assert probe["accepted"](fake) is True

    def mislabeled(backend, phase, route):
        result = response(backend, phase, route)
        result["category"] = "UNMARKED_401_NOT_PROVEN_HANDLER"
        return result
    assert probe["run_powered"](sender=mislabeled, sleeper=lambda _: None, idle=0) == 4


def test_source_probe_uses_only_get_and_fixed_synthetic_ids():
    from p0_249_http_comparison_probe import ROUTES, ORIGINS
    assert ROUTES["campaign"].startswith("/api/campaigns/11111111-")
    assert all(value.startswith("https://") for value in ORIGINS.values())
    assert "production" not in ORIGINS


def test_powered_receipts_never_log_private_fields_or_untrusted_timing(capsys):
    import json
    def sender(backend, phase, route):
        item = response(backend, phase, route)
        item.update(
            authorization="Bearer private-token-must-not-appear",
            response_body="customer-personal-body-must-not-appear",
            signed_url="https://private.invalid/signed-asset?token=private",
            headers={"set-cookie": "session-private"},
            request_id="private-server-id",
        )
        return item
    assert probe["run_powered"](sender=sender, sleeper=lambda _: None, idle=0) == 0
    raw = capsys.readouterr().out
    for forbidden in ("private-token", "customer-personal-body", "private.invalid",
                      "session-private", "private-server-id", "signed_url", "authorization"):
        assert forbidden not in raw
    entries = [json.loads(s.split("=", 1)[1]) for s in raw.splitlines()
               if s.startswith("P0249_POWERED_HTTP=")]
    assert len(entries) == 40
    assert all(set(x) == {
        "backend", "phase", "route", "timestamp_utc", "http_status",
        "curl_exit", "category", "application_request_marker",
        "node_adapter_marker", "dns_seconds", "tcp_seconds", "tls_seconds",
        "first_byte_seconds", "total_seconds", "sequence"
    } for x in entries)


def test_nonfinite_negative_and_missing_times_cannot_certify_20_successes(capsys):
    for malformed in (
        float("nan"), float("inf"), -1.0, 9000.0, "0.2", True, None
    ):
        def sender(backend, phase, route):
            row = response(backend, phase, route)
            row["total_seconds"] = malformed
            row["signed_url"] = "https://private.invalid/secret"
            return row
        assert probe["run_powered"](sender=sender, sleeper=lambda _: None, idle=0) == 4
        logged = capsys.readouterr().out
        assert "private.invalid" not in logged
        assert "Infinity" not in logged and "NaN" not in logged
        assert '"category": "INVALID_OBSERVATION"' in logged
        assert '"verified_expected_401": 0' in logged


def test_false_marker_boolean_malformed_timestamp_and_corrupt_status_fail_closed():
    base = response("azure_flex_python", "warm", "campaign")
    for patch in (
        {"application_request_marker": "true"},
        {"timestamp_utc": "2026-10-28T12:00:00+00:00/private"},
        {"timestamp_utc": "2026-99-99T12:00:00+00:00"},
        {"http_status": "401\nAuthorization: Bearer secret"},
        {"curl_exit": True},
        {"category": "EXPECTED_401_private_customer"},
    ):
        item = {**base, **patch}
        clean = probe["public_receipt"](item)
        assert clean["category"] == "INVALID_OBSERVATION"
        assert clean["curl_exit"] != 0
        assert probe["accepted"](item) is False
        assert "private_customer" not in str(clean)
        assert "Authorization:" not in str(clean)
        assert "private" not in str(clean)


def test_valid_curl_timeout_is_counted_as_failure_not_fake_http_503():
    row = response("azure_flex_python", "initial", "campaign",
                   status="000", marked=False, seconds=75.0)
    row["curl_exit"] = 28
    row["category"] = "CLIENT_TIMEOUT"
    receipt = probe["public_receipt"](row)
    assert receipt["curl_exit"] == 28
    assert receipt["category"] == "CLIENT_TIMEOUT"
    summary = probe["summarize_powered"]([row])
    assert summary["azure_flex_python"]["client_timeouts"] == 1
    assert summary["azure_flex_python"]["http_503"] == 0
    assert summary["azure_flex_python"]["verified_expected_401"] == 0
