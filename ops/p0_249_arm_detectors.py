#!/usr/bin/env python3
"""Issue #249: read-only App Service diagnostics for the EXISTING DEV Flex app.

ARM GET only, after tagged DEV subscription/resource ID verification. Never
print dynamic detector text/tables, resource IDs, request content or secrets.
Never enable detectors, deploy, restart, query customer data, or allocate capacity.
"""
from __future__ import annotations

import json
import re
import subprocess
from urllib.parse import quote

from flex_ingress_correlation import audit_scope

API_VERSION = "2024-11-01"
START = "2026-10-28T10:25:40Z"
END = "2026-10-28T10:35:30Z"
CATEGORIES = ("availability", "performance", "configuration")
MAX_DETECTORS = 6
DRILLDOWN = (
    "ColdStartFailuresWorkflowNode",
    "functioncoldstart",
    "functionappdownanderrors",
    "ErrorsInApacheErrorLogForWorker",
    "FNAppOpenTelemetryErrors",
    "AvailabilityAndPerformanceFunctionApp",
)
NAME = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
KEYWORDS = ("worker", "startup", "cold", "runtime", "availability", "503",
            "webappdown", "appdown", "crash", "http", "errors", "restart")
LEVELS = frozenset(("Critical", "Warning", "Info", "Success", "None", "Unknown"))


def arm_get(base: str, route: str, *, historical: bool = False):
    """Only fixed-path ARM GET under the audited original Flex resource."""
    if not base.lower().endswith(
        "/resourcegroups/rg-retailgrowth-dev/providers/microsoft.web/sites/rgai-dev-functions-d4e5ddbd"
    ):
        raise ValueError("exact DEV resource mismatch")
    path = "/".join(quote(piece, safe="") for piece in route.split("/"))
    if not re.fullmatch(r"[A-Za-z0-9_/-]{1,200}", path):
        raise ValueError("unreviewed diagnostic route")
    url = "https://management.azure.com" + base + "/" + path
    url += "?api-version=" + API_VERSION
    if historical:
        url += "&startTime=" + quote(START, safe="") + "&endTime=" + quote(END, safe="")
    res = subprocess.run(["az", "rest", "--method", "get", "--url", url,
                          "--output", "json"], capture_output=True,
                         text=True, timeout=65)
    if res.returncode != 0:
        raise RuntimeError("read-only ARM detector unavailable")
    return json.loads(res.stdout)


def entries(result):
    if isinstance(result, dict) and isinstance(result.get("value"), list):
        return [x for x in result["value"] if isinstance(x, dict)][:80]
    return []


def relevant_detectors(result):
    """Strict allowlist of observed detector names; no IDs/URLs from Azure."""
    matched = []
    for item in entries(result):
        name = item.get("name", "")
        if isinstance(name, str) and NAME.fullmatch(name):
            if any(k in name.lower() for k in KEYWORDS):
                if name not in matched:
                    matched.append(name)
    return matched[:MAX_DETECTORS]


def summarize_response(result):
    """Only bounded structure and fixed status; raw detector prose is private."""
    if not isinstance(result, dict):
        return {"result": "unexpected_shape"}
    prop = result.get("properties") or {}
    if not isinstance(prop, dict):
        prop = {}
    dataset = prop.get("dataset")
    data_count = len(dataset) if isinstance(dataset, list) else None
    # Azure ARM DetectorResponse.properties.status is an OBJECT with statusId,
    # never a free-text status or a reason to expose its .message.
    status_object = prop.get("status")
    raw_level = (status_object.get("statusId") if isinstance(status_object, dict)
                 else status_object)
    status = raw_level if isinstance(raw_level, str) and raw_level in LEVELS else "Unknown"
    insights = prop.get("insights")
    insight_count = len(insights) if isinstance(insights, list) else None
    counts = []
    # Only row COUNTS, not arbitrary table schemas/values/metadata. The detector
    # may return private path/tenant information within cells; never print them.
    if isinstance(dataset, list):
        for section in dataset[:16]:
            table = section.get("table") if isinstance(section, dict) else None
            rows = table.get("rows") if isinstance(table, dict) else None
            counts.append(min(len(rows), 10000) if isinstance(rows, list) else None)
    return {"result": "received", "status": status,
            "dataset_sections": min(data_count, 100) if data_count is not None else None,
            "dataset_rows_per_section": counts,
            "insight_sections": min(insight_count, 100) if insight_count is not None else None,
            "raw_findings_redacted": True, "historical_window_verified": False}


def attempt(label, resource_id, route, *, historical=False):
    try:
        value = arm_get(resource_id, route, historical=historical)
        items = entries(value)
        print("P0249_DETECTOR_READ=" + json.dumps(
            {"operation": label, "result": "available",
             "item_count_max80": len(items), "relevant_names": relevant_detectors(value)},
            sort_keys=True), flush=True)
        return value
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired):
        print("P0249_DETECTOR_READ=" + json.dumps(
            {"operation": label, "result": "unavailable"}, sort_keys=True), flush=True)
        return None


def main():
    resource_id = audit_scope()
    print("P0249_ARM_READ_ONLY_FIXED_APP=true", flush=True)
    # "detectors" endpoint supplies detector responses. Platform may not support
    # this endpoint on Flex; then classify as unavailable instead of successful.
    root = attempt("site_detector_responses", resource_id, "detectors", historical=True)
    for category in CATEGORIES:
        result = attempt("category_" + category, resource_id,
                         "diagnostics/" + category + "/detectors")
        if not isinstance(result, dict):
            continue
        for detector in relevant_detectors(result):
            try:
                response = arm_get(resource_id,
                                   "diagnostics/" + category + "/detectors/" + detector,
                                   historical=True)
                safe = summarize_response(response)
                print("P0249_DETECTOR_DETAIL=" + json.dumps(
                    {"category": category, "detector": detector, **safe},
                    sort_keys=True), flush=True)
            except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired):
                print("P0249_DETECTOR_DETAIL=" + json.dumps(
                    {"category": category, "detector": detector, "result": "unavailable"},
                    sort_keys=True), flush=True)
    # These detector names were returned by the actual audited original app in
    # protected run #40686643501. GET the exact fixed names (not dynamic links).
    # The Azure REST API accepts a startTime/endTime request for detector response;
    # the service's effective data window cannot be attested from this metadata.
    for detector in DRILLDOWN:
        try:
            response = arm_get(resource_id, "detectors/" + detector, historical=True)
            safe = summarize_response(response)
            print("P0249_ROOT_DETECTOR_DETAIL=" + json.dumps(
                {"detector": detector, **safe, "fixed_utc_range_requested": True},
                sort_keys=True), flush=True)
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired):
            print("P0249_ROOT_DETECTOR_DETAIL=" + json.dumps(
                {"detector": detector, "result": "unavailable"}, sort_keys=True),
                flush=True)
    print("P0249_ROOT_CAUSE_NOT_CONFIRMED_BY_SUMMARIES=true", flush=True)
    print("P0249_NO_AZURE_WRITES_NO_HTTP_REQUESTS_NO_PAID_RESOURCES=true", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
