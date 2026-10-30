"""Read-only Azure A100 preflight; not a deployment or quota request.

Parse snapshots captured with signed-in Azure CLI. Do not accept an arbitrary
region, borrowed PROD subscription, or regional A100 catalog as proof of an
actual available GPU quota. No cloud calls or access tokens in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from .contracts import MotionError

DEV_GROUP = "rg-retailgrowth-dev"
CANARY_ENV = "rgai-f5-gpu-canary-eastus"
REGION = "eastus"
PROFILE_MATCH = "NCA100"


def _a100_profile(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    names = [item.get("name"), item.get("workloadProfileType"), item.get("type")]
    return any(isinstance(v, str) and
               ("NCA100" in v.upper() or "NC24-A100" in v.upper() or
                "GPU-A100" in v.upper()) for v in names)


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
    # Azure's managed-environment A100 quota can ONLY be read once a v2
    # workload-profiles environment exists in a supported region. It does
    # NOT need to contain a billable A100 workload profile yet.
    matching = [e for e in environments if isinstance(e, dict)
                and e.get("name") == CANARY_ENV]
    if not matching:
        return A100Readiness("ENVIRONMENT_REQUIRED", (
            "Create reviewed, EMPTY East US workload-profiles DEV environment before quota read",
            "Missing environment does not mean A100 quota is zero",
        ), None)
    if len(matching) != 1:
        return A100Readiness("BLOCKED", ("Ambiguous dedicated DEV environment",), None)
    e = matching[0]
    tags = {str(k).lower(): str(v).lower()
            for k, v in (e.get("tags") or {}).items()}
    profiles = (e.get("properties") or {}).get("workloadProfiles") or []
    if (str(e.get("location", "")).lower().replace(" ", "") != REGION or
        e.get("provisioningState") != "Succeeded" or
        tags.get("app") != "retailgrowthai" or tags.get("environment") != "dev" or
        tags.get("feature") != "feature5" or
        profiles != [{"name": "Consumption", "workloadProfileType": "Consumption"}]):
        return A100Readiness("BLOCKED", ("Unexpected environment, tags or paid profile",), CANARY_ENV)
    target = CANARY_ENV
    if not isinstance(usage_by_environment, dict):
        return A100Readiness("BLOCKED", ("GPU quota inventory is malformed",), target)
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
        # A missing current-usage field is NOT evidence of zero GPUs in use.
        # Reject booleans, which Python otherwise coerces to 0 and 1.
        raw_limit = q["limit"]
        raw_used = q["currentValue"] if "currentValue" in q else q["value"]
        if type(raw_limit) is bool or type(raw_used) is bool:
            raise ValueError("Boolean GPU quota is not a count")
        limit = float(raw_limit)
        used = float(raw_used)
    except (ValueError, TypeError, KeyError, OverflowError):
        return A100Readiness("BLOCKED", ("A100 quota values invalid",), target)
    # Float accepts Infinity/NaN and 1e309; a fabricated infinite limit
    # must never qualify an environment for a later paid GPU launch.
    if not (isfinite(limit) and isfinite(used) and
            limit.is_integer() and used.is_integer() and
            0 <= used < limit and limit >= 1):
        return A100Readiness("BLOCKED", ("No verified finite A100 GPU quota",), target)
    return A100Readiness(
        "INSPECTION_PASS_ONLY",
        ("Quota is available, but image/weights/identity/approved budget not verified",
         "No GPU has been created or deployed"),
        target,
    )
