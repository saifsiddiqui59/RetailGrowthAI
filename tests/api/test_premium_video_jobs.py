"""Mocked Part 3 orchestration: no hosted DB, WAN, Azure or paid APIs."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "azure-functions" / "campaign-api"))
# This independently-owned workstream targets the provider interface without
# copying its implementation. CI on the isolated jobs branch stubs it; once
# provider PR is merged first, pytest imports the real module automatically.
import importlib.util
if importlib.util.find_spec("ai_agents.premium_video") is None:
    import types
    module = types.ModuleType("ai_agents.premium_video")
    class FakeWanRequest:
        def __init__(self, mode, prompt, duration_seconds=5, resolution="720P",
                     signed_first_frame=None, shop_id=None):
            self.mode, self.prompt = mode, prompt
            self.duration_seconds, self.resolution = duration_seconds, resolution
    class FakePremiumVideoDisabled(RuntimeError):
        pass
    module.WanRequest = FakeWanRequest
    module.AlibabaWanProvider = object
    module.PremiumVideoDisabled = FakePremiumVideoDisabled
    module.campaign_video_prompt = lambda day: "Marketing: " + day["topic"]
    sys.modules["ai_agents.premium_video"] = module

from premium_video_jobs import PremiumVideoCoordinator, PremiumSubmissionWorker

UID = "123e4567-e89b-42d3-a456-426614174001"
SID = "123e4567-e89b-42d3-a456-426614174002"
CID = "123e4567-e89b-42d3-a456-426614174003"
DID = "123e4567-e89b-42d3-a456-426614174004"
AID = "123e4567-e89b-42d3-a456-426614174005"
JID = "123e4567-e89b-42d3-a456-426614174006"
LEASE = "123e4567-e89b-42d3-a456-426614174007"

class Users:
    def __init__(self, *, allow=True, asset_allowed=True):
        self.allow, self.asset_allowed = allow, asset_allowed
    def campaign(self, token, user, cid):
        assert token == "signed-test-jwt" and user == UID
        return {"id": cid, "shop_id": SID, "status": "DRAFT",
                "days": [{"id": DID, "shop_id": SID, "topic": "Autumn coats",
                          "instagram": {"reel": {"cta": "Visit us"}},
                          "review_status": "DRAFT"}]}
    def member(self, token, user, shop, write=False):
        return self.allow and shop == SID and user == UID
    def asset(self, token, sid, asset):
        return ({"id": asset, "mime_type": "image/jpeg"} if self.asset_allowed else None)

class Rights:
    def __init__(self, allowed=True): self.allowed = allowed
    def valid_media(self, sid, ids): return self.allowed

class Store:
    def __init__(self):
        self.inserted = []
        self.found = None
    def find_authenticated(self, token, shop, digest): return self.found
    def insert_reserved(self, row):
        self.inserted.append(row)
        return row
    def get_authenticated(self, token, job_id):
        return self.found

def payload(mode="text", aid=None):
    return {"day_id": DID, "mode": mode, "resolution": "720P",
            "duration_seconds": 5, "input_asset_id": aid}

def test_fails_closed_without_approval_or_creating_job():
    store = Store()
    api = PremiumVideoCoordinator(Users(), store, Rights(), enabled=False)
    assert api.create("signed-test-jwt", UID, CID, payload()) == (
        503, {"error": "PREMIUM_VIDEO_DISABLED"})
    assert not store.inserted

def test_authenticated_tenant_and_reviewed_campaign_required():
    store = Store()
    api = PremiumVideoCoordinator(Users(allow=False), store, Rights(), enabled=True)
    assert api.create("signed-test-jwt", UID, CID, payload())[0] == 403
    assert not store.inserted

def test_source_only_insert_is_canonical_and_idempotent():
    store = Store()
    api = PremiumVideoCoordinator(Users(), store, Rights(), enabled=True)
    code, res = api.create("signed-test-jwt", UID, CID, payload())
    assert code == 202 and res["status"] == "QUEUED" and res["job_id"]
    assert "provider_task_id" not in res and "idempotency_key" not in res
    record = store.inserted[0]
    assert record["shop_id"] == SID and record["requested_by"] == UID
    assert record["model_id"] == "wan2.7-t2v-2026-06-12"
    assert len(record["idempotency_key"]) == 64
    store.found = record
    assert api.create("signed-test-jwt", UID, CID, payload())[0] == 200
    assert len(store.inserted) == 1

def test_image_mode_checks_current_asset_membership_and_commercial_rights():
    for allow_asset, allow_rights in [(False, True), (True, False)]:
        store = Store()
        api = PremiumVideoCoordinator(Users(asset_allowed=allow_asset), store,
                                      Rights(allow_rights), enabled=True)
        assert api.create("signed-test-jwt", UID, CID, payload("image", AID))[0] == 403
        assert store.inserted == []
    store = Store()
    api = PremiumVideoCoordinator(Users(), store, Rights(), enabled=True)
    assert api.create("signed-test-jwt", UID, CID, payload("image", AID))[0] == 202
    assert store.inserted[0]["input_asset_id"] == AID
    assert store.inserted[0]["model_id"] == "wan2.7-i2v-2026-04-25"

@pytest.mark.parametrize("body", [
    {"mode": "text"}, payload("invalid"), payload("text", AID),
    payload("image", None), {**payload(), "duration_seconds": 16},
    {**payload(), "duration_seconds": True}, {**payload(), "resolution": "4K"}
])
def test_rejects_invalid_paid_video_requests(body):
    store = Store()
    api = PremiumVideoCoordinator(Users(), store, Rights(), enabled=True)
    assert api.create("signed-test-jwt", UID, CID, body)[0] == 400
    assert store.inserted == []

def test_status_never_exposes_provider_id_or_foreign_job():
    store = Store()
    store.found = {"id": JID, "shop_id": SID, "status": "RUNNING",
                   "provider_task_id": "secret-provider-task", "reserved_usd": 1.5}
    api = PremiumVideoCoordinator(Users(), store, Rights(), enabled=True)
    code, result = api.status("signed-test-jwt", UID, JID)
    assert code == 200 and result["job_id"] == JID
    assert "provider_task_id" not in result and "reserved_usd" not in result
    api = PremiumVideoCoordinator(Users(allow=False), store, Rights(), enabled=True)
    assert api.status("signed-test-jwt", UID, JID)[0] == 404

class WorkerStore:
    def __init__(self):
        self.claimed = {"id": JID, "shop_id": SID, "status": "SUBMITTING",
                        "attempt_token": LEASE, "mode": "text",
                        "prompt": "Approved reviewed creative", "seconds": 5,
                        "resolution": "720P"}
        self.calls = []
    def claim(self, job_id): return self.claimed
    def finish_attempt(self, *args, **kwargs): self.calls.append(("finish", args, kwargs))
    def record_task(self, *args): self.calls.append(("task", args))
    def claim_poll(self, jid):
        return {"provider_task_id": "job-12345678", "attempt_token": LEASE}
    def record_poll(self, *args): self.calls.append(("poll", args))

class Provider:
    def __init__(self, error=None): self.error, self.count = error, 0
    def submit(self, spec):
        self.count += 1
        if self.error: raise self.error
        return {"task_id": "job-12345678"}
    def poll(self, task_id):
        return {"task_id": task_id, "status": "SUCCEEDED"}

def test_worker_submits_once_without_calling_paid_provider_twice():
    store, provider = WorkerStore(), Provider()
    worker = PremiumSubmissionWorker(store, provider)
    assert worker.submit_once(JID) == "PENDING"
    assert provider.count == 1
    assert store.calls == [("task", (JID, LEASE, "job-12345678"))]

def test_unknown_provider_response_never_retries_or_double_charges():
    store, provider = WorkerStore(), Provider(RuntimeError("network response lost"))
    worker = PremiumSubmissionWorker(store, provider)
    assert worker.submit_once(JID) == "UNKNOWN"
    assert provider.count == 1
    assert store.calls[0][0] == "finish"
    assert store.calls[0][2]["error_code"] == "PROVIDER_RESULT_UNKNOWN"

def test_provider_success_not_mistaken_for_private_media_download():
    store, provider = WorkerStore(), Provider()
    assert PremiumSubmissionWorker(store, provider).poll_once(JID) == "SUCCEEDED"
    assert store.calls == [("poll", (JID, LEASE, "IMPORTING"))]
