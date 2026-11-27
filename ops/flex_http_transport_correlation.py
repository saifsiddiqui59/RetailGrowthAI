"""Anonymous GET-only transport-phase evidence for existing RetailGrowthAI DEV Flex app.

Observational only: no credentials, customer data, request bodies, mutable verbs,
secrets, unapproved capacity or resources.
"""
from __future__ import annotations
import datetime as dt
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path
from flex_ingress_correlation import RG, LAW, UUID, HOST, audit_scope, azure
from p0_249_cold_warm_http_probe import final_app_request_marker

PHASE_FORMAT = ("%{http_code}|%{time_namelookup}|%{time_connect}|"
                "%{time_appconnect}|%{time_pretransfer}|"
                "%{time_starttransfer}|%{time_total}")
CASES = (
    ("campaign_auth_gate", "/api/campaigns/" + UUID, 401),
    ("unknown_route", "/api/p0-route-that-does-not-exist", 404),
    ("reel_auth_gate", "/api/render-jobs/" + UUID, 401),
    ("campaign_auth_gate", "/api/campaigns/" + UUID, 401),
    ("unknown_route", "/api/p0-route-that-does-not-exist", 404),
    ("campaign_auth_gate", "/api/campaigns/" + UUID, 401),
    ("reel_auth_gate", "/api/render-jobs/" + UUID, 401),
    ("unknown_route", "/api/p0-route-that-does-not-exist", 404),
)

def probe_once(label: str, path: str, expected: int, index: int) -> bool:
    """Record bounded timing phases and presence, never contents, of app correlation."""
    with tempfile.TemporaryDirectory(prefix="rgai-p0-http-") as temp:
        headers = Path(temp) / "headers"
        cmd = [
            "curl", "--silent", "--show-error", "--http1.1",
            "--noproxy", "*", "--connect-timeout", "5", "--max-time", "20",
            "--output", "/dev/null", "--dump-header", str(headers),
            "--write-out", PHASE_FORMAT,
            "--header", "Accept: application/json",
            "--header", "Cache-Control: no-store", HOST + path,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
            fields = result.stdout.strip().split("|")
            if len(fields) != 7:
                raise ValueError("Missing timing fields")
            status = int(fields[0]) if fields[0].isdigit() else 0
            raw_phases = [float(v) for v in fields[1:]]
            if any(not math.isfinite(v) or not 0 <= v <= 25 for v in raw_phases):
                raise ValueError("Untrusted transport timing")
            phases = [round(v, 3) for v in raw_phases]
            marker = (final_app_request_marker(headers.read_text(errors="replace"))
                      if headers.is_file() else False)
            transport = "ok" if result.returncode == 0 else "curl_failure"
        except (OSError, ValueError, subprocess.TimeoutExpired):
            status, phases, marker, transport = 0, [0.0] * 6, False, "unavailable"
        # A failed curl command cannot certify a healthy handler even if it
        # happened to print an expected HTTP status and fast phase timings.
        bad = (transport != "ok" or status != expected
               or (label != "unknown_route" and not marker)
               or phases[-1] > 10)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print("P0_TRANSPORT_SAMPLE=" + json.dumps({
            "seq": index, "utc": stamp, "route_class": label,
            "status": status, "app_marker_present": bool(marker),
            "dns_s": phases[0], "tcp_s": phases[1], "tls_s": phases[2],
            "pretransfer_s": phases[3], "first_byte_s": phases[4],
            "total_s": phases[5], "transport": transport, "anomalous": bad,
        }, sort_keys=True, separators=(",", ":")), flush=True)
        return bad

# Azure CLI can return either a row-list or REST-style tables. Extract only
# the fixed aggregate fields from both shapes, NEVER raw Kusto data/log content.
_ALLOWED_FIELDS = frozenset((
    "bucket", "ResultCode", "requests", "p95_ms", "p99_ms", "class",
    "events", "Level", "ActivityStatusValue", "operations",
))
_FIXED_CLASSES = frozenset(("worker_exit", "worker_start", "host_start", "host_lease"))
_FIXED_LEVELS = frozenset(("Information", "Warning", "Error", "Critical", "Verbose", "Debug"))
_FIXED_ACTIVITY = frozenset(("Succeeded", "Failed", "Accepted", "Started", "Canceled", "Cancelled"))
_BUCKET_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d{1,7})?(?:Z|\+00:00)$"
)


def _safe_aggregate_value(field, value):
    """Only schema-validated scalars; never surface arbitrary Azure text."""
    if field == "bucket":
        return value if isinstance(value, str) and _BUCKET_RE.fullmatch(value) else None
    if field == "ResultCode":
        return str(value) if type(value) in (str, int) and re.fullmatch(
            r"[1-5][0-9]{2}", str(value)) else None
    if field == "class":
        return value if isinstance(value, str) and value in _FIXED_CLASSES else None
    if field == "Level":
        return value if isinstance(value, str) and value in _FIXED_LEVELS else None
    if field == "ActivityStatusValue":
        return value if isinstance(value, str) and value in _FIXED_ACTIVITY else None
    if field in ("requests", "events", "operations"):
        return value if type(value) is int and 0 <= value <= 10000000 else None
    if field in ("p95_ms", "p99_ms"):
        return (round(value, 3) if type(value) in (float, int)
                and math.isfinite(value) and 0 <= value <= 10000000 else None)
    return None


