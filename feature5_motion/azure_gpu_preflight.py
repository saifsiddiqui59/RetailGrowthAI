"""Read-only Azure A100 preflight; not a deployment or quota request.

Parse snapshots captured with signed-in Azure CLI. Do not accept an arbitrary
region, borrowed PROD subscription, or regional A100 catalog as proof of an
actual available GPU quota. No cloud calls or access tokens in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import MotionError

DEV_GROUP = "rg-retailgrowth-dev"
REGION = "eastus"
PROFILE_MATCH = "NCA100"


def _a100_profile(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    profile = item.get("name") or item.get("workloadProfileType") or item.get("type") or ""
    return isinstance(profile, str) and PROFILE_MATCH in profile.upper()


def _name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("value", ""))
    return str(value or "")


@dataclass(frozen=True)
class A100Readiness:
    status: str
    reasons: tuple[str, ...]
    eligible_environment: str | None


def assess_azure_a100_preflight(*, account: dict, resource_group: dict,
                                supported_profiles: list, environments: list,
                                usage_by_environment: dict[str, list],
                                expected_subscription_id: str) -> A100Readiness:
    """Fail closed, no resource creation. Quota is needed, not just meter price."""
    if not isinstance(expected_subscription_id, str) or not expected_subscription_id.strip():
        raise MotionError("Expected DEV subscription ID missing")
    if not isinstance(account, dict) or account.get("id") != expected_subscription_id or account.get("state") != "Enabled":
        raise MotionError("Incorrect/inactive Azure subscription: no GPU deployment")
    if (not isinstance(resource_group, dict) or
        resource_group.get("name") != DEV_GROUP or
        str(resource_group.get("location", "")).lower().replace(" ", "") != "centralindia"):
        raise MotionError("Not the isolated RetailGrowthAI DEV resource group")
    tags = resource_group.get("tags") or {}
    if not isinstance(tags, dict):
        raise MotionError("Invalid DEV ownership tags")
    normalized = {str(k).lower(): str(v).lower() for k, v in tags.items()}
    if normalized.get("app") != "retailgrowthai" or normalized.get("environment") != "dev":
        raise MotionError("Dedicated DEV ownership tags not verified")
    if not isinstance(supported_profiles, list) or not isinstance(environments, list):
        raise MotionError("Malformed Azure GPU inventory response")
    if not any(_a100_profile(x) for x in supported_profiles):
        return A100Readiness("BLOCKED", ("No A100 consumption profile verified in East US",), None)
    eligible = []
    for e in environments:
        if not isinstance(e, dict):
            continue
        if (str(e.get("location", "")).lower().replace(" ", "") != REGION or
            e.get("provisioningState") != "Succeeded"):
            continue
        # The actual environment must have a Consumption A100 workload profile.
        profiles = (e.get("properties") or {}).get("workloadProfiles", [])
        if any(_a100_profile(p) for p in profiles):
            eligible.append(e.get("name"))
    if len(eligible) != 1 or not isinstance(eligible[0] if eligible else None, str):
        return A100Readiness("BLOCKED", ("No unique existing East US A100 DEV environment",), None)
    target = eligible[0]
    rows = usage_by_environment.get(target)
    if not isinstance(rows, list):
        return A100Readiness("BLOCKED", ("GPU quota not readable for selected environment",), target)
    gpu_rows = [q for q in rows if isinstance(q, dict) and
                PROFILE_MATCH in _name(q.get("name")).upper() and
                "GPU" in _name(q.get("name")).upper()]
    if len(gpu_rows) != 1:
        return A100Readiness("BLOCKED", ("A100 quota row absent or ambiguous",), target)
    q = gpu_rows[0]
    try:
        limit = float(q["limit"])
        used = float(q.get("currentValue", q.get("value", 0)))
    except (ValueError, TypeError, KeyError):
        return A100Readiness("BLOCKED", ("A100 quota values invalid",), target)
    if not (0 <= used < limit and limit >= 1):
        return A100Readiness("BLOCKED", ("No unconsumed A100 environment GPU quota",), target)
    return A100Readiness(
        "INSPECTION_PASS_ONLY",
        ("Quota is available, but image/weights/identity/approved budget not verified",
         "No GPU has been created or deployed"),
        target,
    )
