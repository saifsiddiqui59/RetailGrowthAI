"""One-shot read-only Azure Flex ingress/scale correlation for RetailGrowthAI DEV.

No sensitive Azure settings, tenant identifiers, response bodies, headers, or raw
Application Insights messages are printed. This is NOT a health acceptance test.
"""
import datetime
import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request

RG = "rg-retailgrowth-dev"
APP = "rgai-dev-functions-d4e5ddbd"
LAW = "rgai-dev-law"
HOST = f"https://{APP}.azurewebsites.net"
UUID = "11111111-1111-4111-8111-111111111111"


def azure(*args):
    """Use fixed Azure CLI read methods; never emit raw stderr or response."""
    cmd = ["az", *args, "--output", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=65)
    if result.returncode:
        raise RuntimeError("Azure read unavailable")
    return json.loads(result.stdout)


def audit_scope():
    sub = os.environ.get("RGAI_DEV_EXPECTED_SUBSCRIPTION", "")
    if not sub:
        raise RuntimeError("Missing protected DEV subscription")
    account = azure("account", "show")
    if account.get("id") != sub:
        raise RuntimeError("Azure subscription mismatch")
    group = azure("group", "show", "-n", RG)
    app = azure("functionapp", "show", "-g", RG, "-n", APP)
    tags = {k.lower(): str(v).lower() for k, v in (group.get("tags") or {}).items()}
    if not (group.get("name") == RG
            and group.get("location", "").replace(" ", "").lower() == "centralindia"
            and tags.get("app") == "retailgrowthai"
            and tags.get("environment") == "dev"
            and app.get("name") == APP
            and app.get("location", "").replace(" ", "").lower() == "centralindia"):
        raise RuntimeError("DEV resource identity mismatch")
    scale = (app.get("functionAppConfig") or {}).get("scaleAndConcurrency") or {}
    runtime = (app.get("functionAppConfig") or {}).get("runtime") or {}
    always_ready = scale.get("alwaysReady")
    http_count = (sum(int(x.get("instanceCount", 0)) for x in always_ready
                      if x.get("name") == "http")
                  if isinstance(always_ready, list) else "unknown")
    print("P0_DEV_EXACT_SCOPE_VERIFIED=true", flush=True)
    for key, val in (
        ("HOST_STATE", app.get("state", "unknown")),
        ("RUNTIME", str(runtime.get("name", "unknown")) + ":" +
         str(runtime.get("version", "unknown"))),
        ("INSTANCE_MEMORY_MB", scale.get("instanceMemoryMB", "unknown")),
        ("MAX_INSTANCES", scale.get("maximumInstanceCount", "unknown")),
        ("HTTP_CONCURRENCY", ((scale.get("triggers") or {}).get("http") or {}).get(
            "perInstanceConcurrency", "unknown")),
        ("ALWAYS_READY_HTTP", http_count),
    ):
        print(f"P0_{key}={val}", flush=True)
    print("P0_NO_ENV_VALUES_OR_CREDENTIALS_EXPORTED=true", flush=True)
    return app["id"]


def probe_http():
    routes = [
        ("GET", "campaign.read", f"/api/campaigns/{UUID}", 401),
        ("GET", "unknown.route", "/api/p0-route-that-does-not-exist", 404),
        ("POST", "campaign.create", "/api/campaigns", 401),
        ("GET", "campaign.read", f"/api/campaigns/{UUID}", 401),
        ("GET", "reel.read", f"/api/render-jobs/{UUID}", 401),
        ("POST", "poster.select", f"/api/poster-drafts/{UUID}/select", 401),
        ("GET", "campaign.read", f"/api/campaigns/{UUID}", 401),
        ("GET", "unknown.route", "/api/p0-route-that-does-not-exist", 404),
    ]
    anomalies = 0
    for idx, (method, label, path, expected) in enumerate(routes, 1):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat(
            timespec="seconds")
        t0 = time.monotonic()
        request = urllib.request.Request(
            HOST + path, method=method,
            data=b"{}" if method == "POST" else None,
            headers={"Accept": "application/json", "Cache-Control": "no-store",
                     "Content-Type": "application/json"})
        status = None
        marker = False
        transport = "ok"
        try:
            with urllib.request.urlopen(request, timeout=18) as response:
                status = response.status
                marker = bool(response.headers.get("X-Request-ID"))
        except urllib.error.HTTPError as error:
            status = error.code
            marker = bool(error.headers.get("X-Request-ID"))
            error.close()
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
            transport = "timeout_or_network"
        seconds = round(time.monotonic() - t0, 3)
        bad = (status != expected or seconds > 10 or
               (label != "unknown.route" and not marker))
        anomalies += int(bad)
        # Deliberately omit host path, UUID, response body, header values and tokens.
        print(f"P0_HTTP_SAMPLE_{idx}=utc:{now} method:{method} label:{label} "
              f"status:{status or '000'} seconds:{seconds} "
              f"app_marker:{str(marker).lower()} transport:{transport} "
              f"anomalous:{str(bad).lower()}", flush=True)
    print(f"P0_HTTP_ANOMALIES={anomalies}_OF_{len(routes)}", flush=True)
    print("P0_OBSERVATION_SUCCESS_IS_NOT_HTTP_ACCEPTANCE=true", flush=True)


