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
import json
import os
import subprocess
import sys
import tempfile

from inspect_azure_connections_readonly import (read_azure, safe_setting_map, function_names,
                                                site_read_args, exact_site_state,
                                                cors_read_args, exact_cors)
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


FAILURE_CATEGORIES = frozenset({
    "AZURE_APPSETTINGS_SHAPE_INVALID",
    "AZURE_CORS_RESOURCE_IDENTITY_MISMATCH",
    "AZURE_CORS_SHAPE_INVALID",
    "AZURE_CORS_PROPERTIES_NOT_OBJECT",
    "AZURE_CORS_VALUE_NOT_OBJECT",
    "AZURE_CORS_ORIGINS_INVALID",
    "AZURE_CORS_CREDENTIALS_UNVERIFIED",
    "AZURE_CORS_DECLARATION_ABSENT",
    "AZURE_CORS_DECLARATIONS_CONFLICT",
    "UNAPPROVED_AZURE_CORS_RESOURCE_READ",
    "AZURE_SITE_IDENTITY_MISMATCH",
    "AZURE_SITE_STATE_UNVERIFIED",
    "UNAPPROVED_AZURE_SITE_READ",
    "ORIGINAL_FLEX_STOPPED",
    "TARGET_Y1_STOPPED",
    "AZURE_INDEX_DUPLICATE_FUNCTION",
    "AZURE_INDEX_FOREIGN_FUNCTION",
    "AZURE_INDEX_SHAPE_INVALID",
    "AZURE_INDEX_UNEXPECTED_FUNCTION_NAME",
    "AZURE_INVENTORY_SHAPE_INVALID",
    "AZURE_READ_ONLY_INVENTORY_FAILED",
    "DEV_RESOURCE_GROUP_UNVERIFIED",
    "EXISTING_Y1_CORE_SETTING_DRIFT",
    "FOREIGN_DEV_RESOURCE_GROUP",
    "FOREIGN_DEV_SUBSCRIPTION",
    "FOREIGN_OR_STOPPED_APP",
    "ORIGINAL_CORE_SETTING_ABSENT_OR_MALFORMED",
    "ORIGINAL_FLEX_RUNTIME_UNVERIFIED",
    "ORIGINAL_OR_TARGET_RUNTIME_UNVERIFIED",
    "ORIGINAL_RUNTIME_CONFIG_MALFORMED",
    "ORIGINAL_SUPABASE_URL_MISMATCH",
    "PROTECTED_DEV_CORS_WRITE_FAILED",
    "PROTECTED_DEV_STAGE_CONFIRMATION_REQUIRED",
    "PROTECTED_DEV_STAGE_WRITE_FAILED",
    "STAGED_CORE_CONNECTION_READBACK_MISMATCH",
    "TARGET_Y1_HOST_STORAGE_ABSENT",
    "TARGET_Y1_RUNTIME_UNVERIFIED",
    "TRUSTED_DEV_MAIN_OIDC_REQUIRED",
    "UNAPPROVED_AZURE_APPSETTING_COMMAND",
    "UNAPPROVED_AZURE_CORS_COMMAND",
    "UNAPPROVED_AZURE_FUNCTION_COMMAND",
    "UNAPPROVED_AZURE_READ_COMMAND",
    "UNAPPROVED_STAGED_SETTING",
    "UNVERIFIED_CROSS_IDENTITY_SECRET_REFERENCE",
    "Y1_FRONTEND_CORS_UNVERIFIED",
    "Y1_NOT_EXACT_FIVE_GET_BASELINE",
})


def _failure_category(error):
    """Reflect only known constant categories, never CLI output or exception text."""
    if type(error) in (RuntimeError, ValueError) and len(error.args) == 1:
        code = error.args[0]
        if type(code) is str and code in FAILURE_CATEGORIES:
            return code
    if isinstance(error, subprocess.TimeoutExpired):
        return "AZURE_COMMAND_TIMEOUT"
    if isinstance(error, OSError):
        return "AZURE_COMMAND_UNAVAILABLE"
    return "UNKNOWN_REDACTED"


def _checkpoint(name):
    # Caller passes only source-defined labels, never Azure response values.
    print("P0249_Y1_STAGE_CHECKPOINT=" + name, flush=True)


