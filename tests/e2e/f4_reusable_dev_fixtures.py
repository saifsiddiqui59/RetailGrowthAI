#!/usr/bin/env python3
"""Reusable DEV-only test identities and ordinary signed shop bootstrap.

No customer account, platform privilege, approval change, SQL, paid calls or
fixture cleanup. Credentials are random, private and only rotated for these
exact Auth Admin-marked identities. Refuse unmarked pre-existing identities.
"""
import os
import secrets
import sys
import uuid
from urllib.parse import urlencode

import p0249_dev_signed_jwt_read_once as helper

ACCOUNTS = (
    ("a", "rgai-owner-test@retailgrowth.test", "Synthetic Boutique A"),
    ("b", "rgai-editor-test@retailgrowth.test", "Synthetic Boutique B"),
)
CONFIRM = "OWNER-AUTHORIZED-REUSABLE-DEV-F4-FIXTURES"
MARK = "retailgrowthai-f4-two-shop-v1"


def require(condition, category):
    if not condition:
        raise RuntimeError(category)


def canonical(value):
    result = str(uuid.UUID(value))
    require(result == value, "INVALID_UUID")
    return result


def preflight(env):
    require(env.get("GITHUB_ACTIONS") == "true"
            and env.get("GITHUB_REPOSITORY") == "saifsiddiqui59/RetailGrowthAI"
            and env.get("GITHUB_REF") == "refs/heads/main"
            and env.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
            and env.get("RGAI_REUSABLE_FIXTURES_CONFIRM") == CONFIRM
            and env.get("RGAI_DEV_PUBLISHABLE_KEY") == helper.PUBLIC,
            "PROTECTED_DEV_GUARD")
    key = env.get("RGAI_DEV_SERVICE_KEY", "")
    require(len(key) >= 40, "MISSING_DEV_ADMIN_KEY")
    helper.admin_headers(key)
    return key


def admin(key, path, method="GET", data=None, expected=(200,)):
    return helper.request(helper.SUPABASE + "/auth/v1/admin/users" + path,
                          method=method, data=data, headers=helper.admin_headers(key),
                          expected=expected, timeout=25)[1]


def verify_account(row, email, uid=None):
    require(isinstance(row, dict) and row.get("email") == email
            and row.get("role") == "authenticated"
            and row.get("is_anonymous") is not True, "AUTH_IDENTITY_MISMATCH")
    metadata = row.get("app_metadata")
    require(isinstance(metadata, dict)
            and metadata.get("rgai_test_account") is True
            and metadata.get("rgai_env") == "DEV"
            and metadata.get("rgai_fixture") == MARK,
            "UNMARKED_OR_NONDEV_ACCOUNT_REFUSED")
    result = canonical(row.get("id"))
    require(uid is None or result == uid, "AUTH_IDENTITY_CHANGED")
    return result


def inventory(key):
    matches = {}
    emails = {email for _, email, _ in ACCOUNTS}
    for page in range(1, 21):
        data = admin(key, "?" + urlencode({"page": page, "per_page": 50}))
        require(isinstance(data, dict) and isinstance(data.get("users"), list),
                "AUTH_INVENTORY_UNVERIFIABLE")
        users = data["users"]
        for row in users:
            if isinstance(row, dict) and row.get("email") in emails:
                email = row["email"]
                require(email not in matches, "DUPLICATE_FIXTURE_EMAIL")
                matches[email] = verify_account(row, email)
        next_page = data.get("next_page")
        if next_page not in (None, 0, ""):
            require(type(next_page) is int and next_page == page + 1,
                    "AUTH_PAGINATION_INVALID")
            continue
        if "next_page" in data or len(users) < 50:
            return matches
    raise RuntimeError("AUTH_INVENTORY_LIMIT")


def user_call(bearer, path, method="GET", data=None, expected=(200,)):
    return helper.request(helper.SUPABASE + path, method=method, data=data,
                          headers=bearer, expected=expected, timeout=25)[1]


def sign_in(email, password, uid):
    auth = helper.request(helper.SUPABASE + "/auth/v1/token?grant_type=password",
                          method="POST", data={"email": email, "password": password},
                          headers={"apikey": helper.PUBLIC}, expected=(200,), timeout=25)[1]
    require(isinstance(auth, dict) and isinstance(auth.get("access_token"), str),
            "LOGIN_NO_TOKEN")
    token = auth["access_token"]
    claims = helper.jwt_claims_for_local_shape_only(token)
    require(claims.get("sub") == uid, "LOGIN_WRONG_USER")
    bearer = {"apikey": helper.PUBLIC, "Authorization": "Bearer " + token}
    verify_account(user_call(bearer, "/auth/v1/user"), email, uid)
    return bearer


