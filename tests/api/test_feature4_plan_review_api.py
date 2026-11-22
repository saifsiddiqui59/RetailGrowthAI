"""F2→F4 real retailer creative-review HTTP boundary negative tests.

Offline RLS fakes test the Python JWT router. Actual signed tenant data and
immutability are independently covered by disposable PostgreSQL SQL tests.
No GitHub reviewer, paid render or synthetic-auto-approval shortcut.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
from http_api import HTTPAPI  # noqa: E402
from feature4_plan_review_api import Feature4PlanReviewAPI  # noqa: E402
from security import AuthenticationError  # noqa: E402

SHOP = "11111111-1111-4111-8111-111111111111"
OTHER_SHOP = "22222222-2222-4222-8222-222222222222"
PLAN = "33333333-3333-4333-8333-333333333333"
CAMPAIGN = "44444444-4444-4444-8444-444444444444"
USER = "55555555-5555-4555-8555-555555555555"
FOREIGN = "66666666-6666-4666-8666-666666666666"
VIEWER = "77777777-7777-4777-8777-777777777777"
DIGEST = "a" * 64
REVIEW = "b" * 64


class RLSFake:
    def __init__(self):
        self.active = True
        self.reviews = 0
        self.revocations = 0
        self.db_revoke = True
        self.db_review_denied = False
        self.data = {
            "id": PLAN, "shop_id": SHOP, "campaign_id": CAMPAIGN,
            "proposal": {"version": "creative_direction_v1",
                         "approved": False, "scenes": []},
            "proposal_sha256": DIGEST,
            "state": "DRAFT", "review_sha256": None,
            "approved_direction": None,
        }

    def feature4_creative_plan(self, token, user_id, plan_id):
        assert plan_id == PLAN
        return self.data if self.active and token in ("owner", "viewer") else None

    def member(self, token, user_id, shop_id, *, write=False):
        if not self.active or shop_id != SHOP:
            return False
        return token == "owner" or (token == "viewer" and not write)

    def feature4_review_cpu_plan(self, token, plan_id, digest):
        assert token == "owner" and plan_id == PLAN and digest == DIGEST
        self.reviews += 1
        if self.db_review_denied:
            return None
        return {"approval_id": PLAN, "shop_id": SHOP,
                "campaign_id": CAMPAIGN, "review_hash": REVIEW,
                "status": "APPROVED"}

    def feature4_revoke_cpu_plan(self, token, plan_id):
        assert token == "owner" and plan_id == PLAN
        self.revocations += 1
        return self.db_revoke


def verify(token):
    result = {"owner": USER, "foreign": FOREIGN, "viewer": VIEWER}.get(token)
    if result is None:
        raise AuthenticationError("missing or bad signature")
    return result


def setup(*, enabled=True):
    store = RLSFake()
    api = HTTPAPI(verify, store,
                  feature4_review_api=Feature4PlanReviewAPI(store)
                  if enabled else None)
    return api, store


def test_creative_review_routes_default_off_and_jwt_verified_before_503():
    api, store = setup(enabled=False)
    for method, path, body in [
        ("GET", f"/feature4-creative-plans/{PLAN}", None),
        ("POST", f"/feature4-creative-plans/{PLAN}/review",
         {"expected_source_sha256": DIGEST}),
        ("POST", f"/feature4-creative-plans/{PLAN}/revoke", {}),
    ]:
        assert api.handle(method, path, "Bearer forged", body) == (
            401, {"error": "UNAUTHORIZED"})
        assert api.handle(method, path, "Bearer owner", body) == (
            503, {"error": "FEATURE4_REVIEW_DISABLED"})
    assert store.reviews == store.revocations == 0


def test_owner_can_read_and_review_exact_persisted_f2_source_not_browser_copy():
    api, store = setup()
    path = f"/feature4-creative-plans/{PLAN}"
    code, item = api.handle("GET", path, "Bearer owner")
    assert code == 200 and item["proposal_sha256"] == DIGEST
    assert item["proposal"]["approved"] is False
    assert item["status"] == "DRAFT"
    assert item["shop_id"] == SHOP
    assert api.handle("POST", path + "/review", "Bearer owner",
                      {"expected_source_sha256": DIGEST}) == (
        200, {"plan_id": PLAN, "shop_id": SHOP,
              "campaign_id": CAMPAIGN, "review_hash": REVIEW,
              "status": "APPROVED"})
    assert store.reviews == 1


def test_bad_format_foreign_viewer_or_revoked_never_approve_or_revoke():
    api, store = setup()
    path = f"/feature4-creative-plans/{PLAN}"
    assert api.handle("GET", path, "Bearer foreign")[0] == 404
    assert api.handle("POST", path + "/review", "Bearer foreign",
                      {"expected_source_sha256": DIGEST})[0] == 404
    assert api.handle("POST", path + "/revoke", "Bearer foreign", {})[0] == 404
    assert api.handle("GET", path, "Bearer viewer")[0] == 200
    assert api.handle("POST", path + "/review", "Bearer viewer",
                      {"expected_source_sha256": DIGEST})[0] == 403
    assert api.handle("POST", path + "/revoke", "Bearer viewer", {})[0] == 403
    for data in (
        {}, {"expected_source_sha256": "0"},
        {"expected_source_sha256": DIGEST, "approved": True},
        {"expected_source_sha256": ["a" * 64]},
        {"expected_source_sha256": "c" * 64},
    ):
        assert api.handle("POST", path + "/review", "Bearer owner", data)[0] in (400, 404)
    assert store.reviews == store.revocations == 0
    store.active = False
    assert api.handle("GET", path, "Bearer owner")[0] == 404
    assert api.handle("POST", path + "/review", "Bearer owner",
                      {"expected_source_sha256": DIGEST})[0] == 404


def test_sql_revocation_receipt_and_current_membership_fail_closed():
    api, store = setup()
    path = f"/feature4-creative-plans/{PLAN}"
    store.db_review_denied = True
    assert api.handle("POST", path + "/review", "Bearer owner",
                      {"expected_source_sha256": DIGEST}) == (
                          409, {"error": "REVIEW_STALE_OR_DENIED"})
    store.db_revoke = False
    assert api.handle("POST", path + "/revoke", "Bearer owner", {}) == (
        409, {"error": "REVOKE_DENIED_OR_STALE"})
    store.db_revoke = True
    assert api.handle("POST", path + "/revoke", "Bearer owner", {}) == (
        200, {"plan_id": PLAN, "shop_id": SHOP, "status": "REVOKED"})
    assert store.revocations == 2


def test_no_malformed_review_route_or_method_will_call_any_sql_rpc():
    api, store = setup()
    for method, path in [
        ("POST", f"/feature4-creative-plans/{PLAN}"),
        ("GET", f"/feature4-creative-plans/{PLAN}/review"),
        ("PUT", f"/feature4-creative-plans/{PLAN}/revoke"),
        ("POST", f"/feature4-creative-plans/{PLAN}/download"),
        ("POST", f"/feature4-creative-plans/{PLAN}/review/again"),
    ]:
        assert api.handle(method, path, "Bearer owner", {})[0] == 404
    assert api.handle("GET", "/feature4-creative-plans/not-uuid",
                      "Bearer owner")[0] == 400
    assert store.reviews == store.revocations == 0
