#!/usr/bin/env python3
"""Protected DEV Y1 *five-hosted-GET -> 38-HTTP* package handoff (#249).

This is not a deployment launcher. Only an independently gated dev workflow
may call prepare/verify/rollback, and only after building the immutable
HTTP-only package. Never log package URLs, settings, secrets or CLI errors.

The historic two-GET release helper MUST NOT be reused: the actual live
baseline now contains FIVE handlers. No original Flex, queues, customer SPA,
billing, or worker registrations are changed by this file.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p0249_y1_canary_guard as guard
import p0249_y1_remote_build_mode as legacy

from prepare_http_only import HTTP, WORKERS

FIVE = legacy.FIVE
THIRTY_EIGHT = HTTP | {"p0249_health"}
INDEX_ALLOWLIST = FIVE | THIRTY_EIGHT
BACKUP = "RGAI_P0249_Y1_38_FIVE_BASELINE_PACKAGE_REF"
OWNER = "RGAI_P0249_Y1_38_RELEASE_RUN_ID"
MAX_INDEX = 48


def _pinned_package(value):
    """Never accept foreign/local/blob-http package or external redirect."""
    if not isinstance(value, str) or not (48 <= len(value) <= 8192):
        return False
    try:
        u = urlsplit(value)
    except ValueError:
        return False
    try:
        port = u.port
    except ValueError:
        return False
    return (
        u.scheme == "https" and
        u.hostname == guard.STORAGE + ".blob.core.windows.net" and
        u.username is None and u.password is None and
        port in (None, 443) and
        bool(u.path) and u.path.startswith("/") and
        not u.path.startswith("//") and
        not u.fragment and not u.query.startswith("#")
    )


def _index():
    rows = legacy._az("functionapp", "function", "list", "-g", guard.RG,
                      "-n", guard.SITE, "--query", "[].name")
    if not isinstance(rows, list) or len(rows) > MAX_INDEX:
        raise RuntimeError("Untrusted Y1 function inventory")
    names = []
    for item in rows:
        if not isinstance(item, str):
            raise RuntimeError("Malformed Y1 index")
        if "/" in item:
            if item.count("/") != 1 or not item.startswith(guard.SITE + "/"):
                raise RuntimeError("Foreign Y1 index")
            item = item.split("/", 1)[1]
        if item not in INDEX_ALLOWLIST or item in names:
            raise RuntimeError("Unknown or duplicate Y1 route")
        names.append(item)
    return frozenset(names)


def _assert_original_five(settings):
    if _index() != FIVE:
        raise RuntimeError("Y1 is no longer the five-route protected baseline")
    if not _pinned_package(settings.get("WEBSITE_RUN_FROM_PACKAGE")):
        raise RuntimeError("Y1 current five-route ZIP pointer not pinned to DEV")
    if "ENABLE_ORYX_BUILD" in settings and (
        str(settings["ENABLE_ORYX_BUILD"]).lower() not in ("true", "false")
    ):
        raise RuntimeError("Y1 baseline build setting malformed")


def preflight():
    guard.verify()
    settings = legacy._settings()
    if BACKUP in settings or OWNER in settings:
        raise RuntimeError("Prior five-to-38 release ownership exists")
    _assert_original_five(settings)
    print("P0249_Y1_FIVE_TO_38_PREFLIGHT=FIVE_PINNED_NO_WRITE", flush=True)


def prepare():
    """Backup this exact live FIVE package without changing its active URI."""
    guard.verify()
    settings = legacy._settings()
    if BACKUP in settings or OWNER in settings:
        raise RuntimeError("Refuse to overwrite an existing release owner/backup")
    _assert_original_five(settings)
    owner = legacy._run_id()
    baseline = settings["WEBSITE_RUN_FROM_PACKAGE"]
    # Quarantined Azure CLI output. These markers are unique to the NEW 38
    # release; never overwrite retained previous two-route recovery markers.
    legacy._set(**{BACKUP: baseline, OWNER: owner})
    after = legacy._settings()
    if (after.get(BACKUP) != baseline or after.get(OWNER) != owner
        or after.get("WEBSITE_RUN_FROM_PACKAGE") != baseline):
        raise RuntimeError("Five-route baseline backup was not atomically retained")
    guard.verify()
    if _index() != FIVE:
        raise RuntimeError("Y1 indexes changed during backup")
    print("P0249_Y1_FIVE_TO_38_BACKUP=PINNED_OWNER_CONFIRMED", flush=True)


def verify():
    """Requires actual 38 Azure indexes, never source ZIP claims."""
    guard.verify()
    settings = legacy._settings()
    if (settings.get(OWNER) != legacy._run_id()
        or not _pinned_package(settings.get(BACKUP))
        or not _pinned_package(settings.get("WEBSITE_RUN_FROM_PACKAGE"))
        or settings["WEBSITE_RUN_FROM_PACKAGE"] == settings[BACKUP]):
        raise RuntimeError("Five-route rollback or new active ZIP not independently pinned")
    if _index() != THIRTY_EIGHT:
        raise RuntimeError("Y1 has not indexed exactly 38 HTTP-only handlers")
    if THIRTY_EIGHT & WORKERS:
        raise RuntimeError("Y1 38 HTTP source accidentally contains workers")
    print("P0249_Y1_38_INDEXED=EXACT_NO_WORKER_BASELINE_RETAINED", flush=True)


def _wait_for_five(attempts=12, delay=10):
    for _ in range(attempts):
        try:
            if _index() == FIVE:
                return True
        except RuntimeError:
            pass
        time.sleep(delay)
    return False


def rollback():
    """Restore the actual FIVE URI and ARM re-sync, not historic TWO functions.

    A failed/denied preflight never changes settings. No owner/backup means
    inspect the unchanged FIVE baseline and return without any Azure write.
    All real writes require the matching exact GitHub protected run owner.
    """
    guard.verify()
    settings = legacy._settings()
    backup = settings.get(BACKUP)
    owner = settings.get(OWNER)
    if backup is None and owner is None:
        _assert_original_five(settings)
        guard.probe()
        print("P0249_Y1_FIVE_BASELINE=UNCHANGED_NO_ROLLBACK_WRITE", flush=True)
        return
    if owner != legacy._run_id() or not _pinned_package(backup):
        raise RuntimeError("Unowned or unsafe five-route backup; stop")
    # No arbitrary unknown functions, queues or timers may be overwritten.
    _index()
    legacy._set(WEBSITE_RUN_FROM_PACKAGE=backup)
    after = legacy._settings()
    if (after.get("WEBSITE_RUN_FROM_PACKAGE") != backup
        or after.get(BACKUP) != backup or after.get(OWNER) != owner):
        raise RuntimeError("Y1 original five-route package restore failed")
    # Linux Consumption needs explicit ARM sync after externally hosted URI
    # restore; the old CLI function-trigger sync is not reliable for Y1.
    legacy._az("resource", "invoke-action", "-g", guard.RG, "-n",
               guard.SITE, "--resource-type", "Microsoft.Web/sites",
               "--action", "syncfunctiontriggers")
    if not _wait_for_five():
        raise RuntimeError("Original five routes not reindexed")
    guard.probe()
    legacy._delete(BACKUP, OWNER)
    if BACKUP in legacy._settings() or OWNER in legacy._settings():
        raise RuntimeError("Y1 new release backup-marker cleanup failed")
    if not _wait_for_five():
        raise RuntimeError("Five indexes lost after rollback cleanup")
    guard.probe()
    print("P0249_Y1_FIVE_ROUTE_INDEPENDENT_ROLLBACK=PASS_20OF20", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation",
                        choices=("preflight", "prepare", "verify", "rollback"))
    args = parser.parse_args()
    {"preflight": preflight, "prepare": prepare,
     "verify": verify, "rollback": rollback}[args.operation]()


if __name__ == "__main__":
    main()