def provision(key, existing, email):
    password = secrets.token_urlsafe(36)
    if email in existing:
        uid = existing[email]
        verify_account(admin(key, "/" + uid), email, uid)
        # Only this exact dedicated fixture is rotated. Never touch real users.
        verify_account(admin(key, "/" + uid, method="PUT",
                             data={"password": password}), email, uid)
    else:
        # If POST acknowledgement is lost, fail; next authorized run must
        # reconcile exact admin inventory before attempting another create.
        row = admin(key, "", method="POST",
                    data={"email": email, "password": password, "email_confirm": True,
                          "app_metadata": {"rgai_test_account": True, "rgai_env": "DEV",
                                           "rgai_fixture": MARK}}, expected=(200, 201))
        uid = verify_account(row, email)
    verify_account(admin(key, "/" + uid), email, uid)
    bearer = sign_in(email, password, uid)
    return uid, bearer


def shop_id(uid):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, MARK + ":" + uid))


def memberships(bearer):
    rows = user_call(bearer, "/rest/v1/shop_memberships?select=shop_id,role,active&limit=3")
    require(isinstance(rows, list) and len(rows) <= 1, "UNEXPECTED_SHOP_MEMBERSHIPS")
    return rows


def validate_memberships(bearer, sid):
    rows = memberships(bearer)
    if rows:
        row = rows[0]
        require(row == {"shop_id": sid, "role": "OWNER", "active": True},
                "FOREIGN_OR_INACTIVE_MEMBERSHIP_REFUSED")
    return bool(rows)


def read_shop(bearer, sid):
    rows = user_call(bearer, "/rest/v1/shops?" + urlencode({
        "id": "eq." + sid, "select": "id,name,slug,owner_user_id", "limit": 2}))
    require(isinstance(rows, list) and len(rows) <= 1, "SHOP_RLS_RESPONSE_INVALID")
    return rows


def expected_shop(slot, name, uid):
    return {"id": shop_id(uid), "name": name, "slug": "rgai-f4-fixture-" + slot,
            "owner_user_id": uid}


def provision_shop(bearer, expected):
    sid = expected["id"]
    member = validate_memberships(bearer, sid)
    rows = read_shop(bearer, sid)
    if member or rows:
        require(member and rows == [expected], "EXISTING_FIXTURE_SHOP_MISMATCH")
    else:
        status = user_call(bearer, "/rest/v1/rpc/retail_onboarding_status",
                           method="POST", data={})
        require(isinstance(status, dict) and status.get("status") == "APPROVED",
                "NORMAL_ONBOARDING_APPROVAL_REQUIRED")
        # Ordinary authenticated INSERT; all server policies stay in force.
        user_call({**bearer, "Prefer": "return=minimal"}, "/rest/v1/shops",
                  method="POST", data={**expected, "timezone": "Asia/Kolkata"},
                  expected=(201, 204))
    require(validate_memberships(bearer, sid) and read_shop(bearer, sid) == [expected],
            "OWN_SHOP_RLS_UNVERIFIED")


def main():
    key = preflight(os.environ)
    existing = inventory(key)
    subjects = []
    try:
        for slot, email, name in ACCOUNTS:
            uid, bearer = provision(key, existing, email)
            expected = expected_shop(slot, name, uid)
            validate_memberships(bearer, expected["id"])
            subjects.append((bearer, expected))
            print("F4_REUSABLE_AUTH_" + slot.upper() + "=PASS", flush=True)
        require(subjects[0][1]["owner_user_id"] != subjects[1][1]["owner_user_id"],
                "DISTINCT_FIXTURE_USERS_REQUIRED")
        print("F4_REUSABLE_TWO_AUTH_ACCOUNTS_RETAINED=true", flush=True)
        # Preflight both normal onboarding states before either new shop write.
        for bearer, expected in subjects:
            if not validate_memberships(bearer, expected["id"]):
                state = user_call(bearer, "/rest/v1/rpc/retail_onboarding_status",
                                  method="POST", data={})
                require(isinstance(state, dict) and state.get("status") == "APPROVED",
                        "NORMAL_ONBOARDING_APPROVAL_REQUIRED")
        for bearer, expected in subjects:
            provision_shop(bearer, expected)
        for i in range(2):
            bearer, _ = subjects[i]
            require(read_shop(bearer, subjects[1-i][1]["id"]) == [],
                    "CROSS_TENANT_SHOP_LEAK")
        print("F4_REUSABLE_TWO_ISOLATED_SHOPS=PASS", flush=True)
        print("F4_FIXTURE_USERS_AND_SHOPS_RETAINED=true", flush=True)
    finally:
        # Release sessions; identities and shops intentionally stay available.
        for bearer, _ in subjects:
            user_call(bearer, "/auth/v1/logout?scope=local", method="POST",
                      expected=(200, 204))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Only fixed internal status codes, not external response text.
        reason = str(exc)
        if reason == "NORMAL_ONBOARDING_APPROVAL_REQUIRED":
            print("F4_REUSABLE_SHOPS=BLOCKED_NORMAL_ONBOARDING", file=sys.stderr)
        else:
            print("F4_REUSABLE_FIXTURE_RUN=FAILED_OR_BLOCKED", file=sys.stderr)
        raise SystemExit(2)
