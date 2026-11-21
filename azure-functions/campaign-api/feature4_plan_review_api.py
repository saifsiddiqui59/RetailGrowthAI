"""JWT+RLS Feature2→Feature4 creative review, NOT GitHub PR approval.

Real retailer editorial approval requires an explicit signed UI action
against a service-issued immutable plan; source hash, active tenant/editor,
media references and review digest are checked atomically by SQL. No browser
can mint a source plan, select arbitrary external media or start GPU/billing.
"""
import re

from tenant_store import canonical_uuid

_SHA = re.compile(r"^[0-9a-f]{64}$")


class Feature4PlanReviewAPI:
    def __init__(self, users):
        self.users = users

    def get(self, token, user_id, plan_id):
        pid = canonical_uuid(plan_id)
        plan = self.users.feature4_creative_plan(token, user_id, pid)
        if plan is None:
            return 404, {"error": "NOT_FOUND"}
        sid = canonical_uuid(plan["shop_id"])
        if not self.users.member(token, user_id, sid, write=False):
            return 404, {"error": "NOT_FOUND"}
        return 200, {
            "plan_id": pid,
            "shop_id": sid,
            "campaign_id": canonical_uuid(plan["campaign_id"]),
            "proposal": plan["proposal"],
            "proposal_sha256": plan["proposal_sha256"],
            "status": plan["state"],
            "review_hash": plan["review_sha256"],
            "approved_direction": plan["approved_direction"],
        }

    def review(self, token, user_id, plan_id, body):
        pid = canonical_uuid(plan_id)
        if type(body) is not dict or set(body) != {"expected_source_sha256"}:
            return 400, {"error": "INVALID_REQUEST"}
        digest = body["expected_source_sha256"]
        if type(digest) is not str or _SHA.fullmatch(digest) is None:
            return 400, {"error": "INVALID_REQUEST"}
        plan = self.users.feature4_creative_plan(token, user_id, pid)
        if plan is None or plan["proposal_sha256"] != digest:
            return 404, {"error": "NOT_FOUND"}
        sid = canonical_uuid(plan["shop_id"])
        if not self.users.member(token, user_id, sid, write=True):
            return 403, {"error": "FORBIDDEN"}
        # The database, not this intermediate RLS snapshot, is authoritative:
        # it locks the plan, validates current media, copy hash and membership,
        # and creates the immutable approved SHA on a single transaction.
        result = self.users.feature4_review_cpu_plan(token, pid, digest)
        if result is None:
            return 409, {"error": "REVIEW_STALE_OR_DENIED"}
        if (type(result) is not dict or result.get("status") != "APPROVED"
                or result.get("shop_id") != sid
                or result.get("campaign_id") != plan["campaign_id"]
                or result.get("approval_id") != pid
                or type(result.get("review_hash")) is not str
                or _SHA.fullmatch(result["review_hash"]) is None):
            return 503, {"error": "SERVICE_UNAVAILABLE"}
        return 200, {"plan_id": pid, "shop_id": sid,
                     "campaign_id": plan["campaign_id"],
                     "review_hash": result["review_hash"], "status": "APPROVED"}

    def revoke(self, token, user_id, plan_id, body):
        pid = canonical_uuid(plan_id)
        if body not in (None, {}):
            return 400, {"error": "INVALID_REQUEST"}
        plan = self.users.feature4_creative_plan(token, user_id, pid)
        if plan is None:
            return 404, {"error": "NOT_FOUND"}
        sid = canonical_uuid(plan["shop_id"])
        if not self.users.member(token, user_id, sid, write=True):
            return 403, {"error": "FORBIDDEN"}
        if self.users.feature4_revoke_cpu_plan(token, pid) is not True:
            return 409, {"error": "REVOKE_DENIED_OR_STALE"}
        return 200, {"plan_id": pid, "shop_id": sid, "status": "REVOKED"}


# CPU-only render endpoint remains co-located with editorial review in the
# existing Azure package module. No extra function ZIP member is added.
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MP4 = re.compile(
    r"^(?P<shop>[0-9a-f-]{36})/renders/"
    r"(?P<job>[0-9a-f-]{36})/(?P<lease>[0-9a-f-]{36})\.mp4$")
_STATES = {"QUEUED", "RUNNING", "SUCCEEDED", "FAILED"}


