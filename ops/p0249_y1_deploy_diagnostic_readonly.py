#!/usr/bin/env python3
"""Read-only, redacted Azure Y1 deployment/indexing diagnosis for Issue #249.

Never emit raw Azure CLI output: app settings and deployment messages can contain
credentials, resource IDs or signed URLs. This prints only fixed allowlisted
status booleans/enums and request outcome counts, not raw logs.
"""
import json
import os
import subprocess
import sys
from urllib.parse import urlsplit

from p0249_y1_canary_guard import RG, SITE, verify


def az_read(*args):
    try:
        p = subprocess.run(
            ["az", *args, "--only-show-errors", "-o", "json"],
            check=False, capture_output=True, text=True, timeout=90,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode:
        return None
    try:
        return json.loads(p.stdout or "null")
    except ValueError:
        return None



def classify_package_mode(value):
    """Return a fixed nonsecret enum; never log a package URL or SAS token."""
    if value is None:
        return "ABSENT"
    if not isinstance(value, str):
        return "UNRECOGNIZED"
    stripped = value.strip()
    if stripped == "0":
        return "DISABLED"
    if stripped == "1":
        return "LOCAL_PACKAGE"
    try:
        parsed = urlsplit(stripped)
    except ValueError:
        return "UNRECOGNIZED"
    if (parsed.scheme == "https" and parsed.hostname and not parsed.username
            and not parsed.password and stripped.startswith("https://")):
        return "EXTERNAL_HTTPS_URL"
    return "UNRECOGNIZED"


def setting_flags(rows):
    """Permit only expected keys and their boolean states, not values."""
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        raise RuntimeError("Unknown app settings metadata structure")
    allowed = ("SCM_DO_BUILD_DURING_DEPLOYMENT", "ENABLE_ORYX_BUILD",
               "WEBSITE_RUN_FROM_PACKAGE", "FUNCTIONS_WORKER_RUNTIME",
               "FUNCTIONS_EXTENSION_VERSION")
    by_name = {}
    for row in rows:
        raw_name = row.get("name")
        if not isinstance(raw_name, str):
            raise RuntimeError("Malformed app setting name")
        name = raw_name.upper()
        if name not in allowed:
            continue  # Do not retain or print unrelated settings or secrets.
        if name in by_name:
            raise RuntimeError("Duplicate diagnostic app setting name")
        by_name[name] = row.get("value")
    flags = {
        name: {
            "present": name in by_name,
            "is_true": str(by_name.get(name, "")).strip().lower() == "true",
            "is_false": str(by_name.get(name, "")).strip().lower() == "false",
            "is_one": str(by_name.get(name, "")).strip() == "1",
        }
        for name in allowed
    }
    package_mode = classify_package_mode(by_name.get("WEBSITE_RUN_FROM_PACKAGE"))
    flags["WEBSITE_RUN_FROM_PACKAGE"]["nonsecret_mode"] = package_mode
    # This is only a compatibility hint, not a conclusion about a ZIP build.
    # A pre-vendored local-build ZIP cannot be proven active from this read.
    if flags["SCM_DO_BUILD_DURING_DEPLOYMENT"]["is_true"]:
        flags["WEBSITE_RUN_FROM_PACKAGE"]["build_config_class"] = (
            "REMOTE_BUILD_FLAGS_ALIGNED"
            if flags["ENABLE_ORYX_BUILD"]["is_true"]
            and package_mode in ("ABSENT", "DISABLED")
            else "REMOTE_BUILD_FLAGS_MIXED"
        )
    elif package_mode == "EXTERNAL_HTTPS_URL":
        flags["WEBSITE_RUN_FROM_PACKAGE"]["build_config_class"] = "EXTERNAL_PACKAGE_MODE"
    else:
        flags["WEBSITE_RUN_FROM_PACKAGE"]["build_config_class"] = "UNDETERMINED"
    return flags


def deployment_summary(rows):
    if not isinstance(rows, list):
        return {"available": False}
    totals = {"success": 0, "failed": 0, "pending": 0, "other": 0}
    for row in rows[:20]:
        if not isinstance(row, dict):
            totals["other"] += 1
            continue
        status = str(row.get("status", "")).lower()
        if status in ("4", "success", "succeeded"):
            totals["success"] += 1
        elif status in ("3", "failed", "failure"):
            totals["failed"] += 1
        elif status in ("0", "1", "2", "pending", "building", "deploying"):
            totals["pending"] += 1
        else:
            totals["other"] += 1
    return {"available": True, "entries_capped": min(len(rows), 20),
            "status_counts": totals}


def log_categories(data):
    if data is None:
        return {"available": False}
    # Classify internally without ever publishing raw (possibly private) text.
    raw = json.dumps(data, ensure_ascii=True).lower()
    patterns = (
        "oryx", "python", "host.json", "function_app.py",
        "error", "exception", "failed", "startup", "sync",
        "deployment completed", "deployment successful", "requirements.txt",
    )
    return {"available": True,
            "categories": {s: s in raw for s in patterns}}



def index_shape(names):
    """Return only fixed identifiers; never print unexpected function names."""
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        return "INVALID"
    normalized = []
    prefix = SITE + "/"
    styles = set()
    for name in names:
        if (not name or "\\\\" in name or
                any(ord(char) <= 32 or ord(char) == 127 for char in name)):
            return "INVALID"
        prefixed = "/" in name
        styles.add(prefixed)
        if prefixed:
            # Azure CLI normally returns SITE/function. Never classify a
            # foreign host or nested ARM path by its final suffix alone.
            if not name.startswith(prefix) or name.count("/") != 1:
                return "OTHER_UNVERIFIED"
            normalized.append(name[len(prefix):])
        else:
            normalized.append(name)
    if len(styles) > 1:
        return "OTHER_UNVERIFIED"
    two = {"p0249_health", "campaign_read"}
    five = two | {"render_job_read", "poster_job_read", "poster_draft_read"}
    if len(normalized) == 2 and set(normalized) == two:
        return "EXACT_TWO"
    if len(normalized) == 5 and set(normalized) == five:
        return "EXACT_FIVE"
    return "OTHER_UNVERIFIED"


def _cors_fields(value):
    # Fixed categories only; arbitrary provider values never enter logs.
    if value is None:
        return {"shape": "NULL"}
    if not isinstance(value, dict):
        return {"shape": "NOT_OBJECT"}
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent / "p0249-y1-cutover"))
    from retirement_gate import FRONTEND
    origins = value.get("allowedOrigins")
    if "allowedOrigins" not in value:
        origin_state = "ABSENT"
    elif origins is None:
        origin_state = "NULL"
    elif not isinstance(origins, list) or any(type(v) is not str for v in origins):
        origin_state = "INVALID"
    elif len(set(origins)) != len(origins):
        origin_state = "DUPLICATE"
    elif not origins:
        origin_state = "EMPTY"
    elif any(v not in (FRONTEND, "https://portal.azure.com") for v in origins):
        origin_state = "FOREIGN_OR_WILDCARD"
    elif FRONTEND in origins:
        origin_state = "APPROVED_WITH_FRONTEND"
    else:
        origin_state = "PORTAL_ONLY"
    credentials = value.get("supportCredentials")
    flag = ("ABSENT" if "supportCredentials" not in value else
            "NULL" if credentials is None else
            "TRUE" if credentials is True else "FALSE" if credentials is False else "INVALID")
    return {"shape": "OBJECT", "origins": origin_state, "credentials": flag}


