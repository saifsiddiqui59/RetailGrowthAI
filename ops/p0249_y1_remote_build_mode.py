#!/usr/bin/env python3
"""Owner-approved Issue #249 isolated DEV Y1 remote-build mode transition.

Only this existing tagged Linux Consumption Y1 app may be mutated. Two
temporary app settings store the original opaque HTTPS package reference
and the exact owner GitHub run ID for idempotent same-run/independent
rollback. Never log a SAS URL, app-setting values, or raw Azure errors.
Do NOT use this script on original Flex, PROD or WineShopPOS.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from urllib.parse import urlsplit

import p0249_y1_canary_guard as guard

RG = guard.RG
SITE = guard.SITE
BACKUP = "RGAI_P0249_Y1_BASELINE_PACKAGE_REF"
OWNER = "RGAI_P0249_Y1_REMOTE_BUILD_RUN_ID"
LEGACY_FAILED_RUN = "44629301025"  # Exact prior owned protected release, never arbitrary
SHADOWS = (
    "RGAI_P0249_READONLY_SHADOW", "RGAI_P0249_EXTRA_GET_SHADOW",
    "RETAIL_SUPABASE_URL", "RETAIL_SUPABASE_PUBLISHABLE_KEY",
)
ALLOWED = frozenset(("p0249_health", "campaign_read", "render_job_read",
                     "poster_job_read", "poster_draft_read"))
TWO = frozenset(("p0249_health", "campaign_read"))
FIVE = ALLOWED


def _az(*args: str):
    """Return parsed Azure JSON while quarantining all raw output and errors."""
    command = ["az", *args, "--only-show-errors", "-o", "json"]
    try:
        p = subprocess.run(command, capture_output=True, text=True,
                           check=False, timeout=150)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Y1 Azure command unavailable") from exc
    if p.returncode:
        raise RuntimeError("Y1 Azure command failed (redacted)")
    if not p.stdout.strip():
        return None
    try:
        return json.loads(p.stdout)
    except ValueError as exc:
        raise RuntimeError("Y1 Azure returned malformed JSON") from exc


def _settings():
    rows = _az("functionapp", "config", "appsettings", "list", "-g", RG, "-n", SITE)
    if not isinstance(rows, list):
        raise RuntimeError("Y1 appsettings not a list")
    found = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise RuntimeError("Malformed Y1 appsettings")
        key = row["name"]
        upper = key.upper()
        if upper in found:
            raise RuntimeError("Duplicate Y1 setting")
        found[upper] = row.get("value")
    return found


def _package_url(value):
    """Treat old package reference as an opaque credential, never log it."""
    if not isinstance(value, str) or len(value) > 8192:
        return False
    try:
        u = urlsplit(value)
    except ValueError:
        return False
    return (u.scheme == "https" and bool(u.hostname)
            and u.hostname.endswith(".blob.core.windows.net")
            and u.username is None and u.password is None
            and bool(u.path) and "#" not in value)


def _run_id():
    value = os.environ.get("GITHUB_RUN_ID", "")
    if not value.isdecimal() or len(value) > 22:
        raise RuntimeError("Missing approved GitHub run identity")
    return value


def _index():
    rows = _az("functionapp", "function", "list", "-g", RG, "-n", SITE,
               "--query", "[].name")
    if not isinstance(rows, list):
        raise RuntimeError("Y1 function index unavailable")
    names = []
    for item in rows:
        if not isinstance(item, str):
            raise RuntimeError("Malformed Y1 function index")
        if "/" in item:
            if item.count("/") != 1 or not item.startswith(SITE + "/"):
                raise RuntimeError("Foreign Y1 function index")
            item = item.split("/", 1)[1]
        if not item or item not in ALLOWED:
            raise RuntimeError("Unknown Y1 function; deny mutation")
        names.append(item)
    if len(names) != len(set(names)) or len(names) > 5:
        raise RuntimeError("Ambiguous Y1 function index")
    return frozenset(names)


def _assert_settings(s):
    if any(k in s for k in SHADOWS):
        raise RuntimeError("Unexpected Y1 shadow or customer settings")
    if str(s.get("SCM_DO_BUILD_DURING_DEPLOYMENT", "")).lower() != "true":
        raise RuntimeError("Y1 original build setting drifted")


def _set(**pairs):
    args = tuple(key + "=" + value for key, value in pairs.items())
    _az("functionapp", "config", "appsettings", "set", "-g", RG, "-n", SITE,
        "--settings", *args)


def _delete(*names):
    if names:
        _az("functionapp", "config", "appsettings", "delete", "-g", RG,
            "-n", SITE, "--setting-names", *names)


def prepare():
    guard.verify()  # original FC1, exact isolated app, plan, tags, location
    if _index() != TWO:
        raise RuntimeError("Y1 baseline is not exactly two functions")
    before = _settings()
    _assert_settings(before)
    original = before.get("WEBSITE_RUN_FROM_PACKAGE")
    # Preserve the existing fail-closed second-run/foreign-owner rejection
    # before inspecting a package URL removed by an earlier active trial.
    if (BACKUP in before or OWNER in before) and before.get(OWNER) != LEGACY_FAILED_RUN:
        raise RuntimeError("Y1 protected backup/owner already exists")
    if not _package_url(original):
        raise RuntimeError("Y1 baseline is not an expected Azure HTTPS package URL")
    # Previous protected run #44629301025 retained an OWNED original URI
    # backup after its failed rollback. Re-adopt ONLY that exact known owner
    # with active and backup URLs byte-identical; never accept arbitrary
    # owners, partial markers, or an active package different from backup.
    if BACKUP in before or OWNER in before:
        if not (before.get(OWNER) == LEGACY_FAILED_RUN
                and before.get(BACKUP) == original
                and urlsplit(original).hostname == guard.STORAGE + ".blob.core.windows.net"):
            raise RuntimeError("Y1 existing backup/owner is not safe to adopt")
    if "ENABLE_ORYX_BUILD" in before:
        raise RuntimeError("Y1 Oryx baseline unexpected; do not overwrite")
    run_id = _run_id()
    # First persist the rollback URL and owner in the SAME protected Y1 site.
    # Azure CLI output can contain raw appsettings: always quarantine it.
    _set(**{BACKUP: original, OWNER: run_id})
    prepared = _settings()
    if prepared.get(BACKUP) != original or prepared.get(OWNER) != run_id:
        raise RuntimeError("Y1 rollback reference not persisted")
    # Azure Linux Consumption remote-build mode explicitly requires that the
    # external URL setting be ABSENT and both remote build flags be true.
    _delete("WEBSITE_RUN_FROM_PACKAGE")
    _set(ENABLE_ORYX_BUILD="true")
    selected = _settings()
    _assert_settings(selected)
    if (selected.get(BACKUP) != original or
            selected.get(OWNER) != run_id or
            "WEBSITE_RUN_FROM_PACKAGE" in selected or
            str(selected.get("ENABLE_ORYX_BUILD", "")).lower() != "true"):
        raise RuntimeError("Y1 remote-build transition incomplete")
    guard.verify()
    print("P0249_Y1_REMOTE_BUILD_MODE=READY_ORIGINAL_PACKAGE_BACKED_UP", flush=True)


def _wait_for_index(target, attempts=16, delay=12):
    for _ in range(attempts):
        try:
            if _index() == target:
                return True
        except RuntimeError:
            pass  # Functions may restart while settings are updated.
        time.sleep(delay)
    return False


def rollback():
    guard.verify()
    run_id = _run_id()
    before = _settings()
    _assert_settings(before)
    old = before.get(BACKUP)
    owner = before.get(OWNER)
    # If a new trial was denied before any setting write, a prior known
    # owner must not be mistaken for our own rollback ownership. Prove
    # unchanged original URL, no Oryx flag, exactly two handlers and live
    # 20/20 health instead; do not mutate or delete legacy recovery keys.
    if (owner == LEGACY_FAILED_RUN and _package_url(old)
            and urlsplit(old).hostname == guard.STORAGE + ".blob.core.windows.net"
            and before.get("WEBSITE_RUN_FROM_PACKAGE") == old
            and "ENABLE_ORYX_BUILD" not in before and _index() == TWO):
        guard.probe()
        print("P0249_Y1_LEGACY_ORIGINAL_PACKAGE_RETAINED=PASS_20OF20", flush=True)
        return
    if old is None and owner is None:
        if ("WEBSITE_RUN_FROM_PACKAGE" in before
                and _package_url(before.get("WEBSITE_RUN_FROM_PACKAGE"))
                and "ENABLE_ORYX_BUILD" not in before
                and _index() == TWO):
            guard.probe()
            print("P0249_Y1_ORIGINAL_EXTERNAL_PACKAGE_RETAINED=PASS", flush=True)
            return
        raise RuntimeError("No Y1 backup or safe unchanged baseline")
    if owner != run_id or not _package_url(old):
        raise RuntimeError("Unowned or malformed Y1 rollback reference")
    # No unknown function and no customer settings may have appeared.
    indexed = _index()
    if not indexed.issubset(FIVE):
        raise RuntimeError("Unexpected Y1 index; refuse rollback")
    # On Linux Consumption the original saved URI, not a config-zip push,
    # restores the exact previously mounted two-GET package.
    _set(WEBSITE_RUN_FROM_PACKAGE=old)
    if "ENABLE_ORYX_BUILD" in _settings():
        _delete("ENABLE_ORYX_BUILD")
    after = _settings()
    _assert_settings(after)
    if (after.get("WEBSITE_RUN_FROM_PACKAGE") != old or
            "ENABLE_ORYX_BUILD" in after or after.get(OWNER) != run_id):
        raise RuntimeError("Y1 original package reference not restored")
    # Re-sync the external package after its URL is restored; no raw URL/log.
    # Azure CLI sync-function-triggers is not reliable on this Linux Y1;
    # use the pinned WebSites ARM syncfunctiontriggers action.
    _az("resource", "invoke-action", "-g", RG, "-n", SITE,
        "--resource-type", "Microsoft.Web/sites",
        "--action", "syncfunctiontriggers")
    if not _wait_for_index(TWO):
        raise RuntimeError("Y1 rollback did not reindex the original two functions")
    guard.probe()
    # Remove rollback secrets ONLY after original 20/20 HTTP and exact index.
    _delete(BACKUP, OWNER)
    if BACKUP in _settings() or OWNER in _settings():
        raise RuntimeError("Y1 rollback marker cleanup incomplete")
    if not _wait_for_index(TWO):
        raise RuntimeError("Y1 index changed after backup cleanup")
    guard.probe()
    print("P0249_Y1_ORIGINAL_EXTERNAL_PACKAGE_ROLLBACK=PASS", flush=True)


def _postpublisher_oryx_allowed(s):
    """Official Functions Action Oryx input is temporary, not a persistent flag.

    Permit only true or ABSENT; the next gated index/HTTP checks must still
    prove the code actually launched. Never allow a false/unknown Oryx value.
    """
    return ("ENABLE_ORYX_BUILD" not in s or
            str(s.get("ENABLE_ORYX_BUILD", "")).lower() == "true")


def _pinned_package_on_storage(value):
    """Require a package URL hosted on exact existing RetailGrowthAI DEV storage."""
    if not _package_url(value):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return parsed.hostname == guard.STORAGE + ".blob.core.windows.net"


def _postpublisher_package_allowed(settings):
    """Linux Consumption publisher may install a NEW run-from-package Blob URL.

    Refuse the old baseline pointer, foreign domain/account, local-package
    marker or malformed URL.  Five hosted indexes and real GET/401 checks
    remain required separately.
    """
    original = settings.get(BACKUP)
    if not _pinned_package_on_storage(original):
        return False
    installed = settings.get("WEBSITE_RUN_FROM_PACKAGE")
    if installed is None:
        return True  # remote-build mode; hosted evidence still required
    return _pinned_package_on_storage(installed) and installed != original


def verify_build_mode():
    """Verify persistent ownership/package state, not ephemeral Action flags."""
    guard.verify()
    s = _settings()
    # Fixed booleans only; never print credential-bearing URL, token or keys.
    print("P0249_Y1_POSTPUBLISH_FLAGS=" + json.dumps({
        "scm_true": str(s.get("SCM_DO_BUILD_DURING_DEPLOYMENT", "")).lower() == "true",
        "oryx_absent": "ENABLE_ORYX_BUILD" not in s,
        "oryx_true": str(s.get("ENABLE_ORYX_BUILD", "")).lower() == "true",
        "runfrompackage_absent": "WEBSITE_RUN_FROM_PACKAGE" not in s,
        "new_pinned_package_url": (
            _pinned_package_on_storage(s.get("WEBSITE_RUN_FROM_PACKAGE"))
            and s.get("WEBSITE_RUN_FROM_PACKAGE") != s.get(BACKUP)),
        "old_package_still_active": (
            s.get("WEBSITE_RUN_FROM_PACKAGE") == s.get(BACKUP)),
        "backup_url_valid": _pinned_package_on_storage(s.get(BACKUP)),
        "owner_matches_current_run": s.get(OWNER) == _run_id(),
    }, sort_keys=True), flush=True)
    _assert_settings(s)
    if (s.get(OWNER) != _run_id() or
            not _postpublisher_package_allowed(s) or
            not _postpublisher_oryx_allowed(s)):
        raise RuntimeError("Y1 remote build settings or owner drifted")
    print("P0249_Y1_REMOTE_BUILD_POSTPUBLISH_SETTINGS=PASS", flush=True)


def verify_five():
    guard.verify()
    value = _settings()
    _assert_settings(value)
    if (value.get(OWNER) != _run_id() or
            not _postpublisher_package_allowed(value) or
            not _postpublisher_oryx_allowed(value)):
        raise RuntimeError("Protected Y1 remote-build owner/mode drifted")
    if _index() != FIVE:
        raise RuntimeError("Five Y1 functions not actually indexed")
    print("P0249_Y1_REMOTE_BUILD_FIVE_INDEXES=PASS_BACKUP_RETAINED", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("prepare", "rollback", "verify-five", "verify-build-mode"))
    args = p.parse_args()
    {"prepare": prepare, "rollback": rollback,
     "verify-five": verify_five,
     "verify-build-mode": verify_build_mode}[args.mode]()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never disclose SAS URLs, app settings, credential-bearing CLI stderr.
        print("P0249_Y1_REMOTE_BUILD_TRANSITION=FAILED_REDACTED", flush=True)
        raise SystemExit(2)
