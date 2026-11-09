#!/usr/bin/env python3
"""One-shot #249 DEV HTTP Always Ready trial; requires reviewed manual GH workflow.

The operator must independently verify Azure billing. Best-effort in-process
rollback plus an independent GitHub cleanup job; cancellation of the entire
workflow cannot guarantee a rollback. Never use for PROD or other resources.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time

RG = "rg-retailgrowth-dev"
APP = "rgai-dev-functions-d4e5ddbd"
ORIGIN = "https://" + APP + ".azurewebsites.net"
ROUTES = (
    ("campaign", "/api/campaigns/11111111-1111-4111-8111-111111111111"),
    ("unknown", "/api/p0-249-nonexistent-path"),
)
MEMORY_MB = 2048
MAX_EXPERIMENT_SECONDS = 720
ROLLBACK_RESERVE = 120


def az(*parts):
    """Never reveal CLI output or stderr on error; only parse trusted JSON locally."""
    result = subprocess.run(
        ["az", *parts, "--only-show-errors", "-o", "json"],
        text=True, capture_output=True, timeout=85,
    )
    if result.returncode:
        raise RuntimeError("Scoped Azure CLI command failed")
    return json.loads(result.stdout or "null")


def read_scope():
    subscription = os.environ.get("RGAI_DEV_EXPECTED_SUBSCRIPTION", "")
    if not re.fullmatch(r"[a-fA-F0-9-]{36}", subscription):
        raise RuntimeError("Missing exact DEV subscription")
    account = az("account", "show")
    if str(account.get("id", "")).lower() != subscription.lower():
        raise RuntimeError("Azure subscription not authorized")
    group = az("group", "show", "-n", RG)
    tags = {str(k).lower(): str(v).lower() for k, v in (group.get("tags") or {}).items()}
    if (group.get("name") != RG or
        str(group.get("location", "")).replace(" ", "").lower() != "centralindia" or
        tags.get("app") != "retailgrowthai" or tags.get("environment") != "dev"):
        raise RuntimeError("DEV tagged resource-group mismatch")
    app = az("functionapp", "show", "-g", RG, "-n", APP)
    rid = f"/subscriptions/{subscription}/resourceGroups/{RG}/providers/Microsoft.Web/sites/{APP}"
    if (str(app.get("id", "")).lower() != rid.lower() or
        str(app.get("location", "")).replace(" ", "").lower() != "centralindia"):
        raise RuntimeError("DEV Function App identity/region mismatch")
    plan_id = str(app.get("serverFarmId") or
                  (app.get("properties") or {}).get("serverFarmId") or "")
    expected_plan = f"/subscriptions/{subscription}/resourceGroups/{RG}/providers/Microsoft.Web/serverfarms/"
    if not plan_id.lower().startswith(expected_plan.lower()):
        raise RuntimeError("Unexpected Azure plan owner")
    plan = az("appservice", "plan", "show", "--ids", plan_id)
    zone = plan.get("zoneRedundant", (plan.get("properties") or {}).get("zoneRedundant"))
    if zone is not False:
        raise RuntimeError("Cannot prove non-zone-redundant plan; one may bill as two")
    full = az("resource", "show", "--ids", rid, "--api-version", "2024-11-01")
    if str(full.get("id", "")).lower() != rid.lower():
        raise RuntimeError("Azure ARM resource identity mismatch")
    cfg = (full.get("properties") or {}).get("functionAppConfig") or full.get("functionAppConfig")
    if not isinstance(cfg, dict) or not isinstance(cfg.get("scaleAndConcurrency"), dict):
        raise RuntimeError("Missing exact Flex ARM scale configuration")
    scale = cfg["scaleAndConcurrency"]
    if scale.get("instanceMemoryMB") != MEMORY_MB:
        raise RuntimeError("Unexpected memory size")
    entries = scale.get("alwaysReady")
    if entries is None:
        entries = []
    if not isinstance(entries, list) or any(not isinstance(row, dict) for row in entries):
        raise RuntimeError("Malformed Always Ready configurations")
    return entries


def http_count(entries):
    rows = [x for x in entries if x.get("name") == "http"]
    if len(rows) > 1:
        raise RuntimeError("Duplicate HTTP Always Ready groups")
    return None if not rows else rows[0].get("instanceCount")


def check_snapshot(path):
    with open(path, encoding="utf-8") as f:
        snapshot = json.load(f)
    if snapshot != {
        "schema": "retailgrowthai/p0249-trial/v1",
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "http_count_before": None,
    }:
        raise RuntimeError("Mismatched or altered trial preflight marker")


def preflight(snapshot_path):
    entries = read_scope()
    if http_count(entries) is not None:
        raise RuntimeError("Pre-existing HTTP designation: refusing to modify")
    payload = {
        "schema": "retailgrowthai/p0249-trial/v1",
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "http_count_before": None,
    }
    with open(snapshot_path, "x", encoding="utf-8") as f:
        json.dump(payload, f)
    print("P0249_DEV_PREFLIGHT_PASS: exact app, zone=false, 2048MB, HTTP absent", flush=True)


def rollback(snapshot_path):
    """Bounded cleanup of only HTTP group, preserving all other designations."""
    check_snapshot(snapshot_path)
    for attempt in range(1, 5):
        try:
            count = http_count(read_scope())
            if count is None:
                print("P0249_ROLLBACK_VERIFIED=HTTP_ABSENT", flush=True)
                return True
            if count != 1:
                print("P0249_ROLLBACK_ABORT=UNEXPECTED_HTTP_COUNT", flush=True)
                return False
            az("functionapp", "scale", "config", "always-ready", "delete",
               "-g", RG, "-n", APP, "--setting-names", "http")
            if http_count(read_scope()) is None:
                print("P0249_ROLLBACK_VERIFIED=HTTP_REMOVED", flush=True)
                return True
        except (RuntimeError, subprocess.TimeoutExpired, OSError, ValueError):
            print(f"P0249_ROLLBACK_RETRY={attempt}", flush=True)
        time.sleep(5)
    print("P0249_ROLLBACK_UNVERIFIED=MANUAL_AZURE_CHECK_REQUIRED", flush=True)
    return False


def probe(label, route, index):
    import tempfile
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as hdr:
        try:
            p = subprocess.run(
                ["curl", "-sS", "--max-time", "12", "--connect-timeout", "5",
                 "-X", "GET", "-H", "Cache-Control: no-cache",
                 "-D", "/dev/fd/" + str(hdr.fileno()),
                 "-o", "/dev/null", "-w", "%{http_code}|%{time_total}|%{time_starttransfer}",
                 ORIGIN + route[1]],
                pass_fds=(hdr.fileno(),), capture_output=True, text=True, timeout=17,
            )
            fields = p.stdout.strip().split("|")
            status = fields[0] if len(fields) == 3 else "000"
            total = float(fields[1]) if len(fields) == 3 else 12.0
            hdr.seek(0)
            marker = any(line.lower().startswith("x-request-id:") for line in hdr)
            good = (p.returncode == 0 and total <= 10 and
                    (status == "401" and marker if route[0] == "campaign"
                     else status == "404"))
        except (OSError, ValueError, subprocess.TimeoutExpired):
            status, total, marker, good = "000", 12.0, False, False
    record = {"window": label, "kind": route[0], "i": index,
              "http": status, "seconds": round(total, 3), "handler_marker": marker,
              "accepted": good}
    print("P0249_HTTP=" + json.dumps(record, sort_keys=True), flush=True)
    return good


def trial(snapshot_path):
    check_snapshot(snapshot_path)
    if http_count(read_scope()) is not None:
        raise RuntimeError("HTTP group changed since guarded preflight")
    attempted_write = False
    started = time.monotonic()
    passed, total = 0, 0
    try:
        attempted_write = True  # before call, even an uncertain Azure ACK must be cleaned
        az("functionapp", "scale", "config", "always-ready", "set",
           "-g", RG, "-n", APP, "--settings", "http=1")
        if http_count(read_scope()) != 1:
            raise RuntimeError("Failed to confirm HTTP=1")
        print("P0249_TRIAL_HTTP_ONE=VERIFIED", flush=True)
        time.sleep(25)
        for window in ("warm", "post_idle"):
            if window == "post_idle":
                if time.monotonic() - started > MAX_EXPERIMENT_SECONDS - 300 - ROLLBACK_RESERVE:
                    break
                time.sleep(300)
            for i in range(12):
                if time.monotonic() - started > MAX_EXPERIMENT_SECONDS - ROLLBACK_RESERVE - 17:
                    break
                total += 1
                passed += int(probe(window, ROUTES[i % len(ROUTES)], i + 1))
        print(f"P0249_RESULTS_OK={passed}_OF_{total}", flush=True)
        return 0 if total >= 12 and total == passed else 4
    finally:
        if attempted_write and not rollback(snapshot_path):
            raise RuntimeError("CRITICAL: in-process rollback unverified; independent cleanup required")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "trial", "rollback"))
    parser.add_argument("--snapshot", required=True)
    args = parser.parse_args()
    if args.mode == "preflight":
        preflight(args.snapshot)
        return 0
    if args.mode == "trial":
        return trial(args.snapshot)
    return 0 if rollback(args.snapshot) else 5


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print("P0249_TRIAL_FAILED_OR_NEEDS_MANUAL_ROLLBACK_CHECK", file=sys.stderr, flush=True)
        sys.exit(5)
