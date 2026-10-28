#!/usr/bin/env python3
"""Azure Issue #249: built-in Microsoft.Web app diagnostic detector (GET only).

Exact previously verified tagged RetailGrowthAI Central India DEV app.
The only URLs are Microsoft-documented ARM GET detector endpoints. All Azure
responses remain in memory; only bounded response/dataset COUNTS are printed.
Historical window is the original confirmed HTTP 503 canary, no fresh probes.
"""
from __future__ import annotations
import json
import subprocess
from urllib.parse import urlencode
from flex_ingress_correlation import audit_scope

START = "2026-10-28T19:35:00Z"
END = "2026-10-28T19:51:00Z"
API = "2024-11-01"
EXPECTED_END = ("/resourcegroups/rg-retailgrowth-dev/providers/"
                "microsoft.web/sites/rgai-dev-functions-d4e5ddbd")
ALLOWED_NAMES = frozenset((
    "runtimeavailability", "sitecrashes", "functionappdown",
    "functionappstartupissue", "functionappdownorreportingerrors",
))
MODES = ("list_detectors", "runtimeavailability")


def make_url(resource_id: str, mode: str) -> str:
    if not isinstance(resource_id, str) or not resource_id.lower().endswith(EXPECTED_END):
        raise ValueError("Only exact tagged RetailGrowthAI DEV ARM function app allowed")
    if mode not in MODES:
        raise ValueError("Disallowed detector request")
    if mode == "list_detectors":
        suffix = "/detectors"
    else:
        suffix = "/detectors/runtimeavailability"
    args = {"api-version": API, "startTime": START, "endTime": END, "timeGrain": "PT1M"}
    return "https://management.azure.com" + resource_id + suffix + "?" + urlencode(args)


def safe_payload(data: object, mode: str) -> dict:
    if not isinstance(data, dict):
        return {"result": "UNEXPECTED_RESPONSE"}
    records = data.get("value") if mode == "list_detectors" else [data]
    if not isinstance(records, list):
        return {"result": "UNEXPECTED_RESPONSE"}
    summary = {"result": "RESPONDED", "detector_count_capped": min(len(records), 100),
               "known_detector_names": [], "dataset_blocks": 0,
               "abnormal_periods": 0}
    for record in records[:100]:
        if not isinstance(record, dict):
            continue
        raw_name = record.get("name")
        if isinstance(raw_name, str) and raw_name.lower() in ALLOWED_NAMES:
            summary["known_detector_names"].append(raw_name.lower())
        props = record.get("properties")
        if isinstance(props, dict):
            for field, dest in (("dataset", "dataset_blocks"),
                                ("abnormalTimePeriods", "abnormal_periods")):
                v = props.get(field)
                if isinstance(v, list):
                    summary[dest] += min(len(v), 100)
    summary["known_detector_names"] = sorted(set(summary["known_detector_names"]))
    return summary


def read_detector(resource_id: str, mode: str) -> dict:
    url = make_url(resource_id, mode)
    # Capture stdout/stderr; never emit raw diagnostic text, HTTP URLs, token,
    # app metrics/requests, resource names or platform messages.
    try:
        run = subprocess.run(["az", "rest", "--method", "get", "--url", url,
                              "--output", "json"], capture_output=True, text=True, timeout=65)
        if run.returncode:
            return {"result": "UNAVAILABLE_OR_UNSUPPORTED"}
        return safe_payload(json.loads(run.stdout), mode)
    except (OSError, subprocess.TimeoutExpired, TypeError, ValueError):
        return {"result": "UNAVAILABLE_OR_UNSUPPORTED"}


def main() -> int:
    resource_id = audit_scope()  # prior protected DEV OIDC + RG tags/location
    for mode in MODES:
        summary = read_detector(resource_id, mode)
        print("P0249_OFFICIAL_ARM_DETECTOR=" + json.dumps(
            {"mode": mode, **summary}, sort_keys=True, separators=(",", ":")), flush=True)
    print("P0249_DETECTOR_NO_REQUEST_TO_WORKER_CAUSAL_CLAIM=true", flush=True)
    print("P0249_NO_CLOUD_WRITES_NO_HTTP_PROBES_NO_PROD_NO_WINESHOPPOS=true", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
