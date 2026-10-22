"""Authenticated render-job endpoints; no client-supplied paths or download URLs."""
import hashlib
import json
from uuid import uuid4

from ai_agents.schemas import validate_campaign
from tenant_store import canonical_uuid, StorageUnavailable

PRESET = "instagram_reel_30s"


class RenderAPI:
    def __init__(self, user_store, admin, queue):
        self.users, self.admin, self.queue = user_store, admin, queue

    def create(self, token, user_id, campaign_id, body):
        cid = canonical_uuid(campaign_id)
        if not isinstance(body, dict) or set(body) != {"day_id", "preset"} or body["preset"] != PRESET:
            return 400, {"error": "INVALID_REQUEST"}
        did = canonical_uuid(body["day_id"])
        campaign = self.users.campaign(token, user_id, cid)
        if campaign is None:
            return 404, {"error": "NOT_FOUND"}
        if campaign["status"] != "DRAFT":
            return 409, {"error": "CAMPAIGN_NOT_DRAFT"}
        validate_campaign(campaign)
        sid = campaign["shop_id"]
        if not self.users.member(token, user_id, sid, write=True):
            return 403, {"error": "FORBIDDEN"}
        days = [day for day in campaign["days"] if day["id"] == did and day["shop_id"] == sid]
        if len(days) != 1:
            return 404, {"error": "NOT_FOUND"}
        day = days[0]
        if day["review_status"] == "REJECTED":
            return 409, {"error": "DAY_REJECTED"}
        reel = day["instagram"]["reel"]
        ids = [s["asset_id"] for s in reel["storyboard"]]
        if reel["music_asset_id"]:
            ids.append(reel["music_asset_id"])
        if not self.users.assets(token, sid, list(dict.fromkeys(ids))):
            return 403, {"error": "ASSET_ACCESS_DENIED"}
        if not self.admin.valid_media(sid, ids):
            return 403, {"error": "ASSET_RIGHTS_UNVERIFIED"}
        # Same authorized storyboard/request -> same idempotency key, incl. edits.
        digest = hashlib.sha256(json.dumps(
            [user_id, cid, did, reel], sort_keys=True, separators=(",", ":")
        ).encode()).hexdigest()
        previous = self.admin.find_render_job(sid, digest)
        if previous:
            return 202 if previous["status"] in ("QUEUED", "RUNNING") else 200, {
                "job_id": previous["id"], "status": previous["status"]
            }
        jid = str(uuid4())
        try:
            self.admin.insert_render_job({
                "id": jid, "shop_id": sid, "campaign_id": cid, "day_id": did,
                "requested_by": user_id, "preset": PRESET, "status": "QUEUED",
                "idempotency_key": digest,
            })
        except StorageUnavailable:
            # Another concurrent request may have inserted this exact unique key.
            previous = self.admin.find_render_job(sid, digest)
            if not previous:
                raise
            return 202, {"job_id": previous["id"], "status": previous["status"]}
        try:
            self.queue.enqueue(jid)
        except Exception:
            self.admin.fail_render_job(jid, sid, "QUEUE_UNAVAILABLE")
            return 503, {"error": "QUEUE_UNAVAILABLE"}
        return 202, {"job_id": jid, "status": "QUEUED"}

    def get(self, token, user_id, job_id):
        jid = canonical_uuid(job_id)
        item = self.users.render_job(token, user_id, jid)
        if item is None:
            return 404, {"error": "NOT_FOUND"}
        return 200, {key: item.get(field) for key, field in {
            "job_id": "id", "status": "status", "output_asset_id": "output_asset_id",
            "error_code": "error_code",
        }.items()}

    def download(self, token, user_id, job_id):
        jid = canonical_uuid(job_id)
        item = self.users.render_job(token, user_id, jid)
        if item is None:
            return 404, {"error": "NOT_FOUND"}
        if item["status"] != "SUCCEEDED" or not item["output_asset_id"]:
            return 409, {"error": "OUTPUT_NOT_READY"}
        asset = self.users.asset(token, item["shop_id"], item["output_asset_id"])
        if asset is None or asset["mime_type"] != "video/mp4":
            return 404, {"error": "OUTPUT_NOT_FOUND"}
        return 200, {"url": self.users.sign_download(token, item["shop_id"], asset["object_path"])}