def _original_python(site, settings):
    """Read either ARM properties or the Azure CLI flattened resource shape.

    Flex runtime is defined by functionAppConfig.runtime.name; the historical
    FUNCTIONS_WORKER_RUNTIME setting may be absent. Conflicting nonempty
    runtime declarations or malformed explicit config fail closed.
    """
    names = []
    if "FUNCTIONS_WORKER_RUNTIME" in settings:
        names.append(settings["FUNCTIONS_WORKER_RUNTIME"])
    props = site.get("properties")
    if props is not None and not isinstance(props, dict):
        raise RuntimeError("ORIGINAL_RUNTIME_CONFIG_MALFORMED")
    for parent in (site, props or {}):
        config = parent.get("functionAppConfig")
        if config is None:
            continue
        if not isinstance(config, dict):
            raise RuntimeError("ORIGINAL_RUNTIME_CONFIG_MALFORMED")
        runtime = config.get("runtime")
        if not isinstance(runtime, dict) or not isinstance(runtime.get("name"), str):
            raise RuntimeError("ORIGINAL_RUNTIME_CONFIG_MALFORMED")
        names.append(runtime["name"])
    return bool(names) and all(type(name) is str and name.lower() == "python" for name in names)


def _required_scope(env):
    if (env.get("GITHUB_ACTIONS") != "true"
        or env.get("GITHUB_REPOSITORY") != REPO
        or env.get("GITHUB_REF") != "refs/heads/main"
        or not env.get("AZURE_SUBSCRIPTION_ID")):
        raise RuntimeError("TRUSTED_DEV_MAIN_OIDC_REQUIRED")
    return env["AZURE_SUBSCRIPTION_ID"]


def plan(*, env=None, runner=subprocess.run):
    env = os.environ if env is None else env
    subscription = _required_scope(env)

    def az(checkpoint, *args):
        _checkpoint(checkpoint)
        return read_azure(*args, runner=runner)

    account = az("ACCOUNT", "account", "show")
    if not isinstance(account, dict) or str(account.get("id", "")).lower() != subscription.lower():
        raise RuntimeError("FOREIGN_DEV_SUBSCRIPTION")
    group = az("RESOURCE_GROUP", "group", "show", "-g", RG)
    if not isinstance(group, dict):
        raise RuntimeError("DEV_RESOURCE_GROUP_UNVERIFIED")
    tags = {str(k).lower(): str(v).lower() for k,v in (group.get("tags") or {}).items()}
    if (group.get("name") != RG
        or str(group.get("location", "")).lower().replace(" ", "") != "centralindia"
        or tags.get("app") != "retailgrowthai"
        or tags.get("environment") != "dev"):
        raise RuntimeError("FOREIGN_DEV_RESOURCE_GROUP")

    old = az("ORIGINAL_FLEX_ARM_SITE", *site_read_args(FLEX))
    old_state = exact_site_state(old, FLEX, subscription)
    print("P0249_Y1_ORIGINAL_FLEX_RUNNING=" + str(old_state == "Running").lower(), flush=True)
    if old_state != "Running":
        raise RuntimeError("ORIGINAL_FLEX_STOPPED")
    target = az("TARGET_Y1_ARM_SITE", *site_read_args(Y1))
    target_state = exact_site_state(target, Y1, subscription)
    print("P0249_Y1_TARGET_RUNNING=" + str(target_state == "Running").lower(), flush=True)
    if target_state != "Running":
        raise RuntimeError("TARGET_Y1_STOPPED")
    names = function_names(
        az("TARGET_Y1_INDEX", "functionapp", "function", "list", "-g", RG, "-n", Y1), Y1)
    if set(names) != FIVE:
        raise RuntimeError("Y1_NOT_EXACT_FIVE_GET_BASELINE")

    cors = exact_cors(az("TARGET_Y1_ARM_CORS", *cors_read_args(Y1, subscription)),
                      Y1, subscription)
    if (not isinstance(cors, dict)
        or cors.get("supportCredentials") is not False
        or not isinstance(cors.get("allowedOrigins"), list)
        or any(origin not in (FRONTEND, "https://portal.azure.com")
               for origin in cors["allowedOrigins"])):
        raise RuntimeError("Y1_FRONTEND_CORS_UNVERIFIED")

    source = safe_setting_map(az("ORIGINAL_FLEX_SETTINGS", "functionapp", "config", "appsettings",
                                 "list", "-g", RG, "-n", FLEX))
    existing = safe_setting_map(az("TARGET_Y1_SETTINGS", "functionapp", "config", "appsettings",
                                   "list", "-g", RG, "-n", Y1))
    _checkpoint("CORE_RUNTIME_VALIDATION")
    if source.get("RETAIL_SUPABASE_URL") != SUPABASE:
        raise RuntimeError("ORIGINAL_SUPABASE_URL_MISMATCH")
    if not _original_python(old, source):
        raise RuntimeError("ORIGINAL_FLEX_RUNTIME_UNVERIFIED")
    if existing.get("FUNCTIONS_WORKER_RUNTIME") != "python":
        raise RuntimeError("TARGET_Y1_RUNTIME_UNVERIFIED")
    if not existing.get("AzureWebJobsStorage"):
        raise RuntimeError("TARGET_Y1_HOST_STORAGE_ABSENT")
    _checkpoint("CORE_SETTING_VALIDATION")
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
    return (tuple(missing), {name: source[name] for name in missing},
            FRONTEND not in cors["allowedOrigins"])


