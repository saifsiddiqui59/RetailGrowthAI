#!/usr/bin/env python3
"""Scoped DEV Y1 external private package rollout with exact baseline URI recovery.

Only Azure's previously tagged isolated issue249 Y1 in Central India can be
modified; the original Flex is verified and never targeted. No raw Azure
output, app secrets, SAS token or storage account keys are logged.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlsplit

import p0249_y1_canary_guard as guard
import p0249_y1_remote_build_mode as mode

ACCOUNT = guard.STORAGE
RG = guard.RG
SITE = guard.SITE
EXPECTED_FAILED_OWNER = "44629301025"
NEW_OWNER = "RGAI_P0249_Y1_EXTERNAL_PACKAGE_TRIAL_RUN"
EXPECTED_URI_HOST = ACCOUNT + ".blob.core.windows.net"
PACKAGE_KEY = "WEBSITE_RUN_FROM_PACKAGE"
BACKUP = mode.BACKUP
OLD_OWNER = mode.OWNER

# Diagnostic labels are an immutable allowlist, never Azure stderr or a signed URL.
SAFE_STAGES = frozenset({
    "START", "BASELINE_READ", "CONTAINER_CHECK", "SAS_GENERATION",
    "BLOB_UPLOAD", "BLOB_PROPERTIES", "BLOB_SIZE_CHECK",
    "OWNER_MARK", "OWNER_PROOF", "PACKAGE_SWITCH", "PACKAGE_PROOF",
    "TRIGGER_SYNC", "INDEX_VERIFY", "ROLLBACK_VERIFY",
})
CURRENT_STAGE = "START"


def mark_stage(stage):
    global CURRENT_STAGE
    if type(stage) is not str or stage not in SAFE_STAGES:
        raise RuntimeError("Unknown redacted Y1 diagnostic stage")
    CURRENT_STAGE = stage



def azure(*args):
    """Azure CLI JSON with all stderr/URI-bearing output quarantined."""
    try:
        p = subprocess.run(["az", *args, "--only-show-errors", "-o", "json"],
                           text=True, capture_output=True, check=False, timeout=155)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Y1 scoped Azure operation unavailable") from exc
    if p.returncode:
        raise RuntimeError("Y1 scoped Azure operation failed (redacted)")
    if not p.stdout.strip():
        return None
    try:
        return json.loads(p.stdout)
    except ValueError as exc:
        raise RuntimeError("Y1 scoped Azure JSON malformed") from exc


def scoped_baseline(settings, indexes, *, recovery=False):
    """Fail closed before using the original signed Blob package reference."""
    if not isinstance(settings, dict) or not isinstance(indexes, frozenset):
        raise RuntimeError("Unrecognized Y1 baseline shape")
    if not indexes.issubset(mode.FIVE) or (not indexes and not recovery):
        raise RuntimeError("Unknown Y1 index; refuse mutation")
    if any(key in settings for key in mode.SHADOWS):
        raise RuntimeError("Unexpected customer or shadow Y1 settings")
    old = settings.get(BACKUP)
    try:
        parsed = urlsplit(old) if isinstance(old, str) else None
    except ValueError as exc:
        raise RuntimeError("Original Y1 package URI invalid (redacted)") from None
    if not (mode._package_url(old) and parsed.hostname == EXPECTED_URI_HOST
            and parsed.path.count("/") >= 2 and settings.get(OLD_OWNER) == EXPECTED_FAILED_OWNER):
        raise RuntimeError("Original package backup missing or unowned")
    actual = settings.get(PACKAGE_KEY)
    if not recovery and (indexes != mode.TWO or actual != old or NEW_OWNER in settings):
        raise RuntimeError("Unexpected active Y1 package or concurrent trial")
    if recovery and (settings.get(NEW_OWNER) != _run_id()
                     and (NEW_OWNER in settings or actual != old)):
        raise RuntimeError("Unowned Y1 external rollout")
    if "ENABLE_ORYX_BUILD" in settings:
        raise RuntimeError("Unexpected Y1 Oryx setting; refuse external mode")
    if (not recovery and
            str(settings.get("SCM_DO_BUILD_DURING_DEPLOYMENT", "")).lower() != "true"):
        raise RuntimeError("Unexpected Y1 build setting drift")
    container = parsed.path.strip("/").split("/", 1)[0]
    if not container or len(container) > 63 or not all(c.islower() or c.isdigit() or c=="-" for c in container):
        raise RuntimeError("Unapproved original Y1 private Blob container")
    return old, container


def _run_id():
    value = os.environ.get("GITHUB_RUN_ID", "")
    if not value.isdecimal() or not (6 <= len(value) <= 22):
        raise RuntimeError("Missing protected GitHub run ID")
    return value


def _read_site():
    mark_stage("BASELINE_READ")
    guard.verify()
    return mode._settings(), mode._index()


def _blob_name():
    return "p0249-y1-trial/" + _run_id() + "/five-readonly.zip"


def _sas(account, container, name):
    mark_stage("SAS_GENERATION")
    # The user delegation SAS lifetime is intentionally bounded to SIX days
    # for isolated non-production canary verification (maximum SDK: 7 days).
    expiry = (datetime.now(timezone.utc) + timedelta(days=6)).strftime("%Y-%m-%dT%H:%MZ")
    value = azure("storage", "blob", "generate-sas",
                  "--account-name", account, "--container-name", container,
                  "--name", name, "--permissions", "r", "--expiry", expiry,
                  "--auth-mode", "login", "--as-user", "--https-only")
    if not isinstance(value, str) or len(value) > 4096 or "sig=" not in value:
        raise RuntimeError("Private Y1 delegated SAS was not generated")
    return value.lstrip("?")


def _upload(account, container, name, zippath):
    mark_stage("BLOB_UPLOAD")
    info = azure("storage", "blob", "upload",
                 "--account-name", account, "--container-name", container,
                 "--name", name, "--file", str(zippath),
                 "--auth-mode", "login", "--overwrite", "false",
                 "--content-type", "application/zip")
    if not isinstance(info, dict):
        raise RuntimeError("Y1 private Blob upload not confirmed")
    mark_stage("BLOB_PROPERTIES")
    check = azure("storage", "blob", "show",
                  "--account-name", account, "--container-name", container,
                  "--name", name, "--auth-mode", "login")
    props = check.get("properties") if isinstance(check,dict) else None
    size = (props or {}).get("contentLength") if isinstance(props,dict) else None
    mark_stage("BLOB_SIZE_CHECK")
    if not isinstance(size, int) or size != zippath.stat().st_size:
        raise RuntimeError("Y1 new Blob size not verified")
    print("P0249_Y1_VERSIONED_PRIVATE_BLOB=UPLOADED_VERIFIED",flush=True)


def preflight(zippath):
    site, indexed = _read_site()
    old, container = scoped_baseline(site, indexed)
    if not isinstance(zippath, Path) or not zippath.is_file():
        raise RuntimeError("Missing reviewed Y1 five-GET ZIP")
    if not (1024 < zippath.stat().st_size < 70*1024*1024):
        raise RuntimeError("Reviewed Y1 ZIP size outside bound")
    # Fail before any upload if caller cannot read the preexisting private
    # container or generate a short-lived read-only user delegation SAS.
    mark_stage("CONTAINER_CHECK")
    exists = azure("storage","container","exists","--account-name", ACCOUNT,
                   "--name",container,"--auth-mode","login")
    if not (isinstance(exists,dict) and exists.get("exists") is True):
        raise RuntimeError("Original Y1 private container not available to OIDC")
    _sas(ACCOUNT,container,_blob_name())
    print("P0249_Y1_EXISTING_PRIVATE_STORAGE_AND_SAS_PREFLIGHT=PASS_NO_WRITES",flush=True)


def publish(zippath):
    preflight(zippath)
    # Read again to avoid publishing after another actor moved the baseline.
    values,indexed=_read_site()
    old, container=scoped_baseline(values,indexed)
    name=_blob_name()
    sas=_sas(ACCOUNT,container,name)
    _upload(ACCOUNT,container,name,zippath)
    values,indexed=_read_site()
    if scoped_baseline(values,indexed)[0]!=old:
        raise RuntimeError("Y1 baseline changed after private upload")
    # Owner set BEFORE the active package ref, so recovery can always
    # attribute the trial. Both settings are applied to the isolated Y1 only.
    mark_stage("OWNER_MARK")
    mode._set(**{NEW_OWNER:_run_id()})
    mark_stage("OWNER_PROOF")
    switched=mode._settings()
    if (switched.get(NEW_OWNER)!=_run_id() or switched.get(PACKAGE_KEY)!=old):
        raise RuntimeError("Y1 new trial owner not persisted")
    uri="https://"+EXPECTED_URI_HOST+"/"+container+"/"+name+"?"+sas
    mark_stage("PACKAGE_SWITCH")
    mode._set(**{PACKAGE_KEY:uri})
    mark_stage("PACKAGE_PROOF")
    after=mode._settings()
    if (after.get(PACKAGE_KEY)!=uri or after.get(NEW_OWNER)!=_run_id()
            or after.get(BACKUP)!=old):
        raise RuntimeError("Y1 package reference switch not persisted")
    guard.verify()
    print("P0249_Y1_VERSIONED_EXTERNAL_PACKAGE=ACTIVATED_REDACTED",flush=True)
    # Linux Consumption external package mode requires trigger sync.
    # Use the WebSites ARM action (no command may contain the signed URI).
    mark_stage("TRIGGER_SYNC")
    azure("resource","invoke-action","-g",RG,"-n",SITE,
          "--resource-type","Microsoft.Web/sites",
          "--action","syncfunctiontriggers")
    print("P0249_Y1_EXTERNAL_PACKAGE_SYNC=REQUESTED",flush=True)


def _wait_for(target, attempts=18, delay=12):
    for i in range(attempts):
        try:
            if mode._index()==target:
                return True
        except RuntimeError:
            pass
        time.sleep(delay)
    return False


def verify():
    values,indexed=_read_site()
    mark_stage("INDEX_VERIFY")
    old,_=scoped_baseline(values,indexed,recovery=True)
    current=values.get(PACKAGE_KEY)
    if (values.get(NEW_OWNER)!=_run_id() or
            not mode._package_url(current) or
            urlsplit(current).hostname != EXPECTED_URI_HOST or
            current==old or indexed!=mode.FIVE):
        raise RuntimeError("Hosted five-function external package not active")
    print("P0249_Y1_VERSIONED_PRIVATE_FIVE_INDEX=PASS",flush=True)


def rollback():
    values,indexed=_read_site()
    old,_=scoped_baseline(values,indexed,recovery=True)
    if values.get(PACKAGE_KEY)!=old:
        mode._set(**{PACKAGE_KEY:old})
    values2=mode._settings()
    if values2.get(PACKAGE_KEY)!=old or values2.get(BACKUP)!=old:
        raise RuntimeError("Y1 original external URI was not restored")
    # The original HTTP triggers should be discoverable after app-setting
    # restart. Do not make trigger-sync failure a false-negative if actual
    # twenty real safe handler health/unknown responses and exact two index
    # are already observed.
    if not _wait_for(mode.TWO):
        raise RuntimeError("Original two-function index not restored")
    mark_stage("ROLLBACK_VERIFY")
    guard.probe()
    print("P0249_Y1_EXACT_ORIGINAL_URI_AND_HTTP_ROLLBACK=PASS_20OF20",flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("preflight","publish","verify","rollback"))
    p.add_argument("--zip",type=Path)
    args=p.parse_args()
    if args.mode in ("preflight","publish") and args.zip is None:
        raise RuntimeError("Missing Y1 reviewed ZIP path")
    {"preflight":lambda:preflight(args.zip),
     "publish":lambda:publish(args.zip),
     "verify":verify,
     "rollback":rollback}[args.mode]()


def entrypoint():
    mark_stage("START")
    try:
        main()
    except Exception:
        # Only a static phase label; never exception text, Azure CLI output or SAS.
        print(f"P0249_Y1_VERSIONED_EXTERNAL_RELEASE=FAILED_REDACTED phase={CURRENT_STAGE}",flush=True)
        raise SystemExit(2)


if __name__=="__main__":
    entrypoint()