def _cors_summary(config, resource_id):
    if not isinstance(config, dict):
        return {"shape": "UNAVAILABLE_OR_INVALID"}
    if not isinstance(config.get("id"), str) or config["id"].lower() != resource_id.lower():
        return {"shape": "IDENTITY_MISMATCH"}
    properties = config.get("properties")
    return {
        "shape": "EXACT_RESOURCE",
        "top": _cors_fields(config["cors"]) if "cors" in config else {"shape": "ABSENT"},
        "nested": _cors_fields(properties["cors"]) if isinstance(properties, dict)
                  and "cors" in properties else {"shape": "ABSENT"},
    }


def core_stage_diagnostics():
    # This function is called only after existing exact DEV verify() succeeds.
    # Re-verify both site IDs, the subscription and exact five-route baseline
    # before reading only the two known DEV sites' setting maps.
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent / "p0249-y1-cutover"))
    from inspect_azure_connections_readonly import (
        cors_resource_id, cors_read_args, site_read_args, exact_site_state,
        function_names, safe_setting_map,
    )
    from stage_core_connections import CORE, FIVE, _original_python
    from retirement_gate import Y1, FLEX, SUPABASE
    subscription = os.environ.get("RGAI_DEV_EXPECTED_SUBSCRIPTION", "")
    account = az_read("account", "show")
    if not subscription or not isinstance(account, dict) or str(account.get("id", "")).lower() != subscription.lower():
        raise RuntimeError("CORE_DIAGNOSTIC_SCOPE_INVALID")
    old = az_read(*site_read_args(FLEX))
    target = az_read(*site_read_args(Y1))
    if (exact_site_state(old, FLEX, subscription) != "Running"
        or exact_site_state(target, Y1, subscription) != "Running"):
        raise RuntimeError("CORE_DIAGNOSTIC_SITE_NOT_RUNNING")
    names = function_names(az_read("functionapp", "function", "list", "-g", RG, "-n", Y1), Y1)
    if set(names) != FIVE:
        raise RuntimeError("CORE_DIAGNOSTIC_FIVE_INDEX_REQUIRED")
    rid = cors_resource_id(Y1, subscription)
    resource = az_read(*cors_read_args(Y1, subscription))
    direct = az_read("rest", "--method", "get", "--uri",
                     "https://management.azure.com" + rid + "?api-version=2024-11-01")
    print("P0249_CORE_CORS_ARM_CLI=" + json.dumps(_cors_summary(resource, rid), sort_keys=True), flush=True)
    print("P0249_CORE_CORS_ARM_REST=" + json.dumps(_cors_summary(direct, rid), sort_keys=True), flush=True)
    # Independently inspect the CLI projection; null output remains unknown.
    projected = az_read("functionapp", "cors", "show", "-g", RG, "-n", Y1)
    print("P0249_CORE_CORS_PROJECTION=" + json.dumps(_cors_fields(projected), sort_keys=True), flush=True)
    # Only fixed named categories; never output appsetting values or arbitrary names.
    source = safe_setting_map(az_read("functionapp", "config", "appsettings", "list", "-g", RG, "-n", FLEX))
    existing = safe_setting_map(az_read("functionapp", "config", "appsettings", "list", "-g", RG, "-n", Y1))
    statuses = {}
    for key in CORE:
        v = source.get(key)
        if not isinstance(v, str) or len(v) < (1 if key == "RETAIL_SUPABASE_URL" else 35):
            statuses[key] = "SOURCE_ABSENT_OR_MALFORMED"
        elif v.startswith("@Microsoft.KeyVault("):
            statuses[key] = "SOURCE_KEY_VAULT_REFERENCE"
        elif key == "RETAIL_SUPABASE_URL" and v != SUPABASE:
            statuses[key] = "SOURCE_FOREIGN_PROJECT"
        elif key not in existing:
            statuses[key] = "TARGET_MISSING"
        elif existing[key] != v:
            statuses[key] = "TARGET_DRIFT"
        else:
            statuses[key] = "MATCH"
    print("P0249_CORE_CONNECTION_CLASSIFICATIONS=" + json.dumps(statuses, sort_keys=True), flush=True)
    print("P0249_CORE_ORIGINAL_PYTHON=" + str(_original_python(old, source)).lower(), flush=True)
    print("P0249_CORE_TARGET_PYTHON=" + str(existing.get("FUNCTIONS_WORKER_RUNTIME") == "python").lower(), flush=True)
    print("P0249_CORE_TARGET_HOST_STORAGE_PRESENT=" + str(bool(existing.get("AzureWebJobsStorage"))).lower(), flush=True)
    print("P0249_CORE_DIAGNOSTIC_READ_ONLY=true", flush=True)


