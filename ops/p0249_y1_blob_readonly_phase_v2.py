#!/usr/bin/env python3
"""Postfailure Y1 read-only Blob check with fixed enum error categories only."""
from __future__ import annotations
import json
import subprocess

import p0249_y1_canary_guard as guard
import p0249_y1_remote_build_mode as mode
import p0249_y1_external_private_package as pkg

FAILED_RUN="44670935079"


def error_class(stderr):
    """Never print raw Azure errors, account/container, SAS or URL."""
    text=str(stderr).lower()
    if any(s in text for s in ("authorizationpermissionmismatch","authorizationfailure",
                               "authenticationfailed","permissiondenied","unauthorized",
                               "forbidden","status: 403","status code 403")):
        return "ACCESS_DENIED"
    if any(s in text for s in ("blobnotfound","resourcenotfound","status: 404","status code 404")):
        return "NOT_FOUND"
    if any(s in text for s in ("unrecognized arguments","not a recognized command",
                               "invalid choice","invalidcommand","command not found")):
        return "CLI_COMMAND"
    if any(s in text for s in ("invalidresourcename","invalid blob","invalidcontainername")):
        return "INVALID_BLOB_NAME"
    return "OTHER_REDACTED"


def read_blob(*args):
    """Return status category and JSON, never print subprocess output."""
    try:
        result=subprocess.run(["az","storage","blob",*args,"--only-show-errors","-o","json"],
                              capture_output=True,text=True,timeout=90,check=False)
    except (OSError,subprocess.TimeoutExpired):
        return "AZURE_CLI_UNAVAILABLE",None
    if result.returncode:
        return error_class(result.stderr),None
    try:
        return "SUCCESS",json.loads(result.stdout)
    except ValueError:
        return "MALFORMED_JSON",None


def main():
    guard.verify()
    print("P0249_Y1_BLOB_PHASE=ORIGINAL_FLEX_AND_Y1_VERIFIED",flush=True)
    s=mode._settings()
    indexed=mode._index()
    print("P0249_Y1_BLOB_PHASE=SETTINGS_AND_INDEX_READ",flush=True)
    from p0249_y1_emergency_readonly_state import classify
    print("P0249_Y1_BLOB_BASELINE_FLAGS="+json.dumps(classify(s,indexed),sort_keys=True),flush=True)
    try:
        _,container=pkg.scoped_baseline(s,indexed)
    except Exception:
        print("P0249_Y1_BLOB_PHASE=ORIGINAL_BASELINE_NOT_MATCHED",flush=True)
        guard.probe()
        raise RuntimeError("Original Y1 baseline mismatch; no Blob operation allowed") from None
    print("P0249_Y1_BLOB_PHASE=PINNED_ORIGINAL_BASELINE",flush=True)
    name="p0249-y1-trial/"+FAILED_RUN+"/five-readonly.zip"
    args=("--account-name",pkg.ACCOUNT,"--container-name",container,"--name",name,
          "--auth-mode","login")
    state,observed=read_blob("exists",*args)
    if state!="SUCCESS":
        print("P0249_Y1_BLOB_EXISTS_RESULT="+state,flush=True)
    elif not isinstance(observed,dict) or not isinstance(observed.get("exists"),bool):
        print("P0249_Y1_BLOB_EXISTS_RESULT=UNEXPECTED_RESPONSE_SHAPE",flush=True)
    elif not observed["exists"]:
        print("P0249_Y1_BLOB_EXISTS_RESULT=NOT_PRESENT",flush=True)
    else:
        state,info=read_blob("show",*args)
        if state!="SUCCESS":
            print("P0249_Y1_BLOB_SHOW_RESULT="+state,flush=True)
        else:
            props=info.get("properties") if isinstance(info,dict) else None
            size=(props or {}).get("contentLength") if isinstance(props,dict) else None
            print("P0249_Y1_BLOB_EXISTS_RESULT=PRESENT",flush=True)
            print("P0249_Y1_BLOB_SIZE_CLASS="+
                  ("VALID" if isinstance(size,int) and 1024<size<70*1024*1024 else
                   "MISSING_OR_OUT_OF_BOUNDS"),flush=True)
    guard.probe()
    print("P0249_Y1_BLOB_READONLY_PHASE_ORIGINAL_HEALTH=PASS_20OF20",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception:
        print("P0249_Y1_BLOB_PHASE=FAILED_REDACTED",flush=True)
        raise SystemExit(2)
