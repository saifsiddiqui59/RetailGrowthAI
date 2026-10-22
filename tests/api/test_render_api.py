"""Tenant isolation, idempotent render jobs and signed-download authorization."""
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from render_api import RenderAPI

UID, SID, CID, DID, AID, JID, OUTID = (str(uuid4()) for _ in range(7))


def make_campaign():
    return {"id": CID, "shop_id": SID, "status": "DRAFT", "days": [{
        "id": DID, "campaign_id": CID, "shop_id": SID,
        "day_index": 1, "scheduled_date": "2026-11-01",
        "topic": "Style", "linkedin": {"post_text": "Post", "hashtags": ["#Style"]},
        "instagram": {"caption": "Caption", "banner_asset_id": None,
                      "reel": {"duration_seconds": 30, "aspect_ratio": "9:16",
                               "storyboard": [
                                   {"start_seconds": t, "duration_seconds": 10, "asset_id": AID,
                                    "overlay_text": "Hello"} for t in (0, 10, 20)
                               ],
                               "music_asset_id": None, "cta": "Visit"}},
        "review_status": "DRAFT",
    }]}


class Users:
    allow = True
    def campaign(self, token, user, cid):
        return make_campaign() if self.allow and token == "user-jwt" and user == UID and cid == CID else None
    def member(self, token, user, sid, write=False):
        return self.allow and user == UID and sid == SID
    def assets(self, token, sid, ids):
        return self.allow and sid == SID and ids == [AID]
    def render_job(self, token, user, jid):
        if not self.allow or user != UID or jid != JID: return None
        return {"id": JID, "shop_id": SID, "status": "SUCCEEDED",
                "output_asset_id": OUTID, "error_code": None}
    def asset(self, token, sid, aid):
        return {"mime_type": "video/mp4", "object_path": SID + "/render.mp4"} if sid == SID and aid == OUTID else None
    def sign_download(self, token, sid, path):
        assert token == "user-jwt" and sid == SID and path.startswith(SID + "/")
        return "https://safe.supabase.co/storage/v1/object/sign/test?token=signed"


class Admin:
    def __init__(self): self.jobs = []; self.existing = None; self.failed = []
    def valid_media(self, sid, ids): return sid == SID and ids == [AID, AID, AID]
    def find_render_job(self, sid, key): return self.existing
    def insert_render_job(self, row): self.jobs.append(row)
    def fail_render_job(self, jid, sid, reason): self.failed.append((jid, sid, reason))


class Queue:
    def __init__(self, broken=False): self.sent = []; self.broken = broken
    def enqueue(self, jid):
        if self.broken: raise OSError("not configured")
        self.sent.append(jid)


def test_cross_shop_and_unavailable_job_denied_before_insert():
    user, admin, queue = Users(), Admin(), Queue()
    svc = RenderAPI(user, admin, queue)
    user.allow = False
    assert svc.create("other", UID, CID, {"day_id": DID, "preset": "instagram_reel_30s"})[0] == 404
    assert svc.get("other", UID, JID)[0] == 404
    assert svc.download("other", UID, JID)[0] == 404
    assert not admin.jobs


def test_valid_job_and_idempotent_request():
    admin, queue = Admin(), Queue()
    svc = RenderAPI(Users(), admin, queue)
    status, payload = svc.create("user-jwt", UID, CID, {"day_id": DID, "preset": "instagram_reel_30s"})
    assert status == 202 and payload["status"] == "QUEUED"
    assert len(queue.sent) == 1 and len(admin.jobs) == 1
    admin.existing = {"id": payload["job_id"], "status": "QUEUED"}
    status, next_payload = svc.create("user-jwt", UID, CID, {"day_id": DID, "preset": "instagram_reel_30s"})
    assert status == 202 and next_payload["job_id"] == payload["job_id"]
    assert len(admin.jobs) == 1 and len(queue.sent) == 1


def test_queue_failure_returns_503_and_marks_job_failed():
    admin = Admin()
    status, body = RenderAPI(Users(), admin, Queue(broken=True)).create(
        "user-jwt", UID, CID, {"day_id": DID, "preset": "instagram_reel_30s"})
    assert status == 503 and body["error"] == "QUEUE_UNAVAILABLE"
    assert admin.failed[0][0] == admin.jobs[0]["id"]


def test_download_signs_only_authorized_succeeded_private_output():
    svc = RenderAPI(Users(), Admin(), Queue())
    status, payload = svc.download("user-jwt", UID, JID)
    assert status == 200 and "token=signed" in payload["url"]
    assert svc.get("user-jwt", UID, JID) == (
        200, {"job_id": JID, "status": "SUCCEEDED", "output_asset_id": OUTID, "error_code": None}
    )


def test_invalid_preset_not_queued():
    admin=Admin()
    assert RenderAPI(Users(), admin, Queue()).create("user-jwt", UID, CID, {
        "day_id": DID, "preset": "arbitrary_file"
    })[0] == 400
    assert not admin.jobs
