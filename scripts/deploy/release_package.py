#!/usr/bin/env python3
"""Offline Azure DEV Gate 2 release manifest. Never authorizes or changes cloud."""
from __future__ import annotations
import argparse
import ast
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
QUEUES = {
    "plan_campaign": "retail-campaign-planning",
    "render_campaign_reel": "retail-reel-render",
    "planning_poison": "retail-campaign-planning-poison",
    "render_poison": "retail-reel-render-poison",
}
REQUIRED = {"environmentName", "location", "storageAccountName",
            "functionAppName", "functionPlanName", "frontendOrigin"}
OPTIONAL = {"maxInstances", "instanceMemoryMB"}
SHA40 = re.compile(r"[a-fA-F0-9]{40}\Z")


def load_module(name):
    spec = importlib.util.spec_from_file_location("retail_q_" + name, HERE / (name + ".py"))
    assert spec and spec.loader
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def parameters(path: Path) -> dict:
    source = json.loads(path.read_text(encoding="utf8"))
    data = source.get("parameters")
    if not isinstance(data, dict) or not REQUIRED <= set(data) or set(data) - REQUIRED - OPTIONAL:
        raise ValueError("Missing/unexpected DEV Bicep parameters")
    if any(not isinstance(x, dict) or set(x) != {"value"} for x in data.values()):
        raise ValueError("No reference, secret or expression parameters accepted")
    values = {k: v["value"] for k, v in data.items()}
    if any(not isinstance(values[k], str) or not values[k] for k in REQUIRED):
        raise ValueError("Incomplete DEV parameters")
    if values["environmentName"] != "dev" or values["location"] != "centralindia":
        raise ValueError("Only RetailGrowthAI Central India DEV")
    for key in REQUIRED:
        if any(x in values[key].lower() for x in ("replace", "example", "localhost", "wineshop")):
            raise ValueError("Placeholder/foreign environment not allowed: " + key)
    if not re.fullmatch("[a-z0-9]{3,24}", values["storageAccountName"]):
        raise ValueError("Storage account name must be globally unique lowercase alphanumeric")
    for key in ("functionAppName", "functionPlanName"):
        name = values[key]
        if not re.fullmatch("[a-z][a-z0-9-]{2,59}", name) or "dev" not in name:
            raise ValueError("Function App/plan must use valid DEV-only name")
    origin = urlsplit(values["frontendOrigin"])
    if (origin.scheme != "https" or not origin.hostname or origin.username or origin.password
        or origin.path not in ("", "/") or origin.query or origin.fragment
        or "*" in values["frontendOrigin"] or "@" in values["frontendOrigin"]):
        raise ValueError("Frontend requires exact HTTPS origin without wildcard or path")
    if type(values.get("maxInstances", 1)) is not int or values.get("maxInstances", 1) not in (1, 2):
        raise ValueError("Flex instances must be 1–2 per independently scaling group")
    if type(values.get("instanceMemoryMB", 2048)) is not int or values.get("instanceMemoryMB", 2048) != 2048:
        raise ValueError("DEV worker memory is fixed at 2048 MiB")
    return values


def packaged_triggers(source: bytes) -> None:
    declarations = {}
    timer = False
    for node in ast.parse(source).body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            kw = {x.arg: x.value.value for x in decorator.keywords
                  if x.arg and isinstance(x.value, ast.Constant)}
            if decorator.func.attr == "queue_trigger":
                declarations[node.name] = (kw.get("queue_name"), kw.get("connection"))
            if decorator.func.attr == "timer_trigger" and node.name == "recover_stale_jobs":
                timer = (kw.get("schedule") == "0 */2 * * * *"
                         and kw.get("run_on_startup") is False
                         and kw.get("use_monitor") is True)
    for name, queue in QUEUES.items():
        if declarations.get(name) != (queue, "RETAIL_STORAGE"):
            raise ValueError("Package lacks queue/poison trigger: " + name)
    if not timer:
        raise ValueError("Package lacks safe 2-minute reconciliation timer")


