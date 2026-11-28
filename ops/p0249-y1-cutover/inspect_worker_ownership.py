#!/usr/bin/env python3
"""Protected DEV read-only worker ownership inventory; never a handoff approval."""
import os
import sys
from inspect_azure_connections_readonly import (
    read_azure, safe_setting_map, function_names, site_read_args, exact_site_state,
)
from retirement_gate import RG, FLEX, Y1, ALL_HTTP_FUNCTIONS, QUEUE_FUNCTIONS, TIMER_FUNCTIONS

WORKERS = QUEUE_FUNCTIONS | TIMER_FUNCTIONS | {"render_campaign_reel"}

def classify(names, settings, worker):
    # Registration metadata and disable flags are separate evidence. A flag
    # alone never proves a running listener has drained or stopped.
    key = "AzureWebJobs." + worker + ".Disabled"
    matching = [v for k, v in settings.items() if k.lower() == key.lower()]
    if len(matching) > 1:
        return "AMBIGUOUS"
    if matching and matching[0].lower() not in ("true", "false", "1", "0"):
        return "INVALID_FLAG"
    if worker not in names:
        return "NOT_INDEXED"
    if matching and matching[0].lower() in ("true", "1"):
        return "INDEXED_DISABLED_SETTING"
    return "INDEXED_POTENTIAL_CONSUMER"

def inventory(env=None, reader=read_azure):
    env = os.environ if env is None else env
    subscription = env.get("AZURE_SUBSCRIPTION_ID")
    if (env.get("GITHUB_ACTIONS") != "true" or env.get("GITHUB_REPOSITORY") !=
            "saifsiddiqui59/RetailGrowthAI" or env.get("GITHUB_REF") != "refs/heads/main"
            or not subscription):
        raise RuntimeError("UNVERIFIED_DEV_SCOPE")
    account = reader("account", "show")
    if not isinstance(account, dict) or str(account.get("id", "")).lower() != subscription.lower():
        raise RuntimeError("UNVERIFIED_DEV_SCOPE")
    group = reader("group", "show", "-g", RG)
    tags = group.get("tags", {}) if isinstance(group, dict) else {}
    if (not isinstance(group, dict) or group.get("name") != RG
            or str(group.get("location", "")).lower().replace(" ", "") != "centralindia"
            or not isinstance(tags, dict)
            or {str(k).lower(): str(v).lower() for k,v in tags.items()}.get("app") != "retailgrowthai"
            or {str(k).lower(): str(v).lower() for k,v in tags.items()}.get("environment") != "dev"):
        raise RuntimeError("UNVERIFIED_DEV_SCOPE")
    result = {}
    for app in (FLEX, Y1):
        if exact_site_state(reader(*site_read_args(app)), app, subscription) != "Running":
            raise RuntimeError("UNVERIFIED_RUNNING_SITE")
        names = set(function_names(reader("functionapp", "function", "list", "-g", RG, "-n", app), app))
        settings = safe_setting_map(reader("functionapp", "config", "appsettings", "list", "-g", RG, "-n", app))
        result[app] = (names, {w: classify(names, settings, w) for w in sorted(WORKERS)})
    old, target = result[FLEX], result[Y1]
    return {"flex_worker_flags": old[1], "y1_worker_flags": target[1],
            "y1_exact_http_only": target[0] == ALL_HTTP_FUNCTIONS,
            "y1_exact_short_worker_index": target[0] == ALL_HTTP_FUNCTIONS | (WORKERS - {"render_campaign_reel"}),
            "y1_long_render_indexed": "render_campaign_reel" in target[0],
            "unknown_y1_index": bool(target[0] - ALL_HTTP_FUNCTIONS - WORKERS),
            "duplicate_potential_consumers": [w for w in sorted(WORKERS)
                 if old[1][w] == target[1][w] == "INDEXED_POTENTIAL_CONSUMER"],
            "drain_proven": False, "handoff_authorized": False}

if __name__ == "__main__":
    import json
    try:
        print("P0249_WORKER_OWNERSHIP_READONLY=" + json.dumps(inventory(), sort_keys=True))
    except Exception:
        print("P0249_WORKER_OWNERSHIP_READONLY=BLOCKED", file=sys.stderr)
        raise SystemExit(2)
