#!/usr/bin/env python3
"""Feature3 FLUX.2 Klein GPU start/stop safety wrapper (dry-run by default).

Targets an EXISTING manually provisioned Azure Container Apps manual GPU job
only. Does not create GPU resources, install checkpoints, modify ACA settings,
schedule automation, or approve inference. Never touches Feature5's job.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
import os
import re
import subprocess
import sys
from uuid import UUID

GROUP = "rg-retailgrowth-dev"
ENVIRONMENT = "rgai-f5-gpu-canary-eastus"
MAX_SECONDS = 900
MAX_CAP_USD = Decimal("2.5")
TERMINAL = {"succeeded", "failed", "stopped", "cancelled", "canceled", "completed"}
_SHA_IMAGE = re.compile(r"^[^@\s]+@sha256:[0-9a-f]{64}$")
_NAME = re.compile(r"^[a-z][a-z0-9-]{1,30}[a-z0-9]$")


class GPUControlDenied(ValueError):
    pass


def _guid(value):
    try:
        if str(UUID(value)) != value:
            raise ValueError("not canonical")
        return value
    except (ValueError, TypeError, AttributeError) as exc:
        raise GPUControlDenied("Explicit canonical Azure subscription UUID required") from exc


def _money(value):
    try:
        x = Decimal(value)
    except (ValueError, InvalidOperation, TypeError) as exc:
        raise GPUControlDenied("Current numeric all-in Azure rate and cap required") from exc
    if not x.is_finite() or x <= 0 or x.as_tuple().exponent < -6:
        raise GPUControlDenied("Positive bounded six-decimal USD amount required")
    return x


def _az(args, runner=subprocess.run):
    proc = runner(["az", *args, "--only-show-errors", "-o", "json"],
                  capture_output=True, text=True, timeout=90, check=False)
    if proc.returncode != 0:
        # Do not leak Azure error output: it may contain credentials/details.
        raise GPUControlDenied("Azure read or job operation failed; inspect private operator logs")
    try:
        return json.loads(proc.stdout or "null")
    except json.JSONDecodeError as exc:
        raise GPUControlDenied("Malformed Azure CLI result") from exc


def _job(job, sub, runner):
    data = _az(["containerapp", "job", "show", "--name", job,
                "--resource-group", GROUP, "--subscription", sub], runner)
    props = data.get("properties") if isinstance(data, dict) else None
    config = props.get("configuration") if isinstance(props, dict) else None
    template = props.get("template") if isinstance(props, dict) else None
    tags = data.get("tags", {}) if isinstance(data, dict) else {}
    expected = ("/subscriptions/" + sub + "/resourceGroups/" + GROUP +
                "/providers/Microsoft.App/managedEnvironments/" + ENVIRONMENT)
    env = props.get("environmentId", "") if isinstance(props, dict) else ""
    if (not isinstance(env, str) or env.lower() != expected.lower() or
        not isinstance(tags, dict) or tags.get("project") != "retailgrowthai" or
        tags.get("environment") != "dev" or tags.get("feature") != "feature3" or
        not isinstance(config, dict) or
        str(config.get("triggerType", "")).lower() != "manual" or
        type(config.get("replicaTimeout")) is not int or
        not 1 <= config["replicaTimeout"] <= MAX_SECONDS or
        config.get("replicaRetryLimit") != 0 or
        not isinstance(template, dict) or
        not isinstance(template.get("containers"), list) or
        len(template["containers"]) != 1 or
        not _SHA_IMAGE.fullmatch(template["containers"][0].get("image", ""))):
        raise GPUControlDenied("Existing job fails RetailGrowthAI DEV manual/immutable/timeout guard")
    manual = config.get("manualTriggerConfig")
    if not isinstance(manual, dict) or manual.get("parallelism") != 1 or \
            manual.get("replicaCompletionCount") != 1:
        raise GPUControlDenied("Only one replica and zero retry allowed")
    return data


def _executions(job, sub, runner):
    rows = _az(["containerapp", "job", "execution", "list", "--name", job,
                "--resource-group", GROUP, "--subscription", sub], runner)
    if not isinstance(rows, list):
        raise GPUControlDenied("Cannot confirm currently active GPU job executions")
    return rows


def execute(args, *, runner=subprocess.run, environ=None):
    env = os.environ if environ is None else environ
    sub = _guid(args.subscription)
    if not isinstance(args.job, str) or not _NAME.fullmatch(args.job):
        raise GPUControlDenied("Explicit existing Feature3 GPU job name required")
    plan = {"action": args.action, "job": args.job, "resource_group": GROUP,
            "environment": ENVIRONMENT, "subscription": sub,
            "gpu_off_by_default": True, "mode": "DRY_RUN" if not args.execute else "LIVE"}
    if args.action == "start":
        rate = _money(args.rate_usd_per_sec)
        cap = _money(args.max_usd)
        if cap > MAX_CAP_USD or rate * MAX_SECONDS > cap:
            raise GPUControlDenied("900-second all-in Azure bill estimate exceeds explicit <=$2.50 cap")
        plan["worst_case_usd"] = str(rate * MAX_SECONDS)
        plan["max_usd"] = str(cap)
    if args.action == "stop" and not args.execution:
        raise GPUControlDenied("Stop requires an explicit execution name; never stop another feature's jobs")
    if not args.execute:
        return plan
    if args.action == "start" and (
            env.get("RETAIL_FEATURE3_GPU_ENABLED") != "1" or
            env.get("RETAIL_FEATURE3_FLUX_START_APPROVED") != "YES"):
        raise GPUControlDenied("GPU disabled: explicit two-gate operator activation required")
    account = _az(["account", "show", "--subscription", sub], runner)
    if not isinstance(account, dict) or account.get("id", "").lower() != sub:
        raise GPUControlDenied("Azure subscription context does not match explicit DEV subscription")
    _job(args.job, sub, runner)
    running = _executions(args.job, sub, runner)
    if args.action == "start":
        if any(str(x.get("status", "")).lower() not in TERMINAL for x in running):
            raise GPUControlDenied("Current/pending or unknown GPU execution exists; refuse second billable start")
        # Start is only one manual attempt: no new resource, image, args or
        # environment overrides; CLI execution can still incur storage/egress.
        result = _az(["containerapp", "job", "start", "--name", args.job,
                      "--resource-group", GROUP, "--subscription", sub], runner)
    elif args.action == "stop":
        matched = [x for x in running if x.get("name") == args.execution]
        if len(matched) != 1:
            raise GPUControlDenied("Specific Feature3 execution not found; no bulk stop")
        if str(matched[0].get("status", "")).lower() in TERMINAL:
            return {**plan, "result": "ALREADY_TERMINAL"}
        result = _az(["containerapp", "job", "stop", "--name", args.job,
                      "--job-execution-name", args.execution,
                      "--resource-group", GROUP, "--subscription", sub], runner)
    else:
        raise GPUControlDenied("Unsupported action")
    # No success claim until operator independently reads back execution state.
    return {**plan, "result": "COMMAND_SUBMITTED_NOT_VERIFIED",
            "azure_receipt_returned": result is not None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "stop"))
    parser.add_argument("--subscription", required=True)
    parser.add_argument("--job", required=True, help="Existing Feature3 manual Container Apps Job")
    parser.add_argument("--execution", help="Required exact job execution name for stop")
    parser.add_argument("--rate-usd-per-sec", help="Current reviewed all-in rate, start only")
    parser.add_argument("--max-usd", help="Explicit upper per-run estimate <=2.50 USD, start only")
    parser.add_argument("--execute", action="store_true", help="Otherwise print dry-run, no Azure calls")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(execute(args), sort_keys=True))
    except GPUControlDenied as exc:
        parser.exit(2, "DENIED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
