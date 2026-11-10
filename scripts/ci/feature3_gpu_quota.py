"""Read-only Azure Container Apps GPU quota validator for Feature3 FLUX.

Fail closed: an existing EMPTY Feature5 workload-profiles environment is not
an allocated GPU. Check the exact resource group, region, named environment,
profile and **T4** quota separately from its A100 quota. This helper never
issues Azure management API writes or calls an inference model.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TARGET_ENV = "rgai-f5-gpu-canary-eastus"
LOCATION = "eastus"
GPU_PROFILE = "Consumption-GPU-NC8as-T4"


class CapacityBlocked(ValueError):
    pass


def probe_feature3_t4(env: dict, usage: object) -> dict:
    if not isinstance(env, dict) or env.get("name") != TARGET_ENV or (
        str(env.get("location", "")).lower().replace(" ", "") != LOCATION
    ):
        raise CapacityBlocked("Unexpected existing Feature5 managed environment")
    if env.get("properties", {}).get("provisioningState") not in ("Succeeded", "succeeded"):
        raise CapacityBlocked("Existing Feature5 environment is not healthy")
    profiles = env.get("properties", {}).get("workloadProfiles")
    if not isinstance(profiles, list) or not any(
        p.get("name") == "Consumption" and p.get("workloadProfileType") == "Consumption"
        for p in profiles if isinstance(p, dict)
    ):
        raise CapacityBlocked("Expected preexisting Consumption workload-profiles environment")
    items = usage if isinstance(usage, list) else (
        usage.get("value", []) if isinstance(usage, dict) else []
    )
    if not isinstance(items, list):
        raise CapacityBlocked("GPU quota response malformed")
    matches = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        field = item.get("name") or {}
        text = field.get("value") if isinstance(field, dict) else field
        key = str(text or "").replace(" ", "").replace("_", "").lower()
        if "consumptiont4gpu" in key and "consumptiont4gpus" not in key:
            # Avoid silently equating A100 or non-GPU quotas.
            key = "managedenvironmentconsumptiont4gpus" if "managedenvironment" in key else key
        if "managedenvironmentconsumptiont4gpus" == key:
            if "t4" in matches:
                raise CapacityBlocked("Duplicate T4 quota records")
            try:
                limit = int(item.get("limit"))
                used = int(item.get("currentValue"))
            except (TypeError, ValueError) as exc:
                raise CapacityBlocked("Unrecognized T4 quota values") from exc
            if type(item.get("limit")) is bool or type(item.get("currentValue")) is bool:
                raise CapacityBlocked("Boolean GPU quota is invalid")
            if limit < 0 or used < 0 or used > limit:
                raise CapacityBlocked("Contradictory GPU quota")
            matches["t4"] = {"limit": limit, "used": used, "remaining": limit - used}
    if "t4" not in matches:
        raise CapacityBlocked("T4 quota not published for existing environment")
    return {
        "existing_environment": TARGET_ENV, "region": LOCATION,
        "profile": GPU_PROFILE, "t4_limit": matches["t4"]["limit"],
        "t4_in_use": matches["t4"]["used"],
        "t4_available": matches["t4"]["remaining"],
        "eligible_for_future_deployment_review": matches["t4"]["remaining"] >= 1,
        "gpu_allocated_by_this_check": False,
        "deployment_executed": False,
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--environment", type=Path, required=True)
    p.add_argument("--quota", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        env = json.loads(args.environment.read_text(encoding="utf-8"))
        quota = json.loads(args.quota.read_text(encoding="utf-8"))
        result = probe_feature3_t4(env, quota)
    except (CapacityBlocked, OSError, UnicodeError, ValueError) as exc:
        print("FEATURE3_T4_READONLY_BLOCKED:", str(exc))
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
