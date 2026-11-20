#!/usr/bin/env python3
"""Read-only post-failure Y1 package/owner/health inventory; never print credentials."""
from __future__ import annotations

import json

import p0249_y1_canary_guard as guard
import p0249_y1_remote_build_mode as y1

FAILED_RUN_ID = "44629301025"


def classify(settings, names):
    current = settings.get("WEBSITE_RUN_FROM_PACKAGE")
    original = settings.get(y1.BACKUP)
    owner = settings.get(y1.OWNER)
    return {
        "original_flex_unchanged": True,  # only after guard.verify succeeds
        "current_external_blob_package": y1._package_url(current),
        "backup_external_blob_package": y1._package_url(original),
        "current_matches_backup": (
            isinstance(current, str) and y1._package_url(original)
            and current == original
        ),
        "backup_key_present": y1.BACKUP in settings,
        "owner_key_present": y1.OWNER in settings,
        "owner_is_failed_release": owner == FAILED_RUN_ID,
        "enable_oryx_present": "ENABLE_ORYX_BUILD" in settings,
        "scm_remote_build_true": str(settings.get("SCM_DO_BUILD_DURING_DEPLOYMENT","")).lower()=="true",
        "no_customer_or_shadow_settings": not any(k in settings for k in y1.SHADOWS),
        "two_function_index": names == y1.TWO,
        "five_function_index": names == y1.FIVE,
        "unexpected_function_index": not names.issubset(y1.ALLOWED),
    }


def main():
    guard.verify()
    settings = y1._settings()
    names = y1._index()
    facts = classify(settings, names)
    print("P0249_Y1_POST_FAILURE_STATE=" + json.dumps(facts, sort_keys=True), flush=True)
    if not facts["two_function_index"] or not facts["no_customer_or_shadow_settings"]:
        raise RuntimeError("Y1 state is not safe for assumed original-route recovery")
    guard.probe()
    print("P0249_Y1_POST_FAILURE_ORIGINAL_HEALTH_20OF20=PASS", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("P0249_Y1_POST_FAILURE_STATE=FAILED_REDACTED", flush=True)
        raise SystemExit(2)
