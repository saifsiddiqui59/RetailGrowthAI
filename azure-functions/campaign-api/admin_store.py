"""Worker-only service-role PostgREST adapter. Never import into the browser.

This adapter can only be instantiated with explicitly provided backend credentials.
Atomic DB claim prevents parallel queue deliveries generating duplicate campaigns.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tenant_store import StorageUnavailable, SubscriptionDenied, canonical_uuid


def backend_headers(secret):
    """Use opaque Supabase secret keys as API keys, not bearer tokens."""
    if isinstance(secret, str) and secret.startswith("sb_secret_"):
        return {"apikey": secret}
    if isinstance(secret, str) and secret.startswith("eyJ") and secret.count(".") == 2:
        return {"apikey": secret, "Authorization": "Bearer " + secret}
    raise ValueError("unsupported backend Supabase secret key format")


class AdminStore:
    def __init__(self, origin, service_role_key, transport=None):
        if not origin.startswith("https://") or not service_role_key:
            raise ValueError("worker-only Supabase HTTPS origin and secret key required")
        self.origin, self.secret = origin.rstrip("/"), service_role_key
        self.transport = transport or urlopen

    def request(self, path, *, query=None, data=None, method="GET", upsert=False):
        if path not in ("rpc/claim_campaign_job", "rpc/claim_render_job",
                        "rpc/complete_campaign_claim", "rpc/fail_campaign_claim",
                        "rpc/complete_render_claim", "rpc/fail_render_claim",
                        "rpc/claim_outbox_events", "rpc/confirm_outbox_event",
                        "rpc/record_poison_event", "rpc/reconcile_stale_jobs",
                        "campaigns", "campaign_days", "shop_memberships", "media_assets", "render_jobs",
                        "trend_snapshots", "rpc/feature2_claim_collection", "rpc/feature2_finish_collection",
                        "shop_content_drafts",
                        "rpc/feature2_reserve_ai_budget", "rpc/feature2_settle_ai_budget",
                        "rpc/feature3_reserve_gpu_job", "rpc/feature3_claim_gpu_job",
                        "rpc/feature3_finish_gpu_job", "feature3_gpu_jobs",
                        "shop_ai_spend_reservations",
                        "feature3_poster_designs", "feature3_models",
                        "shop_subscriptions",
                        "rpc/feature3_commit_gpu_private_output",
                        "rpc/feature3_claim_gpu_dispatch",
                        "rpc/feature3_confirm_gpu_dispatch",
                        "rpc/feature3_audit_gpu_recovery",
                        "rpc/retail_feature_worker_append"):
            raise ValueError("unsupported worker path")
        # Immutable live job/reservation/model/design/subscription snapshots
        # are service-role GET-only. All GPU job/ledger changes remain RPC-only.
        if path in {"feature3_gpu_jobs", "shop_ai_spend_reservations",
                    "feature3_poster_designs", "feature3_models",
                    "shop_subscriptions"} and method != "GET":
            raise ValueError("GPU planning tables are read-only via this transport")
        # A queue claim/financial/media CAS is never exposed via a GET read
        # or a generic table write. Only the service-only POST RPC is valid.
        if path in {
            "rpc/feature3_commit_gpu_private_output",
            "rpc/feature3_claim_gpu_dispatch",
            "rpc/feature3_confirm_gpu_dispatch",
            "rpc/feature3_audit_gpu_recovery",
        } and method != "POST":
            raise ValueError("Feature3 privileged GPU RPC requires POST")
        url = self.origin + "/rest/v1/" + path
        if query:
            url += "?" + urlencode(query, safe="(),.*")
        headers = {
            **backend_headers(self.secret),
            "Accept": "application/json", "Content-Type": "application/json",
        }
        if method != "GET":
            headers["Prefer"] = ("resolution=merge-duplicates,return=representation"
                                 if upsert else "return=representation")
        body = None if data is None else json.dumps(data).encode("utf-8")
        try:
            with self.transport(Request(url, data=body, headers=headers, method=method),
                                timeout=10) as resp:
                raw = resp.read()
                return json.loads(raw.decode()) if raw else None
        except HTTPError as exc:
            try:
                response_code = json.loads(exc.read(4096)).get("code")
            except (ValueError, AttributeError, TypeError):
                response_code = None
            if response_code in ("RG001", "RG002", "RG003", "RG004"):
                raise SubscriptionDenied(response_code) from exc
            raise StorageUnavailable("worker database request failed") from exc
        except (URLError, OSError, json.JSONDecodeError) as exc:
            raise StorageUnavailable("worker database request failed") from exc

    def fail_pending(self, campaign_id, shop_id, created_by):
        """Backend-only cleanup; user RLS must not grant status updates."""
        rows = self.request("campaigns", method="PATCH", query={
            "id": "eq." + canonical_uuid(campaign_id),
            "shop_id": "eq." + canonical_uuid(shop_id),
            "created_by": "eq." + canonical_uuid(created_by),
            "status": "eq.PLANNING",
        }, data={"status": "FAILED", "planning_error_code": "QUEUE_UNAVAILABLE",
                 "planning_lease_until": None})
        if not isinstance(rows, list) or len(rows) != 1:
            raise StorageUnavailable("pending cleanup could not be confirmed")

    def claim(self, cid):
        return self.request("rpc/claim_campaign_job", method="POST",
                            data={"p_id": canonical_uuid(cid)})

    def campaign_status(self, cid):
        rows = self.request("campaigns", query={
            "select": "status", "id": "eq." + canonical_uuid(cid), "limit": "1",
        })
        return rows[0]["status"] if rows else None

    def still_authorized(self, row):
        sid, uid = canonical_uuid(row["shop_id"]), canonical_uuid(row["created_by"])
        memberships = self.request("shop_memberships", query={
            "select": "role", "shop_id": "eq." + sid, "user_id": "eq." + uid,
            "active": "eq.true", "limit": "1",
        })
        if not memberships or memberships[0]["role"] not in ("OWNER", "EDITOR"):
            return False
        asset_ids = row["media_asset_ids"]
        if not isinstance(asset_ids, list) or not 1 <= len(asset_ids) <= 21:
            return False
        ids = [canonical_uuid(a) for a in asset_ids]
        if len(ids) != len(set(ids)):
            return False
        assets = self.request("media_assets", query={
            "select": "id,shop_id,license_name,source", "shop_id": "eq." + sid,
            "id": "in.(" + ",".join(ids) + ")",
        })
        # Missing license declarations or tenant-owned assets fail closed.
        return ({a["id"] for a in assets} == set(ids) and
                all(a["shop_id"] == sid and a.get("license_name") for a in assets))

    def _claim_rpc(self, action, row, extra):
        """Fail closed on an expired, replaced, or missing lease. No direct status PATCH."""
        kind = "planning" if "campaign" in action else "render"
        prefix = "planning" if kind == "planning" else "render"
        attempt_key = "planning_attempts" if kind == "planning" else "attempts"
        token = row.get(prefix + "_claim_token")
        attempt = row.get(attempt_key)
        if not token or type(attempt) is not int or attempt < 1:
            raise StorageUnavailable("missing fenced worker claim")
        payload = {"p_id": canonical_uuid(row["id"]), "p_attempt": attempt,
                   "p_token": canonical_uuid(token), **extra}
        result = self.request("rpc/" + action, method="POST", data=payload)
        if result is not True:
            raise StorageUnavailable("stale or revoked worker claim")

    def finish(self, row, campaign):
        cid = canonical_uuid(row["id"])
        if campaign["id"] != cid or campaign["shop_id"] != row["shop_id"]:
            raise StorageUnavailable("wrong campaign owner")
        days = [{
            "id": day["id"], "campaign_id": cid, "shop_id": row["shop_id"],
            "day_index": day["day_index"], "scheduled_date": day["scheduled_date"],
            "topic": day["topic"], "linkedin": day["linkedin"],
            "instagram": day["instagram"],
        } for day in campaign["days"]]
        self._claim_rpc("complete_campaign_claim", row, {"p_days": days})

    def fail(self, row, code, *, permanent=False):
        self._claim_rpc("fail_campaign_claim", row,
                        {"p_code": code, "p_permanent": bool(permanent)})

    def claim_outbox(self, limit=20):
        rows = self.request("rpc/claim_outbox_events", method="POST", data={"p_limit": limit})
        if not isinstance(rows, list):
            raise StorageUnavailable("invalid outbox claim response")
        return rows

    def confirm_outbox(self, event, sent):
        result = self.request("rpc/confirm_outbox_event", method="POST", data={
            "p_id": canonical_uuid(event["id"]),
            "p_token": canonical_uuid(event["lease_token"]), "p_sent": bool(sent)})
        if result is not True:
            raise StorageUnavailable("outbox delivery lease lost")

    def record_poison(self, kind, fingerprint, job_id=None):
        if kind not in ("planning", "render"):
            raise ValueError("invalid queue kind")
        result = self.request("rpc/record_poison_event", method="POST", data={
            "p_kind": kind, "p_fingerprint": fingerprint,
            "p_job_id": canonical_uuid(job_id) if job_id else None})
        if result is not True:
            raise StorageUnavailable("poison receipt not durable")

    def reconcile(self, limit=30):
        return self.request("rpc/reconcile_stale_jobs", method="POST",
                            data={"p_limit": limit})

    def valid_media(self, shop_id, asset_ids):
        sid = canonical_uuid(shop_id)
        ids = {canonical_uuid(asset_id) for asset_id in asset_ids}
        if not ids or len(ids) > 21:
            return False
        rows = self.request("media_assets", query={
            "select": "id,shop_id,license_name", "shop_id": "eq." + sid,
            "id": "in.(" + ",".join(sorted(ids)) + ")",
        })
        return (len(rows) == len(ids) and {row["id"] for row in rows} == ids
                and all(row["shop_id"] == sid and row.get("license_name") in
                        ("owned", "cc0", "royalty_free", "commercial") for row in rows))

    def find_render_job(self, shop_id, key):
        rows = self.request("render_jobs", query={
            "select": "id,status",
            "shop_id": "eq." + canonical_uuid(shop_id),
            "idempotency_key": "eq." + key, "limit": "1",
        })
        return rows[0] if rows else None

    def insert_render_job(self, row):
        result = self.request("render_jobs", method="POST", data=row)
        if len(result) != 1 or result[0]["id"] != row["id"]:
            raise StorageUnavailable("render job not persisted")

    def fail_render_job(self, job_id, shop_id, reason):
        self.request("render_jobs", method="PATCH", query={
            "id": "eq." + canonical_uuid(job_id),
            "shop_id": "eq." + canonical_uuid(shop_id),
        }, data={"status": "FAILED", "error_code": reason})


    def render_status(self, job_id):
        items = self.request("render_jobs", query={
            "select": "status", "id": "eq." + canonical_uuid(job_id), "limit": "1",
        })
        return items[0]["status"] if items else None

    def claim_render(self, job_id):
        return self.request("rpc/claim_render_job", method="POST",
                            data={"p_id": canonical_uuid(job_id)})

    def render_authorized(self, job):
        sid, uid = canonical_uuid(job["shop_id"]), canonical_uuid(job["requested_by"])
        membership = self.request("shop_memberships", query={
            "select": "role", "shop_id": "eq." + sid, "user_id": "eq." + uid,
            "active": "eq.true", "limit": "1",
        })
        return bool(membership) and membership[0]["role"] in ("OWNER", "EDITOR")

    def render_sources(self, job):
        sid, cid, did = [canonical_uuid(job[field]) for field in
                         ("shop_id", "campaign_id", "day_id")]
        campaigns = self.request("campaigns", query={
            "select": "id,shop_id,status", "id": "eq." + cid,
            "shop_id": "eq." + sid, "limit": "1",
        })
        days = self.request("campaign_days", query={
            "select": "id,shop_id,campaign_id,day_index,instagram,review_status",
            "id": "eq." + did, "campaign_id": "eq." + cid,
            "shop_id": "eq." + sid, "limit": "1",
        })
        if len(campaigns) != 1 or len(days) != 1:
            raise StorageUnavailable("render source missing")
        reel = days[0]["instagram"]["reel"]
        ids = {canonical_uuid(s["asset_id"]) for s in reel["storyboard"]}
        if reel.get("music_asset_id"):
            ids.add(canonical_uuid(reel["music_asset_id"]))
        assets = self.request("media_assets", query={
            "select": "id,shop_id,storage_bucket,object_path,mime_type,source,license_name,license_url,attribution",
            "shop_id": "eq." + sid, "id": "in.(" + ",".join(sorted(ids)) + ")",
        })
        if len(assets) != len(ids):
            raise StorageUnavailable("missing authorized render asset")
        return campaigns[0], days[0], {a["id"]: a for a in assets}

    def complete_render(self, job, object_path):
        self._claim_rpc("complete_render_claim", job, {"p_object_path": object_path})

    def render_failure(self, job, code, permanent=False):
        self._claim_rpc("fail_render_claim", job,
                        {"p_code": code, "p_permanent": bool(permanent)})
