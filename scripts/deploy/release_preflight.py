#!/usr/bin/env python3
"""Validate *read-only* Azure DEV inventory. Never calls Azure or modifies resources.

Input is a short-lived sanitized snapshot from azure-readonly-preflight.sh.
Do not publish IAM, function settings, recipient emails, or full snapshots in CI.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

QUEUES = {
    "plan_campaign": "retail-campaign-planning",
    "render_campaign_reel": "retail-reel-render",
    "planning_poison": "retail-campaign-planning-poison",
    "render_poison": "retail-reel-render-poison",
}
SETTINGS = {
    "AzureWebJobsStorage", "RETAIL_STORAGE", "RETAIL_SUPABASE_URL",
    "RETAIL_SUPABASE_PUBLISHABLE_KEY", "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
}
UUID = re.compile(r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
DEV_RG = re.compile(r"^(?:rg-[a-z0-9-]*retailgrowth[a-z0-9-]*dev[a-z0-9-]*|rgai[a-z0-9-]*dev[a-z0-9-]*)$")
HIGH_PRIVILEGE = {
    "owner", "contributor", "user access administrator",
    "role based access control administrator",
}


def check(snapshot: dict, *, phase: str, subscription_id: str, resource_group: str,
          principal_id: str, frontend_origin: str | None = None,
          monthly_budget_limit: float | None = None) -> list[str]:
    """Return *only* actionable failure reasons, never secrets or role assignment dumps."""
    issues = []

    def require(ok: bool, message: str):
        if not ok:
            issues.append(message)

    require(bool(UUID.fullmatch(subscription_id)), "Invalid expected subscription ID")
    require(bool(UUID.fullmatch(principal_id)), "Invalid service principal object ID")
    require(bool(DEV_RG.fullmatch(resource_group)) and "wineshop" not in resource_group.lower(),
            "Resource group must be dedicated RetailGrowthAI DEV")
    require(snapshot.get("subscription_id", "").lower() == subscription_id.lower(),
            "Authenticated subscription mismatch")
    account = snapshot.get("account") or {}
    require(account.get("userType", "").lower() == "serviceprincipal",
            "Azure identity is not the intended OIDC service principal")
    require(bool(account.get("userName")), "Azure identity client ID not available")

    rg = snapshot.get("resource_group") or {}
    expected_scope = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
    require(rg.get("id", "").lower() == expected_scope.lower(), "Missing/mismatched DEV group")
    require(rg.get("name", "").lower() == resource_group.lower(), "DEV group name mismatch")
    require(rg.get("location", "").replace(" ", "").lower() == "centralindia",
            "DEV group must reside in centralindia")
    tags = {str(k).lower(): str(v).lower() for k, v in (rg.get("tags") or {}).items()}
    require(tags.get("app") == "retailgrowthai" and tags.get("environment") == "dev",
            "DEV group needs app=RetailGrowthAI and environment=dev tags")

    roles = [a for a in snapshot.get("role_assignments", [])
             if str(a.get("principalId", "")).lower() == principal_id.lower()]
    require(bool(roles), "No direct principal role assignments visible")
    require(any(str(a.get("scope", "")).lower() == expected_scope.lower()
                and str(a.get("roleDefinitionName", "")).lower() == "contributor"
                for a in roles), "Scoped Contributor on the exact DEV group not verified")
    for assignment in roles:
        scope = str(assignment.get("scope", "")).lower()
        role = str(assignment.get("roleDefinitionName", "")).lower()
        # Reader can be inherited. Unrecognized custom/privileged roles require human review.
        if scope != expected_scope.lower() and role not in ("reader",):
            require(False, "Unexpected inherited or out-of-group permission for deployment identity")
        if scope == expected_scope.lower() and role not in ("reader", "contributor"):
            require(False, "Unexpected DEV group role; review least privilege")
    if phase == "iam":
        return sorted(set(issues))

    if phase != "runtime":
        return ["Unknown preflight phase"]
    origin = urlparse(frontend_origin or "")
    require(origin.scheme == "https" and bool(origin.netloc)
            and not origin.username and not origin.password
            and not origin.path.strip("/") and not origin.query and not origin.fragment
            and "*" not in (frontend_origin or ""),
            "Provide an exact HTTPS frontend origin (no wildcard, path or credentials)")
    require(monthly_budget_limit is not None and 0 < monthly_budget_limit <= 1_000_000,
            "Provide positive DEV monthly budget limit in subscription billing currency")

    storage = snapshot.get("storage") or {}
    require(storage.get("kind") == "StorageV2"
            and (storage.get("sku") or {}).get("name") == "Standard_LRS",
            "DEV storage must be StorageV2 Standard_LRS")
    require(storage.get("location", "").replace(" ", "").lower() == "centralindia",
            "Storage region mismatch")
    storage_props = storage.get("properties") or {}
    require(storage_props.get("allowBlobPublicAccess") is False
            and storage_props.get("supportsHttpsTrafficOnly") is True
            and storage_props.get("minimumTlsVersion") == "TLS1_2",
            "Storage public access/TLS baseline not verified")
    stags = {str(k).lower(): str(v).lower() for k, v in (storage.get("tags") or {}).items()}
    require(stags.get("app") == "retailgrowthai" and stags.get("environment") == "dev",
            "Storage does not have dedicated DEV tags")

    app = snapshot.get("function_app") or {}
    properties = app.get("properties") or {}
    config = properties.get("functionAppConfig") or {}
    runtime = config.get("runtime") or {}
    scaling = config.get("scaleAndConcurrency") or {}
    site = properties.get("siteConfig") or {}
    cors = site.get("cors") or {}
    app_tags = {str(k).lower(): str(v).lower() for k, v in (app.get("tags") or {}).items()}
    require(app_tags.get("app") == "retailgrowthai" and app_tags.get("environment") == "dev",
            "Function app is not tagged as dedicated DEV")
    require(app.get("location", "").replace(" ", "").lower() == "centralindia",
            "Function app region mismatch")
    require(properties.get("httpsOnly") is True and site.get("ftpsState") == "Disabled"
            and site.get("minTlsVersion") == "1.2",
            "Function HTTPS, FTP or TLS policy mismatch")
    require(runtime.get("name") == "python" and runtime.get("version") == "3.12",
            "Flex Python 3.12 runtime not confirmed")
    require(scaling.get("instanceMemoryMB") == 2048
            and isinstance(scaling.get("maximumInstanceCount"), int)
            and 1 <= scaling["maximumInstanceCount"] <= 2
            and not scaling.get("alwaysReady"),
            "Flex memory/independent-function scale bounds or always-ready mismatch")
    require(cors.get("allowedOrigins") == [frontend_origin]
            and cors.get("supportCredentials") is False,
            "CORS must use only exact DEV HTTPS origin without credentials")
    settings = set(snapshot.get("app_setting_names") or [])
    require(SETTINGS <= settings, "Required backend-only app settings missing")
    require(not any(k.startswith("VITE_") for k in settings),
            "Browser VITE_ setting names are forbidden in backend")

    functions = {str(f.get("name", "")).split("/")[-1]: f for f in snapshot.get("functions", [])}
    for fn, queue in QUEUES.items():
        bindings = (functions.get(fn, {}).get("config") or {}).get("bindings") or []
        require(any(b.get("type", "").lower() == "queuetrigger"
                    and b.get("queueName") == queue and b.get("connection") == "RETAIL_STORAGE"
                    for b in bindings), f"Missing/misconfigured queue/poison trigger: {fn}")
    timer_bindings = (functions.get("recover_stale_jobs", {}).get("config") or {}).get("bindings") or []
    require(any(b.get("type", "").lower() == "timertrigger"
                and b.get("schedule") == "0 */2 * * * *"
                and b.get("runOnStartup") is False and b.get("useMonitor") is True
                for b in timer_bindings), "Durable reconciliation timer binding not verified")
    available_queues = {str(q.get("name", "")).split("/")[-1].lower()
                        for q in snapshot.get("queues", [])}
    require(set(QUEUES.values()) <= available_queues,
            "Planning/render/poison ARM queue resources are not all present")

    budgets = (snapshot.get("budgets") or {}).get("value") or []
    protected = False
    for budget in budgets:
        bp = budget.get("properties") or {}
        notifications = bp.get("notifications") or {}
        thresholds = {
            int(n.get("threshold"))
            for n in notifications.values()
            if isinstance(n, dict) and n.get("enabled") is True
            and isinstance(n.get("threshold"), (int, float))
            and n.get("contactEmails")
        }
        budget_id = str(budget.get("id") or "").lower()
        exact_rg_prefix = expected_scope.lower() + "/providers/microsoft.consumption/budgets/"
        if (budget_id.startswith(exact_rg_prefix)
                and bp.get("category") == "Cost" and bp.get("timeGrain") == "Monthly"
                and isinstance(bp.get("amount"), (int, float))
                and monthly_budget_limit is not None
                and 0 < bp["amount"] <= monthly_budget_limit
                and 80 in thresholds and 100 in thresholds):
            protected = True
    require(protected, "No RG-scoped monthly cost budget with <= limit and 80/100% email alerts")
    return sorted(set(issues))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--phase", choices=("iam", "runtime"), required=True)
    parser.add_argument("--subscription-id", required=True)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--principal-id", required=True)
    parser.add_argument("--frontend-origin")
    parser.add_argument("--monthly-budget-limit", type=float)
    args = parser.parse_args()
    try:
        inventory = json.loads(args.snapshot.read_text(encoding="utf-8"))
        if not isinstance(inventory, dict):
            raise ValueError("Expected an object")
        issues = check(inventory, phase=args.phase, subscription_id=args.subscription_id,
                       resource_group=args.resource_group, principal_id=args.principal_id,
                       frontend_origin=args.frontend_origin,
                       monthly_budget_limit=args.monthly_budget_limit)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        print("BLOCKED: unreadable or malformed DEV inventory")
        return 2
    if issues:
        for issue in issues:
            print("BLOCKED:", issue)
        return 3
    print("PASS: " + args.phase + " read-only DEV release preflight (not deployment approval)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
