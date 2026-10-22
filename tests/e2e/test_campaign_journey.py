"""Offline API journey: real HTTPAPI/RenderAPI/DraftAPI boundaries with scoped fake stores.

No Azure/Supabase resources, real JWT signatures, live storage or actual encoder are
used here. Those gates need a separately approved deployed DEV test.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))
sys.path.insert(0, str(ROOT / "ai-agents" / "src"))
from http_api import HTTPAPI
from render_api import RenderAPI
from security import AuthenticationError
from ai_agents.schemas import validate_campaign

SAMPLE = json.loads((ROOT / "frontend/src/features/campaigns/fixtures/sample-campaign.json").read_text())
ALICE, BOB, SHOP_A, SHOP_B, ASSET_A, OUTPUT = [str(uuid4()) for _ in range(6)]
ALL_ASSETS = {
    shot["asset_id"] for day in SAMPLE["days"]
    for shot in day["instagram"]["reel"]["storyboard"]
}


class FakeStore:
    def __init__(self):
        self.members = {(ALICE, SHOP_A): "OWNER", (BOB, SHOP_B): "OWNER"}
        self.owned_assets = {SHOP_A: ALL_ASSETS | {ASSET_A}, SHOP_B: set()}
        self.pending = {}
        self.campaigns = {}
        self.jobs = {}
        self.day_conflict = False
        self.output = {}

    def _allowed(self, token, user, shop, *, write=False):
        role = self.members.get((user, shop))
        return token == ("alice-token" if user == ALICE else "bob-token") and (
            role in ("OWNER", "EDITOR") if write else role in ("OWNER", "EDITOR", "VIEWER")
        )

    def member(self, token, user, shop, *, write=False):
        return self._allowed(token, user, shop, write=write)

    def assets(self, token, shop, ids):
        user = ALICE if token == "alice-token" else BOB
        return self._allowed(token, user, shop, write=True) and bool(ids) and (
            set(ids) <= self.owned_assets.get(shop, set())
        )

    def campaign(self, token, user, cid):
        record = self.campaigns.get(cid)
        if not record or not self._allowed(token, user, record["shop_id"]):
            return None
        return copy.deepcopy(record)

    def save_pending(self, token, user, cid, brief):
        assert self._allowed(token, user, brief.shop_id, write=True)
        self.pending[cid] = {"user": user, "shop": brief.shop_id, "status": "PLANNING"}

    def fail_pending(self, cid, sid, user):
        pending = self.pending[cid]
        assert pending["shop"] == sid and pending["user"] == user
        pending["status"] = "FAILED"

    def finish_planning(self, cid):
        """Simulates a queued planner completion; DOES NOT invoke a model."""
        assert self.pending[cid]["status"] == "PLANNING"
        result = copy.deepcopy(SAMPLE)
        result["id"] = cid
        result["shop_id"] = self.pending[cid]["shop"]
        for day in result["days"]:
            day["campaign_id"] = cid
            day["shop_id"] = result["shop_id"]
        validate_campaign(result)
        self.campaigns[cid] = result
        self.pending[cid]["status"] = "DRAFT"
        return result

    def save_day(self, token, sid, cid, did, expected, changes):
        if self.day_conflict:
            return False
        row = self.campaigns[cid]
        if row["shop_id"] != sid or not self._allowed(token, ALICE, sid, write=True):
            return False
        match = next((d for d in row["days"] if d["id"] == did), None)
        if not match or any(match[k] != expected[k] for k in expected):
            return False
        match.update(copy.deepcopy(changes))
        return True

    def render_job(self, token, user, jid):
        item = self.jobs.get(jid)
        return copy.deepcopy(item) if item and self._allowed(token, user, item["shop_id"]) else None

    def asset(self, token, sid, aid):
        if aid not in self.output or self.output[aid]["shop_id"] != sid:
            return None
        user = ALICE if token == "alice-token" else BOB
        return self.output[aid] if self._allowed(token, user, sid) else None

    def sign_download(self, token, sid, path):
        assert self._allowed(token, ALICE, sid)
        assert path.startswith(sid + "/renders/") and path.endswith(".mp4")
        return "https://e2e.supabase.test/storage/v1/object/sign/retailgrowth-media/" + path + "?token=fake-signed"


class FakeAdmin:
    def __init__(self, store):
        self.store = store
        self.by_key = {}
        self.rights_ok = True

    def fail_pending(self, cid, sid, user):
        self.store.fail_pending(cid, sid, user)

    def valid_media(self, sid, ids):
        return self.rights_ok and sid == SHOP_A and bool(ids) and set(ids) <= ALL_ASSETS

    def find_render_job(self, sid, key):
        jid = self.by_key.get((sid, key))
        return self.store.jobs.get(jid) if jid else None

    def insert_render_job(self, row):
        self.store.jobs[row["id"]] = {**row, "output_asset_id": None, "error_code": None}
        self.by_key[row["shop_id"], row["idempotency_key"]] = row["id"]

    def fail_render_job(self, jid, sid, reason):
        assert self.store.jobs[jid]["shop_id"] == sid
        self.store.jobs[jid].update(status="FAILED", error_code=reason)

    def complete(self, jid):
        job = self.store.jobs[jid]
        job.update(status="SUCCEEDED", output_asset_id=OUTPUT)
        path = job["shop_id"] + "/renders/" + jid + ".mp4"
        self.store.output[OUTPUT] = {
            "shop_id": job["shop_id"], "mime_type": "video/mp4", "object_path": path,
        }


class FakeQueue:
    def __init__(self):
        self.items = []
        self.broken = False

    def enqueue(self, item):
        if self.broken:
            raise OSError("offline queue failed")
        self.items.append(item)


@pytest.fixture
def journey():
    store = FakeStore()
    admin = FakeAdmin(store)
    plan_queue, render_queue = FakeQueue(), FakeQueue()

    def verify(token):
        if token == "alice-token":
            return ALICE
        if token == "bob-token":
            return BOB
        raise AuthenticationError()

    render = RenderAPI(store, admin, render_queue)
    api = HTTPAPI(verify, store, plan_queue, render, failure_store=admin)
    return api, store, admin, plan_queue, render_queue


def call(api, method, path, who="alice-token", body=None):
    return api.handle(method, path, "Bearer " + who if who else "", body)


def brief(shop=SHOP_A, asset=ASSET_A):
    return {
        "shop_id": shop,
        "brief": "Create seven days of autumn outfit inspiration",
        "duration_days": 7,
        "start_date": "2026-11-01",
        "timezone": "Asia/Kolkata",
        "language": "en-IN",
        "platforms": ["linkedin", "instagram"],
        "media_asset_ids": [asset],
        "offer": None,
    }


def draft_changes(day):
    return {key: copy.deepcopy(day[key]) for key in ("topic", "linkedin", "instagram")}


def test_full_authorized_plan_edit_render_and_private_download(journey):
    api, store, admin, planning, rendering = journey
    code, accepted = call(api, "POST", "/campaigns", body=brief())
    assert code == 202 and accepted["status"] == "PLANNING"
    cid = accepted["campaign_id"]
    assert planning.items == [cid]
    store.finish_planning(cid)

    code, result = call(api, "GET", "/campaigns/" + cid)
    assert code == 200 and len(result["days"]) == 7
    assert all(d["campaign_id"] == cid and d["shop_id"] == SHOP_A for d in result["days"])
    assert all(d["instagram"]["reel"]["duration_seconds"] == 30 for d in result["days"])

    day = result["days"][0]
    changed = draft_changes(day)
    changed["linkedin"]["post_text"] = "Edited by an authorized retailer"
    path = f"/campaigns/{cid}/days/{day['id']}"
    code, saved = call(api, "PATCH", path, body=changed)
    assert code == 200 and saved["day"]["linkedin"]["post_text"] == changed["linkedin"]["post_text"]
    assert saved["day"]["id"] == day["id"] and saved["day"]["shop_id"] == SHOP_A

    route = f"/campaigns/{cid}/renders"
    render_body = {"day_id": day["id"], "preset": "instagram_reel_30s"}
    code, queued = call(api, "POST", route, body=render_body)
    assert code == 202 and queued["status"] == "QUEUED"
    jid = queued["job_id"]
    assert rendering.items == [jid]
    repeated = call(api, "POST", route, body=render_body)
    assert repeated[1]["job_id"] == jid and rendering.items == [jid]

    assert call(api, "GET", f"/render-jobs/{jid}")[1]["status"] == "QUEUED"
    assert call(api, "GET", f"/render-jobs/{jid}/download") == (409, {"error": "OUTPUT_NOT_READY"})
    admin.complete(jid)  # Fake worker; no FFmpeg execution or real MP4.
    assert call(api, "GET", f"/render-jobs/{jid}")[1]["status"] == "SUCCEEDED"
    status, link = call(api, "GET", f"/render-jobs/{jid}/download")
    assert status == 200
    assert link["url"].startswith("https://e2e.supabase.test/storage/v1/object/sign/retailgrowth-media/")
    assert "token=fake-signed" in link["url"]

    # Authorization remains enforced for the whole chain, not only creation.
    assert call(api, "GET", f"/campaigns/{cid}", "bob-token")[0] == 404
    assert call(api, "PATCH", path, "bob-token", changed)[0] == 404
    assert call(api, "POST", route, "bob-token", render_body)[0] == 404
    assert call(api, "GET", f"/render-jobs/{jid}", "bob-token")[0] == 404
    assert call(api, "GET", f"/render-jobs/{jid}/download", "bob-token")[0] == 404


def test_wrong_tenant_assets_and_unauthenticated_creation_do_not_queue(journey):
    api, store, _, planning, _ = journey
    assert call(api, "POST", "/campaigns", "", brief())[0] == 401
    assert call(api, "POST", "/campaigns", "forged", brief())[0] == 401
    assert call(api, "POST", "/campaigns", "bob-token", brief())[0] == 403
    assert call(api, "POST", "/campaigns", body=brief(shop=SHOP_B))[0] == 403
    assert call(api, "POST", "/campaigns", body=brief(asset=str(uuid4())))[0] == 403
    assert not planning.items and not store.pending


def test_viewer_revocation_and_queue_failures_are_fail_closed(journey):
    api, store, _, planning, _ = journey
    store.members[(ALICE, SHOP_A)] = "VIEWER"
    assert call(api, "POST", "/campaigns", body=brief())[0] == 403
    store.members[(ALICE, SHOP_A)] = "OWNER"
    planning.broken = True
    status, failure = call(api, "POST", "/campaigns", body=brief())
    assert (status, failure) == (503, {"error": "QUEUE_UNAVAILABLE"})
    assert len(store.pending) == 1
    assert next(iter(store.pending.values()))["status"] == "FAILED"


def test_edit_conflict_rejected_media_and_failed_render_queue(journey):
    api, store, admin, _, rendering = journey
    cid = call(api, "POST", "/campaigns", body=brief())[1]["campaign_id"]
    campaign = store.finish_planning(cid)
    day = campaign["days"][0]
    route = f"/campaigns/{cid}/days/{day['id']}"
    changes = draft_changes(day)
    changes["shop_id"] = SHOP_B
    assert call(api, "PATCH", route, body=changes)[0] == 400
    changes.pop("shop_id")
    store.day_conflict = True
    assert call(api, "PATCH", route, body=changes) == (409, {"error": "EDIT_CONFLICT"})
    store.day_conflict = False
    store.members[(ALICE, SHOP_A)] = "VIEWER"
    assert call(api, "PATCH", route, body=changes)[0] == 403
    store.members[(ALICE, SHOP_A)] = "OWNER"

    admin.rights_ok = False
    render_path = f"/campaigns/{cid}/renders"
    body = {"day_id": day["id"], "preset": "instagram_reel_30s"}
    assert call(api, "POST", render_path, body=body)[0] == 403
    assert not rendering.items
    admin.rights_ok = True
    rendering.broken = True
    assert call(api, "POST", render_path, body=body) == (503, {"error": "QUEUE_UNAVAILABLE"})
    assert not rendering.items
    assert list(store.jobs.values())[0]["status"] == "FAILED"


def test_membership_revocation_blocks_existing_draft_and_download(journey):
    api, store, admin, _, _ = journey
    cid = call(api, "POST", "/campaigns", body=brief())[1]["campaign_id"]
    campaign = store.finish_planning(cid)
    day = campaign["days"][0]
    jid = call(api, "POST", f"/campaigns/{cid}/renders", body={
        "day_id": day["id"], "preset": "instagram_reel_30s",
    })[1]["job_id"]
    admin.complete(jid)
    store.members.pop((ALICE, SHOP_A))
    assert call(api, "GET", "/campaigns/" + cid)[0] == 404
    assert call(api, "GET", "/render-jobs/" + jid)[0] == 404
    assert call(api, "GET", "/render-jobs/" + jid + "/download")[0] == 404
