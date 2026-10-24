"""Private service-role poster job transport; no public or browser credentials."""
from __future__ import annotations
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from admin_store import AdminStore, backend_headers
from tenant_store import StorageUnavailable, canonical_uuid


class PosterAdmin(AdminStore):
    def _poster_call(self, path, *, query=None, data=None):
        if path not in {"poster_jobs", "poster_drafts", "rpc/claim_poster_job",
                        "rpc/complete_poster_job", "rpc/fail_poster_job",
                        "rpc/claim_poster_outbox", "rpc/confirm_poster_outbox",
                        "rpc/reconcile_poster_jobs"}:
            raise ValueError("unlisted private poster route")
        url = self.origin + "/rest/v1/" + path
        if query is not None:
            url += "?" + urlencode(query, safe="(),.*")
        request = Request(url, method="POST" if data is not None else "GET",
            data=json.dumps(data).encode("utf-8") if data is not None else None,
            headers={**backend_headers(self.secret),
                     "Accept": "application/json", "Content-Type": "application/json"})
        try:
            with self.transport(request, timeout=12) as response:
                return json.loads(response.read().decode())
        except (HTTPError, URLError, OSError, ValueError) as exc:
            raise StorageUnavailable("private poster database unavailable") from exc

    def poster_status(self, job_id):
        rows = self._poster_call("poster_jobs", query={"select": "status",
            "id": "eq." + canonical_uuid(job_id), "limit": "1"})
        return rows[0]["status"] if len(rows) == 1 else None

    def claim_poster(self, job_id):
        return self._poster_call("rpc/claim_poster_job",
                                 data={"p_id": canonical_uuid(job_id)})

    def poster_authorized(self, job):
        sid = canonical_uuid(job["shop_id"])
        uid = canonical_uuid(job["requested_by"])
        rows = self.request("shop_memberships", query={
            "select": "role", "shop_id": "eq." + sid, "user_id": "eq." + uid,
            "active": "eq.true", "limit": "1"})
        return len(rows) == 1 and rows[0].get("role") in ("OWNER", "EDITOR")

    def poster_sources(self, job):
        sid = canonical_uuid(job["shop_id"])
        pid = canonical_uuid(job["poster_id"])
        rows = self._poster_call("poster_drafts", query={
            "select": "id,shop_id,campaign_id,day_id,revision,status,template,format,"
                      "business_name,accent_color,background_color,offer_text,"
                      "source_asset_id,logo_asset_id",
            "id": "eq." + pid, "shop_id": "eq." + sid, "limit": "1"})
        if len(rows) != 1:
            raise StorageUnavailable("private poster draft unavailable")
        poster = rows[0]
        cid, did = canonical_uuid(poster["campaign_id"]), canonical_uuid(poster["day_id"])
        campaigns = self.request("campaigns", query={
            "select": "id,shop_id,status", "id": "eq." + cid,
            "shop_id": "eq." + sid, "limit": "1"})
        days = self.request("campaign_days", query={
            "select": "id,campaign_id,shop_id,day_index,topic,instagram,review_status",
            "id": "eq." + did, "campaign_id": "eq." + cid,
            "shop_id": "eq." + sid, "limit": "1"})
        ids = {canonical_uuid(poster["source_asset_id"])}
        if poster["logo_asset_id"]:
            ids.add(canonical_uuid(poster["logo_asset_id"]))
        assets = self.request("media_assets", query={
            "select": "id,shop_id,storage_bucket,object_path,mime_type,source,license_name,"
                      "license_url,attribution",
            "shop_id": "eq." + sid, "id": "in.(" + ",".join(sorted(ids)) + ")"})
        if len(campaigns) != 1 or len(days) != 1 or len(assets) != len(ids):
            raise StorageUnavailable("private poster inputs unavailable")
        if {a["id"] for a in assets} != ids or any(a["shop_id"] != sid for a in assets):
            raise StorageUnavailable("cross-tenant poster source")
        return poster, campaigns[0], days[0], {a["id"]: a for a in assets}

    def complete_poster(self, job, key):
        result = self._poster_call("rpc/complete_poster_job", data={
            "p_id": canonical_uuid(job["id"]),
            "p_attempt": job["attempts"], "p_token": canonical_uuid(job["claim_token"]),
            "p_object_path": key})
        if result is not True:
            raise StorageUnavailable("poster claim was stale or revoked")

    def fail_poster(self, job, *, permanent=False):
        result = self._poster_call("rpc/fail_poster_job", data={
            "p_id": canonical_uuid(job["id"]), "p_attempt": job["attempts"],
            "p_token": canonical_uuid(job["claim_token"]),
            "p_error": "POSTER_RENDER_FAILED", "p_permanent": bool(permanent)})
        if result is not True:
            raise StorageUnavailable("poster failure claim was stale")

    def claim_outbox(self, limit=10):
        return self._poster_call("rpc/claim_poster_outbox", data={"p_limit": limit})

    def confirm_outbox(self, event, succeeded):
        if self._poster_call("rpc/confirm_poster_outbox", data={
                "p_id": canonical_uuid(event["id"]),
                "p_token": canonical_uuid(event["lease_token"]),
                "p_sent": bool(succeeded)}) is not True:
            raise StorageUnavailable("poster dispatch lease was lost")

    def reconcile_posters(self, limit=20):
        return self._poster_call("rpc/reconcile_poster_jobs", data={"p_limit": limit})
