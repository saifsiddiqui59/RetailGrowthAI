"""Azure DEV GPU discovery using READ-ONLY Azure CLI calls.

Run only in an already Azure-authenticated shell with AZURE_SUBSCRIPTION_ID
set to the exact existing DEV subscription. Nothing is provisioned, pushed,
started, or billed by these commands. This does NOT approve deployment.
"""
from __future__ import annotations

import json
import os
import re
import subprocess

from .azure_gpu_preflight import (
    DEV_GROUP, REGION, assess_azure_a100_preflight,
    A100Readiness, _a100_profile,
)
from .contracts import MotionError

_AZ = "az"
_AZ_TIMEOUT = 45
_VALID_ENV = re.compile(r"^[A-Za-z][A-Za-z0-9-]{1,62}$")


def _read_az(*args: str):
    # Command allowlist prevents this inventory from becoming a write-capable
    # arbitrary Azure CLI wrapper (even with malicious environment names).
    commands = (
        ("account", "show"),
        ("group", "show"),
        ("containerapp", "env", "list"),
        ("containerapp", "env", "list-usages"),
        ("containerapp", "env", "workload-profile", "list-supported"),
    )
    if not any(args[:len(p)] == p for p in commands):
        raise MotionError("Disallowed Azure inventory operation")
    cmd = [_AZ, *args, "--output", "json"]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True,
                                timeout=_AZ_TIMEOUT, text=True)
        return json.loads(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        # Never echo an az command's stderr; it might include tenant data.
        raise MotionError("Azure GPU read-only inventory unavailable") from exc


def inspect_current_dev(*, expected_subscription_id: str) -> A100Readiness:
    if not isinstance(expected_subscription_id, str) or len(expected_subscription_id) != 36:
        raise MotionError("Exact pre-approved Azure DEV subscription ID required")
    account = _read_az("account", "show")
    if not isinstance(account, dict) or account.get("id") != expected_subscription_id:
        raise MotionError("Incorrect Azure account; refusing cross-subscription inspection")
    group = _read_az("group", "show", "--name", DEV_GROUP)
    supported = _read_az("containerapp", "env", "workload-profile",
                         "list-supported", "--location", REGION)
    environments = _read_az("containerapp", "env", "list",
                            "--resource-group", DEV_GROUP)
    if not isinstance(environments, list):
        raise MotionError("Azure DEV environment inventory invalid")
    usage: dict[str, list] = {}
    for env in environments:
        if not isinstance(env, dict):
            continue
        name = env.get("name")
        if (str(env.get("location", "")).lower().replace(" ", "") != REGION or
            not isinstance(name, str) or not _VALID_ENV.fullmatch(name) or
            not any(_a100_profile(p) for p in
                    ((env.get("properties") or {}).get("workloadProfiles") or []))):
            continue
        value = _read_az("containerapp", "env", "list-usages",
                         "--resource-group", DEV_GROUP, "--name", name)
        usage[name] = value if isinstance(value, list) else (
            value.get("value", []) if isinstance(value, dict) else [])
    return assess_azure_a100_preflight(
        account=account, resource_group=group,
        supported_profiles=supported, environments=environments,
        usage_by_environment=usage,
        expected_subscription_id=expected_subscription_id,
    )


def main():
    expected = os.environ.get("AZURE_SUBSCRIPTION_ID", "")
    try:
        result = inspect_current_dev(expected_subscription_id=expected)
    except MotionError as exc:
        print("BLOCKED:", exc)
        raise SystemExit(3) from None
    print("Azure A100 DEV preflight:", result.status)
    print("Existing matching environment:", result.eligible_environment or "(none)")
    for reason in result.reasons:
        print(" -", reason)
    print("This was a READ-ONLY check. No Azure GPU or model deployed.")
    if result.status != "INSPECTION_PASS_ONLY":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
