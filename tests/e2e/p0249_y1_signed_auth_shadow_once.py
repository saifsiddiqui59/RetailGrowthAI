#!/usr/bin/env python3
"""Short-lived *real* signed Supabase JWT test of isolated, temporary Y1 GET.

Two synthetic disposable Auth users, no shop, campaign, membership or customer
writes. Service-role credential is used ONLY in protected runner Auth admin
create/delete, never sent to Azure Function App or GitHub logs.
"""
import importlib.util
import json
import os
from pathlib import Path
import secrets
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[2]
UTIL = ROOT / "tests/e2e/p0249_dev_signed_jwt_read_once.py"
spec = importlib.util.spec_from_file_location("p0249_existing_signed_helper", UTIL)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

Y1 = "https://rgai-dev-y1-p0249-d4e5ddbd.azurewebsites.net"
SUPABASE = helper.SUPABASE
CAMPAIGN = "11111111-1111-4111-8111-111111111111"
PREFIX = helper.CANARY_PREFIX


def y1_read(token, *, campaign=CAMPAIGN):
    if campaign != CAMPAIGN:
        raise RuntimeError("Unexpected Y1 canary campaign path")
    req = urllib.request.Request(
        Y1 + "/api/campaigns/" + campaign, method="GET",
        headers={"Authorization": "Bearer " + token, "Cache-Control": "no-store"})
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=18) as response:
            status, headers, body = response.status, response.headers, response.read(4096)
    except urllib.error.HTTPError as response:
        status, headers, body = response.code, response.headers, response.read(4096)
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, False, None, 18.0
    try:
        parsed = json.loads(body) if body else None
    except (ValueError, UnicodeDecodeError):
        parsed = None
    return status, bool(headers.get("X-Request-ID")), parsed, round(time.monotonic()-started, 3)


def create_test_user(key, pub):
    marker = PREFIX + uuid.uuid4().hex[:16]
    password = secrets.token_urlsafe(32)
    email = marker + "@example.invalid"
    uid = None
    # Caller must clean up even if POST returned an uncertain ACK.
    try:
        _, account, _, _ = helper.request(
            SUPABASE + "/auth/v1/admin/users", method="POST",
            data={"email": email, "password": password, "email_confirm": True},
            headers=helper.admin_headers(key), expected=(200, 201), timeout=25)
        if not isinstance(account, dict) or not isinstance(account.get("id"), str):
            raise RuntimeError("Synthetic Auth create response missing ID")
        uid = str(uuid.UUID(account["id"]))
        _, auth, _, _ = helper.request(
            SUPABASE + "/auth/v1/token?grant_type=password", method="POST",
            data={"email": email, "password": password},
            headers={"apikey": pub}, expected=(200,), timeout=25)
        if not isinstance(auth, dict):
            raise RuntimeError("Synthetic sign-in response invalid")
        token = auth.get("access_token")
        claims = helper.jwt_claims_for_local_shape_only(token)
        if claims.get("sub") != uid:
            raise RuntimeError("Synthetic signed JWT subject mismatch")
        return marker, uid, token
    except BaseException:
        helper.owner_only_cleanup(key, marker, uid)
        raise


def main():
    if os.environ.get("RGAI_DEV_P0249_JWT_CANARY_APPROVAL") != "OWNER_APPROVED_READ_ONLY_JWT_TEST":
        raise RuntimeError("Missing exact DEV synthetic signed test approval")
    key = os.environ.get("RGAI_DEV_SERVICE_KEY", "")
    pub = os.environ.get("RGAI_DEV_P0249_PUBLISHABLE_KEY", "")
    if (not key.startswith(("sb_secret_", "eyJ")) or len(key) < 40 or
        pub != helper.PUBLIC):
        raise RuntimeError("Wrong DEV Supabase key class")
    # Deny before creating any account if the original shadow is not enabled:
    # flag-OFF handlers return 503 to a well-formed dummy bearer. No token logs.
    status, _, _, _ = y1_read("fake-but-wellformed-jwt")
    if status != 401:
        # Once active, invalid JWT should always be a marked 401.
        raise RuntimeError("Y1 original auth route is unavailable")
    _, jwks, _, _ = helper.request(
        SUPABASE + "/auth/v1/.well-known/jwks.json", expected=(200,))
    if not any(isinstance(j, dict) and j.get("alg") in ("ES256", "RS256")
               for j in (jwks or {}).get("keys", [])):
        raise RuntimeError("Project asymmetric JWKS unavailable")

    created = []
    try:
        for i in range(2):
            marker, uid, token = create_test_user(key, pub)
            created.append((marker, uid))
            for n in range(3):
                code, marked, payload, sec = y1_read(token)
                if (code != 404 or not marked or
                    payload != {"error": "NOT_FOUND"} or sec >= 18):
                    raise RuntimeError("Valid signed DEV user did not pass original Y1 auth")
                print(f"P0249_Y1_REAL_SIGNED_USER={i+1} GET={n+1} HTTP404_MARKED=PASS SECONDS={sec}",flush=True)
            pieces = token.split(".")
            signature = pieces[2]
            pieces[2] = ("A" if signature[:1] != "A" else "B") + signature[1:]
            code, marked, payload, sec = y1_read(".".join(pieces))
            if code != 401 or not marked or payload != {"error": "UNAUTHORIZED"}:
                raise RuntimeError("Forged JWT not rejected by original Y1 verifier")
            print(f"P0249_Y1_REAL_USER={i+1} FORGED_SIGNATURE=DENIED",flush=True)
        print("P0249_Y1_REAL_SUPABASE_SIGNED_USERS=2_OF_2_ACCEPTED_NO_SHOP_DATA",flush=True)
    finally:
        failures = 0
        for marker, uid in reversed(created):
            try:
                helper.owner_only_cleanup(key, marker, uid)
            except Exception:
                failures += 1
        if failures:
            raise RuntimeError("Critical: disposable Auth user cleanup incomplete")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("P0249_Y1_REAL_SIGNED_TEST_FAILED_OR_CLEANUP_NEEDED",file=sys.stderr)
        raise SystemExit(5)
