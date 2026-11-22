#!/usr/bin/env python3
"""Fail-closed #249 connection inventory: NO Azure mutations and NO stop/close.

A trusted DEV-protected workflow must collect these observations from Azure and
the actually served website plus separately verified E2E receipts. A caller-
supplied snapshot is diagnostic only, never an authorization to retire Flex.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RG = "rg-retailgrowth-dev"
Y1 = "rgai-dev-y1-p0249-d4e5ddbd"
FLEX = "rgai-dev-functions-d4e5ddbd"
FRONTEND = "https://purple-dune-06b5da200.2.azurestaticapps.net"
SUPABASE = "https://jeearzffnjbvghwjjjrf.supabase.co"
Y1_ORIGIN = "https://" + Y1 + ".azurewebsites.net"
FLEX_ORIGIN = "https://" + FLEX + ".azurewebsites.net"
# Microsoft Azure Functions legacy Consumption max functionTimeout 600s.
# Original protected RetailGrowthAI video engine allows up to 780s and its
# Flex worker host is configured for 1200s; cannot silently copy to Y1.
CLASSIC_CONSUMPTION_MAX_SECONDS = 600
ORIGINAL_RENDER_HARD_CAP_SECONDS = 780

# Host App Settings are checked by *name* only in sanitized diagnostics.
# Comparing real values must happen inside an authorized protected Azure
# runner, never in a tracked file, model context, or browser.
CONNECTIONS = frozenset({
    "RETAIL_SUPABASE_URL", "RETAIL_SUPABASE_PUBLISHABLE_KEY",
    "RETAIL_SUPABASE_SERVICE_ROLE_KEY", "RETAIL_STORAGE",
    "AzureWebJobsStorage", "FUNCTIONS_WORKER_RUNTIME",
})
QUEUE_FUNCTIONS = frozenset({
    "plan_campaign", "render_campaign_reel", "planning_poison",
    "render_poison", "render_campaign_poster",
})
TIMER_FUNCTIONS = frozenset({
    "recover_stale_jobs", "dispatch_onboarding_emails",
    "dispatch_pending_posters", "feature2_collect_india_trends",
})
# Original HTTP routes have many optional feature flags; require core v1
# creation, edit, status, downloads and poster CRUD before any retirement.
CORE_FUNCTIONS = frozenset({
    "create_campaign", "read_campaign", "save_campaign_day",
    "create_render", "get_render", "get_render_download",
    "create_poster_draft", "list_saved_posters", "get_poster_draft",
    "select_poster_banner", "request_poster_render",
    "read_poster_render", "download_poster_render", "p0249_health",
})
PROOF = frozenset({
    "signed_two_shop_current_rls",
    "campaign_post_patch_positive_and_foreign_denied",
    "private_render_and_poster_signed_download",
    "queue_outbox_claim_lease_poison_recovery",
    "quota_billing_idempotency",
    "worker_single_owner_no_drain_backlog",
    "frontend_actual_served_y1_origin",
    "y1_240s_idle_and_503_p95_p99",
    "rollback_original_tested",
})


def evaluate(observed: dict) -> tuple[str, ...]:
    """Return *missing* gates, not a permission to stop a cloud resource.

    Never allow a claimed booleans-only test receipt to authorize a stop.
    There is intentionally NO stop/delete/issue-close command in this module.
    """
    if not isinstance(observed, dict):
        return ("untrusted_snapshot",)
    missing = []
    scope = observed.get("scope")
    if not isinstance(scope, dict) or scope != {
        "resource_group": RG, "y1_app": Y1, "flex_app": FLEX,
        "supabase_origin": SUPABASE, "frontend_origin": FRONTEND,
    }:
        missing.append("exact_dev_scope")
    y1 = observed.get("y1")
    flex = observed.get("flex")
    frontend = observed.get("frontend")
    if not isinstance(y1, dict):
        y1 = {}
    if not isinstance(flex, dict):
        flex = {}
    if not isinstance(frontend, dict):
        frontend = {}
    if y1.get("host") != Y1_ORIGIN or y1.get("state") != "Running":
        missing.append("live_y1_host")
    if flex.get("host") != FLEX_ORIGIN:
        missing.append("original_flex_identity")
    settings = y1.get("app_setting_names")
    if (not isinstance(settings, list)
        or not all(isinstance(v, str) and len(v) < 100 for v in settings)
        or not CONNECTIONS.issubset(set(settings))):
        missing.append("server_side_y1_supabase_storage_connections")
    if y1.get("same_retailgrowth_dev_connections_as_flex") is not True:
        missing.append("protected_original_connection_value_comparison")
    names = y1.get("indexed_functions")
    if not isinstance(names, list) or not all(isinstance(v, str) for v in names):
        names = []
    indexed = set(names)
    for group, required in (
        ("original_core_http_routes", CORE_FUNCTIONS),
        ("planning_render_poster_poison_workers", QUEUE_FUNCTIONS),
        ("outbox_recovery_email_trend_timers", TIMER_FUNCTIONS),
    ):
        if not required.issubset(indexed):
            missing.append(group)
    if y1.get("unauthenticated_protected_endpoints_denied") is not True:
        missing.append("y1_anonymous_auth_proof")
    if y1.get("customer_traffic_origin") != Y1_ORIGIN:
        missing.append("verified_y1_http_traffic")
    if frontend.get("served_api_origin") != Y1_ORIGIN:
        missing.append("frontend_live_cutover")
    if flex.get("receiving_customer_traffic") is not False:
        missing.append("flex_customer_traffic_still_possible")
    if flex.get("background_workers_enabled") is not False:
        missing.append("flex_workers_still_active")
    if y1.get("background_workers_enabled") is not True:
        missing.append("y1_workers_not_enabled")
    if y1.get("queue_backlog_reconciled") is not True:
        missing.append("y1_queue_drain_or_unknown_work")
    render = observed.get("render_worker")
    if not isinstance(render, dict):
        render = {}
    # An unmodified classic Y1 Consumption queue worker can time out before
    # the current 780s FFmpeg hard cap. Require an independently verified
    # >=780s CPU execution backend; raw assertions do NOT authorize a stop.
    if (render.get("hosting_mode") != "isolated_on_demand_cpu_worker"
        or type(render.get("max_execution_seconds")) is not int
        or render["max_execution_seconds"] < ORIGINAL_RENDER_HARD_CAP_SECONDS
        or render.get("same_approved_shop_queue_and_lease") is not True
        or render.get("private_media_and_ffmpeg_verified") is not True):
        missing.append("long_render_worker_incompatible_with_classic_y1_600s_limit")
    receipt = observed.get("protected_evidence")
    if not isinstance(receipt, dict):
        receipt = {}
    if any(receipt.get(k) is not True for k in PROOF):
        missing.append("independent_hosted_e2e_and_rollback_receipts")
    # Deliberately keep a second independent gate: arbitrary JSON booleans
    # cannot be promoted into permission for destructive Azure stop.
    if observed.get("verified_by_protected_release_workflow") is not True:
        missing.append("protected_release_origin_unverified")
    return tuple(missing)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnostic-json", type=Path, required=True)
    args = parser.parse_args()
    # Cannot be used as a hidden Azure stop script: this only prints safe
    # missing categories. Never print snapshot or credential values.
    path = args.diagnostic_json
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 40_000:
        raise ValueError("unsafe diagnostic snapshot source")
    try:
        diagnostic = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError):
        diagnostic = None
    missing = evaluate(diagnostic)
    if missing:
        print("P0249_Y1_ALL_CONNECTIONS=INCOMPLETE")
        for name in missing:
            print("P0249_Y1_MISSING=" + name)
        print("P0249_FLEX_RETIREMENT=BLOCKED_DO_NOT_STOP")
        raise SystemExit(2)
    # Even a fully asserted snapshot is not itself proof of trusted live
    # data or approval to stop Flex; the protected workflow must independently
    # verify the evidence provenance and actual traffic/worker ownership.
    print("P0249_Y1_CONNECTION_INVENTORY=ASSERTED_PENDING_INDEPENDENT_VERIFICATION")
    print("P0249_FLEX_RETIREMENT=BLOCKED_PENDING_PROTECTED_AZURE_ACCEPTANCE")


if __name__ == "__main__":
    main()