class Feature4CpuRenderAPI:
    def __init__(self, users):
        self.users = users

    def _review(self, token, user_id, plan_id, shop_id, *, write=False):
        plan = self.users.feature4_creative_plan(token, user_id, plan_id)
        if (plan is None or plan.get("shop_id") != shop_id
                or plan.get("state") != "APPROVED"
                or type(plan.get("review_sha256")) is not str
                or not _SHA256.fullmatch(plan["review_sha256"])
                or not self.users.member(token, user_id, shop_id, write=write)):
            return None
        return plan

    @staticmethod
    def _receipt(row, shop_id, expected_id=None):
        if type(row) is not dict or row.get("shop_id") != shop_id:
            raise ValueError("Foreign CPU render receipt")
        job = canonical_uuid(row.get("id") or row.get("job_id"))
        if expected_id and job != expected_id:
            raise ValueError("CPU render receipt job mismatch")
        status = row.get("status")
        if status not in _STATES:
            raise ValueError("Invalid CPU render state")
        result = {"shop_id": shop_id, "job_id": job, "status": status}
        if status == "FAILED":
            result["error_code"] = str(row.get("error_code") or "RENDER_FAILED")[:70]
        return result

    def create(self, token, user_id, campaign_id, body):
        cid = canonical_uuid(campaign_id)
        if type(body) is not dict or set(body) != {
            "plan_id", "expected_review_hash"
        }:
            return 400, {"error": "INVALID_REQUEST"}
        try:
            pid = canonical_uuid(body["plan_id"])
        except (TypeError, AttributeError, ValueError):
            return 400, {"error": "INVALID_REQUEST"}
        digest = body["expected_review_hash"]
        if type(digest) is not str or not _SHA256.fullmatch(digest):
            return 400, {"error": "INVALID_REQUEST"}
        plan = self.users.feature4_creative_plan(token, user_id, pid)
        if plan is None or plan.get("campaign_id") != cid:
            return 404, {"error": "NOT_FOUND"}
        sid = canonical_uuid(plan["shop_id"])
        approved = self._review(token, user_id, pid, sid, write=True)
        if approved is None or approved["review_sha256"] != digest:
            return 409, {"error": "REVIEW_STALE_OR_DENIED"}
        # No v2 storyboard is transmitted: the SQL RPC uses ONLY a reviewed
        # source plan and derives job, same-period quota and private outbox.
        item = self.users.feature4_submit_cpu_render(token, pid, digest)
        if item is None:
            return 409, {"error": "REVIEW_STALE_OR_DENIED"}
        receipt = self._receipt(item, sid)
        return (202 if receipt["status"] in ("QUEUED", "RUNNING") else 200), receipt

    def get(self, token, user_id, job_id):
        jid = canonical_uuid(job_id)
        row = self.users.feature4_job(token, user_id, jid)
        if row is None:
            return 404, {"error": "NOT_FOUND"}
        sid = canonical_uuid(row["shop_id"])
        if not self.users.member(token, user_id, sid, write=False):
            return 404, {"error": "NOT_FOUND"}
        return 200, self._receipt(row, sid, jid)

    def download(self, token, user_id, job_id):
        jid = canonical_uuid(job_id)
        row = self.users.feature4_job(token, user_id, jid)
        if row is None:
            return 404, {"error": "NOT_FOUND"}
        sid = canonical_uuid(row["shop_id"])
        if not self.users.member(token, user_id, sid, write=False):
            return 404, {"error": "NOT_FOUND"}
        self._receipt(row, sid, jid)
        if row["status"] != "SUCCEEDED" or not row.get("output_asset_id"):
            return 409, {"error": "OUTPUT_NOT_READY"}
        plan_id = canonical_uuid(row["plan_id"])
        approved = self._review(token, user_id, plan_id, sid)
        if (approved is None or approved.get("campaign_id") != row.get("campaign_id")
                or row.get("approved_review_sha256") != approved["review_sha256"]):
            return 404, {"error": "APPROVAL_REVOKED"}
        # Recheck current original rights against the immutable approved
        # media path/source/license snapshot. A revoked source invalidates
        # downloads even if its render finished before revocation.
        sources = approved.get("media_snapshot")
        if type(sources) is not list or not 1 <= len(sources) <= 12:
            return 404, {"error": "SOURCE_RIGHTS_REVOKED"}
        for item in sources:
            if type(item) is not dict or item.get("shop_id") != sid:
                return 404, {"error": "SOURCE_RIGHTS_REVOKED"}
            asset_id = canonical_uuid(item.get("id"))
            source = self.users.feature4_media(token, sid, asset_id)
            if (type(source) is not dict
                    or source.get("shop_id") != sid
                    or source.get("storage_bucket") != "retailgrowth-media"
                    or source.get("object_path") != item.get("path")
                    or source.get("mime_type") != item.get("mime")
                    or source.get("source") != "UPLOAD"
                    or source.get("license_name") != item.get("license")
                    or str(source.get("license_name") or "").lower() != "owned"):
                return 404, {"error": "SOURCE_RIGHTS_REVOKED"}
        asset = self.users.feature4_media(token, sid, row["output_asset_id"])
        if (type(asset) is not dict or asset.get("shop_id") != sid
                or asset.get("storage_bucket") != "retailgrowth-media"
                or asset.get("mime_type") != "video/mp4"
                or asset.get("source") != "GENERATED"):
            return 404, {"error": "OUTPUT_NOT_FOUND"}
        match = _MP4.fullmatch(asset.get("object_path") or "")
        if (match is None or match["shop"] != sid or match["job"] != jid):
            return 404, {"error": "OUTPUT_NOT_FOUND"}
        canonical_uuid(match["lease"])
        url = self.users.sign_download(token, sid, asset["object_path"])
        return 200, {"shop_id": sid, "job_id": jid, "url": url}
