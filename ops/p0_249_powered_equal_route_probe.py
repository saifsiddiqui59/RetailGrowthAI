#!/usr/bin/env python3
"""Issue #249: matched-path 20-GET DEV reliability sample with live p95 gate.

Exact anonymous synthetic campaign GET, fixed original Flex and existing Free
SWA preview only. No JWT, no real media, no POST/PUT/PATCH/DELETE, no retries,
config/deployment/billing changes, or claims of scale-to-zero after inactivity.

This is a bounded *single run*, NOT a statistically representative 24h SLA.
"""
from __future__ import annotations

import json
import math
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from p0_249_cold_warm_http_probe import verify_dev
from p0_249_http_comparison_probe import ORIGINS, ROUTES, DEADLINE_SECONDS, sample, percentile

ROUTE = "campaign"
PER_BACKEND = 20
IDLE_SECONDS = 300
MAX_CONCURRENT_PER_BACKEND = 2
PLAN = (("initial", 2), ("warm", 8), ("concurrent", 4), ("post_idle", 6))
assert sum(count for _, count in PLAN) == PER_BACKEND


# Telemetry printed by this diagnostic is an explicit public allowlist,
# never the entire sender result (which might acquire private fields later).
# The diagnostic must reject malformed/unbounded timing, not report its
# misleading p95 as successful gateway evidence.
PUBLIC_TIMINGS = (
    "dns_seconds", "tcp_seconds", "tls_seconds", "first_byte_seconds",
    "total_seconds",
)
PUBLIC_CATEGORIES = frozenset((
    "EXPECTED_401", "EXPECTED_404_APP_MARKED", "EXPECTED_404_HANDLER_UNVERIFIED",
    "HTTP_503_APP_MARKED", "HTTP_503_UNMARKED_OR_GATEWAY",
    "UNMARKED_401_NOT_PROVEN_HANDLER", "UNEXPECTED_HTTP_STATUS",
    "CLIENT_TIMEOUT", "NETWORK_OR_CURL_ERROR",
))
PUBLIC_TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\+00:00\Z")


def public_receipt(observation):
    """Only fixed, bounded, non-sensitive fields; fail closed on corrupt data."""
    if not isinstance(observation, dict):
        raise ValueError("unexpected observation shape")
    public = {key: observation[key] for key in ("backend", "phase", "route")
              if key in observation}
    valid = True
    stamp = observation.get("timestamp_utc")
    if isinstance(stamp, str) and PUBLIC_TIMESTAMP.fullmatch(stamp):
        try:
            datetime.fromisoformat(stamp)
            public["timestamp_utc"] = stamp
        except ValueError:
            valid = False
    else:
        valid = False
    status = observation.get("http_status")
    if isinstance(status, str) and len(status) == 3 and status.isascii() and status.isdecimal():
        public["http_status"] = status
    else:
        valid = False
    exit_code = observation.get("curl_exit")
    if type(exit_code) is int and 0 <= exit_code <= 255:
        public["curl_exit"] = exit_code
    else:
        valid = False
    category = observation.get("category")
    if isinstance(category, str) and category in PUBLIC_CATEGORIES:
        public["category"] = category
    else:
        valid = False
    for name in ("application_request_marker", "node_adapter_marker"):
        flag = observation.get(name)
        if type(flag) is not bool:
            valid = False
        public[name] = flag is True
    for name in PUBLIC_TIMINGS:
        value = observation.get(name)
        if (type(value) in (int, float) and math.isfinite(value)
                and 0 <= value <= DEADLINE_SECONDS + 5):
            public[name] = round(value, 3)
        else:
            valid = False
    if not valid:
        # Never let a malformed status or NaN/Infinity timing satisfy a
        # successful anonymous handler proof or enter percentile statistics.
        public.update(
            http_status="000", curl_exit=125, category="INVALID_OBSERVATION",
            application_request_marker=False, node_adapter_marker=False,
        )
        for name in PUBLIC_TIMINGS:
            public.pop(name, None)
    return public


def accepted(observation):
    """Count only exact final-response application-marked anonymous HTTP 401."""
    observation = public_receipt(observation)
    if (observation.get("curl_exit") != 0
            or observation.get("http_status") != "401"
            or observation.get("category") != "EXPECTED_401"
            or observation.get("route") != ROUTE):
        return False
    if observation["backend"] == "azure_flex_python":
        return observation.get("application_request_marker") is True
    if observation["backend"] == "free_swa_node":
        return observation.get("node_adapter_marker") is True
    return False


