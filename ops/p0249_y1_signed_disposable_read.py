#!/usr/bin/env python3
"""#249: bounded DEV-only genuine Supabase JWT into isolated Y1 campaign GET.

Creates exactly ONE disposable Auth user via Supabase Auth Admin (never direct
auth.users SQL), tests read-only signature/RLS denial, then deletes the exact
synthetic Auth user. No shops, campaigns, SQL migrations or queue/model calls.
Never log credentials, JWTs, emails, response bodies or private data.
"""
import base64
import json
import os
import secrets
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

SUPABASE = "https://jeearzffnjbvghwjjjrf.supabase.co"
Y1 = "https://rgai-dev-y1-p0249-d4e5ddbd.azurewebsites.net"
PUBLIC = "sb_publishable_tEqNinZfiLzrAyF4E1pAeQ_vZRvJYjq"
PREFIX = "rgai-p0249-y1-jwt-"
CID = "11111111-1111-4111-8111-111111111111"
MAX_SECONDS = 170


def request(url, *, method="GET", data=None, headers=None, timeout=16):
    if not (url.startswith(SUPABASE + "/auth/v1/") or
            url.startswith(Y1 + "/api/")):
        raise RuntimeError("SCOPE_WRONG_ORIGIN")
    body = None if data is None else json.dumps(data).encode("utf-8")
    h = dict(headers or {})
    if body is not None:
        h["Content-Type"] = "application/json"
    req = Request(url, method=method, headers=h, data=body)
    t0 = time.monotonic()
    try:
        with urlopen(req, timeout=timeout) as resp:
            status, response_headers, raw = resp.status, resp.headers, resp.read(16384)
    except HTTPError as resp:
        status, response_headers, raw = resp.code, resp.headers, resp.read(16384)
    elapsed = round(time.monotonic() - t0, 3)
    try:
        parsed = json.loads(raw) if raw else None
    except (UnicodeError, ValueError):
        parsed = None
    return status, parsed, response_headers, elapsed


def auth_headers(secret):
    return {"apikey": secret, "Authorization": "Bearer " + secret}


def check_asymmetric_public_jwks():
    status, body, _, _ = request(SUPABASE + "/auth/v1/.well-known/jwks.json")
    if status != 200 or not isinstance(body, dict) or not any(
        isinstance(k, dict) and k.get("alg") in ("RS256", "ES256")
        for k in body.get("keys", [])
    ):
        raise RuntimeError("PUBLIC_ASYMMETRIC_JWKS_NOT_READY")


def verify_access_token_shape(token, user):
    # Informational shape only; Y1's original PyJWT/JWKS verifier does crypto.
    if not isinstance(token, str) or len(token) > 8192 or token.count(".") != 2:
        raise RuntimeError("INVALID_ACCESS_TOKEN_SHAPE")
    raw=token.split(".")[1]
    payload=json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))
    if (payload.get("role") != "authenticated" or
        payload.get("aud") != "authenticated" or
        payload.get("iss") != SUPABASE + "/auth/v1" or
        str(UUID(payload.get("sub"))) != user):
        raise RuntimeError("SIGNED_USER_CLAIMS_NOT_DEV")
    return token


def cleanup_exact_test_user(key, marker, created_uid):
    if not (marker.startswith(PREFIX) and len(marker) <= 54 and
            marker[len(PREFIX):].isalnum()):
        raise RuntimeError("UNSAFE_CLEANUP_MARKER")
    email = marker + "@example.invalid"
    if created_uid is None:
        # No replay of uncertain Auth create; search exact synthetic marker.
        status, page, _, _ = request(
            SUPABASE + "/auth/v1/admin/users?page=1&per_page=100",
            headers=auth_headers(key),
        )
        if status != 200 or not isinstance(page, dict):
            raise RuntimeError("UNCERTAIN_CREATE_NEEDS_MANUAL_CLEANUP")
        matches = [u for u in page.get("users", [])
                   if isinstance(u, dict) and u.get("email") == email]
        if len(matches) > 1:
            raise RuntimeError("AMBIGUOUS_AUTH_CLEANUP")
        if not matches:
            print("P0249_Y1_TEST_AUTH_USER_ABSENT", flush=True)
            return
        created_uid = matches[0].get("id")
    uid = str(UUID(created_uid))
    status, _, _, _ = request(
        SUPABASE + "/auth/v1/admin/users/" + uid,
        method="DELETE", headers=auth_headers(key), timeout=20,
    )
    if status not in (200, 204):
        raise RuntimeError("DISPOSABLE_AUTH_CLEANUP_NOT_ACKNOWLEDGED")
    print("P0249_Y1_DISPOSABLE_AUTH_DELETED=true", flush=True)


