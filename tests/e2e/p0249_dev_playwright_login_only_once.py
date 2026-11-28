#!/usr/bin/env python3
"""Protected RetailGrowthAI DEV two-user Playwright sign-in without shop grants.

Makes only temporary Supabase Auth Admin create/delete requests. Never bypasses
retailer onboarding or tests Y1 shop RLS; full E2E remains a separate gate.
"""
import hashlib
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import uuid

import p0249_dev_signed_jwt_read_once as helper

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'frontend/e2e/dev-canary-auth-login-only.mjs'


def test_marker(slot):
    run = os.environ.get('GITHUB_RUN_ID', '')
    attempt = os.environ.get('GITHUB_RUN_ATTEMPT', '')
    if slot not in (0, 1) or not re.fullmatch(r'[0-9]{1,20}', run) or not re.fullmatch(r'[0-9]{1,8}', attempt):
        raise RuntimeError('UNSAFE_RUN_BOUND_TEST_ID')
    # Compatible with existing exact-identity, paginated Auth Admin cleanup.
    digest = hashlib.sha256(f'p0249-auth-login:{run}:{attempt}:{slot}'.encode()).hexdigest()[:16]
    return helper.CANARY_PREFIX + digest


def preflight():
    if (os.environ.get('GITHUB_ACTIONS') != 'true' or
            os.environ.get('GITHUB_REPOSITORY') != 'saifsiddiqui59/RetailGrowthAI' or
            os.environ.get('GITHUB_REF') != 'refs/heads/main' or
            os.environ.get('GITHUB_EVENT_NAME') != 'workflow_dispatch' or
            os.environ.get('RGAI_DEV_CANARY_APPROVAL') != 'AUTHORIZED_RETAILGROWTHAI_DEV_ONLY' or
            os.environ.get('RGAI_DEV_LOGIN_ONLY') != '1'):
        raise RuntimeError('PROTECTED_DEV_LOGIN_ONLY_GUARD')
    key = os.environ.get('RGAI_DEV_SERVICE_KEY', '')
    pub = os.environ.get('RGAI_DEV_PUBLISHABLE_KEY', '')
    if (not (key.startswith('sb_secret_') or (key.startswith('eyJ') and key.count('.') == 2)) or
            len(key) < 40 or pub != helper.PUBLIC or not SCRIPT.is_file()):
        raise RuntimeError('DEV_CREDENTIAL_CLASS_OR_SCRIPT_MISMATCH')
    return key, pub


def create_user(key, marker):
    password = secrets.token_urlsafe(32)
    email = marker + '@example.invalid'
    _, account, _, _ = helper.request(
        helper.SUPABASE + '/auth/v1/admin/users', method='POST',
        data={'email': email, 'password': password, 'email_confirm': True},
        headers=helper.admin_headers(key), expected=(200, 201), timeout=25)
    if not isinstance(account, dict) or account.get('email') != email:
        raise RuntimeError('TEST_AUTH_CREATE_IDENTITY_MISMATCH')
    uid = str(uuid.UUID(account.get('id', '')))
    if uid != account['id']:
        raise RuntimeError('TEST_AUTH_CREATE_UUID_MISMATCH')
    return uid, email, password


def browser_login(accounts):
    # Child receives no service-role key, no secret-file path and no Azure OIDC.
    safe_env = {k: os.environ[k] for k in ('PATH', 'HOME', 'TMPDIR') if os.environ.get(k)}
    safe_env.update({
        'GITHUB_ACTIONS': 'true',
        'RGAI_DEV_CANARY_APPROVAL': 'AUTHORIZED_RETAILGROWTHAI_DEV_ONLY',
        'RGAI_DEV_LOGIN_ONLY': '1',
        'RGAI_DEV_LOGIN_A_EMAIL': accounts[0][1],
        'RGAI_DEV_LOGIN_A_PASSWORD': accounts[0][2],
        'RGAI_DEV_LOGIN_B_EMAIL': accounts[1][1],
        'RGAI_DEV_LOGIN_B_PASSWORD': accounts[1][2],
    })
    result = subprocess.run(
        ['node', str(SCRIPT)], cwd=ROOT, env=safe_env, capture_output=True,
        text=True, timeout=200, check=False)
    expected = {
        f'P0249_PLAYWRIGHT_REAL_AUTH_{phase}_USER_{n}=PASS'
        for phase in ('LOGIN', 'LOGOUT') for n in (1, 2)
    }
    lines = set(result.stdout.splitlines())
    if result.returncode != 0 or not expected.issubset(lines) or \
            'P0249_PLAYWRIGHT_TWO_DISPOSABLE_AUTH_LOGINS=PASS' not in lines:
        # Never dump stderr, stdout, browser snapshots or protected identity.
        raise RuntimeError('REAL_BROWSER_AUTH_ONLY_FAILED')
    print('P0249_PLAYWRIGHT_TWO_REAL_DEV_LOGINS_AND_LOGOUTS=PASS', flush=True)


def main():
    key, _ = preflight()
    markers = []
    accounts = []
    clean = False
    try:
        for i in (0, 1):
            marker = test_marker(i)
            # Record only attempted creates; never clean up an unattempted slot.
            markers.append((marker, None))
            uid, email, password = create_user(key, marker)
            markers[-1] = (marker, uid)
            accounts.append((uid, email, password))
        browser_login(accounts)
        clean = True
    finally:
        failures = 0
        for marker, uid in reversed(markers):
            try:
                helper.owner_only_cleanup(key, marker, uid)
            except Exception:
                failures += 1
        if failures:
            raise RuntimeError('DISPOSABLE_AUTH_ONLY_CLEANUP_INCOMPLETE')
        print('P0249_PLAYWRIGHT_TEMP_AUTH_CLEANUP=PASS', flush=True)
    if clean:
        print('P0249_PLAYWRIGHT_AUTH_ONLY=PASS_NOT_SHOP_RLS_OR_Y1_WRITE', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('P0249_PLAYWRIGHT_AUTH_ONLY=FAILED_OR_BLOCKED', file=sys.stderr)
        raise SystemExit(5)
