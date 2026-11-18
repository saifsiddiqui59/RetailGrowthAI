#!/usr/bin/env python3
"""Six bounded synthetic GETs, post-inactivity comparison, existing DEV only.

Never log auth headers, user data, response bodies or unredacted settings.
Post-inactivity does not prove Azure actually scaled to zero.
"""
import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

RG = "rg-retailgrowth-dev"
APP = "rgai-dev-functions-d4e5ddbd"
ORIGIN = "https://" + APP + ".azurewebsites.net"
ROUTES = (
    ("campaign", "/api/campaigns/11111111-1111-4111-8111-111111111111"),
    ("unknown", "/api/p0-249-nonexistent-path"),
)

def read_az(args):
    return json.loads(subprocess.check_output(["az", *args, "-o", "json"],
                       text=True, timeout=25, stderr=subprocess.DEVNULL))

def verify_dev():
    expected = os.getenv("RGAI_DEV_EXPECTED_SUBSCRIPTION")
    if not expected or read_az(["account", "show"]).get("id") != expected:
        raise RuntimeError("wrong or missing expected subscription")
    rg = read_az(["group", "show", "-g", RG])
    tags = {k.lower(): str(v).lower() for k, v in (rg.get("tags") or {}).items()}
    if rg.get("name") != RG or str(rg.get("location")).replace(" ", "").lower() != "centralindia" or tags.get("app") != "retailgrowthai" or tags.get("environment") != "dev":
        raise RuntimeError("DEV resource group scope mismatch")
    if read_az(["functionapp", "show", "-g", RG, "-n", APP]).get("name") != APP:
        raise RuntimeError("DEV Function App scope mismatch")
    print("P0_249_SAFE_EXISTING_DEV_SCOPE=true", flush=True)

def classify(returncode, status, tls, first_byte, elapsed, marker=False, route=None):
    # No 404 on the campaign API is an authentication success; no 401 from
    # the intentionally nonexistent route proves correct dispatch.
    eligible = ((route == "campaign" and status == "401" and marker)
                or (route == "unknown" and status == "404"))
    if returncode == 0 and eligible and elapsed <= 10:
        category = "EXPECTED_401_OR_404"
    elif returncode == 0 and status == "503":
        category = "CONFIRMED_HTTP_503"
    elif returncode != 0 and status == "000":
        category = "CLIENT_TIMEOUT_OR_NETWORK_ERROR"
    else:
        category = "OTHER_UNEXPECTED"
    return {"category": category, "status": status, "seconds": round(elapsed, 3),
            "tls_seconds": round(tls, 3), "first_byte_seconds": round(first_byte, 3),
            "post_tls_no_first_byte": returncode != 0 and status == "000" and tls > 0 and first_byte == 0,
            "app_request_marker": bool(marker)}

def final_app_request_marker(header_text):
    """Do not trust X-Request-ID from curl's earlier proxy/1xx header blocks."""
    if not isinstance(header_text, str):
        return False
    blocks, current = [], []
    for raw in header_text.splitlines():
        line = raw.strip()
        if line.lower().startswith("http/"):
            if current:
                blocks.append(current)
            current = [line]
        elif current:
            if not line:
                blocks.append(current)
                current = []
            else:
                current.append(line)
    if current:
        blocks.append(current)
    return bool(blocks and any(
        line.lower().startswith("x-request-id:")
        and line.partition(":")[2].strip()
        for line in blocks[-1][1:]
    ))


def probe(label, path):
    labels = {value: name for name, value in ROUTES}
    if path not in labels:
        raise ValueError("synthetic fixed paths only")
    route = labels[path]
    with tempfile.TemporaryDirectory() as temp:
        headers = Path(temp) / "headers"
        args = ["curl", "-sS", "--connect-timeout", "3", "--max-time", "12",
                "-X", "GET", "-D", str(headers), "-o", "/dev/null",
                "-w", "%{http_code} %{time_appconnect} %{time_starttransfer} %{time_total}",
                ORIGIN + path]
        try:
            run = subprocess.run(args, capture_output=True, text=True, timeout=15)
            raw = run.stdout.split()
            vals = [float(x) for x in raw[1:4]] if len(raw) == 4 else [0,0,0]
            code = raw[0] if raw else "000"
            marker = (final_app_request_marker(headers.read_text(errors="replace"))
                      if headers.is_file() else False)
            result = classify(run.returncode, code, *vals, marker, route=route)
        except subprocess.TimeoutExpired:
            result = classify(28, "000", 0, 0, 15, route=route)
    print("P0_249_SAFE_PROBE=" + json.dumps({"label":label, "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), **result}, sort_keys=True), flush=True)
    return result

def run_probe(*, sender=probe, sleeper=time.sleep, idle=300):
    # Two first-pass probes + two near-immediate repeats.
    results = [sender("initial-" + n, p) for n,p in ROUTES]
    results.extend(sender("repeat-" + n,p) for n,p in ROUTES)
    print("P0_249_INACTIVITY_SECONDS=" + str(idle), flush=True)
    sleeper(idle)
    results.extend(sender("post-idle-" + n,p) for n,p in ROUTES)
    count = sum(x["category"] != "EXPECTED_401_OR_404" for x in results)
    print("P0_249_ANOMALOUS_PROBES=" + str(count), flush=True)
    print("P0_249_POST_IDLE_IS_NOT_PROOF_OF_COLD_START=true", flush=True)
    return 0 if count == 0 else 4

if __name__ == "__main__":
    verify_dev()
    raise SystemExit(run_probe())