def main():
    if os.environ.get("RGAI_P0249_Y1_SIGNED_TEST_APPROVAL") != "OWNER_APPROVED_Y1_SIGNED_READ":
        raise RuntimeError("DEV_EXPLICIT_APPROVAL_REQUIRED")
    key = os.environ.get("RGAI_DEV_SERVICE_KEY", "")
    pub = os.environ.get("RGAI_DEV_PUBLISHABLE_KEY", "")
    if pub != PUBLIC or not key.startswith(("sb_secret_", "eyJ")) or len(key) < 40:
        raise RuntimeError("DEV_KEYS_NOT_CONFIGURED")
    t0 = time.monotonic()
    check_asymmetric_public_jwks()
    health, _, h, _ = request(Y1 + "/api/p0249/health")
    if health != 200 or not h.get("X-Request-ID"):
        raise RuntimeError("REAL_Y1_HEALTH_NOT_READY")
    campaign_url = Y1 + "/api/campaigns/" + CID
    status, denied, h, _ = request(campaign_url)
    if status != 401 or denied != {"error": "UNAUTHORIZED"} or not h.get("X-Request-ID"):
        raise RuntimeError("REAL_Y1_MISSING_BEARER_NOT_DENIED")

    marker = PREFIX + uuid4().hex[:16]
    email = marker + "@example.invalid"
    password = secrets.token_urlsafe(32)
    uid = None
    try:
        if time.monotonic() - t0 > MAX_SECONDS:
            raise RuntimeError("SIGNED_TEST_TOTAL_TIME_BUDGET_EXHAUSTED")
        status, result, _, _ = request(
            SUPABASE + "/auth/v1/admin/users",
            method="POST",
            data={"email":email,"password":password,"email_confirm":True},
            headers=auth_headers(key), timeout=25,
        )
        if status not in (200, 201) or not isinstance(result, dict):
            raise RuntimeError("DISPOSABLE_AUTH_CREATE_FAILED")
        uid = str(UUID(result.get("id")))
        status, session, _, _ = request(
            SUPABASE + "/auth/v1/token?grant_type=password",
            method="POST", data={"email":email,"password":password},
            headers={"apikey": pub}, timeout=20,
        )
        if status != 200 or not isinstance(session, dict):
            raise RuntimeError("DISPOSABLE_PASSWORD_SIGNIN_FAILED")
        token=verify_access_token_shape(session.get("access_token"), uid)
        good=0
        for i in range(3):
            if time.monotonic() - t0 > MAX_SECONDS:
                raise RuntimeError("SIGNED_TEST_TOTAL_TIME_BUDGET_EXHAUSTED")
            status, payload, h, elapsed = request(
                campaign_url, headers={"Authorization": "Bearer " + token}, timeout=18
            )
            accepted=(status==404 and payload=={"error":"NOT_FOUND"}
                      and bool(h.get("X-Request-ID")) and elapsed <18)
            good+=int(accepted)
            print(f"P0249_Y1_SIGNED_READ i={i+1} http={status} marked={bool(h.get('X-Request-ID'))} elapsed={elapsed} accepted={accepted}",flush=True)
        if good!=3:
            raise RuntimeError("SIGNED_USER_HTTP_RLS_NEGATIVE_FAILED")
        parts=token.split(".")
        sig=parts[2]
        parts[2]=("A" if sig[0]!="A" else "B")+sig[1:]
        forged=".".join(parts)
        status, payload, h, _ = request(
            campaign_url, headers={"Authorization":"Bearer "+forged}, timeout=18
        )
        if status!=401 or payload!={"error":"UNAUTHORIZED"} or not h.get("X-Request-ID"):
            raise RuntimeError("FORGED_JWT_NOT_REJECTED")
        print("P0249_Y1_REAL_SIGNED_JWT_NO_SHOP_READ=3/3_PASS",flush=True)
        print("P0249_Y1_FORGED_SIGNATURE_DENIED=PASS",flush=True)
    finally:
        cleanup_exact_test_user(key, marker, uid)


if __name__=="__main__":
    try:
        main()
    except (RuntimeError, URLError, TimeoutError, ValueError, KeyError, TypeError) as e:
        print("P0249_Y1_SIGNED_SMOKE_FAILED="+type(e).__name__,file=sys.stderr,flush=True)
        sys.exit(1)