def safe_round(sender, phase, indices):
    # max two anonymous synthetic GETs per backend and four across both.
    with ThreadPoolExecutor(max_workers=2 * MAX_CONCURRENT_PER_BACKEND) as pool:
        futures = [(backend, idx, pool.submit(sender, backend, phase, ROUTE))
                   for backend in ORIGINS for idx in indices]
        output = []
        for backend, idx, future in futures:
            result = future.result()
            if (not isinstance(result, dict)
                    or result.get("backend") != backend
                    or result.get("route") != ROUTE
                    or result.get("phase") != phase):
                raise ValueError("unexpected probe backend, route or phase")
            receipt = public_receipt(result)
            receipt["sequence"] = idx
            # Even a future sender that returns headers, JWTs or signed URLs
            # cannot put those values into Actions logs or summary output.
            print("P0249_POWERED_HTTP=" + json.dumps(receipt, sort_keys=True), flush=True)
            output.append(receipt)
        return output


def summarize_powered(observations):
    observations = [public_receipt(row) for row in observations]
    answer = {}
    for backend in ORIGINS:
        rows = [r for r in observations if r.get("backend") == backend]
        successful = [r for r in rows if accepted(r)]
        completed = [r["total_seconds"] for r in rows
                     if r.get("curl_exit") == 0]
        valid_times = [r["total_seconds"] for r in successful]
        codes = Counter(r["http_status"] for r in rows)
        phases = {phase: {
            "attempted": sum(r.get("phase") == phase for r in rows),
            "verified_401": sum(r.get("phase") == phase and accepted(r) for r in rows),
            "http_503": sum(r.get("phase") == phase and r.get("http_status") == "503"
                            and r.get("curl_exit") == 0 for r in rows)
        } for phase, _ in PLAN}
        answer[backend] = {
            "attempts": len(rows),
            "verified_expected_401": len(successful),
            "verified_rate_percent": round(len(successful) * 100 / len(rows), 1) if rows else None,
            "http_503": codes.get("503", 0),
            "client_timeouts": sum(r.get("category") == "CLIENT_TIMEOUT" for r in rows),
            "completed_http": len(completed),
            "p50_all_completed_http_seconds": percentile(completed, .50) if len(completed) >= 2 else None,
            "p95_all_completed_http_seconds": percentile(completed, .95) if len(completed) >= 20 else None,
            "p95_verified_401_seconds": percentile(valid_times, .95) if len(valid_times) >= 20 else None,
            "p99_all_completed_http_seconds": None,
            "phases": phases,
            "percentile_caveat": "p95 only with >=20 eligible observations; p99 unavailable at n=20",
        }
    return answer


def run_powered(*, sender=sample, sleeper=time.sleep, idle=IDLE_SECONDS):
    observations = []
    # Initial 2 requests per backend without implying cold activation.
    for idx in (1, 2):
        observations.extend(safe_round(sender, "initial", (idx,)))
    # Four warm pairs, two per backend concurrently; no write retries.
    for idx in (3, 5, 7, 9):
        observations.extend(safe_round(sender, "warm", (idx, idx + 1)))
    # Two further concurrent pairs per host.
    for idx in (11, 13):
        observations.extend(safe_round(sender, "concurrent", (idx, idx + 1)))
    print("P0249_POWERED_IDLE_SECONDS=" + str(idle), flush=True)
    sleeper(idle)
    # Post-inactivity is NOT a proven cold start.
    for idx in (15, 17, 19):
        observations.extend(safe_round(sender, "post_idle", (idx, idx + 1)))
    summary = summarize_powered(observations)
    print("P0249_POWERED_SUMMARY=" + json.dumps(summary, sort_keys=True), flush=True)
    print("P0249_POWERED_NO_SLA_OR_REAL_COLD_START_INFERENCE=true", flush=True)
    print("P0249_POWERED_NO_WRITES_NO_USER_AUTH_NO_PROD=true", flush=True)
    if any(summary[backend]["attempts"] != PER_BACKEND or
           summary[backend]["verified_expected_401"] != PER_BACKEND
           for backend in ORIGINS):
        return 4
    return 0


if __name__ == "__main__":
    verify_dev()
    raise SystemExit(run_powered())
