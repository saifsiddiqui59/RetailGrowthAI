#!/usr/bin/env python3
"""Sanitized read-only Azure inspection for RetailGrowthAI #249 Y1 cutover.

Trusted DEV runner only: never changes appsettings, routes, plans, workers,
traffic or Azure resource state. Never outputs raw Azure appsetting values,
customer identifiers, tokens, storage keys, or Azure CLI stderr. Results are
diagnostic NOT an automatic permission to retire Flex/close #249.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

try:
    from retirement_gate import RG, Y1, FLEX, CONNECTIONS, CORE_FUNCTIONS, SUPABASE
except ImportError:
    from ops.p0249_y1_cutover.retirement_gate import RG, Y1, FLEX, CONNECTIONS, CORE_FUNCTIONS, SUPABASE


def read_azure(*argv, runner=subprocess.run):
    if argv[0:2] not in (
            ("account", "show"), ("group", "show"),
            ("functionapp", "show"), ("functionapp", "function"),
            ("functionapp", "config")):
        raise ValueError("UNAPPROVED_AZURE_READ_COMMAND")
    if argv[0:2] == ("functionapp", "function"):
        if argv[2:3] != ("list",):
            raise ValueError("UNAPPROVED_AZURE_FUNCTION_COMMAND")
    if argv[0:2] == ("functionapp", "config"):
        if argv[2:5] != ("appsettings", "list", "-g"):
            raise ValueError("UNAPPROVED_AZURE_APPSETTING_COMMAND")
    cmd = ("az",) + argv + ("--output", "json")
    response = runner(cmd, text=True, capture_output=True, timeout=35, check=False)
    if response.returncode != 0 or len(response.stdout) > 2_000_000:
        raise RuntimeError("AZURE_READ_ONLY_INVENTORY_FAILED")
    try:
        return json.loads(response.stdout)
    except ValueError:
        raise RuntimeError("AZURE_INVENTORY_SHAPE_INVALID") from None


def safe_setting_map(settings):
    if not isinstance(settings, list) or len(settings) > 500:
        raise RuntimeError("AZURE_APPSETTINGS_SHAPE_INVALID")
    out = {}
    for setting in settings:
        if (not isinstance(setting, dict) or
                not isinstance(setting.get("name"), str) or
                len(setting["name"]) > 128 or setting["name"] in out or
                not isinstance(setting.get("value"), str)):
            raise RuntimeError("AZURE_APPSETTINGS_SHAPE_INVALID")
        out[setting["name"]] = setting["value"]
    return out


def function_names(items, app_name):
    if not isinstance(items, list) or len(items) > 100:
        raise RuntimeError("AZURE_INDEX_SHAPE_INVALID")
    names = []
    for item in items:
        full = item.get("name") if isinstance(item, dict) else None
        if not isinstance(full, str) or not full.startswith(app_name + "/"):
            raise RuntimeError("AZURE_INDEX_FOREIGN_FUNCTION")
        suffix = full[len(app_name)+1:]
        if not suffix.isascii() or not suffix.replace("_", "").isalnum():
            raise RuntimeError("AZURE_INDEX_UNEXPECTED_FUNCTION_NAME")
        names.append(suffix)
    if len(names) != len(set(names)):
        raise RuntimeError("AZURE_INDEX_DUPLICATE_FUNCTION")
    return sorted(names)


def inspect(runner=subprocess.run):
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("GITHUB_REPOSITORY") != "saifsiddiqui59/RetailGrowthAI"
            or os.environ.get("GITHUB_REF") != "refs/heads/main"):
        raise RuntimeError("PROTECTED_RETAILGROWTHAI_DEV_RUNNER_REQUIRED")
    requested_subscription = os.environ.get("AZURE_SUBSCRIPTION_ID")
    if not requested_subscription:
        raise RuntimeError("AZURE_DEV_SCOPE_NOT_SET")
    def az(*a):
        return read_azure(*a, runner=runner)
    account = az("account", "show")
    if account.get("id", "").lower() != requested_subscription.lower():
        raise RuntimeError("FOREIGN_AZURE_SUBSCRIPTION_DENIED")
    group = az("group", "show", "-g", RG)
    tags = {str(k).lower():str(v).lower()
            for k, v in (group.get("tags") or {}).items()}
    if (group.get("name") != RG
        or group.get("location", "").lower().replace(" ", "") != "centralindia"
        or tags.get("app") != "retailgrowthai"
        or tags.get("environment") != "dev"):
        raise RuntimeError("FOREIGN_AZURE_RESOURCE_GROUP_DENIED")
    result = {}
    for app in (Y1, FLEX):
        site = az("functionapp", "show", "-g", RG, "-n", app)
        rid = site.get("id", "").lower()
        if (site.get("name") != app
            or "/resourcegroups/" + RG.lower() + "/" not in rid
            or not rid.endswith("/sites/" + app.lower())):
            raise RuntimeError("FOREIGN_AZURE_FUNCTION_APP_DENIED")
        settings = safe_setting_map(az("functionapp", "config", "appsettings",
                                       "list", "-g", RG, "-n", app))
        names = function_names(az("functionapp", "function", "list",
                                   "-g", RG, "-n", app), app)
        result[app] = {"state":site.get("state"),"settings":settings,
                       "functions":names}
    original = result[FLEX]
    target = result[Y1]
    # Only RetailGrowthAI application data/queue backends should match.
    # AzureWebJobsStorage is host-internal state and may correctly differ
    # between separately managed Functions apps; do not couple its host locks.
    shared = frozenset({
        "RETAIL_SUPABASE_URL", "RETAIL_SUPABASE_PUBLISHABLE_KEY",
        "RETAIL_SUPABASE_SERVICE_ROLE_KEY", "RETAIL_STORAGE",
    })
    matching = (
        CONNECTIONS.issubset(set(target["settings"]))
        and original["settings"].get("RETAIL_SUPABASE_URL")
            == SUPABASE
        and target["settings"].get("RETAIL_SUPABASE_URL")
            == SUPABASE
        and all(original["settings"].get(name) and
                target["settings"].get(name) == original["settings"][name]
                for name in shared)
        and target["settings"].get("FUNCTIONS_WORKER_RUNTIME") == "python"
        and bool(target["settings"].get("AzureWebJobsStorage"))
    )
    report = {
        "y1_running": target["state"] == "Running",
        "flex_running": original["state"] == "Running",
        "y1_indexed_count": len(target["functions"]),
        "y1_core_http_complete": CORE_FUNCTIONS.issubset(set(target["functions"])),
        "y1_same_core_connection_values": bool(matching),
        "y1_any_background_triggers": any(
           name in set(target["functions"]) for name in (
            "render_campaign_reel","plan_campaign","recover_stale_jobs",
            "render_campaign_poster","planning_poison","render_poison",
            "dispatch_pending_posters")),
    }
    return report


def main():
    try:
        result = inspect()
        # Only fixed result categories; never raw settings or arbitrary host
        # JSON. This cannot be converted into permission to stop a cloud app.
        for key in sorted(result):
            value = result[key]
            if isinstance(value, bool):
                value = str(value).lower()
            print("P0249_Y1_" + key.upper() + "=" + str(value))
        print("P0249_FLEX_STOP_AUTHORIZED=false")
        print("P0249_HOSTED_CUTOVER_PROVEN=false")
    except Exception:
        print("P0249_Y1_READONLY_CONNECTION_INSPECTION=BLOCKED", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
