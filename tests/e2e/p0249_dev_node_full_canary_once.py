"""ROOT-gated existing Part 1 full DEV acceptance against Free SWA Node preview.

Reuses the existing independently reviewed/cleanup-fenced retailer canary.
No credentials in code, no new Auth/shop/onboarding bypass, no new paid
resource, no frontend cutover and no access to WineShopPOS.
Requires manual protected GitHub workflow_dispatch AND explicit ROOT approval
of the two unique, disposable newly signed-up retailer shops.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
import retail_dev_canary_once as canary

NODE_PREVIEW = "https://purple-dune-06b5da200-p0249writes.eastasia.2.azurestaticapps.net"
ALLOWED_MODES = {"node-poster-reel","node-browser-reel"}


def node_preflight(*, include_prompt=False):
    """Real handler 401 markers before provisioning even a temporary Auth user.

    Parent canary.main() always supplies include_prompt=prompt_only. This
    Node-only full poster/Reel acceptance has no Feature2 prompt mode; reject
    any unexpected request rather than silently skipping that prerequisite.
    """
    if include_prompt is not False:
        raise RuntimeError("P0249_NODE_PREFLIGHT_PROMPT_MODE_NOT_SUPPORTED")
    def check(path, method="GET"):
        body = b"{}" if method == "POST" else None
        req = urllib.request.Request(
            NODE_PREVIEW+path, method=method, data=body,
            headers={"Accept":"application/json","Content-Type":"application/json"}
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(req,timeout=12) as response:
                code,headers = response.status,response.headers
        except urllib.error.HTTPError as response:
            code,headers = response.code,response.headers
        if (code != 401 or headers.get("X-RGAI-Secure-Adapter") != "candidate-v1"
                or time.monotonic()-started > 12):
            raise RuntimeError("P0249_NODE_PREVIEW_NOT_AUTHENTICATED_OR_HEALTHY")
    health=urllib.request.Request(NODE_PREVIEW+"/api/p0-secure-health",method="GET")
    with urllib.request.urlopen(health,timeout=12) as response:
        if (response.status != 200 or response.headers.get("X-P0249-Secure-Preview")
                != "real-jwks-rls-dev-write-v1"):
            raise RuntimeError("P0249_WRONG_NODE_DEV_PREVIEW")
    for url,method in [
        ("/api/campaigns/11111111-1111-4111-8111-111111111111","GET"),
        ("/api/poster-jobs/11111111-1111-4111-8111-111111111111","GET"),
        ("/api/render-jobs/11111111-1111-4111-8111-111111111111","GET"),
        ("/api/campaigns","POST"),
        ("/api/campaigns/11111111-1111-4111-8111-111111111111/renders","POST"),
    ]:
        check(url,method)
    print("P0249_REAL_NODE_WRITE_API_PREFLIGHT_PASSED=true",flush=True)



def node_preview_headers(headers):
    """Only a real user JWT may cross into the isolated Node candidate.

    Never forward Supabase apikey, service credentials, cookies, arbitrary
    caller-supplied Node JWT, proxy identity or browser-origin overrides.
    The Node dispatcher independently verifies signature, expiry and RLS.
    """
    if not isinstance(headers, dict):
        raise RuntimeError("P0249_INVALID_NODE_HEADER_SET")
    forwarded = {}
    token = None
    for raw_name, value in headers.items():
        if (not isinstance(raw_name, str) or not isinstance(value, str)
                or not raw_name or "\r" in raw_name or "\n" in raw_name
                or "\r" in value or "\n" in value):
            raise RuntimeError("P0249_INVALID_NODE_HEADER")
        name = raw_name.lower()
        if name == "apikey":
            # Supabase browser publishable key is irrelevant to Node. Never
            # forward any value, including a mistakenly supplied service key.
            continue
        if name == "authorization":
            if token is not None or not value.startswith("Bearer "):
                raise RuntimeError("P0249_INVALID_NODE_USER_BEARER")
            candidate = value[7:]
            segments = candidate.split(".")
            if (len(candidate) > 8192 or len(segments) != 3
                    or not all(re.fullmatch(r"[A-Za-z0-9_-]+", p) for p in segments)):
                raise RuntimeError("P0249_INVALID_NODE_USER_BEARER")
            token = candidate
            continue
        if name not in {"accept", "content-type", "prefer"}:
            # Includes a prefilled x-rgai-supabase-jwt, cookies, Origin,
            # X-Forwarded-*, keys, and any unexpected impersonation header.
            raise RuntimeError("P0249_UNREVIEWED_NODE_HEADER")
        if name in forwarded:
            raise RuntimeError("P0249_DUPLICATE_NODE_HEADER")
        forwarded[name] = value
    if token is None:
        raise RuntimeError("P0249_MISSING_NODE_USER_BEARER")
    forwarded["x-rgai-supabase-jwt"] = token
    return forwarded



class _NodeNeverRedirect(urllib.request.HTTPRedirectHandler):
    """No custom JWT can follow a 30x away from the pinned preview origin."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_NODE_OPENER = urllib.request.build_opener(_NodeNeverRedirect())


