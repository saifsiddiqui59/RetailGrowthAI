#!/usr/bin/env python3
"""Protected, opt-in Y1 missing-only core connection staging for Issue #249.

The default plan is read-only and emits only fixed setting NAMES. The apply
mode may copy only four current same-DEV core values from the original Flex
site to the dedicated Y1 site, through the protected DEV GitHub environment.
It never logs credentials, creates identities, reconfigures workers or routes,
stops Flex, or claims a hosted deployment/cutover.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

from inspect_azure_connections_readonly import read_azure, safe_setting_map, function_names
from retirement_gate import RG, Y1, FLEX, FRONTEND, SUPABASE

REPO = "saifsiddiqui59/RetailGrowthAI"
STAGE_CONFIRM = "YES-P0249-RETAILGROWTHAI-DEV-Y1-MISSING-ONLY"
CORE = (
    "RETAIL_SUPABASE_URL",
    "RETAIL_SUPABASE_PUBLISHABLE_KEY",
    "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
    "RETAIL_STORAGE",
)
FIVE = frozenset({
    "p0249_health", "campaign_read", "render_job_read",
    "poster_job_read", "poster_draft_read",
})


def _required_scope(env):
    if (env.get("GITHUB_ACTIONS") != "true"
        or env.get("GITHUB_REPOSITORY") != REPO
        or env.get("GITHUB_REF") != "refs/heads/main"
        or not env.get("AZURE_SUBSCRIPTION_ID")):
        raise RuntimeError("TRUSTED_DEV_MAIN_OIDC_REQUIRED")
    return env["AZURE_SUBSCRIPTION_ID"]


def _site_ok(site, name, subscription):
    if not isinstance(site, dict):
        return False
    expected = ("/subscriptions/" + subscription + "/resourcegroups/"
                + RG + "/providers/microsoft.web/sites/" + name).lower()
    return (site.get("name") == name
            and str(site.get("id", "")).lower() == expected
            and site.get("state") == "Running")


def plan(*, env=None, runner=subprocess.run):
    env = os.environ if env is None else env
    subscription = _required_scope(env)

    def az(*args):
        return read_azure(*args, runner=runner)

    account = az("account", "show")
    if not isinstance(account, dict) or str(account.get("id", "")).lower() != subscription.lower():
        raise RuntimeError("FOREIGN_DEV_SUBSCRIPTION")
    group = az("group", "show", "-g", RG)
    if not isinstance(group, dict):
        raise RuntimeError("DEV_RESOURCE_GROUP_UNVERIFIED")
    tags = {str(k).lower(): str(v).lower() for k,v in (group.get("tags") or {}).items()}
    if (group.get("name") != RG
        or str(group.get("location", "")).lower().replace(" ", "") != "centralindia"
        or tags.get("app") != "retailgrowthai"
        or tags.get("environment") != "dev"):
        raise RuntimeError("FOREIGN_DEV_RESOURCE_GROUP")

    old = az("functionapp", "show", "-g", RG, "-n", FLEX)
    target = az("functionapp", "show", "-g", RG, "-n", Y1)
    if not _site_ok(old, FLEX, subscription) or not _site_ok(target, Y1, subscription):
        raise RuntimeError("FOREIGN_OR_STOPPED_APP")
    names = function_names(
        az("functionapp", "function", "list", "-g", RG, "-n", Y1), Y1)
    if set(names) != FIVE:
        raise RuntimeError("Y1_NOT_EXACT_FIVE_GET_BASELINE")

    cors = az("functionapp", "cors", "show", "-g", RG, "-n", Y1)
    if (not isinstance(cors, dict)
        or cors.get("supportCredentials") is not False
        or cors.get("allowedOrigins") != [FRONTEND]):
        raise RuntimeError("Y1_FRONTEND_CORS_UNVERIFIED")

    source = safe_setting_map(az("functionapp", "config", "appsettings",
                                 "list", "-g", RG, "-n", FLEX))
    existing = safe_setting_map(az("functionapp", "config", "appsettings",
                                   "list", "-g", RG, "-n", Y1))
    if (source.get("RETAIL_SUPABASE_URL") != SUPABASE
        or source.get("FUNCTIONS_WORKER_RUNTIME") != "python"
        or existing.get("FUNCTIONS_WORKER_RUNTIME") != "python"
        or not existing.get("AzureWebJobsStorage")):
        raise RuntimeError("ORIGINAL_OR_TARGET_RUNTIME_UNVERIFIED")
    missing = []
    for key in CORE:
        value = source.get(key)
        if not isinstance(value, str) or len(value) < (35 if key != "RETAIL_SUPABASE_URL" else 1):
            raise RuntimeError("ORIGINAL_CORE_SETTING_ABSENT_OR_MALFORMED")
        if value.startswith("@Microsoft.KeyVault("):
            raise RuntimeError("UNVERIFIED_CROSS_IDENTITY_SECRET_REFERENCE")
        current = existing.get(key)
        if current is None:
            missing.append(key)
        elif current != value:
            raise RuntimeError("EXISTING_Y1_CORE_SETTING_DRIFT")
    # No mutation or source credentials are returned to an ordinary caller.
    return (tuple(missing), {name: source[name] for name in missing})


def _write_missing(settings, *, runner=subprocess.run):
    if not settings:
        return
    if set(settings) - set(CORE):
        raise RuntimeError("UNAPPROVED_STAGED_SETTING")
    argv = [
        "az", "functionapp", "config", "appsettings", "set",
        "-g", RG, "-n", Y1, "--settings",
        *(name + "=" + settings[name] for name in CORE if name in settings),
        "-o", "none", "--only-show-errors",
    ]
    # Values remain process-local to the trusted runner, never rendered or
    # attached to Actions artifacts/logs. Do not print raw CLI failures.
    result = runner(argv, capture_output=True, text=True, timeout=90, check=False)
    if result.returncode != 0:
        raise RuntimeError("PROTECTED_DEV_STAGE_WRITE_FAILED")


def run(*, apply=False, env=None, reader=subprocess.run, writer=subprocess.run):
    env = os.environ if env is None else env
    missing, values = plan(env=env, runner=reader)
    for name in missing:
        print("P0249_Y1_MISSING_CORE_SETTING=" + name)
    print("P0249_Y1_CONNECTION_STAGE_PLAN=" +
          ("MISSING_" + str(len(missing)) if missing else "ALREADY_MATCHING"))
    if not apply:
        print("P0249_Y1_CORE_CONNECTION_STAGE=READ_ONLY")
        return missing
    if (env.get("RGAI_Y1_CORE_CONNECTION_STAGE") != STAGE_CONFIRM
        or env.get("GITHUB_ENVIRONMENT") != "dev"):
        raise RuntimeError("PROTECTED_DEV_STAGE_CONFIRMATION_REQUIRED")
    _write_missing(values, runner=writer)
    after, _ = plan(env=env, runner=reader)
    if after:
        raise RuntimeError("STAGED_CORE_CONNECTION_READBACK_MISMATCH")
    print("P0249_Y1_CORE_CONNECTION_STAGE=VERIFIED_MISSING_ONLY")
    print("P0249_Y1_HOSTED_38_HTTP_DEPLOYED=false")
    print("P0249_FLEX_RETIREMENT_AUTHORIZED=false")
    return ()


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--apply", action="store_true",
                      help="Requires separately protected DEV workflow identity and confirmation")
    opts = args.parse_args()
    try:
        run(apply=opts.apply)
    except Exception:
        print("P0249_Y1_CORE_CONNECTION_STAGE=BLOCKED", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
