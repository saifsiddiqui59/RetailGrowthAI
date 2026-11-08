#!/usr/bin/env python3
"""#249: read-only, fixed-window correlation of confirmed DEV HTTP failures.

This is an Azure platform hypothesis test, NOT a gateway fix or signed E2E.
Only the previously audited RetailGrowthAI Central India DEV workspace is read.
No customer HTTP, credentials, dynamic Kusto, deployment or billed capacity.
Raw Azure output, URLs, request paths, host identities and messages are never logged.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess

from flex_ingress_correlation import RG, LAW, audit_scope, azure
from p0_249_platform_correlation_readonly import platform_aggregate_rows

APP = "rgai-dev-functions-d4e5ddbd"
WINDOWS = (
    ("nov05_0403", "2026-11-05T04:02:00Z", "2026-11-05T04:11:00Z"),
    ("nov06_1952", "2026-11-06T19:51:00Z", "2026-11-06T19:59:00Z"),
    ("nov07_2019", "2026-11-07T20:18:00Z", "2026-11-07T20:27:00Z"),
    ("nov08_1755", "2026-11-08T17:54:00Z", "2026-11-08T18:00:00Z"),
)
KINDS = ("host", "requests", "activity")
EVENTS = frozenset((
    "drain_mode", "listener_stop", "worker_start", "worker_exit",
    "host_start", "specialization_timeout", "grpc_timeout",
))
COUNTS = ("events", "app_401", "reported_503", "internal_or_missing")
UTC_MINUTE = re.compile(
    r"^2026-11-[0-9]{2}T[0-9]{2}:[0-9]{2}:00(?:\.0{1,7})?(?:Z|\+00:00)$"
)
INSTANCE = 'tostring(column_ifexists("AppRoleInstance",""))'
# Do not let a near-matching app or another DEV project enter the query.
APP_SCOPE = (
    ' | where tolower(tostring(column_ifexists("AppRoleName",""))) == '
    '"rgai-dev-functions-d4e5ddbd"'
    ' or tolower(tostring(column_ifexists("_ResourceId",""))) endswith '
    '"/sites/rgai-dev-functions-d4e5ddbd"'
)


def _timestamp(value):
    if not isinstance(value, str) or not UTC_MINUTE.fullmatch(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed) or parsed.second or parsed.microsecond:
        return None
    for _, first, last in WINDOWS:
        start = datetime.fromisoformat(first.replace("Z", "+00:00"))
        end = datetime.fromisoformat(last.replace("Z", "+00:00"))
        if start <= parsed <= end:
            return value
    return None


def build_query(window, kind):
    """The caller can choose only fixed, incident-approved UTC windows and sources."""
    matches = [(start, end) for label, start, end in WINDOWS if label == window]
    if len(matches) != 1 or kind not in KINDS:
        raise ValueError("unreviewed Azure query")
    start, end = matches[0]
    timebox = f' | where TimeGenerated between (datetime({start}) .. datetime({end}))'
    bucket = 'bucket=bin(TimeGenerated,1m)'
    if kind == "host":
        return (
            'AppTraces' + timebox + APP_SCOPE
            + ' | extend msg=tolower(tostring(column_ifexists("Message","")))'
            + ' | extend event=case('
              'msg contains "drainmode","drain_mode",'
              'msg contains "stopped the listener","listener_stop",'
              'msg contains "worker process exited","worker_exit",'
              'msg contains "worker process started","worker_start",'
              'msg contains "host started","host_start",'
              'msg contains "specializeasync","specialization_timeout",'
              'msg contains "pendingitem.ontimeout","grpc_timeout",'
              '"other")'
            + ' | where event != "other"'
            + f' | summarize events=count() by {bucket},event,instance={INSTANCE}'
            + ' | order by bucket asc | take 80'
        )
    if kind == "requests":
        return (
            'AppRequests' + timebox + APP_SCOPE
            + ' | extend status=tostring(column_ifexists("ResultCode",""))'
            + ' | summarize events=count(),'
              'app_401=countif(status=="401"),'
              'reported_503=countif(status=="503"),'
              'internal_or_missing=countif(status=="0" or isempty(status))'
            + f' by {bucket},instance={INSTANCE}'
            + ' | order by bucket asc | take 80'
        )
    return (
        'AzureActivity' + timebox
        + ' | where ResourceGroup =~ "rg-retailgrowth-dev"'
        + ' | where tolower(tostring(column_ifexists("_ResourceId","")))'
          ' endswith "/sites/rgai-dev-functions-d4e5ddbd"'
        + f' | summarize events=count() by {bucket}'
        + ' | order by bucket asc | take 80'
    )


def _count(value):
    if type(value) is int:
        return value if 0 <= value <= 10000000 else None
    if isinstance(value, str) and value.isascii() and value.isdecimal() and len(value) <= 8:
        v = int(value)
        return v if v <= 10000000 else None
    return None


def safe_rows(payload, *, window, kind):
    if window not in {name for name, _, _ in WINDOWS} or kind not in KINDS:
        raise ValueError("unreviewed evidence scope")
    out = []
    for raw in platform_aggregate_rows(payload):
        when = _timestamp(raw.get("bucket"))
        count = _count(raw.get("events"))
        if when is None or count is None:
            continue
        row = {"bucket": when, "events": count}
        if kind == "host":
            event = raw.get("event")
            if not isinstance(event, str) or event not in EVENTS:
                continue
            row["event"] = event
        if kind == "requests":
            for field in COUNTS[1:]:
                v = _count(raw.get(field))
                if v is not None:
                    row[field] = v
        if kind != "activity":
            instance = raw.get("instance")
            if isinstance(instance, str) and 1 <= len(instance) <= 256:
                try:
                    row["host_hash"] = hashlib.sha256(
                        instance.encode("utf-8")
                    ).hexdigest()[:12]
                except UnicodeEncodeError:
                    pass
        out.append(row)
    return out[:80]


def collect() -> int:
    audit_scope()  # existing protected Azure OIDC + exact RG/app tags and location
    workspace = azure("monitor", "log-analytics", "workspace", "show",
                      "-g", RG, "-n", LAW).get("customerId")
    if not isinstance(workspace, str) or not workspace:
        print("P0249_RECENT_WORKSPACE=UNAVAILABLE", flush=True)
        return 4
    for label, _, _ in WINDOWS:
        for kind in KINDS:
            try:
                payload = azure("monitor", "log-analytics", "query",
                                "-w", workspace, "--analytics-query",
                                build_query(label, kind))
                rows = safe_rows(payload, window=label, kind=kind)
                status = "AGGREGATED" if rows else "NO_MATCHING_EVIDENCE"
            except (RuntimeError, ValueError, TypeError, OSError, subprocess.TimeoutExpired):
                rows, status = [], "UNAVAILABLE"
            # All dynamic Azure text/IDs are excluded before serialization.
            print("P0249_INCIDENT=" + json.dumps({
                "window": label, "source": kind, "status": status, "rows": rows,
            }, sort_keys=True, separators=(",", ":")), flush=True)
    print("P0249_NO_HTTP_REQUEST_TO_INSTANCE_CAUSAL_PROOF=true", flush=True)
    print("P0249_READ_ONLY_NO_CONFIG_WRITES_NO_NEW_RESOURCES=true", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(collect())
