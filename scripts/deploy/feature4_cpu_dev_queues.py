#!/usr/bin/env python3
"""Stage only two dedicated Feature4 CPU queues on the existing DEV account.

Default mode is offline/dry-run. Real --apply requires explicit protected DEV
environment guards, exact subscription/RG/storage identity and storage RBAC.
Does not create Function Apps, issue jobs, change flags or modify legacy queues.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess

DEV_REF = "jeearzffnjbvghwjjjrf"
DEV_RG = "rg-retailgrowth-dev"
DEV_STORAGE = "rgaid4e5ddbdf0d21d96"
QUEUE_NAMES = ("retail-feature4-cpu-render", "retail-feature4-cpu-render-poison")


class QueueGateError(ValueError):
    pass


def _az(args, *, runner=subprocess.run):
    result = runner(["az", *args], capture_output=True, text=True, timeout=45,
                    check=False)
    if result.returncode != 0:
        # No CLI stdout/stderr: errors may contain tenant, storage or tokens.
        raise QueueGateError("Azure read/queue command denied")
    try:
        return json.loads(result.stdout)
    except (ValueError, TypeError) as exc:
        raise QueueGateError("Azure did not provide expected JSON") from exc


def _queue_exists(name, runner):
    value = _az(["storage", "queue", "exists", "--account-name", DEV_STORAGE,
                 "--auth-mode", "login", "--name", name, "--output", "json"],
                runner=runner)
    if type(value) is not dict or type(value.get("exists")) is not bool:
        raise QueueGateError("Azure queue identity status is not verifiable")
    return value["exists"]


def stage_queues(env, *, apply=False, runner=subprocess.run):
    if env.get("RGAI_DEV_PROJECT_REF") != DEV_REF:
        raise QueueGateError("Wrong DEV project reference")
    if not apply:
        return {"mode": "OFFLINE_DRY_RUN", "queues": QUEUE_NAMES,
                "azure_changed": False}
    if env.get("RETAIL_FEATURE4_CPU_QUEUE_APPLY") != "YES":
        raise QueueGateError("Protected F4 DEV apply guard absent")
    if env.get("RETAIL_FEATURE4_CPU_RENDER_ENABLED", "").lower() == "true":
        raise QueueGateError("Customer render must remain disabled")
    subscription = env.get("AZURE_SUBSCRIPTION_ID", "")
    if not subscription or len(subscription) > 128:
        raise QueueGateError("Expected Azure DEV subscription missing")
    identity = _az(["account", "show", "--output", "json"], runner=runner)
    if identity.get("id") != subscription:
        raise QueueGateError("Azure subscription mismatch")
    rg = _az(["group", "show", "--name", DEV_RG, "--subscription", subscription,
              "--output", "json"], runner=runner)
    tags = {str(k).lower(): str(v).lower()
            for k, v in (rg.get("tags") or {}).items()}
    if (rg.get("name") != DEV_RG
            or str(rg.get("location", "")).lower() != "centralindia"
            or tags.get("app") != "retailgrowthai"
            or tags.get("environment") != "dev"):
        raise QueueGateError("Wrong or untagged RetailGrowthAI DEV RG")
    storage = _az(["storage", "account", "show", "--name", DEV_STORAGE,
                   "--resource-group", DEV_RG, "--subscription", subscription,
                   "--output", "json"], runner=runner)
    if (storage.get("name") != DEV_STORAGE
            or not str(storage.get("id", "")).lower().startswith(
                str(rg.get("id", "")).lower() + "/providers/microsoft.storage/storageaccounts/")):
        raise QueueGateError("Wrong storage account scope")
    present = [_queue_exists(name, runner) for name in QUEUE_NAMES]
    if any(present):
        # No implicit takeover of preexisting, possibly active customer queues.
        raise QueueGateError("Existing or partial F4 queue inventory; manual reconciliation needed")
    created = []
    for name in QUEUE_NAMES:
        response = _az(["storage", "queue", "create", "--name", name,
                        "--account-name", DEV_STORAGE, "--auth-mode", "login",
                        "--output", "json"], runner=runner)
        if response.get("created") is not True:
            raise QueueGateError("Azure did not confirm new queue creation")
        created.append(name)
    if not all(_queue_exists(name, runner) for name in QUEUE_NAMES):
        raise QueueGateError("Created queues not observable; leave worker OFF")
    return {"mode": "DEV_QUEUES_CREATED_WORKER_OFF", "queues": created,
            "azure_changed": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = stage_queues(os.environ, apply=args.apply)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
