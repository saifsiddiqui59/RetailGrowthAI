#!/usr/bin/env python3
"""#249 exact DEV Y1 temporary PUBLIC-only JWT shadow settings, with rollback.

NO service-role keys, access JWTs, Auth secrets or real customer data go into
Function App settings. Preflight requires all controlled keys ABSENT. Cleanup
deletes ONLY exact trial keys if still absent or equal to this trial's values.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import p0249_y1_canary_guard as scope

ORIGIN = "https://jeearzffnjbvghwjjjrf.supabase.co"
PUBLIC = "sb_publishable_tEqNinZfiLzrAyF4E1pAeQ_vZRvJYjq"
SETTING_VALUES = {
    "RETAIL_SUPABASE_URL": ORIGIN,
    "RETAIL_SUPABASE_PUBLISHABLE_KEY": PUBLIC,
    "RGAI_P0249_READONLY_SHADOW": "true",
}
KEYS = tuple(SETTING_VALUES)
MARKER_SCHEMA = "retailgrowthai/p0249-y1-signed-trial/v1"


def require_marker(path):
    mark=json.loads(Path(path).read_text(encoding="utf-8"))
    expected={
        "schema": MARKER_SCHEMA,
        "run_id": os.getenv("GITHUB_RUN_ID"),
        "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        "initial_absent": list(KEYS),
    }
    if mark!=expected or not all(expected.values()):
        raise RuntimeError("MISMATCHED_OR_MISSING_TRIAL_MARKER")
    return mark


def read_only_scope():
    scope.verify()  # correct current subscription/RG/app/tags/FC1/sku/Python
    rows=scope.command("functionapp","config","appsettings","list",
                       "-g",scope.RG,"-n",scope.SITE)
    if not isinstance(rows,list) or any(not isinstance(x,dict) for x in rows):
        raise RuntimeError("MALFORMED_AZURE_SETTING_LIST")
    if any(x.get("name")=="RETAIL_SUPABASE_SERVICE_ROLE_KEY" for x in rows):
        raise RuntimeError("SERVICE_ROLE_KEY_MUST_NOT_BE_IN_Y1_APP")
    return {x["name"]:str(x.get("value","")) for x in rows
            if x.get("name") in KEYS}


def preflight(path):
    rows=read_only_scope()
    if rows:
        raise RuntimeError("SHADOW_CONFIG_NOT_ORIGINALLY_ABSENT")
    if not os.getenv("GITHUB_RUN_ID") or not os.getenv("GITHUB_RUN_ATTEMPT"):
        raise RuntimeError("NOT_GITHUB_ACTIONS_RUN")
    with Path(path).open("x",encoding="utf-8") as f:
        json.dump({
            "schema":MARKER_SCHEMA,"run_id":os.environ["GITHUB_RUN_ID"],
            "run_attempt":os.environ["GITHUB_RUN_ATTEMPT"],
            "initial_absent":list(KEYS),
        },f,sort_keys=True)
    print("P0249_Y1_SIGNED_SETTINGS_PREFLIGHT=EXACT_ABSENT",flush=True)


def activate(path):
    require_marker(path)
    if read_only_scope():
        raise RuntimeError("SHADOW_CHANGED_SINCE_PREFLIGHT")
    scope.command("functionapp","config","appsettings","set",
                  "-g",scope.RG,"-n",scope.SITE,
                  "--settings",*[k+"="+SETTING_VALUES[k] for k in KEYS])
    if read_only_scope()!=SETTING_VALUES:
        raise RuntimeError("PUBLIC_ONLY_SHADOW_NOT_VERIFIED")
    print("P0249_Y1_SIGNED_SETTINGS=TEMPORARY_PUBLIC_ONLY",flush=True)


def rollback(path):
    require_marker(path)
    rows=read_only_scope()
    if any(val!=SETTING_VALUES[key] for key,val in rows.items()):
        raise RuntimeError("SHADOW_SETTING_MODIFIED_EXTERNALLY_MANUAL_CHECK")
    if rows:
        scope.command("functionapp","config","appsettings","delete",
                      "-g",scope.RG,"-n",scope.SITE,"--setting-names",*KEYS)
    if read_only_scope():
        raise RuntimeError("CRITICAL_SHADOW_ROLLBACK_UNVERIFIED")
    print("P0249_Y1_SIGNED_SHADOW_ROLLBACK_VERIFIED=ALL_ABSENT",flush=True)


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("preflight","activate","rollback"))
    p.add_argument("--marker",required=True)
    a=p.parse_args()
    try:
        {"preflight":preflight,"activate":activate,"rollback":rollback}[a.action](a.marker)
    except Exception:
        print("P0249_Y1_SIGNED_SETTINGS_FAILED_OR_ROLLBACK_CHECK_REQUIRED",
              file=sys.stderr,flush=True)
        raise SystemExit(4)


if __name__=="__main__":
    main()
