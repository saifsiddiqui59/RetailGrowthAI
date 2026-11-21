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
