"""Anonymous GET-only transport-phase evidence for existing RetailGrowthAI DEV Flex app.

Observational only: no credentials, customer data, request bodies, mutable verbs,
secrets, unapproved capacity or resources.
"""
from __future__ import annotations
import datetime as dt
import json
import subprocess
import tempfile
from pathlib import Path
from flex_ingress_correlation import RG, LAW, UUID, HOST, audit_scope, azure

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
            phases = [round(max(0.0, min(float(v), 25.0)), 3) for v in fields[1:]]
            marker = headers.exists() and any(
                line.lower().startswith("x-request-id:")
                for line in headers.read_text(errors="replace").splitlines())
            transport = "ok" if result.returncode == 0 else "curl_failure"
        except (OSError, ValueError, subprocess.TimeoutExpired):
            status, phases, marker, transport = 0, [0.0] * 6, False, "unavailable"
        bad = (status != expected or (label != "unknown_route" and not marker)
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

def log_buckets() -> None:
    workspace = azure("monitor", "log-analytics", "workspace", "show",
                      "-g", RG, "-n", LAW).get("customerId")
    if not workspace:
        print("P0_CORRELATION_TELEMETRY=unavailable", flush=True)
        return
    # Static KQL only; do not expose raw Azure resource IDs or log messages.
    queries = (
        ("requests", "AppRequests | where TimeGenerated > ago(90m) "
         "| summarize requests=count(),p95_ms=percentile(DurationMs,95) "
         "by bucket=bin(TimeGenerated,5m),ResultCode "
         "| order by bucket desc | take 18"),
        ("host", "AppTraces | where TimeGenerated > ago(90m) "
         "| extend class=case(Message contains 'Worker process exited',"
         "'worker_exit', Message contains 'Worker process started',"
         "'worker_start', Message contains 'host startup','host_start',"
         "Message contains 'Host lock lease','host_lease','other') "
         "| where class!='other' "
         "| summarize events=count() by bucket=bin(TimeGenerated,5m),class "
         "| order by bucket desc | take 18"),
        ("function_logs", "FunctionAppLogs | where TimeGenerated > ago(90m) "
         "| summarize events=count() by bucket=bin(TimeGenerated,5m),Level "
         "| order by bucket desc | take 18"),
        ("azure_activity", "AzureActivity | where TimeGenerated > ago(90m) "
         "| where ResourceGroup =~ 'rg-retailgrowth-dev' "
         "| where _ResourceId has 'rgai-dev-functions-d4e5ddbd' "
         "| summarize operations=count() by bucket=bin(TimeGenerated,5m),ActivityStatusValue "
         "| order by bucket desc | take 18"),
    )
    for name, query in queries:
        try:
            rows = azure("monitor", "log-analytics", "query", "-w", workspace,
                         "--analytics-query", query)
            tables = rows.get("tables", []) if isinstance(rows, dict) else []
            print("P0_CORRELATION_" + name.upper() + "="
                  + json.dumps(tables[:2], separators=(",", ":"), sort_keys=True),
                  flush=True)
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
