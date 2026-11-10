"""Immutable, narrowly scoped Azure environment-only deployment review.

This module performs LOCAL JSON policy checks only. It cannot authenticate
to Azure or deploy resources. The only permissible first-step resource is an
unused, scale-to-zero, East US workload-profiles Container Apps environment.
An existing DEV OIDC coordinator workflow must preview the ARM what-if and
separately authorize the create. The Hunyuan GPU remains disabled.
"""
from __future__ import annotations
import json
from pathlib import Path
from .contracts import MotionError

TEMPLATE = Path(__file__).resolve().parent / "infra" / "empty_gpu_env.json"
TARGET_RG = "rg-retailgrowth-dev"
TARGET_ENV = "rgai-f5-gpu-canary-eastus"
TARGET_TYPE = "Microsoft.App/managedEnvironments"
EXPECTED_TAGS = {
    "app": "RetailGrowthAI", "environment": "dev",
    "feature": "feature5", "purpose": "zero-compute-gpu-quota-probe",
}
EXPECTED_PROPERTIES = {
    "appLogsConfiguration": {"destination": "none"},
    "workloadProfiles": [{"name": "Consumption", "workloadProfileType": "Consumption"}],
}
EXPECTED_KEYS = {"type", "apiVersion", "name", "location", "tags", "properties"}


def validate_template(path: Path = TEMPLATE) -> dict:
    source = Path(path)
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 12_000:
        raise MotionError("Invalid feature5 isolated ARM template")
    try:
        obj = json.loads(source.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise MotionError("Unparseable ARM deployment plan") from exc
    if type(obj) is not dict or obj.get("$schema") != (
        "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#"
    ) or obj.get("parameters") or len(obj.get("resources", [])) != 1:
        raise MotionError("Only one fixed empty DEV environment may be created")
    res = obj["resources"][0]
    if (type(res) is not dict or set(res) != EXPECTED_KEYS or
        res["type"] != TARGET_TYPE or res["apiVersion"] != "2024-03-01" or
        res["name"] != TARGET_ENV or res["location"] != "eastus" or
        res["tags"] != EXPECTED_TAGS or res["properties"] != EXPECTED_PROPERTIES):
        raise MotionError("Unexpected environment, GPU, log sink, region or paid workload")
    return obj


def validate_what_if(change_set: dict, subscription: str) -> None:
    """Require exactly one ARM 'Create'; reject modify/delete/uncertain actions."""
    if not isinstance(change_set, dict) or not isinstance(subscription, str) or len(subscription) != 36:
        raise MotionError("Azure what-if or subscription is untrusted")
    rows = change_set.get("changes", (change_set.get("properties") or {}).get("changes"))
    if not isinstance(rows, list) or len(rows) != 1:
        raise MotionError("Azure what-if did not show exactly one new resource")
    target = (
        "/subscriptions/" + subscription + "/resourcegroups/" + TARGET_RG +
        "/providers/" + TARGET_TYPE + "/" + TARGET_ENV
    ).lower()
    if rows[0].get("changeType") != "Create" or str(rows[0].get("resourceId", "")).lower() != target:
        raise MotionError("Azure what-if attempted other than isolated DEV environment creation")
