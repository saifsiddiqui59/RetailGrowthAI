"""Manual, bounded, no-JWT GET-only gateway sampler for existing RetailGrowthAI DEV."""
import argparse
from collections import Counter
import http.client
import json
from statistics import median
import time

HOST = "rgai-dev-functions-d4e5ddbd.azurewebsites.net"
SENTINEL = "11111111-1111-4111-8111-111111111111"
ROUTES = (
    ("campaign_read", "/api/campaigns/" + SENTINEL),
    ("render_read", "/api/render-jobs/" + SENTINEL),
)
GATEWAY_ERRORS = (502, 503, 504)


def probe_once(path, timeout_seconds):
    started = time.monotonic()
    connection = http.client.HTTPSConnection(HOST, timeout=timeout_seconds)
    try:
        # Fixed GET route, never send Authorization, cookies, real IDs or payload.
        connection.request("GET", path, headers={
            "Accept": "application/json", "Cache-Control": "no-store"})
        response = connection.getresponse()
        return {
            "status": response.status,
            "latency_ms": round((time.monotonic() - started) * 1000),
            "request_id_header": bool(response.getheader("X-Request-ID")),
            "transport": None,
        }
    except (TimeoutError, OSError, http.client.HTTPException) as exc:
        # Never expose exception content, response body, host request headers.
        return {
            "status": None,
            "latency_ms": round((time.monotonic() - started) * 1000),
            "request_id_header": False,
            "transport": "timeout" if isinstance(exc, TimeoutError) else "network",
        }
    finally:
        connection.close()


def collect(samples, timeout_seconds, pause_seconds, *,
            request_fn=probe_once, sleep_fn=time.sleep):
    if (type(samples) is not int or not 1 <= samples <= 6
            or type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 30
            or type(pause_seconds) is not int or not 0 <= pause_seconds <= 30):
        raise ValueError("unsafe sample count or timeout")
    rows = []
    for round_index in range(samples):
        for label, path in ROUTES:
            rows.append({
                "route": label, "round": round_index,
                **request_fn(path, timeout_seconds),
            })
        if round_index + 1 < samples:
            sleep_fn(pause_seconds)
    return rows


def summarize(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("empty sample")
    by_route = {}
    healthy = True
    reachable = True
    unexpected = False
    for label, _ in ROUTES:
        items = [x for x in rows if x["route"] == label]
        if not items:
            raise ValueError("missing route")
        counts = Counter(x["status"] for x in items)
        other = sum(x["status"] not in (None, 401, *GATEWAY_ERRORS) for x in items)
        reached = counts[401] > 0
        healthy = healthy and counts[401] == len(items)
        reachable = reachable and reached
        unexpected = unexpected or other > 0
        later = [x["latency_ms"] for x in items[1:]]
        by_route[label] = {
            "samples": len(items),
            "unauthorized_401": counts[401],
            "gateway_502_503_504": sum(counts[s] for s in GATEWAY_ERRORS),
            "timeouts": sum(x["transport"] == "timeout" for x in items),
            "network_errors": sum(x["transport"] == "network" for x in items),
            "unexpected_responses": other,
            "request_id_header_present": sum(x["request_id_header"] for x in items),
            "first_latency_ms": items[0]["latency_ms"],
            "subsequent_median_ms": round(median(later)) if later else None,
        }
    return {
        "destination": HOST,
        "scope": "unauthenticated_get_only_no_tenant_data",
        "protected_routes_reached": reachable,
        "healthy_all_samples_401": healthy,
        "degraded": not healthy,
        "unexpected_responses": unexpected,
        "routes": by_route,
        "interpretation": (
            "401 proves the protected route reached authentication; a 503 or "
            "missing X-Request-ID is not proof of a cold start or gateway "
            "origin. Correlate sanitized Application Insights and platform logs."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--pause-seconds", type=int, default=5)
    args = parser.parse_args(argv)
    try:
        report = summarize(collect(
            args.samples, args.timeout_seconds, args.pause_seconds))
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(report, sort_keys=True))
    # Degraded observations remain explicitly marked even when exit code is zero.
    return 0 if report["protected_routes_reached"] and not report["unexpected_responses"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
