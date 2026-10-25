"""Read-only scoped Azure Resource/Service Health observation for RetailGrowthAI DEV.

Only Microsoft.ResourceHealth GET calls, following exact OIDC + tagged DEV scope
verification from the existing probe. No customer or subscription IDs, ticket
details, event text, JWTs, app settings, or raw API responses are printed.
"""
from __future__ import annotations

import json
import subprocess
from flex_ingress_correlation import audit_scope, azure

ARM = "https://management.azure.com"
VERSION = "2025-05-01"
RESOURCE_SUFFIX = (
    "/resourcegroups/rg-retailgrowth-dev/providers/"
    "microsoft.web/sites/rgai-dev-functions-d4e5ddbd"
)
_ALLOWED_AVAILABILITY = frozenset(("Available", "Degraded", "Unavailable", "Unknown"))
_ALLOWED_EVENT_STATE = frozenset(("Active", "Resolved", "Closed", "Investigating",
                                  "Mitigating", "Mitigated", "Unknown"))

def _fixed_resource_id(app_id: str, subscription: str) -> None:
    """Fail closed if Azure returns another subscription, app, or resource."""
    if not isinstance(app_id, str) or not app_id.lower().endswith(RESOURCE_SUFFIX):
        raise RuntimeError("Unexpected DEV resource identity")
    prefix = "/subscriptions/" + subscription + "/"
    if not app_id.lower().startswith(prefix.lower()):
        raise RuntimeError("DEV subscription/resource mismatch")
    if any(s in app_id for s in ("?", "#", "\\", "\n")):
        raise RuntimeError("Unexpected resource identifier syntax")

def _get(url: str):
    """Only approved GET endpoints. No raw provider error ever appears in logs."""
    if not url.startswith(ARM + "/subscriptions/") or "api-version=" + VERSION not in url:
        raise RuntimeError("Blocked unapproved Azure endpoint")
    if "/providers/Microsoft.ResourceHealth/" not in url:
        raise RuntimeError("Blocked non-health endpoint")
    return azure("rest", "--method", "get", "--url", url)

def _safe_state(value, allowed):
    return value if type(value) is str and value in allowed else "unavailable_or_other"

def _health(app_id: str):
    url = (ARM + app_id +
           "/providers/Microsoft.ResourceHealth/availabilityStatuses/current?api-version=" + VERSION)
    try:
        result = _get(url)
        properties = result.get("properties", {}) if isinstance(result, dict) else {}
        status = _safe_state(properties.get("availabilityState"), _ALLOWED_AVAILABILITY)
    except (RuntimeError, ValueError, subprocess.TimeoutExpired):
        status = "unavailable"
    print("P0_RESOURCE_HEALTH_STATUS=" + status, flush=True)
    print("P0_RESOURCE_HEALTH_AVAILABLE_DOES_NOT_PROVE_HTTP_RELIABILITY=true", flush=True)

def _normalized(value):
    return "".join(c for c in str(value).lower() if c.isalnum())

def _impact_regions(props):
    impact = props.get("impact", [])
    if isinstance(impact, dict):
        impact = [impact]
    if not isinstance(impact, list):
        return set()
    regions = set()
    for item in impact[:20]:
        if not isinstance(item, dict):
            continue
        for place in item.get("impactedRegions", [])[:40] if isinstance(item.get("impactedRegions"), list) else []:
            if isinstance(place, dict):
                regions.add(_normalized(place.get("impactedRegion", "")))
    return regions

def _events(label: str, url: str):
    try:
        result = _get(url)
        if not isinstance(result, dict) or not isinstance(result.get("value"), list):
            raise ValueError("Missing Azure event list")
        events = result["value"][:200]
        active = 0
        active_central = 0
        ambiguous_regions = 0
        for item in events:
            if not isinstance(item, dict):
                continue
            props = item.get("properties") or {}
            if not isinstance(props, dict):
                continue
            if props.get("status") != "Active":
                continue
            active += 1
            regions = _impact_regions(props)
            if "centralindia" in regions or "indiacentral" in regions:
                active_central += 1
            elif not regions:
                ambiguous_regions += 1
        safe = {
            "active_first_page": active,
            "active_central_india_impact_first_page": active_central,
            "active_without_region_first_page": ambiguous_regions,
            "first_page_count": len(events),
            "next_page_exists": bool(result.get("nextLink")),
        }
        print("P0_" + label + "=" + json.dumps(safe, sort_keys=True, separators=(",", ":")), flush=True)
        print("P0_" + label + "_STATUS=available_subset_not_outage_clearance", flush=True)
    except (RuntimeError, ValueError, subprocess.TimeoutExpired):
        print("P0_" + label + "_STATUS=unavailable_or_permission_denied", flush=True)

def main():
    app_id = audit_scope()
    account = azure("account", "show")
    subscription = account.get("id", "")
    if not isinstance(subscription, str) or not subscription:
        raise RuntimeError("Missing verified Azure subscription")
    _fixed_resource_id(app_id, subscription)
    _health(app_id)
    _events("RESOURCE_EVENTS", ARM + app_id +
            "/providers/Microsoft.ResourceHealth/events?api-version=" + VERSION)
    _events("SUBSCRIPTION_EVENTS", ARM + "/subscriptions/" + subscription +
            "/providers/Microsoft.ResourceHealth/events?api-version=" + VERSION)
    print("P0_READ_ONLY_NO_PROVISION_OR_COST_CHANGE=true", flush=True)
    print("P0_HEALTH_APIS_ARE_NOT_REQUEST_TO_INSTANCE_CORRELATION=true", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