def prepare(param_file: Path, zip_file: Path, commit: str, cap: float,
            first: bool, previous: Path | None = None) -> dict:
    if not SHA40.fullmatch(commit):
        raise ValueError("Reviewed exact 40-hex Git commit required")
    if cap is None or not 0 < cap <= 1_000_000:
        raise ValueError("Positive, approved billing-currency monthly cap required")
    values = parameters(param_file)
    digest, prior = load_module("rollback_guard").verify_pair(zip_file, previous, first)
    with ZipFile(zip_file) as z:
        packaged_triggers(z.read("azure-functions/campaign-api/function_app.py"))
    bicep = (ROOT / "infra/azure/main.bicep").read_text(encoding="utf8")
    for queue in QUEUES.values():
        if queue not in bicep:
            raise ValueError("Bicep lacks a required Azure queue: " + queue)
    return {
        "schema": "retailgrowthai.azure.dev.gate2.v1",
        "approval_status": "NOT_APPROVED",
        "mode": "first-release" if first else "upgrade",
        "commit_sha_supplied_not_authenticated": commit.lower(),
        "candidate_sha256": digest,
        "last_good_sha256": prior,
        "bicep_sha256": hashlib.sha256(bicep.encode()).hexdigest(),
        "environment": "dev", "location": "centralindia",
        "resources": {
            "storage_account": values["storageAccountName"],
            "function_app": values["functionAppName"],
            "function_plan": values["functionPlanName"],
            "frontend_origin": values["frontendOrigin"],
            "max_instances_per_function_group": values.get("maxInstances", 1),
            "instance_memory_mib": 2048,
        },
        "queue_triggers": QUEUES,
        "recovery_timer": "0 */2 * * * *",
        "host_timeout_seconds": 1200,
        "claim_lease_seconds": 1500,
        "ffmpeg_cap_seconds": 780,
        "monthly_budget_ceiling_in_azure_billing_currency": cap,
        "required_external_evidence": [
            "separate_owner_gate2_written_approval",
            "gate1_seven_hosted_sql_migrations_verified",
            "live_exact_resource_group_contributor_iam",
            "centralindia_flex_quota_and_approved_what_if",
            "resource_group_monthly_cost_budget_80_100_email_alerts",
            "protected_supabase_backend_config_and_exact_cors",
            "approved_static_ffmpeg_ffprobe_provenance_codecs_fonts_licenses",
            "representative_flex_1080x1920_video_and_cost_test",
            "live_host_four_queue_and_timer_function_indexing",
            "rollback_app_zip_db_storage_and_queue_consistency",
            "separate_gate3_hosted_e2e_permission",
        ],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--parameters", required=True, type=Path)
    p.add_argument("--check-parameters", action="store_true")
    p.add_argument("--get-function-name", action="store_true")
    p.add_argument("--candidate", type=Path)
    p.add_argument("--previous", type=Path)
    p.add_argument("--first-release", action="store_true")
    p.add_argument("--commit-sha")
    p.add_argument("--monthly-budget-limit", type=float)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    try:
        if a.check_parameters or a.get_function_name:
            if a.candidate or a.previous or a.first_release or a.output:
                raise ValueError("Parameter-only mode cannot deploy or package")
            data = parameters(a.parameters)
            print(data["functionAppName"] if a.get_function_name else
                  "PASS: DEV parameters validated offline; NO cloud operations")
            return 0
        if not a.candidate or not a.output or not a.commit_sha:
            raise ValueError("Candidate ZIP, output path and exact commit are required")
        if a.first_release == bool(a.previous):
            raise ValueError("Choose exactly one: first release OR last-good ZIP")
        manifest = prepare(a.parameters, a.candidate, a.commit_sha,
                           a.monthly_budget_limit, a.first_release, a.previous)
        if a.output.exists():
            raise ValueError("Will not overwrite private release evidence")
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        a.output.chmod(0o600)
    except (OSError, ValueError, TypeError, KeyError, AssertionError, json.JSONDecodeError) as err:
        print("BLOCKED: offline release manifest:", err)
        return 3
    print("PASS: hashed Gate 2 release manifest saved offline (NOT APPROVED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
