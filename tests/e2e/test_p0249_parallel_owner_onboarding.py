"""Offline regressions for the ROOT-gated two temporary DEV shop-owner canary.

No live Supabase, Auth, emails, private media, or ROOT decision is executed.
Fixtures are intentionally distinct from production and real users.
"""
import importlib.util
from pathlib import Path

import pytest


SOURCE = Path(__file__).with_name("retail_dev_canary_once.py")
SPEC = importlib.util.spec_from_file_location("retail_dev_canary_once", SOURCE)
canary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(canary)
MARKER = "012345abcdef"
UIDS = [
    "11111111-1111-4111-8111-111111111111",
    "22222222-2222-4222-8222-222222222222",
]
EMAILS = [f"rgai-canary-{MARKER}-{x}@example.invalid" for x in "ab"]


def test_both_auth_users_are_staged_with_no_owner_role_or_shop_grant(capsys):
    operations = []
    accounts = []
    def send(url, *, method, payload, headers, expect):
        assert method == "POST"
        operations.append((url, payload.copy()))
        if url.endswith("/auth/v1/admin/users"):
            assert payload == {"email": EMAILS[len(operations)//2],
                               "password": "synthetic-fixture-password-is-long-enough",
                               "email_confirm": True}
            assert headers == {"test": "service-in-memory"}
            return 201, {"id": UIDS[len(operations)//2]}
        assert url.endswith("/auth/v1/token?grant_type=password")
        assert payload["email"] in EMAILS
        return 200, {"access_token": "synthetic-local-jwt-fixture"}
    first = canary.stage_two_root_gated_accounts(
        marker=MARKER, admins={"test": "service-in-memory"},
        pub="fake-local-publishable", accounts=accounts, send=send,
        password_factory=lambda: "synthetic-fixture-password-is-long-enough")
    assert first == "synthetic-fixture-password-is-long-enough"
    assert [x[0] for x in accounts] == UIDS
    assert [x[1]["Authorization"] for x in accounts] == ["Bearer synthetic-local-jwt-fixture"] * 2
    assert [x[0].split("/")[-1] for x in operations] == ["users", "token?grant_type=password",
                                                           "users", "token?grant_type=password"]
    assert all("/shops" not in url and "review_onboarding" not in url
               for url, _payload in operations)
    assert "CANARY_TWO_DISPOSABLE_AUTH_USERS_STAGED=true" in capsys.readouterr().out
    assert not any("service_role" in str(payload) for _,payload in operations)


def test_partial_second_auth_failure_keeps_both_ids_for_exact_cleanup():
    accounts = []
    created = 0
    def send(url, *, method, payload, headers, expect):
        nonlocal created
        if url.endswith("/admin/users"):
            created += 1
            return 201, {"id": UIDS[created - 1]}
        if payload["email"] == EMAILS[1]:
            raise RuntimeError("synthetic auth token error, no session")
        return 200, {"access_token": "fake-access"}
    with pytest.raises(RuntimeError, match="synthetic auth token error"):
        canary.stage_two_root_gated_accounts(
            marker=MARKER, admins={}, pub="fixture", accounts=accounts, send=send,
            password_factory=lambda: "synthetic-fixture-password-is-long-enough")
    assert accounts[0][0] == UIDS[0]
    assert accounts[1] == UIDS[1]  # cleanup still knows user B without a JWT


def test_both_pending_are_visible_in_same_round_and_approvable_in_reverse_order(capsys):
    accounts = [(uid, {"Authorization": "Bearer " + uid}) for uid in UIDS]
    polls = [[], []]
    waits = []
    responses = iter([
        "PENDING", "PENDING",
        "PENDING", "APPROVED",  # B approved first
        "APPROVED", "APPROVED",
    ])
    def send(url, *, method, payload, headers, expect):
        assert url.endswith("/rest/v1/rpc/retail_onboarding_status")
        assert method == "POST" and payload == {}
        index = UIDS.index(headers["Authorization"][7:])
        polls[index].append(headers["Authorization"])
        return 200, {"status": next(responses)}
    canary.wait_for_both_root_approvals(accounts, send=send,
                                        sleep=lambda seconds: waits.append(seconds),
                                        attempts=3)
    assert [len(x) for x in polls] == [3, 3]
    assert waits == [4, 4]
    log = capsys.readouterr().out
    assert "CANARY_WAITING_FOR_TWO_EXPLICIT_DEV_OPERATOR_APPROVALS=true" in log
    assert "CANARY_BOTH_OPERATOR_APPROVALS_VERIFIED=true" in log
    assert not any("Bearer " in line for line in log.splitlines())


@pytest.mark.parametrize("unexpected", ["REJECTED", "UNKNOWN", None, "", True])
def test_unknown_or_rejected_status_denies_shop_creation(unexpected):
    accounts = [(uid, {"Authorization": "Bearer synthetic"}) for uid in UIDS]
    queries = []
    def send(url, **kwargs):
        queries.append(url)
        return 200, {"status": unexpected}
    with pytest.raises(RuntimeError, match="onboarding was rejected"):
        canary.wait_for_both_root_approvals(accounts, send=send, sleep=lambda s: None,
                                             attempts=3)
    assert len(queries) == 1
    assert all("/shops" not in url for url in queries)


def test_approval_timeout_is_one_bounded_window_not_two_sequential_waits():
    accounts = [(uid, {"Authorization": "Bearer synthetic"}) for uid in UIDS]
    count = 0
    def send(url, **kwargs):
        nonlocal count
        count += 1
        return 200, {"status": "PENDING"}
    with pytest.raises(RuntimeError, match="Both DEV test fixtures were not approved"):
        canary.wait_for_both_root_approvals(accounts, send=send,
                                             sleep=lambda _seconds: None, attempts=4)
    assert count == 8  # 2 statuses per round; no 2x serialized 5-minute wait


def test_main_preserves_gateway_preflight_and_keeps_shops_after_both_root_approvals():
    source = SOURCE.read_text(encoding="utf-8")
    main = source.split("\ndef main():\n", 1)[1]
    preflight = main.index("preflight_dev_http_auth_routes(include_prompt=prompt_only)")
    staged = main.index("account_password_a = stage_two_root_gated_accounts(")
    approved = main.index("wait_for_both_root_approvals(accounts)")
    shop = main.index('call(SUPABASE+"/rest/v1/shops",')
    assert preflight < staged < approved < shop
    assert main.index("shops.append(sid)", approved) < shop
    assert "finally:" in main and '"/auth/v1/admin/users/"+uid' in main
    assert "CANARY_TWO_DISPOSABLE_AUTH_USERS_STAGED=true" in source
    assert "CANARY_BOTH_OPERATOR_APPROVALS_VERIFIED=true" in source
    assert "service_role" not in source.split("\ndef main():\n")[0].lower()
