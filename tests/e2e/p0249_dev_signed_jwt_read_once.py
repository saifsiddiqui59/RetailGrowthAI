#!/usr/bin/env python3
"""RetailGrowthAI #249: one owner-authorized disposable Auth-only JWT DEV canary.

No shop, tenant grant, campaign, media, payment, Azure Queue/worker or production
mutation. A true Supabase-signed access JWT is used only with the existing Free
SWA p0249secure read-only named preview. It is NEVER logged or persisted.
"""
import base64
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request
import uuid

SUPABASE = "https://jeearzffnjbvghwjjjrf.supabase.co"
PREVIEW = "https://purple-dune-06b5da200-p0249secure.eastasia.2.azurestaticapps.net"
PUBLIC = "sb_publishable_tEqNinZfiLzrAyF4E1pAeQ_vZRvJYjq"
CANARY_PREFIX = "rgai-p0249-jwt-"
CAMPAIGN = "11111111-1111-4111-8111-111111111111"


def request(url, method="GET", data=None, headers=None, expected=(200,), timeout=20):
    if not (url.startswith(SUPABASE + "/") or url.startswith(PREVIEW + "/")):
        raise RuntimeError("UNTRUSTED_EXTERNAL_HOST")
    meta = dict(headers or {})
    body = None
    if data is not None:
        body = json.dumps(data, separators=(",", ":")).encode("utf8")
        meta["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=meta)
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            headers_out = response.headers
            body_raw = response.read(32768)
    except urllib.error.HTTPError as response:
        status = response.code
        headers_out = response.headers
        body_raw = response.read(32768)
    elapsed = time.monotonic() - started
    if status not in expected:
        # No token, private payload, service key or response body in errors.
        raise RuntimeError("DEV_TEST_UNEXPECTED_HTTP_" + str(status) + "_ON_" + method)
    try:
        parsed = json.loads(body_raw) if body_raw else None
    except (UnicodeError, ValueError):
        parsed = None
    return status, parsed, headers_out, elapsed


def admin_headers(key):
    return {"apikey": key, "Authorization": "Bearer " + key}


def jwt_claims_for_local_shape_only(jwt):
    # The canary is NOT a JWT verifier; ONLY deployed Node JWKS verifies crypto.
    if not isinstance(jwt, str) or len(jwt) > 8192 or jwt.count(".") != 2:
        raise RuntimeError("AUTH_DID_NOT_ISSUE_JWT")
    text = jwt.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(text + "=" * (-len(text) % 4)))
    if claims.get("role") != "authenticated" or claims.get("aud") != "authenticated":
        raise RuntimeError("AUTH_JWT_ROLE_WRONG")
    if claims.get("iss") != SUPABASE + "/auth/v1":
        raise RuntimeError("AUTH_JWT_ISSUER_WRONG")
    return claims


def owner_only_cleanup(key, marker, created_uid):
    if not marker.startswith(CANARY_PREFIX) or len(marker) > 64:
        raise RuntimeError("UNSAFE_AUTH_CLEANUP_SCOPE")
    if created_uid is None:
        # Reconcile uncertain admin-create ACK by an EXACT synthetic email
        # search. Never delete any real user or replay a possibly committed POST.
        _, page, _, _ = request(
            SUPABASE + "/auth/v1/admin/users?page=1&per_page=100",
            headers=admin_headers(key), expected=(200,), timeout=20
        )
        users = page.get("users", []) if isinstance(page, dict) else []
        matches = [u for u in users
                   if isinstance(u, dict) and u.get("email") == marker + "@example.invalid"]
        if len(matches) > 1:
            raise RuntimeError("AMBIGUOUS_SYNTHETIC_AUTH_FIXTURE")
        if not matches:
            print("P0249_DISPOSABLE_AUTH_ACCOUNT_NOT_CREATED=true", flush=True)
            return
        created_uid = matches[0].get("id")
    request(
        SUPABASE + "/auth/v1/admin/users/" + str(uuid.UUID(created_uid)),
        method="DELETE", headers=admin_headers(key), expected=(200, 204), timeout=20
    )
    print("P0249_DISPOSABLE_AUTH_ACCOUNT_DELETED=true", flush=True)


