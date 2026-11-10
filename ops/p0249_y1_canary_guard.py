#!/usr/bin/env python3
"""Fail-closed DEV-only classic Y1 canary deployment checks for #249.

No Azure mutation in this script: provisioning is a separate protected
GitHub Actions step after a strict ARM what-if preview.
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RG = "rg-retailgrowth-dev"
SITE = "rgai-dev-y1-p0249-d4e5ddbd"
PLAN = "rgai-dev-y1-p0249"
FLEX_SITE = "rgai-dev-functions-d4e5ddbd"
FLEX_PLAN = "rgai-dev-flex"
STORAGE = "rgaid4e5ddbdf0d21d96"
TEMPLATE = "infra/azure/p0249-classic-y1-dev-canary.bicep"


def command(*args):
    p = subprocess.run(["az", *args, "-o", "json", "--only-show-errors"],
                       check=False, text=True, capture_output=True, timeout=180)
    if p.returncode:
        raise RuntimeError("Azure DEV read/preview command failed")
    return json.loads(p.stdout)


def group_scoped():
    expected = os.environ.get("RGAI_DEV_EXPECTED_SUBSCRIPTION", "")
    if not expected or command("account", "show").get("id") != expected:
        raise RuntimeError("DEV subscription mismatch")
    rg = command("group", "show", "-n", RG)
    tags = {str(k).lower(): str(v).lower() for k, v in (rg.get("tags") or {}).items()}
    if rg.get("name") != RG or rg.get("location") != "centralindia":
        raise RuntimeError("Unexpected DEV RG identity/region")
    if tags.get("app") != "retailgrowthai" or tags.get("environment") != "dev":
        raise RuntimeError("DEV RG tags missing")
    storage = command("storage", "account", "show", "-g", RG, "-n", STORAGE)
    if (storage.get("name") != STORAGE or storage.get("kind") != "StorageV2" or
        storage.get("location") != "centralindia" or
        (storage.get("sku") or {}).get("name") != "Standard_LRS" or
        storage.get("allowBlobPublicAccess") is not False):
        raise RuntimeError("Existing private storage mismatched")
    original = command("resource", "show", "-g", RG, "-n", FLEX_SITE,
                       "--resource-type", "Microsoft.Web/sites")
    original_plan = command("resource", "show", "-g", RG, "-n", FLEX_PLAN,
                            "--resource-type", "Microsoft.Web/serverfarms")
    if (original.get("name") != FLEX_SITE or original_plan.get("name") != FLEX_PLAN or
        (original_plan.get("sku") or {}).get("name") != "FC1"):
        raise RuntimeError("Original DEV Flex unexpectedly changed")
    return expected


def resource(name, rtype):
    return command("resource", "show", "-g", RG, "-n", name,
                   "--resource-type", rtype)


def assert_absent(name, rtype):
    """List succeeds with [] on absence; a 403 or other CLI error must STOP."""
    resources = command("resource", "list", "-g", RG, "--resource-type", rtype)
    if not isinstance(resources, list):
        raise RuntimeError("DEV ARM inventory is not a resource list")
    if any(not isinstance(item, dict) for item in resources):
        raise RuntimeError("Malformed DEV ARM inventory")
    if any(str(item.get("name", "")).casefold() == name.casefold()
           for item in resources):
        raise RuntimeError("Refusing to overwrite existing canary resource")


def expected_two_creations(preview):
    changes = preview.get("changes") or (preview.get("properties") or {}).get("changes") or []
    expected = {
        "/providers/microsoft.web/sites/" + SITE.lower(),
        "/providers/microsoft.web/serverfarms/" + PLAN.lower(),
    }
    observed = set()
    for change in changes:
        typ = change.get("changeType")
        rid = str(change.get("resourceId") or "").lower()
        if typ in ("NoChange", "Ignore"):
            continue
        if typ != "Create" or "/resourcegroups/" + RG.lower() + "/" not in rid:
            raise RuntimeError("ARM preview contains non-create or out-of-scope change")
        matches = [p for p in expected if rid.endswith(p)]
        if len(matches) != 1:
            raise RuntimeError("ARM preview creates unexpected resource")
        observed.add(matches[0])
    if observed != expected:
        raise RuntimeError("ARM preview does not create exactly new site+plan")
    return True


def preflight():
    group_scoped()
    assert_absent(SITE, "Microsoft.Web/sites")
    assert_absent(PLAN, "Microsoft.Web/serverfarms")
    preview = command("deployment", "group", "what-if", "-g", RG,
                      "--template-file", TEMPLATE, "--no-pretty-print")
    expected_two_creations(preview)
    print("P0249_Y1_PREFLIGHT_PASS=EXACT_TWO_NEW_WEB_RESOURCES", flush=True)


def verify():
    group_scoped()
    site = resource(SITE, "Microsoft.Web/sites")
    plan = resource(PLAN, "Microsoft.Web/serverfarms")
    tags = {str(k).lower(): str(v).lower() for k, v in (site.get("tags") or {}).items()}
    if (site.get("name") != SITE or site.get("location") != "centralindia" or
        plan.get("name") != PLAN or plan.get("location") != "centralindia" or
        (plan.get("sku") or {}).get("name") != "Y1" or
        (plan.get("sku") or {}).get("tier") != "Dynamic" or
        not site.get("properties", {}).get("reserved") or
        tags.get("app") != "retailgrowthai" or tags.get("environment") != "dev" or
        tags.get("purpose") != "p0249-http-ingress-isolation"):
        raise RuntimeError("New resource shape, role or tag mismatch")
    cfg = command("functionapp", "config", "show", "-g", RG, "-n", SITE)
    if str(cfg.get("linuxFxVersion", "")).upper() != "PYTHON|3.12":
        raise RuntimeError("Y1 runtime mismatch")
    print("P0249_Y1_ARM_VERIFIED=Y1_LINUX_PYTHON312_ORIGINAL_FLEX_UNCHANGED", flush=True)


def get(endpoint, timeout):
    start = time.monotonic()
    try:
        req = urllib.request.Request(
            "https://" + SITE + ".azurewebsites.net" + endpoint,
            headers={"Cache-Control": "no-store"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            marked = bool(response.headers.get("X-Request-ID"))
    except urllib.error.HTTPError as exc:
        status = exc.code
        marked = bool(exc.headers.get("X-Request-ID"))
    except (urllib.error.URLError, TimeoutError, OSError):
        status, marked = 0, False
    return status, marked, round(time.monotonic() - start, 3)


def probe():
    # Cold start with retry; *not* counted as warm canary success.
    ready = False
    for attempt in range(3):
        status, marked, latency = get("/api/p0249/health", 60)
        print("P0249_Y1_COLD=" + json.dumps({
            "attempt": attempt + 1, "http": status, "marked": marked, "s": latency
        }), flush=True)
        if status == 200 and marked:
            ready = True
            break
        time.sleep(5)
    if not ready:
        raise RuntimeError("Y1 canary failed initial readiness")
    ok = 0
    for i in range(20):
        health = i % 2 == 0
        status, marked, latency = get(
            "/api/p0249/health" if health else "/api/p0249/unknown-" + str(i),
            18,
        )
        success = (status == 200 and marked if health else status == 404)
        if latency >= 18:
            success = False
        ok += int(success)
        print("P0249_Y1_HTTP=" + json.dumps({
            "index": i + 1, "kind": "health" if health else "unknown",
            "http": status, "marked": marked, "seconds": latency,
            "accepted": success,
        }, sort_keys=True), flush=True)
    print(f"P0249_Y1_HTTP_ACCEPTED={ok}/20", flush=True)
    if ok != 20:
        raise RuntimeError("Y1 ingress cannot meet 20/20 canary acceptance")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("preflight", "verify", "probe"):
        raise SystemExit("Expected preflight, verify or probe")
    try:
        {"preflight": preflight, "verify": verify, "probe": probe}[sys.argv[1]]()
    except Exception:
        print("P0249_Y1_CHECK_FAILED; no claim of successful migration", file=sys.stderr)
        raise SystemExit(1)