# Restrict ALL telemetry sources to the original Flex Function App, not just
# the shared DEV workspace. Missing app identifiers fail to match.
_APP_FILTER = (
    ' | where (tolower(tostring(column_ifexists("AppRoleName",""))) == '
    '"rgai-dev-functions-d4e5ddbd" or '
    'tolower(tostring(column_ifexists("_ResourceId",""))) endswith '
    '"/sites/rgai-dev-functions-d4e5ddbd")'
)


def safe_aggregate_rows(result):
    candidates = []
    if isinstance(result, list):
        candidates = result[:18]
    elif isinstance(result, dict):
        tables = result.get("tables")
        if isinstance(tables, list):
            for table in tables[:2]:
                if not isinstance(table, dict):
                    continue
                cols = [c.get("name") if isinstance(c, dict) else ""
                        for c in table.get("columns", [])]
                for entry in table.get("rows", [])[:18]:
                    if isinstance(entry, list):
                        candidates.append(dict(zip(cols, entry)))
        elif isinstance(result.get("value"), list):
            candidates = result["value"][:18]
    safe = []
    for row in candidates[:18]:
        if not isinstance(row, dict):
            continue
        verified = {}
        for key, val in row.items():
            if key not in _ALLOWED_FIELDS:
                continue
            clean = _safe_aggregate_value(key, val)
            if clean is not None:
                verified[key] = clean
        if verified:
            safe.append(verified)
    return safe

def log_buckets() -> None:
    workspace = azure("monitor", "log-analytics", "workspace", "show",
                      "-g", RG, "-n", LAW).get("customerId")
    if not workspace:
        print("P0_CORRELATION_TELEMETRY=unavailable", flush=True)
        return
    # Static KQL only; do not expose raw Azure resource IDs or log messages.
    queries = (
        ("requests", "AppRequests | where TimeGenerated > ago(90m) "
         + _APP_FILTER
         + " | summarize requests=count(),p95_ms=percentile(DurationMs,95),"
           "p99_ms=percentile(DurationMs,99) "
           "by bucket=bin(TimeGenerated,5m),ResultCode "
         + " | extend p95_ms=iff(requests>=20,p95_ms,real(null)),"
           "p99_ms=iff(requests>=100,p99_ms,real(null)) "
           " | order by bucket desc | take 18"),
        ("host", "AppTraces | where TimeGenerated > ago(90m) "
         + _APP_FILTER
         + " | extend class=case(Message contains 'Worker process exited',"
           "'worker_exit', Message contains 'Worker process started',"
           "'worker_start', Message contains 'host startup','host_start',"
           "Message contains 'Host lock lease','host_lease','other') "
           " | where class!='other' "
           " | summarize events=count() by bucket=bin(TimeGenerated,5m),class "
           " | order by bucket desc | take 18"),
        ("function_logs", "FunctionAppLogs | where TimeGenerated > ago(90m) "
         + _APP_FILTER
         + " | summarize events=count() by bucket=bin(TimeGenerated,5m),Level "
           " | order by bucket desc | take 18"),
        ("azure_activity", "AzureActivity | where TimeGenerated > ago(90m) "
         "| where ResourceGroup =~ 'rg-retailgrowth-dev' "
         "| where tolower(tostring(column_ifexists('_ResourceId',''))) "
           "endswith '/sites/rgai-dev-functions-d4e5ddbd' "
         "| summarize operations=count() by bucket=bin(TimeGenerated,5m),ActivityStatusValue "
         "| order by bucket desc | take 18"),
    )
    for name, query in queries:
        try:
            rows = azure("monitor", "log-analytics", "query", "-w", workspace,
                         "--analytics-query", query)
            # Azure CLI usually returns a list of row dictionaries, while some
            # interfaces use {tables:[{columns,rows}]}. Both are sanitized.
            safe_rows = safe_aggregate_rows(rows)
            print("P0_CORRELATION_" + name.upper() + "="
                  + json.dumps(safe_rows, separators=(",", ":"), sort_keys=True),
                  flush=True)
            if not safe_rows:
                print("P0_CORRELATION_" + name.upper()
                      + "_EMPTY_OR_UNAVAILABLE=true", flush=True)
        except (RuntimeError, ValueError, subprocess.TimeoutExpired):
            print("P0_CORRELATION_" + name.upper() + "=unavailable", flush=True)
    print("P0_TELEMETRY_SAMPLED_AND_INGESTION_LAG_POSSIBLE=true", flush=True)

def main() -> int:
    audit_scope()  # Exact OIDC subscription, tagged DEV RG, Central India function.
    anomalies = sum(probe_once(label, path, expected, i)
                    for i, (label, path, expected) in enumerate(CASES, 1))
    print(f"P0_TRANSPORT_ANOMALIES={anomalies}_OF_{len(CASES)}", flush=True)
    log_buckets()
    print("P0_READ_ONLY_OBSERVATION_NOT_PROOF_OF_ROOT_CAUSE_OR_FIX=true", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
