"""Real F2 plan → proposed atomic adapter via authenticated v2 HTTP source router.

In-memory backend: proves code wiring and denials, NOT real Supabase RLS,
billing/outbox, Azure Functions registration, customer footage or hosted E2E.
"""
import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
sys.path.insert(0, str(ROOT / "video-engine"))
sys.path.insert(0, str(ROOT / "tests" / "media"))

from http_api import HTTPAPI  # noqa: E402
from feature4_http_handoff import Feature4HTTP  # noqa: E402
from feature2_feature4_intake import Feature4ApprovedPlanIntake  # noqa: E402
from test_feature2_feature4_intake import make, FakeAtomicStore, USER  # noqa: E402
from security import AuthenticationError  # noqa: E402

SHOP = "11111111-1111-4111-8111-111111111111"
CAMPAIGN = "22222222-2222-4222-8222-222222222222"
JOB = "33333333-3333-4333-8333-333333333333"
FOREIGN = "44444444-4444-4444-8444-444444444444"


class UserRLS:
    """Fake current JWT membership for wiring only; real JWT/RLS is pending."""
    def __init__(self):
        self.can_write = True
    def campaign(self, token, user_id, campaign_id):
        if token == "signed-shop" and user_id == USER and campaign_id == CAMPAIGN:
            return {"shop_id": SHOP, "id": CAMPAIGN, "status": "DRAFT"}
        return None
    def member(self, token, user_id, shop_id, *, write=False):
        return (token == "signed-shop" and user_id == USER
                and shop_id == SHOP and self.can_write)
    def feature4_job(self, token, user_id, job_id):
        if (token == "signed-shop" and user_id == USER and
                job_id == JOB and self.can_write):
            return {"id": JOB, "shop_id": SHOP, "status": "QUEUED"}
        return None


def setup():
    direction, snapshot, item = make()
    store = FakeAtomicStore(direction, snapshot)
    users = UserRLS()
    def verify(token):
        if token == "signed-shop":
            return USER
        if token == "signed-foreign":
            return FOREIGN
        raise AuthenticationError("invalid JWT")
    api = HTTPAPI(verify, users,
                  feature4_api=Feature4HTTP(
                      users, Feature4ApprovedPlanIntake(store)))
    body = {key: copy.deepcopy(item[key])
            for key in ("shop_id", "campaign_id", "approval_id", "draft")}
    return api, users, store, body


def test_approved_f2_direction_exact_script_reaches_F4_request_through_real_router():
    api, _, store, body = setup()
    path = f"/campaigns/{CAMPAIGN}/feature4-renders"
    status, receipt = api.handle("POST", path, "Bearer signed-shop", body)
    assert status == 202
    assert receipt == {"shop_id": SHOP, "job_id": JOB, "status": "QUEUED"}
    assert store.writes == 1
    assert store.compiled["request"]["version"] == "creative_reel_v1"
    assert store.compiled["request"]["script"]["approved_text"]
    assert store.compiled["request"]["scenes"][0]["headline"] == (
        body["draft"]["scenes"][0]["headline"])
    assert store.compiled["approved_draft"] == body["draft"]
    assert api.handle("POST", path, "Bearer signed-shop", body) == (202, receipt)
    assert store.writes == 1


def test_revised_plan_foreign_user_revoked_grant_never_reserve_or_sign():
    api, users, store, body = setup()
    path = f"/campaigns/{CAMPAIGN}/feature4-renders"
    assert api.handle("POST", path, "Bearer forged", body)[0] == 401
    assert api.handle("POST", path, "Bearer signed-foreign", body)[0] == 404
    users.can_write = False
    assert api.handle("POST", path, "Bearer signed-shop", body)[0] == 403
    users.can_write = True
    store.rights_revoked = True
    assert api.handle("POST", path, "Bearer signed-shop", body)[0] != 202
    store.rights_revoked = False
    changed = copy.deepcopy(body)
    changed["draft"]["scenes"][0]["headline"] = "UNAPPROVED FREE OFFER"
    assert api.handle("POST", path, "Bearer signed-shop", changed)[0] == 400
    store.direction["scenes"][0]["headline"] = "UNAPPROVED CHANGE"
    assert api.handle("POST", path, "Bearer signed-shop", body)[0] != 202
    assert store.writes == 0


def test_status_never_exposes_foreign_and_disabled_route_remains_off():
    api, users, store, body = setup()
    path = f"/feature4-render-jobs/{JOB}"
    assert api.handle("GET", path, "Bearer signed-foreign")[0] == 404
    assert api.handle("GET", path + "/download", "Bearer signed-foreign")[0] == 404
    assert api.handle("GET", path, "Bearer signed-shop")[0] == 200
    users.can_write = False
    assert api.handle("GET", path, "Bearer signed-shop")[0] == 404
    assert store.writes == 0
