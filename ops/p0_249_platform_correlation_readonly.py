#!/usr/bin/env python3
"""Issue #249: scoped read-only Azure host/worker/ingress diagnostic.

Exact existing RetailGrowthAI DEV only. Historical UTC windows are fixed.
All Azure records are aggregated in Kusto; output is only timestamp buckets,
allowlisted event categories/status/counts and hashed host-instance identity.
Never print HTTP path, tenant IDs, request IDs, messages, exceptions, raw
instance IDs, credentials or Azure CLI stderr. No HTTP probes or cloud writes.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from flex_ingress_correlation import RG, LAW, audit_scope, azure

WINDOWS = (
    ("failed_canary", "2026-10-28T19:35:00Z", "2026-10-28T19:51:00Z"),
    ("post_rollback", "2026-10-28T19:59:00Z", "2026-10-28T20:02:00Z"),
)
APP_FILTER = (
    ' | where (tolower(tostring(column_ifexists("_ResourceId", ""))) '
    'contains "rgai-dev-functions-d4e5ddbd" or '
    'tolower(tostring(column_ifexists("AppRoleName", ""))) '
    'contains "rgai-dev-functions-d4e5ddbd")'
)
TYPES = (
    "specialization_timeout", "grpc_pending_timeout", "worker_startstream",
    "worker_startup_timeout", "worker_start", "worker_exit",
    "host_start", "rpc_exception", "connection_aborted",
    "host_initialization", "other",
)
CATEGORIES = frozenset(TYPES)
INSTANCE = 'tostring(column_ifexists("AppRoleInstance",""))'
STATES = frozenset(("requests", "traces", "exceptions", "function_logs", "activity", "host_timeline", "request_status_timeline", "startup_401_link"))
STATUS = re.compile(r"^[1-5][0-9]{2}$")
BUCKET = re.compile(r"^2026-10-28T(19|20):[0-5][0-9]:00(?:Z|\+00:00)$")


def classify_expr(*, field: str) -> str:
    """Kusto category labels come from constants, never raw exception/message."""
    clauses = (
        ("SpecializeAsync", "specialization_timeout"),
        ("PendingItem.OnTimeout", "grpc_pending_timeout"),
        ("StartStream", "worker_startstream"),
        ("ProcessStartupTimeout", "worker_startup_timeout"),
        ("Worker process exited", "worker_exit"),
        ("Worker process started", "worker_start"),
        ("host startup", "host_start"),
        ("RpcException", "rpc_exception"),
        ("ConnectionAbortedException", "connection_aborted"),
        ("host initialization", "host_initialization"),
    )
    return 'case(' + ', '.join(
        f'{field} contains "{needle}", "{label}"' for needle, label in clauses
    ) + ', "other")'


def queries(start: str, end: str) -> dict[str, str]:
    if (start, end) not in {(a, b) for _, a, b in WINDOWS}:
        raise ValueError("unreviewed Azure time range")
    time_range = (
        f' | where TimeGenerated between (datetime({start}) .. datetime({end}))'
    )
    exception_message = 'strcat(ExceptionType, " ", tostring(column_ifexists("OuterMessage","")))'
    function_message = 'tostring(column_ifexists("Message", ""))'
    prefix = lambda table: table + time_range + APP_FILTER
    instance = f' | extend instance={INSTANCE}'
    bucket = 'bucket=bin(TimeGenerated,1m)'
    return {
        "requests": (
            prefix("AppRequests") + instance
            + f' | summarize events=count() by {bucket}, status=tostring(ResultCode), instance'
            + ' | order by bucket asc | take 80'
        ),
        "traces": (
            prefix("AppTraces") + instance
            + f' | extend category={classify_expr(field="Message")}'
            + ' | where category != "other"'
            + f' | summarize events=count() by {bucket}, category, instance'
            + ' | order by bucket asc | take 80'
        ),
        # A full-window minute timeline does not group by host instance, so
        # the first 30 rows cannot conceal later startup/timeout events. Counts
        # distinguish routine initialization from actual timeout/exit hints.
        "host_timeline": (
            prefix("AppTraces")
            + ' | summarize events=count(), '
              'worker_start=countif(Message contains "Worker process started"), '
              'host_initialization=countif(Message contains "host initialization"), '
              'worker_exit=countif(Message contains "Worker process exited"), '
              'specialization_timeout=countif(Message contains "SpecializeAsync"), '
              'grpc_pending_timeout=countif(Message contains "PendingItem.OnTimeout"), '
              'worker_startstream=countif(Message contains "StartStream"), '
              'worker_startup_timeout=countif(Message contains "ProcessStartupTimeout"), '
              'rpc_exception=countif(Message contains "RpcException") '
              'by bucket=bin(TimeGenerated,1m)'
            + ' | order by bucket asc | take 25'
        ),
        # ResultCode in AppRequests can contain non-HTTP/internal values.
        # Count classes without outputting raw codes or request paths.
        # An internal/unclassified request is NOT a client HTTP 503.
        "request_status_timeline": (
            prefix("AppRequests")
            + ' | extend result=tostring(column_ifexists("ResultCode", ""))'
              ' | summarize events=count(),'
              ' app_401=countif(result=="401"),'
              ' reported_503=countif(result=="503"),'
              ' other_4xx=countif(result startswith "4" and result!="401"),'
              ' other_5xx=countif(result startswith "5" and result!="503"),'
              ' missing_or_zero=countif(isempty(result) or result=="0"),'
              ' other_status=countif(isnotempty(result) and result!="0"'
              ' and not(result startswith "4") and not(result startswith "5"))'
              ' by bucket=bin(TimeGenerated,1m)'
            + ' | order by bucket asc | take 25'
        ),
        # A worker-start trace plus ANY 401 on the same instance at ANY time
        # in the incident window was previously called linked. That could
        # count a 401 from BEFORE startup or many minutes later. Limit this
        # aggregate hint to 401 logged within 120s AFTER the start event.
        # The 401 remains unverified at request/handler level: log sampling,
        # scale groups and absent request-ID joins forbid causal attribution.
        "startup_401_link": (
            'let starts = ' + prefix("AppTraces")
            + ' | where Message contains "Worker process started"'
            + f' | extend instance={INSTANCE}'
            + ' | where isnotempty(instance)'
            + ' | project start_time=TimeGenerated, instance; '
            + 'let authenticated = ' + prefix("AppRequests")
            + ' | where tostring(column_ifexists("ResultCode", "")) == "401"'
            + f' | extend instance={INSTANCE}'
            + ' | where isnotempty(instance)'
            + ' | project request_time=TimeGenerated, instance; '
            + 'starts | join kind=leftouter authenticated on instance'
            + ' | summarize nearby_401=max(iff(isnotnull(request_time)'
              ' and request_time >= start_time and request_time <= start_time + 2m, 1, 0))'
              ' by start_time, instance'
            + ' | summarize events=count(),'
              ' linked_401=countif(nearby_401>0),'
              ' unlinked=countif(nearby_401==0)'
              ' by bucket=bin(start_time,1m)'
            + ' | order by bucket asc | take 25'
        ),
        "exceptions": (
            prefix("AppExceptions") + instance
            + f' | extend category={classify_expr(field=exception_message)}'
            + ' | where category != "other"'
            + f' | summarize events=count() by {bucket}, category, instance'
            + ' | order by bucket asc | take 80'
        ),
        "function_logs": (
            prefix("FunctionAppLogs") + instance
            + f' | extend category={classify_expr(field=function_message)}'
            + ' | where category != "other"'
            + f' | summarize events=count() by {bucket}, category, instance'
            + ' | order by bucket asc | take 80'
        ),
        "activity": (
            'AzureActivity' + time_range
            + ' | where ResourceGroup =~ "rg-retailgrowth-dev"'
            + ' | where tolower(tostring(column_ifexists("_ResourceId","")))'
              ' contains "rgai-dev-functions-d4e5ddbd"'
            + f' | summarize events=count() by {bucket}'
            + ' | order by bucket asc | take 80'
        ),
    }


def _safe_count(value):
    """Only a small, nonnegative integer; never turn arbitrary log fields into output."""
    if isinstance(value, str) and value.isascii() and value.isdecimal() and len(value) <= 8:
        value = int(value)
    elif type(value) is float and value.is_integer():
        value = int(value)
    return value if type(value) is int and 0 <= value <= 10000000 else None


COUNT_FIELDS = frozenset((
    "worker_start", "host_initialization", "worker_exit",
    "specialization_timeout", "grpc_pending_timeout", "worker_startstream",
    "worker_startup_timeout", "rpc_exception",
    "app_401", "reported_503", "other_4xx", "other_5xx",
    "missing_or_zero", "other_status", "linked_401", "unlinked",
))


# Historical platform inspector Kusto queries explicitly return at most 80
# aggregate rows. The generic historical telemetry decoder caps at 30; using
# it here silently discarded later worker/host evidence. Keep this bounded
# parser private to this inspector; raw Azure rows never reach stdout.
MAX_AGGREGATE_ROWS = 80


def platform_aggregate_rows(payload) -> list[dict]:
    if isinstance(payload, list):
        return [r for r in payload[:MAX_AGGREGATE_ROWS] if isinstance(r, dict)]
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("value"), list):
        return [r for r in payload["value"][:MAX_AGGREGATE_ROWS]
                if isinstance(r, dict)]
    tables = payload.get("tables")
    if not isinstance(tables, list):
        return []
    collected = []
    for table in tables[:2]:
        if not isinstance(table, dict):
            continue
        cols, rows = table.get("columns"), table.get("rows")
        if not isinstance(cols, list) or not isinstance(rows, list):
            continue
        names = [c.get("name") if isinstance(c, dict) else None
                 for c in cols[:64]]
        if (not names or len(cols) > 64
                or any(not isinstance(n, str) or not n for n in names)
                or len(set(names)) != len(names)):
            continue
        for row in rows:
            if len(collected) >= MAX_AGGREGATE_ROWS:
                return collected
            if isinstance(row, list) and len(row) == len(names):
                collected.append(dict(zip(names, row)))
    return collected


def safe_rows(payload) -> list[dict]:
    """Sanitize before reporting; never serialize complete Azure query output."""
    out = []
    for raw in platform_aggregate_rows(payload):
        row = {}
        count = _safe_count(raw.get("events"))
        if count is not None:
            row["events"] = count
        for key in COUNT_FIELDS:
            value = _safe_count(raw.get(key))
            if value is not None:
                row[key] = value
        when = raw.get("bucket")
        if isinstance(when, str) and BUCKET.fullmatch(when):
            row["bucket"] = when
        category = raw.get("category")
        if category in CATEGORIES:
            row["category"] = category
        status = raw.get("status")
        if isinstance(status, str) and STATUS.fullmatch(status):
            row["status"] = status
        instance = raw.get("instance")
        if isinstance(instance, str) and 0 < len(instance) <= 256:
            row["host_hash"] = hashlib.sha256(instance.encode()).hexdigest()[:12]
        if row.get("bucket") and "events" in row:
            out.append(row)
    return out[:80]


def collect() -> int:
    # Owner-approved read-only identity check; never query any other app.
    audit_scope()
    data = azure("monitor", "log-analytics", "workspace", "show", "-g", RG, "-n", LAW)
    wid = data.get("customerId")
    if not isinstance(wid, str) or not wid:
        print("P0249_WORKSPACE=UNAVAILABLE", flush=True)
        return 0
    print("P0249_WORKSPACE=EXISTING_DEV_VERIFIED", flush=True)
    for label, start, end in WINDOWS:
        for kind, q in queries(start, end).items():
            try:
                result = azure("monitor", "log-analytics", "query",
                               "-w", wid, "--analytics-query", q)
                raw_rows = platform_aggregate_rows(result)
                rows = safe_rows(result)
                outcome = "AGGREGATED" if rows else "EMPTY_OR_FILTERED"
                # Only report schema presence/type of fixed allowlisted fields,
                # never values/messages or dynamic Kusto column names.
                if not rows and raw_rows:
                    sample = raw_rows[0]
                    known = ("bucket", "events", "status", "category", "instance")
                    print("P0249_SCHEMA=" + json.dumps({
                        "window": label, "source": kind,
                        "total_rows_capped": len(raw_rows),
                        "field_types": {key: type(sample[key]).__name__
                                        for key in known if key in sample},
                    }, sort_keys=True), flush=True)
            except (RuntimeError, ValueError, TypeError, subprocess.TimeoutExpired):
                rows, outcome = [], "UNAVAILABLE"
            print("P0249_CAUSAL=" + json.dumps({
                "window": label, "source": kind, "result": outcome,
                "rows": rows,
            }, separators=(",", ":"), sort_keys=True), flush=True)
    print("P0249_CAUSE=UNPROVEN_WITHOUT_REQUEST_TO_INSTANCE_PLATFORM_TRACE", flush=True)
    print("P0249_READ_ONLY_NO_HTTP_TRAFFIC_NO_CLOUD_MUTATION=true", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(collect())
