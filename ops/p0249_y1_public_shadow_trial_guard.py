#!/usr/bin/env python3
"""DEV-only temporary Y1 original-auth read shadow trial; no tenant writes.

Uses ONLY existing isolated Y1 Function App. Does not copy service_role.
On run failures, independent cleanup job must verify restoration.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

from p0249_y1_canary_guard import RG, SITE, verify as verify_y1

PROJECT_URL = "https://jeearzffnjbvghwjjjrf.supabase.co"
NAMES = ("RETAIL_SUPABASE_URL", "RETAIL_SUPABASE_PUBLISHABLE_KEY",
         "RGAI_P0249_READONLY_SHADOW")
EXPECTED_FUNCTIONS = {"p0249_health", "campaign_read"}
CAMPAIGN_PATH = "/api/campaigns/11111111-1111-4111-8111-111111111111"
MARKER_SCHEMA = "retailgrowthai/p0249-public-shadow-absent/v1"


def cli(*args):
    result = subprocess.run(["az", *args, "-o", "json", "--only-show-errors"],
                            text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError("Y1 Azure management command failed")
    return json.loads(result.stdout or "null")


def mutate(*args):
    result = subprocess.run(["az", *args, "-o", "none", "--only-show-errors"],
                            text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError("Y1 Azure management write failed")


def key():
    value = os.environ.get("RGAI_DEV_P0249_PUBLISHABLE_KEY", "")
    if not re.fullmatch(r"sb_publishable_[A-Za-z0-9_-]{15,}", value):
        raise RuntimeError("Missing valid DEV public-only Supabase key")
    return value


def current():
    rows = cli("functionapp", "config", "appsettings", "list",
               "-g", RG, "-n", SITE)
    if not isinstance(rows, list):
        raise RuntimeError("Malformed Azure appsetting response")
    cfg = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise RuntimeError("Malformed appsetting item")
        name = row["name"]
        if name in cfg:
            raise RuntimeError("Duplicate appsetting name")
        if name in NAMES:
            cfg[name] = row.get("value")
    return cfg


def indexed():
    rows = cli("functionapp", "function", "list", "-g", RG, "-n", SITE)
    if not isinstance(rows, list):
        raise RuntimeError("Malformed Azure function index")
    names = [str(x.get("name", "")).rsplit("/", 1)[-1].lower()
             for x in rows if isinstance(x, dict)]
    if len(names) != 2 or set(names) != EXPECTED_FUNCTIONS:
        raise RuntimeError("Unexpected Y1 function inventory")


def marker():
    value = {"schema": MARKER_SCHEMA, "run": os.environ.get("GITHUB_RUN_ID"),
             "attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
             "before": "all-three-absent"}
    if not value["run"] or not value["attempt"]:
        raise RuntimeError("Run identity missing")
    return value


def read_marker(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if data != marker():
        raise RuntimeError("Untrusted or mismatched Y1 rollback marker")


def preflight(path):
    verify_y1()
    indexed()
    key()
    if current():
        raise RuntimeError("Y1 trial settings already exist; refuse override")
    with open(path, "x", encoding="utf-8") as fh:
        json.dump(marker(), fh)
    print("P0249_SHADOW_PREFLIGHT=EXACT_Y1_TWO_ROUTES_AND_ABSENT_SETTINGS", flush=True)


def set_public_only(path):
    read_marker(path)
    verify_y1()
    indexed()
    if current():
        raise RuntimeError("Y1 trial settings changed after preflight")
    mutate("functionapp", "config", "appsettings", "set",
           "-g", RG, "-n", SITE, "--settings",
           "RETAIL_SUPABASE_URL=" + PROJECT_URL,
           "RETAIL_SUPABASE_PUBLISHABLE_KEY=" + key(),
           "RGAI_P0249_READONLY_SHADOW=true")
    cfg = current()
    if cfg != {"RETAIL_SUPABASE_URL": PROJECT_URL,
               "RETAIL_SUPABASE_PUBLISHABLE_KEY": key(),
               "RGAI_P0249_READONLY_SHADOW": "true"}:
        raise RuntimeError("Y1 public-only activation did not verify")
    print("P0249_SHADOW_PUBLIC_ONLY_CONFIG=VERIFIED", flush=True)


def rollback(path):
    read_marker(path)
    for attempt in range(1, 5):
        try:
            verify_y1()
            cfg = current()
            if not cfg:
                print("P0249_SHADOW_RESTORED=ALL_THREE_ABSENT", flush=True)
                return True
            expected = {
                "RETAIL_SUPABASE_URL": PROJECT_URL,
                "RETAIL_SUPABASE_PUBLISHABLE_KEY": key(),
                "RGAI_P0249_READONLY_SHADOW": "true",
            }
            if any(val != expected[name] for name, val in cfg.items()):
                print("P0249_SHADOW_ROLLBACK_ABORT=UNKNOWN_CONCURRENT_SETTING", flush=True)
                return False
            mutate("functionapp", "config", "appsettings", "delete",
                   "-g", RG, "-n", SITE, "--setting-names", *list(cfg))
            if not current():
                print("P0249_SHADOW_RESTORED=ALL_THREE_ABSENT", flush=True)
                return True
        except (ValueError, KeyError, RuntimeError, OSError, subprocess.TimeoutExpired):
            print(f"P0249_SHADOW_ROLLBACK_RETRY={attempt}", flush=True)
        time.sleep(5)
    print("P0249_SHADOW_RESTORATION_UNVERIFIED=MANUAL_REVIEW_REQUIRED", flush=True)
    return False


def get(path, token=""):
    headers = {"Cache-Control": "no-store"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(
        "https://" + SITE + ".azurewebsites.net" + path,
        headers=headers, method="GET")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=18) as response:
            status = response.status
            marked = bool(response.headers.get("X-Request-ID"))
    except urllib.error.HTTPError as exc:
        status = exc.code
        marked = bool(exc.headers.get("X-Request-ID"))
    except (urllib.error.URLError, TimeoutError, OSError):
        status, marked = 0, False
    return status, marked, round(time.monotonic() - started, 3)


def test_negative():
    indexed()
    results = []
    for n in range(16):
        path = CAMPAIGN_PATH if n % 2 == 0 else "/api/p0249/health"
        token = "" if n % 4 != 0 else "definitely-not-a-signed-jwt"
        status, marked, seconds = get(path, token)
        expected = 401 if path == CAMPAIGN_PATH else 200
        passed = status == expected and marked and seconds < 18
        results.append(passed)
        print("P0249_SHADOW_NEGATIVE=" + json.dumps({
            "index": n + 1, "route": "campaign" if expected == 401 else "health",
            "http": status, "marker": marked, "seconds": seconds, "accepted": passed
        }, sort_keys=True), flush=True)
    print(f"P0249_SHADOW_NEGATIVE_ACCEPTED={sum(results)}/{len(results)}", flush=True)
    if not all(results):
        raise RuntimeError("Public-only Y1 negative auth/readiness failed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "activate", "rollback", "test"))
    parser.add_argument("--marker", required=True)
    args = parser.parse_args()
    if args.mode == "preflight":
        preflight(args.marker)
    elif args.mode == "activate":
        set_public_only(args.marker)
    elif args.mode == "rollback":
        if not rollback(args.marker):
            raise RuntimeError("Critical: Y1 trial public-only config not restored")
    elif args.mode == "test":
        read_marker(args.marker)
        test_negative()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("P0249_SHADOW_TRIAL_FAILED; CHECK_INDEPENDENT_ROLLBACK", file=sys.stderr)
        raise SystemExit(5)
