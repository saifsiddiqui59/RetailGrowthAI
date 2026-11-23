#!/usr/bin/env python3
"""Fail-closed read-only DEV F4 original API readiness before source flag staging.

Reads Azure CLI JSON files (never prints setting names/values or tenant data).
Does NOT activate CPU rendering, create users, change IAM or deploy ZIP files.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

DEV_RG = "rg-retailgrowth-dev"
API = "rgai-dev-functions-d4e5ddbd"
WORKER = "rgai-dev-f4cpu-d4e5ddbd"
DEV_URL = "https://jeearzffnjbvghwjjjrf.supabase.co"
WORKER_FUNCTIONS = frozenset({
    "feature4_cpu_render_message", "feature4_cpu_poison_message",
    "feature4_cpu_dispatch_timer",
})
API_FUNCTIONS = frozenset({
    "issue_feature4_creative_plan", "read_feature4_creative_plan",
    "review_feature4_creative_plan", "revoke_feature4_creative_plan",
    "create_feature4_render", "get_feature4_render",
    "download_feature4_render",
})
API_FLAGS = (
    "RETAIL_FEATURE4_PLAN_ISSUE_ENABLED", "RETAIL_FEATURE4_PLAN_REVIEW_ENABLED",
    "RETAIL_FEATURE4_CPU_WORKER_ENABLED", "RETAIL_FEATURE4_CPU_RENDER_ENABLED",
)
REQUIRED_BACKEND = (
    "RETAIL_SUPABASE_URL", "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
    "RETAIL_STORAGE",
)


class NotReady(ValueError):
    pass


def _require(condition: bool, category: str):
    if not condition:
        raise NotReady(category)


def _site(data, subscription, name):
    scope = f"/subscriptions/{subscription}/resourceGroups/{DEV_RG}/providers/Microsoft.Web/sites/{name}".lower()
    _require(isinstance(data, dict) and str(data.get("id", "")).lower() == scope,
             "site-identity")
    tags = {str(k).lower(): str(v).lower()
            for k, v in (data.get("tags") or {}).items()}
    _require(tags.get("app") == "retailgrowthai" and
             tags.get("environment") == "dev", "site-tags")
    return data


def _settings(data):
    _require(isinstance(data, list) and len(data) <= 200, "settings-shape")
    _require(all(isinstance(v, dict) and isinstance(v.get("name"), str)
                 and isinstance(v.get("value"), str) for v in data), "settings-shape")
    out = {entry["name"]: entry["value"] for entry in data}
    _require(len(out) == len(data), "duplicate-setting")
    return out


def _functions(data):
    _require(isinstance(data, list) and len(data) <= 200, "function-shape")
    names = set()
    for entry in data:
        _require(isinstance(entry, dict) and isinstance(entry.get("name"), str),
                 "function-shape")
        name = entry["name"].rsplit("/", 1)[-1]
        _require(bool(name) and name not in names, "function-duplicate")
        names.add(name)
    return names


def verify(snapshot: dict, subscription: str, protected_secret: str) -> bool:
    _require(isinstance(snapshot, dict) and isinstance(subscription, str) and
             len(subscription) == 36 and subscription.count("-") == 4,
             "subscription")
    _require(isinstance(protected_secret, str) and len(protected_secret) >= 32 and
             (protected_secret.startswith("sb_secret_") or
              (protected_secret.startswith("eyJ") and protected_secret.count(".") == 2)),
             "protected-service-identity")
    worker = _site(snapshot.get("worker_app"), subscription, WORKER)
    _site(snapshot.get("api_app"), subscription, API)
    wt = {str(k).lower(): str(v).lower()
          for k, v in (worker.get("tags") or {}).items()}
    _require(wt.get("purpose") == "feature4-cpu-private-worker",
             "private-worker-purpose")
    cfg = (worker.get("properties") or {}).get("functionAppConfig") or {}
    scale, runtime = cfg.get("scaleAndConcurrency") or {}, cfg.get("runtime") or {}
    _require(scale.get("maximumInstanceCount") == 1 and
             scale.get("instanceMemoryMB") == 2048 and
             runtime.get("name") == "python" and runtime.get("version") == "3.11",
             "worker-capacity")
    original, private = (_settings(snapshot.get("api_settings")),
                         _settings(snapshot.get("worker_settings")))
    for setting in REQUIRED_BACKEND:
        _require(bool(original.get(setting)) and bool(private.get(setting))
                 and original[setting] == private[setting],
                 "backend-connection-parity")
    _require(original["RETAIL_SUPABASE_URL"] == DEV_URL, "dev-project")
    _require(original["RETAIL_SUPABASE_SERVICE_ROLE_KEY"] == protected_secret,
             "service-role-parity")
    _require(bool(original.get("RETAIL_SUPABASE_PUBLISHABLE_KEY")),
             "api-publishable-key")
    _require(bool(original.get("AzureWebJobsStorage")) and
             bool(private.get("AzureWebJobsStorage")),
             "storage-host-config")
    _require(all(original.get(name, "false").lower() == "false"
                 for name in API_FLAGS), "customer-flags-not-off")
    _require(private.get("RETAIL_FEATURE4_CPU_WORKER_ENABLED") == "true" and
             private.get("RETAIL_FEATURE4_CPU_RENDER_ENABLED") == "false",
             "private-worker-flags")
    _require(private.get("RETAIL_SUPABASE_SERVICE_ROLE_KEY") == protected_secret,
             "worker-service-role")
    _require(_functions(snapshot.get("worker_functions")) == WORKER_FUNCTIONS,
             "private-trigger-index")
    names = _functions(snapshot.get("api_functions"))
    _require(API_FUNCTIONS <= names, "original-api-f4-index")
    _require(all(isinstance(snapshot.get(k), dict) and
                 snapshot[k].get("exists") is True
                 for k in ("queue_render", "queue_poison")),
             "private-queues")
    _require(snapshot.get("f4_jobs_empty") is True, "inflight-jobs")
    return True


def main() -> int:
    try:
        directory = Path(os.environ["F4_READINESS_DIR"])
        expected = {
            "worker_app": "worker-app.json", "api_app": "api-app.json",
            "worker_settings": "worker-settings.json",
            "api_settings": "api-settings.json",
            "worker_functions": "worker-functions.json",
            "api_functions": "api-functions.json",
            "queue_render": "queue-render.json",
            "queue_poison": "queue-poison.json",
            "f4_jobs_empty": "jobs-empty.json",
        }
        values = {name: json.loads((directory / filename).read_text())
                  for name, filename in expected.items()}
        values["f4_jobs_empty"] = values["f4_jobs_empty"].get("empty") is True
        verify(values, os.environ["AZURE_SUBSCRIPTION_ID"],
               os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"])
    except (NotReady, OSError, ValueError, KeyError, TypeError):
        print("BLOCKED: exact protected DEV F4 API readiness could not be proved")
        return 3
    print("PASS: DEV F4 original package, three private triggers, DB parity and flags verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
