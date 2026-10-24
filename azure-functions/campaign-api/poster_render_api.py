"""Authenticated poster rendering routes backed by strict user RLS.

A stored poster draft is not a rendered image. Queue requests are transactions
via the dedicated Postgres RPC; HTTP does not enqueue out-of-transaction.
"""
from tenant_store import canonical_uuid


class PosterRenderAPI:
    def __init__(self, user_store):
        self.users = user_store

    def create(self, token, user_id, poster_id):
        pid = canonical_uuid(poster_id)
        draft = self.users.poster_draft(token, user_id, pid)
        if draft is None:
            return 404, {"error": "NOT_FOUND"}
        if not self.users.member(token, user_id, draft["shop_id"], write=True):
            return 403, {"error": "FORBIDDEN"}
        job_id = self.users.request_poster_job(token, pid)
        if job_id is None:
            return 409, {"error": "POSTER_NOT_RENDERABLE"}
        return 202, {"job_id": canonical_uuid(job_id), "status": "QUEUED"}

    def get(self, token, user_id, job_id):
        jid = canonical_uuid(job_id)
        job = self.users.poster_job(token, user_id, jid)
        if job is None:
            return 404, {"error": "NOT_FOUND"}
        return 200, {"job_id": jid, "poster_id": job["poster_id"],
                     "status": job["status"], "output_asset_id": job["output_asset_id"],
                     "error_code": job.get("error_code")}

    def download(self, token, user_id, job_id):
        jid = canonical_uuid(job_id)
        job = self.users.poster_job(token, user_id, jid)
        if job is None:
            return 404, {"error": "NOT_FOUND"}
        if job["status"] != "SUCCEEDED" or not job["output_asset_id"]:
            return 409, {"error": "OUTPUT_NOT_READY"}
        sid = canonical_uuid(job["shop_id"])
        asset = self.users.asset(token, sid, job["output_asset_id"])
        if asset is None or asset["mime_type"] != "image/png":
            return 404, {"error": "OUTPUT_NOT_FOUND"}
        # Only the exact versioned poster output path can be served as a poster.
        expected = sid + "/posters/" + canonical_uuid(job["poster_id"]) + "/"
        if not asset["object_path"].startswith(expected):
            return 404, {"error": "OUTPUT_NOT_FOUND"}
        return 200, {"url": self.users.sign_download(token, sid, asset["object_path"])}
