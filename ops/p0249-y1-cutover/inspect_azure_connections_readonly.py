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
import re
import subprocess
import sys

try:
    from retirement_gate import RG, Y1, FLEX, CONNECTIONS, CORE_FUNCTIONS, ALL_HTTP_FUNCTIONS, EXPECTED_FULL_Y1_INDEX, QUEUE_FUNCTIONS, TIMER_FUNCTIONS, SUPABASE, FRONTEND
except ImportError:
    from ops.p0249_y1_cutover.retirement_gate import RG, Y1, FLEX, CONNECTIONS, CORE_FUNCTIONS, SUPABASE, FRONTEND


def site_read_args(name):
    """Exact ARM resource read, matching the established DEV verification path."""
    if name not in (Y1, FLEX):
        raise ValueError("UNAPPROVED_AZURE_SITE_READ")
    return ("resource", "show", "-g", RG, "-n", name,
            "--resource-type", "Microsoft.Web/sites", "--api-version", "2024-11-01")


def exact_site_state(site, name, subscription):
    if name not in (Y1, FLEX) or not isinstance(site, dict):
        raise RuntimeError("AZURE_SITE_IDENTITY_MISMATCH")
    expected = ("/subscriptions/" + subscription + "/resourcegroups/" + RG
                + "/providers/microsoft.web/sites/" + name).lower()
    if (site.get("name") != name or not isinstance(site.get("id"), str)
            or site["id"].lower() != expected):
        raise RuntimeError("AZURE_SITE_IDENTITY_MISMATCH")
    properties = site.get("properties")
    if properties is not None and not isinstance(properties, dict):
        raise RuntimeError("AZURE_SITE_STATE_UNVERIFIED")
    # ARM resources nest state under properties; some CLI representations
    # expose the identical state at the top level. Never accept conflict,
    # missing state, or any value other than Running/Stopped.
    states = [value for value in (site.get("state"), (properties or {}).get("state"))
              if value is not None]
    if (not states or any(type(v) is not str or v not in ("Running", "Stopped") for v in states)
            or len(set(states)) != 1):
        raise RuntimeError("AZURE_SITE_STATE_UNVERIFIED")
    return states[0]


def cors_resource_id(name, subscription):
    if name not in (Y1, FLEX) or not isinstance(subscription, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,80}", subscription):
        raise ValueError("UNAPPROVED_AZURE_CORS_RESOURCE_READ")
    return ("/subscriptions/" + subscription + "/resourceGroups/" + RG
            + "/providers/Microsoft.Web/sites/" + name + "/config/web")


def cors_read_args(name, subscription):
    # ARM Web Apps Get Configuration: properties.cors, API 2024-11-01.
    return ("resource", "show", "--ids", cors_resource_id(name, subscription),
            "--api-version", "2024-11-01")


def exact_cors(config, name, subscription):
    expected = cors_resource_id(name, subscription)
    if (not isinstance(config, dict) or not isinstance(config.get("id"), str)
        or config["id"].lower() != expected.lower()):
        raise RuntimeError("AZURE_CORS_RESOURCE_IDENTITY_MISMATCH")
    properties = config.get("properties")
    cors = properties.get("cors") if isinstance(properties, dict) else None
    if (not isinstance(cors, dict)
        or not isinstance(cors.get("allowedOrigins"), list)
        or any(type(v) is not str for v in cors["allowedOrigins"])
        or len(set(cors["allowedOrigins"])) != len(cors["allowedOrigins"])
        or type(cors.get("supportCredentials")) is not bool):
        raise RuntimeError("AZURE_CORS_SHAPE_INVALID")
    return {"allowedOrigins": cors["allowedOrigins"],
            "supportCredentials": cors["supportCredentials"]}


def read_azure(*argv, runner=subprocess.run):
    if argv[0:2] not in (
            ("account", "show"), ("group", "show"),
            ("functionapp", "show"), ("functionapp", "function"),
            ("functionapp", "config"), ("functionapp", "cors"), ("resource", "show")):
        raise ValueError("UNAPPROVED_AZURE_READ_COMMAND")
    if argv[0:2] == ("resource", "show"):
        if argv not in (site_read_args(Y1), site_read_args(FLEX)):
            # Permit only exact scoped /config/web reads, never arbitrary ARM resources.
            valid = False
            if len(argv) == 6 and argv[2] == "--ids":
                parts = argv[3].split("/")
                if len(parts) == 11 and parts[1].lower() == "subscriptions":
                    try:
                        valid = any(argv == cors_read_args(app, parts[2]) for app in (Y1, FLEX))
                    except ValueError:
                        pass
            if not valid:
                raise ValueError("UNAPPROVED_AZURE_SITE_READ")
    if argv[0:2] == ("functionapp", "function"):
        if argv[2:3] != ("list",):
            raise ValueError("UNAPPROVED_AZURE_FUNCTION_COMMAND")
    if argv[0:2] == ("functionapp", "config"):
        if argv[2:5] != ("appsettings", "list", "-g"):
            raise ValueError("UNAPPROVED_AZURE_APPSETTING_COMMAND")
    if argv[0:2] == ("functionapp", "cors"):
        if argv[2:3] != ("show",):
            raise ValueError("UNAPPROVED_AZURE_CORS_COMMAND")
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
        site = az(*site_read_args(app))
        state = exact_site_state(site, app, requested_subscription)
        settings = safe_setting_map(az("functionapp", "config", "appsettings",
                                       "list", "-g", RG, "-n", app))
        names = function_names(az("functionapp", "function", "list",
                                   "-g", RG, "-n", app), app)
        cors = exact_cors(az(*cors_read_args(app, requested_subscription)),
                          app, requested_subscription)
        result[app] = {"state":state,"settings":settings,
                       "functions":names,"cors":cors}
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
        "y1_all_original_http_indexed": ALL_HTTP_FUNCTIONS.issubset(set(target["functions"])),
        "y1_exact_http_only_index": set(target["functions"]) == ALL_HTTP_FUNCTIONS,
        "y1_exact_full_short_worker_index":
            set(target["functions"]) == EXPECTED_FULL_Y1_INDEX,
        "y1_same_core_connection_values": bool(matching),
        "y1_frontend_cors_allowed": (
            FRONTEND in target["cors"]["allowedOrigins"]
            and target["cors"]["supportCredentials"] is False
        ),
        "y1_any_background_triggers": bool(
            set(target["functions"]) &
            (QUEUE_FUNCTIONS | TIMER_FUNCTIONS | {"render_campaign_reel"})),
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
