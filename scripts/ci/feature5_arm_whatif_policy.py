"""Validate the exact single-change Azure Feature5 ARM what-if safely.

Azure what-if in incremental mode includes unchanged resource-group members
as Ignore entries. Only the previously verified eight pre-existing DEV
resource names are allowed as Ignore. Any other change fails closed.
"""
from __future__ import annotations

import json
from pathlib import Path

ALLOWED_IGNORED = frozenset({
    "smartdetectoralertrules/failure anomalies - rgai-dev-appinsights",
    "accounts/rgai-dev-openai-d4e5ddbd",
    "components/rgai-dev-appinsights",
    "workspaces/rgai-dev-law",
    "storageaccounts/rgaid4e5ddbdf0d21d96",
    "serverfarms/rgai-dev-flex",
    "sites/rgai-dev-functions-d4e5ddbd",
    "staticsites/retailgrowthai-dev-preview",
})
TARGET_NAME = "rgai-f5-gpu-canary-eastus"


class UnsafeWhatIf(ValueError):
    """Azure would deploy, mutate, or ignore an unreviewed resource."""


def validate_what_if(payload: dict, subscription: str, resource_group: str,
                     environment: str = TARGET_NAME) -> dict:
    if not isinstance(payload, dict) or not isinstance(subscription, str) or len(subscription) != 36:
        raise UnsafeWhatIf("Invalid or untrusted Azure what-if envelope")
    if resource_group != "rg-retailgrowth-dev" or environment != TARGET_NAME:
        raise UnsafeWhatIf("Not the exact RetailGrowthAI DEV canary")
    if payload.get("error") or payload.get("status") not in (None, "Succeeded", "Success"):
        raise UnsafeWhatIf("Azure what-if reported an error or unsuccessful state")
    if payload.get("potentialChanges"):
        raise UnsafeWhatIf("Azure what-if included unreviewed potential changes")
    rows = payload.get("changes")
    if not isinstance(rows, list):
        raise UnsafeWhatIf("Azure what-if did not return a changes list")
    prefix = ("/subscriptions/" + subscription + "/resourcegroups/" +
              resource_group + "/providers/").lower()
    target = prefix + "microsoft.app/managedenvironments/" + environment.lower()
    creates = []
    ignored = set()
    for row in rows:
        if not isinstance(row, dict):
            raise UnsafeWhatIf("Azure returned malformed change record")
        rid = row.get("resourceId")
        if not isinstance(rid, str) or not rid.lower().startswith(prefix):
            raise UnsafeWhatIf("What-if contains foreign/unscoped resource")
        action = row.get("changeType")
        if action == "Create":
            if rid.lower() != target:
                raise UnsafeWhatIf("Azure would create another resource")
            creates.append(rid.lower())
        elif action == "Ignore":
            tail = "/".join(rid.lower().split("/")[-2:])
            if tail not in ALLOWED_IGNORED or tail in ignored:
                raise UnsafeWhatIf("Unreviewed/duplicate unchanged DEV resource")
            ignored.add(tail)
        else:
            # Modify, Delete, Deploy, NoChange, Unsupported: all disallowed.
            raise UnsafeWhatIf("Unexpected resource change action: " + str(action))
    if len(creates) != 1 or ignored != ALLOWED_IGNORED or len(rows) != 9:
        raise UnsafeWhatIf("Not exactly one approved Create and eight known Ignore entries")
    return {"creates": 1, "ignored": len(ignored), "target": TARGET_NAME}


def validate_file(path: str, subscription: str, resource_group: str,
                  environment: str = TARGET_NAME) -> dict:
    source = Path(path)
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 3_000_000:
        raise UnsafeWhatIf("Invalid what-if input file")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise UnsafeWhatIf("Unparseable what-if JSON") from exc
    return validate_what_if(payload, subscription, resource_group, environment)
