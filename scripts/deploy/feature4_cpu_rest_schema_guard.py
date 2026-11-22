#!/usr/bin/env python3
"""Read-only protected DEV F4 schema proof when DB pooler credentials are stale.

This guard tests the *actual* already-installed F4 tables and private worker
claim RPC through scoped Supabase REST as service_role. No record is modified:
the claim request uses p_id:null, which server code returns without writes.
No tokens, URL responses, HTTP errors, or customer records are printed.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from urllib.request import Request

DEV_REF = "jeearzffnjbvghwjjjrf"
ROOT = f"https://{DEV_REF}.supabase.co"
KEY_ENV = "RETAIL_SUPABASE_SERVICE_ROLE_KEY"
RESOURCE_PATHS = (
    "/rest/v1/feature4_creative_plans?select=id&limit=0",
    "/rest/v1/feature4_cpu_render_jobs?select=id&limit=0",
)


class GuardDenied(ValueError):
    pass


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GuardDenied("Unexpected protected DEV API redirect")


def _headers(key: str) -> dict:
    if key.startswith("sb_secret_") and len(key) > 16:
        return {"apikey": key}
    if key.startswith("eyJ") and key.count(".") == 2:
        return {"apikey": key, "Authorization": "Bearer " + key}
    raise GuardDenied("Unsupported protected service identity format")


def verify(key: str, *, opener=None) -> bool:
    """Fail closed unless the true DEV REST host returns only expected data."""
    if not isinstance(key, str):
        raise GuardDenied("Missing protected Supabase service key")
    headers = _headers(key)
    headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    if opener is None:
        opener = urllib.request.build_opener(NoRedirects()).open
    for path in RESOURCE_PATHS:
        url = ROOT + path
        if not url.startswith(ROOT + "/rest/v1/"):
            raise GuardDenied("Foreign project requested")
        req = Request(url, headers=headers, method="GET")
        try:
            with opener(req, timeout=25) as response:
                code = response.status
                body = response.read(8192)
        except (urllib.error.URLError, OSError, GuardDenied) as exc:
            raise GuardDenied("Protected DEV table read denied") from None
        if code != 200 or body != b"[]":
            raise GuardDenied("Required F4 DEV table missing or not empty")
    # Strictly nonmutating worker-RPC inventory proof: p_id=NULL is rejected
    # before any SELECT ... FOR UPDATE, claim, media or billing activity.
    req = Request(ROOT + "/rest/v1/rpc/feature4_claim_cpu_render",
                  headers=headers, data=b'{"p_id":null}', method="POST")
    try:
        with opener(req, timeout=25) as response:
            code = response.status
            body = response.read(256)
    except (urllib.error.URLError, OSError, GuardDenied) as exc:
        raise GuardDenied("Protected DEV service-only RPC unavailable") from None
    if code != 200 or body.strip() != b"null":
        raise GuardDenied("F4 worker claim null-denial proof failed")
    return True


def main() -> int:
    try:
        key = os.getenv(KEY_ENV, "")
        if verify(key):
            print("PASS: exact Supabase DEV F4 tables and nonmutating service-only claim verified via protected REST")
            return 0
    except GuardDenied:
        print("BLOCKED: protected DEV F4 REST schema/identity proof denied")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
