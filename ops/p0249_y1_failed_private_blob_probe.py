#!/usr/bin/env python3
"""Read-only versioned Y1 package publication diagnosis; no secrets or Azure writes."""
from __future__ import annotations
import json
from urllib.parse import urlsplit

import p0249_y1_canary_guard as guard
import p0249_y1_remote_build_mode as baseline
import p0249_y1_external_private_package as pkg

FAILED_RELEASE="44670935079"
BLOB="p0249-y1-trial/"+FAILED_RELEASE+"/five-readonly.zip"


def safe_blob_shape(blob, *, exists):
    if not exists:
        return {"exists":False, "size_reported":False,"size_in_zip_bounds":False}
    if not isinstance(blob,dict):
        raise RuntimeError("Missing private Blob properties")
    props=blob.get("properties")
    val=(props or {}).get("contentLength") if isinstance(props,dict) else None
    return {"exists":True,
            "size_reported":isinstance(val,int),
            "size_in_zip_bounds":isinstance(val,int) and 1024<val<70*1024*1024}


def main():
    guard.verify()
    settings=baseline._settings()
    indexed=baseline._index()
    old,container=pkg.scoped_baseline(settings,indexed)
    assert urlsplit(old).hostname==pkg.EXPECTED_URI_HOST
    # The owner from the previous attempt MUST not have changed the active
    # original package. No writes or token/URL/identity values are displayed.
    exists=pkg.azure("storage","blob","exists",
                     "--account-name",pkg.ACCOUNT,
                     "--container-name",container,
                     "--name",BLOB,"--auth-mode","login")
    if not isinstance(exists,dict) or not isinstance(exists.get("exists"),bool):
        raise RuntimeError("Cannot establish Y1 failed upload existence")
    found=exists["exists"]
    obj=(pkg.azure("storage","blob","show",
                   "--account-name",pkg.ACCOUNT,
                   "--container-name",container,
                   "--name",BLOB,"--auth-mode","login") if found else {})
    facts=safe_blob_shape(obj,exists=found)
    print("P0249_Y1_FAILED_BLOB_READONLY="+json.dumps(facts,sort_keys=True),flush=True)
    guard.probe()
    print("P0249_Y1_FAILED_BLOB_ORIGINAL_20OF20=PASS",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception:
        print("P0249_Y1_FAILED_BLOB_READONLY=FAILED_REDACTED",flush=True)
        raise SystemExit(2)