def _call_node_preview(url, *, method, payload, headers, timeout, expect):
    """Bounded Node-only HTTP transport; no redirect or uncertain write retry.

    The original Supabase client remains untouched. The preview receives
    only node_preview_headers output; this helper never accepts arbitrary hosts.
    """
    if not url.startswith(NODE_PREVIEW + "/api/") or method not in ("GET", "POST", "PATCH"):
        raise RuntimeError("P0249_INVALID_NODE_REQUEST_TARGET")
    if payload is not None and isinstance(payload, (bytes, bytearray)):
        raise RuntimeError("P0249_NODE_BINARY_WRITE_UNSUPPORTED")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    safe_headers = dict(headers)
    if data is not None:
        safe_headers.setdefault("content-type", "application/json")
    request = urllib.request.Request(url, data=data, method=method, headers=safe_headers)
    status, body = None, b""
    for attempt in range(3 if method == "GET" else 1):
        try:
            with _NODE_OPENER.open(request, timeout=(65 if method == "GET" else timeout)) as response:
                status, body = response.status, response.read(1_000_001)
            if len(body) > 1_000_000:
                raise RuntimeError("P0249_NODE_RESPONSE_TOO_LARGE")
            break
        except urllib.error.HTTPError as response:
            status, body = response.code, response.read(4097)
            if 300 <= status <= 399:
                raise RuntimeError("P0249_NODE_REDIRECT_DENIED") from None
            if method == "GET" and status in (502, 503, 504) and attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            break
        except (TimeoutError, ConnectionResetError, OSError):
            if method == "GET" and attempt < 2:
                time.sleep(4 * (attempt + 1))
                continue
            raise RuntimeError("P0249_REAL_NODE_HTTP_TRANSACTION_UNCONFIRMED") from None
    if status not in expect:
        if status in (502, 503, 504):
            raise RuntimeError("P0249_REAL_NODE_HTTP_TRANSACTION_UNCONFIRMED")
        # Never surface error bodies, signed IDs, private URL or request JWTs.
        raise RuntimeError("P0249_NODE_UNEXPECTED_HTTP_STATUS_" + str(status))
    if not body:
        return status, None
    try:
        return status, json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return status, body


def main():
    if os.environ.get("RGAI_DEV_CANARY_APPROVAL") != "AUTHORIZED_RETAILGROWTHAI_DEV_ONLY":
        raise RuntimeError("ROOT_APPROVAL_PRECONDITION_MISSING")
    if os.environ.get("RGAI_DEV_NODE_PREVIEW_MODE") not in ALLOWED_MODES:
        raise RuntimeError("INVALID_NODE_PREVIEW_TEST_MODE")
    # This script is never invoked by an ordinary PR push; a protected manual
    # job must explicitly supply the exact mode and operator approval code.
    # All shop onboarding stays gated by the real SaaS ROOT account.
    previous_call=canary.call
    canary.API=NODE_PREVIEW

    def node_routed_call(url,method="GET",payload=None,headers=None,timeout=30,
                         expect=(200,201,202,204)):
        is_node=url.startswith(NODE_PREVIEW+"/api/")
        if is_node:
            # One customer JWT only; reject forged inbound Node identity.
            original=node_preview_headers(headers or {})
        else:
            original=dict(headers or {})
        if is_node:
            return _call_node_preview(url, method=method, payload=payload,
                                      headers=original, timeout=timeout, expect=expect)
        return previous_call(url,method=method,payload=payload,
                             headers=original,timeout=timeout,expect=expect)

    canary.call=node_routed_call
    canary.preflight_dev_http_auth_routes=node_preflight
    node_preflight()
    print("P0249_NODE_PREVIEW_TARGET_NOT_PRODUCTION=true",flush=True)
    # Existing canary handles newly created synthetic image/media and RLS
    # two-tenant/VIEWER checks, ROOT onboarding, poster, Python queue/FFmpeg,
    # 30s H264/AAC private URL and exact-scoped finally cleanup.
    # Mode controls only whether the upload uses Playwright or signed REST.
    canary.main()
    print("P0249_NODE_FULL_SIGNED_TENANT_E2E_AND_CLEANUP=PASSED",flush=True)


if __name__ == "__main__":
    main()