def platform_metrics(app_id):
    definitions = azure("monitor", "metrics", "list-definitions",
                        "--resource", app_id)
    supported = set()
    for entry in definitions.get("value", []) if isinstance(definitions, dict) else definitions:
        name = entry.get("name") or {}
        supported.add(name.get("value") if isinstance(name, dict) else name)
    for metric, aggregate in (
        ("InstanceCount", "Average"),
        ("Requests", "Total"),
        ("AlwaysReadyUnits", "Total"),
        ("CpuPercentage", "Average"),
        ("AverageMemoryWorkingSet", "Average"),
    ):
        if metric not in supported:
            print(f"P0_METRIC_{metric}=unsupported", flush=True)
            continue
        try:
            data = azure("monitor", "metrics", "list", "--resource", app_id,
                         "--metric", metric, "--interval", "PT1M",
                         "--aggregation", aggregate)
            points = []
            for obj in data.get("value", []):
                for series in obj.get("timeseries", []):
                    for row in series.get("data", []):
                        val = row.get(aggregate.lower())
                        if isinstance(val, (int, float)):
                            points.append((row.get("timeStamp"), round(val, 2)))
            # No instance or subscription dimension printed.
            print("P0_METRIC_" + metric + "=" +
                  json.dumps(points[-20:], separators=(",", ":")), flush=True)
        except (RuntimeError, subprocess.TimeoutExpired, ValueError):
            print(f"P0_METRIC_{metric}=unavailable", flush=True)


def safe_telemetry():
    workspace = azure("monitor", "log-analytics", "workspace", "show",
                      "-g", RG, "-n", LAW).get("customerId")
    if not workspace:
        raise RuntimeError("DEV telemetry workspace unavailable")
    queries = [
        "AppRequests | where TimeGenerated > ago(1h) "
        "| summarize n=count(),p95_ms=percentile(DurationMs,95) "
        "by bucket=bin(TimeGenerated,5m),ResultCode | order by bucket asc",
        "AppExceptions | where TimeGenerated > ago(1h) "
        "| summarize n=count() by bucket=bin(TimeGenerated,5m),ExceptionType "
        "| order by bucket asc",
        "AppTraces | where TimeGenerated > ago(1h) "
        "| extend category=case(Message contains 'Worker process exited',"
        "'worker.exit',Message contains 'Worker process started','worker.start',"
        "Message contains 'host startup','host.startup','other') "
        "| where category!='other' "
        "| summarize n=count() by bucket=bin(TimeGenerated,5m),category "
        "| order by bucket asc",
    ]
    for idx, query in enumerate(queries, 1):
        try:
            result = azure("monitor", "log-analytics", "query", "-w", workspace,
                           "--analytics-query", query)
            # These KQL queries have only allowlisted bucket/type/count columns.
            tables = result.get("tables", []) if isinstance(result, dict) else result
            print("P0_TELEMETRY_" + str(idx) + "=" +
                  json.dumps(tables[:15], sort_keys=True), flush=True)
        except (RuntimeError, subprocess.TimeoutExpired, ValueError):
            print(f"P0_TELEMETRY_{idx}=unavailable", flush=True)
    print("P0_TELEMETRY_MAY_LAG_AND_IS_SAMPLED=true", flush=True)


def main():
    app_id = audit_scope()
    probe_http()
    platform_metrics(app_id)
    safe_telemetry()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
