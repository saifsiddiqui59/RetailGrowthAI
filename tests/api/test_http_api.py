"""Negative API tests use per-user token and fake RLS store; no hosted resources."""
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from http_api import HTTPAPI

USER_A, USER_B, SHOP_A, SHOP_B, ASSET_A = [str(uuid4()) for _ in range(5)]
CID = str(uuid4())


def request(shop=SHOP_A):
    return {"shop_id": shop, "brief": "Seven days of fresh styling ideas",
            "duration_days": 7, "start_date": "2026-11-01", "timezone": "Asia/Kolkata",
            "language": "en-IN", "platforms": ["linkedin", "instagram"],
            "media_asset_ids": [ASSET_A], "offer": None}


class FakeStore:
    def __init__(self):
        self.saved = []
        self.failed = []
        self.member_calls = []
        self.result = None

    def member(self, token, user, shop, *, write=False):
        self.member_calls.append((token, user, shop, write))
        return token == "signed-A" and user == USER_A and shop == SHOP_A

    def assets(self, token, shop, asset_ids):
        return token == "signed-A" and shop == SHOP_A and asset_ids == (ASSET_A,)

    def campaign(self, token, user, cid):
        return self.result if token == "signed-A" and user == USER_A and cid == CID else None

    def save_pending(self, token, user, cid, brief):
        self.saved.append((token, user, cid, brief.shop_id))

    def fail(self, token, cid):
        self.failed.append((token, cid))


class FakeAdmin:
    def __init__(self):
        self.failed = []

    def fail_pending(self, cid, sid, user_id):
        self.failed.append((cid, sid, user_id))


def api(store, queue=None, failure_store=None):
    def verified(token):
        if token not in ("signed-A", "signed-B"):
            from security import AuthenticationError
            raise AuthenticationError()
        return USER_A if token == "signed-A" else USER_B
    return HTTPAPI(verified, store, queue, failure_store=failure_store or FakeAdmin())


def test_requires_auth_even_when_queue_unconfigured():
    store = FakeStore()
    app = api(store)
    assert app.handle("POST", "/campaigns", "", request())[0] == 401
    assert app.handle("POST", "/campaigns", "Bearer invalid", request())[0] == 401
    assert app.handle("POST", "/campaigns", "Bearer signed-A", request()) == (503, {"error": "PLANNING_NOT_CONFIGURED"})
    assert not store.saved


def test_cross_shop_post_denied_before_write():
    store = FakeStore()
    class Queue:
        def enqueue(self, cid): raise AssertionError("must not queue")
    app = api(store, Queue())
    assert app.handle("POST", "/campaigns", "Bearer signed-B", request())[0] == 403
    assert app.handle("POST", "/campaigns", "Bearer signed-A", request(SHOP_B))[0] == 403
    assert not store.saved


def test_missing_asset_denied_before_write():
    store = FakeStore()
    store.assets = lambda *args: False
    app = api(store, object())
    assert app.handle("POST", "/campaigns", "Bearer signed-A", request())[0] == 403
    assert not store.saved


def test_valid_post_only_accepted_after_queue_ack():
    store = FakeStore()
    class Queue:
        accepted = []
        def enqueue(self, cid): self.accepted.append(cid)
    queue = Queue()
    status, body = api(store, queue).handle("POST", "/campaigns", "Bearer signed-A", request())
    assert status == 202 and body["status"] == "PLANNING"
    assert queue.accepted == [body["campaign_id"]]
    assert store.saved[0][:2] == ("signed-A", USER_A)


def test_queue_failure_marks_failed():
    store = FakeStore()
    class Queue:
        def enqueue(self, cid): raise OSError("queue is down")
    admin = FakeAdmin()
    status, body = api(store, Queue(), admin).handle("POST", "/campaigns", "Bearer signed-A", request())
    assert status == 503 and body["error"] == "QUEUE_UNAVAILABLE"
    assert admin.failed == [(store.saved[0][2], SHOP_A, USER_A)]


def test_get_foreign_returns_404():
    store = FakeStore()
    app = api(store)
    assert app.handle("GET", "/campaigns/" + CID, "Bearer signed-B")[0] == 404
    assert app.handle("GET", "/campaigns/garbage", "Bearer signed-A")[0] == 400
    assert app.handle("GET", "/campaigns/" + CID, "Bearer signed-A")[0] == 404


def test_get_returns_normalized_tenant_campaign():
    store = FakeStore()
    store.result = {"id": CID, "shop_id": SHOP_A, "status": "PLANNING", "days": []}
    code, row = api(store).handle("GET", "/campaigns/" + CID, "Bearer signed-A")
    assert code == 200 and row["id"] == CID

def test_no_backend_cleanup_prevents_any_persisted_unqueued_job():
    store = FakeStore()
    app = HTTPAPI(lambda token: USER_A, store, planning_queue=object())
    assert app.handle("POST", "/campaigns", "Bearer signed-A", request()) == (
        503, {"error": "PLANNING_NOT_CONFIGURED"})
    assert not store.saved