def _write_cors(*, runner=subprocess.run):
    # Only the exact already-approved Free SWA origin, never a wildcard.
    argv = ["az", "functionapp", "cors", "add", "-g", RG, "-n", Y1,
            "--allowed-origins", FRONTEND, "-o", "none", "--only-show-errors"]
    outcome = runner(argv, capture_output=True, text=True, timeout=90, check=False)
    if outcome.returncode != 0:
        raise RuntimeError("PROTECTED_DEV_CORS_WRITE_FAILED")


def _write_missing(settings, *, runner=subprocess.run):
    if not settings:
        return
    if set(settings) - set(CORE) or any(
        not isinstance(value, str) for value in settings.values()
    ):
        raise RuntimeError("UNAPPROVED_STAGED_SETTING")

    # Azure CLI supports --settings @file with a JSON name/value array.
    # Never put service-role or storage credentials in subprocess argv,
    # environment variables, GitHub logs or command output.
    with tempfile.TemporaryDirectory(prefix="rgai-p0249-y1-") as directory:
        os.chmod(directory, 0o700)
        settings_path = os.path.join(directory, "missing-appsettings.json")
        fd = os.open(settings_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as payload:
            json.dump([
                {"name": name, "value": settings[name], "slotSetting": False}
                for name in CORE if name in settings
            ], payload)
            payload.write("\n")
        argv = [
            "az", "functionapp", "config", "appsettings", "set",
            "-g", RG, "-n", Y1, "--settings", "@" + settings_path,
            "-o", "none", "--only-show-errors",
        ]
        # Suppress *both* output streams; the file is removed on success,
        # Azure error, timeout and Python exceptions.
        result = runner(argv, capture_output=True, text=True,
                        timeout=90, check=False)
        if result.returncode != 0:
            raise RuntimeError("PROTECTED_DEV_STAGE_WRITE_FAILED")


def run(*, apply=False, env=None, reader=subprocess.run, writer=subprocess.run):
    env = os.environ if env is None else env
    missing, values, missing_cors = plan(env=env, runner=reader)
    for name in missing:
        print("P0249_Y1_MISSING_CORE_SETTING=" + name)
    print("P0249_Y1_CONNECTION_STAGE_PLAN=" +
          ("MISSING_" + str(len(missing)) if missing else "ALREADY_MATCHING"))
    print("P0249_Y1_MISSING_FRONTEND_CORS=" + str(missing_cors).lower())
    if not apply:
        print("P0249_Y1_CORE_CONNECTION_STAGE=READ_ONLY")
        return missing
    if (env.get("RGAI_Y1_CORE_CONNECTION_STAGE") != STAGE_CONFIRM
        or env.get("GITHUB_ENVIRONMENT") != "dev"):
        raise RuntimeError("PROTECTED_DEV_STAGE_CONFIRMATION_REQUIRED")
    # Stage credentials first: a failed settings write must not leave CORS
    # newly exposed. A later CORS failure leaves only missing-only settings;
    # the next protected run can safely read back and resume without overwrite.
    _write_missing(values, runner=writer)
    if missing_cors:
        _write_cors(runner=writer)
    after, _, after_cors = plan(env=env, runner=reader)
    if after or after_cors:
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
    except Exception as error:
        print("P0249_Y1_STAGE_FAILURE_CATEGORY=" + _failure_category(error), file=sys.stderr)
        print("P0249_Y1_CORE_CONNECTION_STAGE=BLOCKED", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