def main():
    verify()  # Exact DEV RG, app tag/region/Linux Y1 SKU and original FC1.
    core_stage_diagnostics()
    rows = az_read("functionapp", "config", "appsettings", "list",
                   "-g", RG, "-n", SITE)
    if rows is None:
        print("P0249_Y1_SETTINGS_READ=UNAVAILABLE", flush=True)
    else:
        print("P0249_Y1_SETTING_FLAGS=" +
              json.dumps(setting_flags(rows), sort_keys=True), flush=True)
    deployments = az_read("webapp", "log", "deployment", "list",
                          "-g", RG, "-n", SITE)
    print("P0249_Y1_DEPLOYMENT_HISTORY=" +
          json.dumps(deployment_summary(deployments), sort_keys=True), flush=True)
    last = az_read("webapp", "log", "deployment", "show",
                   "-g", RG, "-n", SITE)
    print("P0249_Y1_DEPLOYMENT_LOG_CATEGORIES=" +
          json.dumps(log_categories(last), sort_keys=True), flush=True)
    names = az_read("functionapp", "function", "list", "-g", RG, "-n", SITE,
                    "--query", "[].name")
    if not isinstance(names, list):
        print("P0249_Y1_FUNCTION_INDEX=UNAVAILABLE", flush=True)
    else:
        # Count and classify but never emit potentially private function names.
        print("P0249_Y1_INDEXED_FUNCTION_COUNT=" + str(len(names)), flush=True)
        print("P0249_Y1_INDEX_SHAPE=" + index_shape(names), flush=True)


def assert_no_pinned_package_for_zip():
    """Abort before Azure writes if a Linux Y1 ZIP would leave old code active."""
    verify()  # Scope to exact tagged isolated DEV Y1; never original Flex.
    rows = az_read("functionapp", "config", "appsettings", "list",
                   "-g", RG, "-n", SITE)
    if rows is None:
        raise RuntimeError("Y1 package-mode settings unavailable")
    flags = setting_flags(rows)
    mode = flags["WEBSITE_RUN_FROM_PACKAGE"]["nonsecret_mode"]
    build = flags["WEBSITE_RUN_FROM_PACKAGE"]["build_config_class"]
    # Both conditions were seen in hosted failed deployment #44618073780.
    # Print only fixed enums, never actual URLs or credential-bearing values.
    if mode != "ABSENT" or build == "REMOTE_BUILD_FLAGS_MIXED":
        print("P0249_Y1_ZIP_PREFLIGHT=BLOCKED_PINNED_OR_MIXED_PACKAGE_MODE", flush=True)
        raise RuntimeError("Y1 package mode incompatible with unchanged ZIP release")
    print("P0249_Y1_ZIP_PREFLIGHT=NO_PINNED_PACKAGE_POINTER", flush=True)

if __name__ == "__main__":
    try:
        if len(sys.argv) == 1:
            main()
        elif sys.argv[1:] == ["--fail-if-pinned-package"]:
            assert_no_pinned_package_for_zip()
        else:
            raise RuntimeError("Unapproved diagnostic option")
    except Exception:
        print("P0249_Y1_READONLY_DIAGNOSTIC_FAILED", flush=True)
        raise SystemExit(1)
