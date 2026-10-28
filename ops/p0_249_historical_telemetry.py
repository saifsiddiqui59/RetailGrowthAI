#!/usr/bin/env python3
"""Read-only fixed-window Azure Flex host/worker telemetry for confirmed Issue #249.

Public-output contract: allowlisted *aggregate* counts/buckets/metric numbers only.
Never emit raw messages, exception text, resource/customer identifiers or secrets.
A 503 with no application marker is NOT itself proof of cold start/worker failure.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone

from flex_ingress_correlation import APP, RG, LAW, audit_scope, azure

START = "2026-10-28T10:25:40Z"
END = "2026-10-28T10:35:30Z"
WINDOWS = (
    ("live_75s", START, END),
    ("signed_feature2", "2026-10-28T08:48:30Z", "2026-10-28T08:51:30Z"),
    ("prior_12s", "2026-10-28T09:39:45Z", "2026-10-28T09:46:30Z"),
)
METRICS = (("InstanceCount", "Average"), ("AlwaysReadyUnits", "Total"),
           ("CpuPercentage", "Average"), ("AverageMemoryWorkingSet", "Average"))
OUTPUT_COLUMNS = frozenset(("bucket", "status", "events", "p95_ms", "category",
                            "metric", "value", "success"))
APP_FILTER = ('| where tolower(tostring(column_ifexists("_ResourceId", ""))) '
              'contains "rgai-dev-functions-d4e5ddbd" '
              'or tolower(tostring(column_ifexists("AppRoleName", ""))) '
              'contains "rgai-dev-functions-d4e5ddbd"')
WINDOW_PREFIX = ' | where TimeGenerated between (datetime({start}) .. datetime({end})) '


def aggregate_records(output):
    """Azure CLI returns either row dicts or tables/columns/rows."""
    if isinstance(output, list):
        return [x for x in output if isinstance(x, dict)][:30]
    if isinstance(output, dict):
        if isinstance(output.get("value"), list):
            return [x for x in output["value"] if isinstance(x, dict)][:30]
        out = []
        for t in output.get("tables", [])[:2]:
            if not isinstance(t, dict):
                continue
            cols = [c.get("name", "") for c in t.get("columns", []) if isinstance(c, dict)]
            for row in t.get("rows", [])[:30]:
                if isinstance(row, list) and len(row) == len(cols):
                    out.append(dict(zip(cols, row)))
        return out[:30]
    return []


def safe_aggregate_rows(output):
    rows = []
    for item in aggregate_records(output):
        row = {}
        for key in OUTPUT_COLUMNS:
            v = item.get(key)
            if type(v) in (int, float, bool):
                row[key] = v
            elif isinstance(v, str) and len(v) <= 64:
                # No raw dynamic identifiers or messages, just known buckets/codes/classes.
                if key == "bucket" and v.startswith("2026-10-28T"):
                    row[key] = v
                elif key in ("category", "metric") and v in (
                    "worker_start", "worker_exit", "host_start", "rpc_exception",
                    "connection_aborted", "other", "InstanceCount", "AlwaysReadyUnits",
                    "CpuPercentage", "AverageMemoryWorkingSet"):
                    row[key] = v
                elif key == "status" and (v.isdecimal() and len(v) <= 3):
                    row[key] = v
        if row:
            rows.append(row)
    return rows


def build_queries(start, end):
    if (start, end) not in [(s, e) for _, s, e in WINDOWS]:
        raise ValueError("unapproved timestamp window")
    time_filter = WINDOW_PREFIX.format(start=start, end=end)
    status = ("AppRequests" + time_filter + APP_FILTER +
              ' | summarize events=count(), p95_ms=round(percentile(DurationMs,95),1)'
              ' by bucket=bin(TimeGenerated,1m),status=tostring(ResultCode)'
              ' | order by bucket asc | take 30')
    trace = ("AppTraces" + time_filter + APP_FILTER +
             ' | extend category=case(Message contains "Worker process started", "worker_start",'
             ' Message contains "Worker process exited", "worker_exit",'
             ' Message contains "host startup", "host_start", "other")'
             ' | where category != "other"'
             ' | summarize events=count() by bucket=bin(TimeGenerated,1m),category'
             ' | order by bucket asc | take 30')
    exceptions = ("AppExceptions" + time_filter + APP_FILTER +
                  ' | extend category=case(ExceptionType contains "RpcException","rpc_exception",'
                  ' ExceptionType contains "ConnectionAbortedException","connection_aborted","other")'
                  ' | summarize events=count() by bucket=bin(TimeGenerated,1m),category'
                  ' | order by bucket asc | take 30')
    deps = ("AppDependencies" + time_filter + APP_FILTER +
            ' | summarize events=count() by bucket=bin(TimeGenerated,1m),'
            ' success=tostring(Success) | order by bucket asc | take 30')
    activity = ('AzureActivity' + time_filter +
                ' | where ResourceGroup =~ "rg-retailgrowth-dev"'
                ' | where tolower(tostring(column_ifexists("_ResourceId", "")))'
                ' contains "rgai-dev-functions-d4e5ddbd"'
                ' | summarize events=count() by bucket=bin(TimeGenerated,1m)'
                ' | order by bucket asc | take 30')
    return (("requests", status), ("worker_traces", trace),
            ("exceptions", exceptions), ("dependencies", deps),
            ("activity", activity))


def safe_metric_points(result, aggregation, name):
    rows = result.get("value", []) if isinstance(result, dict) else result if isinstance(result, list) else []
    points = []
    for entry in rows[:8]:
        if not isinstance(entry, dict):
            continue
        for series in entry.get("timeseries", [])[:3]:
            for point in series.get("data", [])[:22]:
                value = point.get(aggregation.lower())
                stamp = point.get("timeStamp")
                if type(value) in (int, float) and isinstance(stamp, str) and stamp.startswith("2026-10-28T"):
                    points.append({"bucket": stamp, "metric": name, "value": round(value, 3)})
    return points[:22]


def collect():
    resource_id = audit_scope()  # OIDC exact subscription, Central India tagged DEV app
    info = azure("monitor", "log-analytics", "workspace", "show", "-g", RG, "-n", LAW)
    workspace = info.get("customerId", "")
    if not isinstance(workspace, str) or not workspace:
        print("P0249_LAW=UNAVAILABLE", flush=True)
    else:
        print("P0249_LAW=EXISTING_DEV_WORKSPACE_VERIFIED", flush=True)
        for label, start, end in WINDOWS:
            for kind, query in build_queries(start, end):
                try:
                    data = azure("monitor", "log-analytics", "query", "-w", workspace,
                                 "--analytics-query", query)
                    rows = safe_aggregate_rows(data)
                    print("P0249_TELEMETRY=" + json.dumps(
                        {"window": label, "kind": kind, "result": "rows" if rows else "empty_or_filtered",
                         "rows": rows}, sort_keys=True, separators=(",", ":")), flush=True)
                except (RuntimeError, subprocess.TimeoutExpired, ValueError, TypeError):
                    print("P0249_TELEMETRY=" + json.dumps(
                        {"window": label, "kind": kind, "result": "UNAVAILABLE"}, sort_keys=True), flush=True)
    try:
        defs = azure("monitor", "metrics", "list-definitions", "--resource", resource_id)
        known = set()
        for entry in aggregate_records(defs):
            name = entry.get("name", {})
            known.add(name.get("value") if isinstance(name, dict) else name)
        print("P0249_AZURE_METRIC_DEFINITIONS=READ", flush=True)
    except (RuntimeError, subprocess.TimeoutExpired, ValueError, TypeError):
        known = set()
        print("P0249_AZURE_METRIC_DEFINITIONS=UNAVAILABLE", flush=True)
    for name, aggregate in METRICS:
        if name not in known:
            print("P0249_METRIC=" + json.dumps(
                {"metric": name, "result": "unsupported_or_unavailable"}, sort_keys=True), flush=True)
            continue
        try:
            resp = azure("monitor", "metrics", "list", "--resource", resource_id,
                         "--metric", name, "--interval", "PT1M",
                         "--start-time", START, "--end-time", END,
                         "--aggregation", aggregate)
            points = safe_metric_points(resp, aggregate, name)
            print("P0249_METRIC=" + json.dumps({"metric": name, "result": "rows" if points else "empty",
                  "rows": points}, sort_keys=True, separators=(",", ":")), flush=True)
        except (RuntimeError, subprocess.TimeoutExpired, ValueError, TypeError):
            print("P0249_METRIC=" + json.dumps({"metric": name, "result": "UNAVAILABLE"},
                                              sort_keys=True), flush=True)
    print("P0249_ROOT_CAUSE_NOT_ASSUMED=true", flush=True)
    print("P0249_READ_ONLY_NO_HTTP_PROBES_NO_PROD_NO_SETTINGS_CHANGED=true", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(collect())
