#!/usr/bin/env python3
"""Read-only, redacted Azure Y1 deployment/indexing diagnosis for Issue #249.

Never emit raw Azure CLI output: app settings and deployment messages can contain
credentials, resource IDs or signed URLs. This prints only fixed allowlisted
status booleans/enums and request outcome counts, not raw logs.
"""
import json
import subprocess
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


def main():
    verify()  # Exact DEV RG, app tag/region/Linux Y1 SKU and original FC1.
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


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("P0249_Y1_READONLY_DIAGNOSTIC_FAILED", flush=True)
        raise SystemExit(1)