def main():
    if os.environ.get("RGAI_DEV_P0249_JWT_CANARY_APPROVAL") != "OWNER_APPROVED_READ_ONLY_JWT_TEST":
        raise RuntimeError("OWNER_AUTH_ONLY_CANARY_APPROVAL_REQUIRED")
    key = os.environ["RGAI_DEV_SERVICE_KEY"]
    pub = os.environ["RGAI_DEV_PUBLISHABLE_KEY"]
    if pub != PUBLIC or not key.startswith(("sb_secret_", "eyJ")) or len(key) < 40:
        raise RuntimeError("WRONG_RETAILGROWTHAI_DEV_CREDENTIAL_TYPE")
    # Before touching Auth, check current real preview is alive, no JWT => 401,
    # not a synthetic 401 from the original p0249node mock preview.
    _, health, h, _ = request(PREVIEW + "/api/p0-secure-health")
    if health != {"status": "READ_ONLY_PREVIEW"} or h.get("X-P0249-Secure-Preview") != "real-jwks-rls-readonly-v1":
        raise RuntimeError("SECURE_REAL_PREVIEW_NOT_DEPLOYED")
    path = PREVIEW + "/api/campaigns/" + CAMPAIGN
    _, denied, _, _ = request(path, expected=(401,))
    if denied != {"error": "UNAUTHORIZED"}:
        raise RuntimeError("ANONYMOUS_JWT_NOT_DENIED")
    # Fail before Auth creation if project has no asymmetric signing keys.
    _, jwks, _, _ = request(SUPABASE + "/auth/v1/.well-known/jwks.json")
    if not isinstance(jwks, dict) or not any(
        isinstance(k, dict) and k.get("alg") in ("ES256", "RS256")
        for k in jwks.get("keys", [])
    ):
        raise RuntimeError("ASYMMETRIC_JWKS_NOT_AVAILABLE")
    marker = CANARY_PREFIX + uuid.uuid4().hex[:16]
    email = marker + "@example.invalid"
    password = secrets.token_urlsafe(32)
    uid = None
    try:
        _, account, _, _ = request(SUPABASE + "/auth/v1/admin/users",
            method="POST", data={"email":email,"password":password,"email_confirm":True},
            headers=admin_headers(key), expected=(200,201), timeout=25)
        if not isinstance(account, dict) or not isinstance(account.get("id"), str):
            raise RuntimeError("NO_TEST_USER_ID_FOR_SAFE_CLEANUP")
        uid = str(uuid.UUID(account["id"]))
        _, auth, _, _ = request(SUPABASE + "/auth/v1/token?grant_type=password",
            method="POST", data={"email":email,"password":password},
            headers={"apikey":pub}, expected=(200,), timeout=25)
        if not isinstance(auth, dict):
            raise RuntimeError("JWT_AUTH_RESPONSE_INVALID")
        signed = auth.get("access_token")
        claims = jwt_claims_for_local_shape_only(signed)
        if claims.get("sub") != uid:
            raise RuntimeError("JWT_ACTOR_MISMATCH")

        # This request must enter the genuine Node JWKS verification and the
        # user-token PostgREST RLS reader. No approved shop/campaign exists,
        # hence 404 rather than 401 (bad JWT) or 503 (gateway/DB failure).
        real_user = {"x-rgai-supabase-jwt": signed}
        timings = []
        for n in range(1, 6):
            _, body, meta, elapsed = request(path, headers=real_user,
                expected=(404,), timeout=20)
            if body != {"error":"NOT_FOUND"} or meta.get("X-RGAI-Secure-Adapter") != "read-only-v1":
                raise RuntimeError("SIGNED_JWT_NOT_ACCEPTED_BY_RLS_READ")
            timings.append(round(elapsed, 3))
        print("P0249_GENUINE_SIGNED_JWT_JWKS_RLS_READ=PASSED", flush=True)
        print("P0249_VALID_SIGNED_JWT_5_HTTP_404_LATENCIES=" +
              ",".join(str(value) for value in timings), flush=True)
        _, job_missing, _, _ = request(PREVIEW + "/api/render-jobs/" + CAMPAIGN,
                                      headers=real_user, expected=(404,))
        if job_missing != {"error": "NOT_FOUND"}:
            raise RuntimeError("PRIVATE_RENDER_JOB_RLS_NOT_ENFORCED")
        print("P0249_GENUINE_SIGNED_JWT_PRIVATE_JOB_DENIED=PASSED", flush=True)
        pieces = signed.split(".")
        signature = pieces[2]
        pieces[2] = ("A" if signature[0] != "A" else "B") + signature[1:]
        forged = ".".join(pieces)
        _, forged_response, _, _ = request(path,
            headers={"x-rgai-supabase-jwt":forged}, expected=(401,))
        if forged_response != {"error":"UNAUTHORIZED"}:
            raise RuntimeError("JWT_SIGNATURE_FORGERY_ACCEPTED")
        print("P0249_MODIFIED_SIGNATURE_REJECTED=PASSED", flush=True)
        print("P0249_REAL_JWT_PREVIEW_AUTH_READ_ONLY_ACCEPTANCE=PASSED", flush=True)
    finally:
        # No shop or media deletion: none were ever created by this canary.
        owner_only_cleanup(key, marker, uid)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        print("P0249_REAL_JWT_DEV_CANARY_FAILED=" + type(exc).__name__, file=sys.stderr)
        sys.exit(1)
