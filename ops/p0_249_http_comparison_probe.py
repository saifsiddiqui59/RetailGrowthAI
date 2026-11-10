#!/usr/bin/env python3
"""Issue #249: guarded read-only original Flex versus Free SWA HTTP probe.

Only fixed anonymous synthetic GETs. No user tokens, tenant IDs, writes, config,
response bodies, host secrets, or retries for mutations. No proof of scale-to-zero.
"""
import json
import statistics
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from p0_249_cold_warm_http_probe import verify_dev

FLEX = "https://rgai-dev-functions-d4e5ddbd.azurewebsites.net"
SWA = "https://purple-dune-06b5da200-p0249writes.eastasia.2.azurestaticapps.net"
ORIGINS = {"azure_flex_python": FLEX, "free_swa_node": SWA}
ROUTES = {
    "campaign": "/api/campaigns/11111111-1111-4111-8111-111111111111",
    "unknown": "/api/p0-249-nonexistent-path",
}
DEADLINE_SECONDS = 75
CURL_FORMAT = "%{http_code} %{time_namelookup} %{time_connect} %{time_appconnect} %{time_starttransfer} %{time_total}"


def classify(exit_code, status, marker, backend):
    if exit_code != 0:
        return "CLIENT_TIMEOUT" if exit_code in (28, 124) else "NETWORK_OR_CURL_ERROR"
    if status == "503":
        return "HTTP_503_APP_MARKED" if marker else "HTTP_503_UNMARKED_OR_GATEWAY"
    if status == "401":
        if backend == "azure_flex_python" and not marker:
            return "UNMARKED_401_NOT_PROVEN_HANDLER"
        return "EXPECTED_401"
    if status == "404":
        return "EXPECTED_404_HANDLER_UNVERIFIED" if not marker else "EXPECTED_404_APP_MARKED"
    return "UNEXPECTED_HTTP_STATUS"



def sanitized_metric_names(payload):
    """Accept Azure CLI metric definitions in row-list or REST {value:[]} form."""
    entries = payload if isinstance(payload, list) else payload.get("value", []) if isinstance(payload, dict) else []
    names = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name", {})
        name = name.get("value", "") if isinstance(name, dict) else name
        if isinstance(name, str) and any(k in name.lower() for k in ("request", "http", "response", "error")):
            names.append(name)
    return names

def sample(backend, phase, route):
    if backend not in ORIGINS or route not in ROUTES:
        raise ValueError("fixed safe DEV backends and synthetic routes only")
    with tempfile.TemporaryDirectory() as tmp:
        headers = Path(tmp) / "headers"
        command = ["curl", "--silent", "--show-error", "--connect-timeout", "4",
                   "--max-time", str(DEADLINE_SECONDS), "--request", "GET",
                   "--dump-header", str(headers), "--output", "/dev/null",
                   "--write-out", CURL_FORMAT, ORIGINS[backend] + ROUTES[route]]
        try:
            proc = subprocess.run(command, text=True, capture_output=True, timeout=DEADLINE_SECONDS + 5)
            parts = proc.stdout.strip().split()
            status = parts[0] if len(parts) == 6 else "000"
            times = [float(x) for x in parts[1:]] if len(parts) == 6 else [0.0] * 5
            lines = headers.read_text(errors="replace").lower().splitlines() if headers.is_file() else []
            marker = any(x.startswith("x-request-id:") for x in lines)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            status, times, marker, code = "000", [0.0, 0.0, 0.0, 0.0, float(DEADLINE_SECONDS + 5)], False, 124
    names = ("dns_seconds", "tcp_seconds", "tls_seconds", "first_byte_seconds", "total_seconds")
    observation = dict(zip(names, (round(x, 3) for x in times)))
    observation.update(
        backend=backend, phase=phase, route=route, timestamp_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        http_status=status, curl_exit=code, application_request_marker=marker,
        category=classify(code, status, marker, backend),
    )
    return observation


def percentile(values, q):
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    low = int(pos)
    upper = min(low + 1, len(ordered) - 1)
    return round(ordered[low] + (ordered[upper] - ordered[low]) * (pos - low), 3)


def summarize(observations):
    outcome = {}
    for backend in ORIGINS:
        rows = [x for x in observations if x["backend"] == backend]
        times = [x["total_seconds"] for x in rows if x["curl_exit"] == 0]
        outcome[backend] = {
            "samples": len(rows),
            "completed_http": sum(x["curl_exit"] == 0 for x in rows),
            "http_503": sum(x["http_status"] == "503" and x["curl_exit"] == 0 for x in rows),
            "client_timeouts": sum(x["category"] == "CLIENT_TIMEOUT" for x in rows),
            "network_errors": sum(x["category"] == "NETWORK_OR_CURL_ERROR" for x in rows),
            "unexpected_http": sum(x["category"].startswith(("UNEXPECTED", "UNMARKED")) for x in rows),
            "success_rate_http_percent": round(100 * sum(x["curl_exit"] == 0 and x["http_status"] in ("401", "404") for x in rows) / len(rows), 1) if rows else None,
            "p50_completed_http_seconds": percentile(times, .5) if len(times) >= 2 else None,
            "p95_completed_http_seconds": percentile(times, .95) if len(times) >= 20 else None,
            "p99_completed_http_seconds": percentile(times, .99) if len(times) >= 100 else None,
            "percentile_caveat": "p95 requires >=20 completed HTTP samples; p99 requires >=100",
        }
    return outcome


def run_series(sender=sample, sleeper=time.sleep, idle=300):
    observations = []
    # First and repeated anonymous GETs, same synthetic paths on each backend.
    for phase, route in (("initial", "campaign"), ("initial", "unknown"),
                         ("repeat", "campaign"), ("repeat", "unknown")):
        with ThreadPoolExecutor(max_workers=2) as pool:
            tasks = [pool.submit(sender, backend, phase, route) for backend in ORIGINS]
            observations.extend(f.result() for f in tasks)
    # Maximum two concurrent GETs per backend; no writes or privileged calls.
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = [pool.submit(sender, backend, "concurrent-" + str(index), "campaign")
                 for backend in ORIGINS for index in (1, 2)]
        observations.extend(f.result() for f in tasks)
    print("P0_249_NEW_PROBE_IDLE_SECONDS=" + str(idle), flush=True)
    sleeper(idle)
    for route in ("campaign", "unknown"):
        with ThreadPoolExecutor(max_workers=2) as pool:
            tasks = [pool.submit(sender, backend, "post-idle", route) for backend in ORIGINS]
            observations.extend(f.result() for f in tasks)
    for x in observations:
        print("P0_249_NEW_HTTP_OBSERVATION=" + json.dumps(x, sort_keys=True), flush=True)
    final = summarize(observations)
    print("P0_249_NEW_HTTP_SUMMARY=" + json.dumps(final, sort_keys=True), flush=True)
    print("P0_249_IDLE_NOT_PROVEN_AZURE_COLD_START=true", flush=True)
    failed = any(x["curl_exit"] != 0 or x["http_status"] == "503" or
                 x["category"].startswith(("UNEXPECTED", "UNMARKED")) for x in observations)
    return 4 if failed else 0


if __name__ == "__main__":
    verify_dev()
    raise SystemExit(run_series())
