"""Feature #4 additive authenticated HTTP API contract, NOT a registered Azure route.

Coordinator-owned Azure Functions HTTPAPI may compose this after its existing
JWT verifier has produced token + user_id. The injected stores MUST be the
existing Supabase RLS user store and transactional service admin, not request
data. Does not touch the legacy /campaigns/:id/renders FFmpeg API.
"""
import hashlib
import json
import re
from uuid import UUID

ALLOWED_STATES = {"QUEUED", "RUNNING", "SUCCEEDED", "FAILED"}
APPROVAL = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
TENANT_MEDIA = re.compile(
    r"^(?P<shop>[0-9a-f-]{36})/renders/(?P<job>[0-9a-f-]{36})/"
    r"(?P<lease>[0-9a-f-]{36})\.mp4$"
)


def _id(value):
    if type(value) is not str:
        raise ValueError("Invalid resource ID")
    parsed = str(UUID(value))
    if parsed != value or UUID(value).version is None:
        raise ValueError("Noncanonical resource ID")
    return value


def _receipt(raw, shop, expected_job=None):
    if type(raw) is not dict or raw.get("shop_id") != shop:
        raise ValueError("Feature4 job tenant mismatch")
    jid = _id(raw.get("id"))
    if expected_job is not None and jid != expected_job:
        raise ValueError("Feature4 job ID mismatch")
    state = raw.get("status")
    if state not in ALLOWED_STATES:
        raise ValueError("Unexpected Feature4 job status")
    return {"shop_id": shop, "job_id": jid, "status": state}


class Feature4HTTP:
    """All handlers receive JWT-verified user_id; owner supplies route bindings.

    Required injected user_store callbacks:
      campaign(jwt, user_id, campaign_id) -> RLS-limited record
      member(jwt, user_id, shop_id, write=bool) -> bool
      feature4_job(jwt, user_id, job_id) -> RLS-limited job
      asset(jwt, shop_id, asset_id) -> RLS-limited asset
      sign_download(jwt, shop_id, object_path) -> private signed HTTPS URL
    Required transactional admin:
      create_feature4_intent(item) -> immutable job row with id/shop/status;
    its ONE atomic transaction MUST reauthorize approved Feature #2 copy,
    media provenance/rights, recorded tenant ownership, revision, plan/quota,
    idempotency and output media ledger; it MUST NOT infer approval from the
    browser's 'authorized' flags, or create double reservations.
    """
    def __init__(self, users, admin):
        self.users, self.admin = users, admin

    def create(self, token, user_id, campaign_id, body):
        cid = _id(campaign_id)
        if type(body) is not dict or set(body) != {
            "shop_id", "campaign_id", "approval_id", "draft"
        }:
            return 400, {"error": "INVALID_REQUEST"}
        try:
            sid = _id(body["shop_id"])
            if _id(body["campaign_id"]) != cid:
                return 400, {"error": "INVALID_REQUEST"}
        except (TypeError, ValueError, AttributeError):
            return 400, {"error": "INVALID_REQUEST"}
        approval = body["approval_id"]
        draft = body["draft"]
        if (type(approval) is not str or not APPROVAL.fullmatch(approval)
                or type(draft) is not dict or draft.get("version") != "rg_video_v2"
                or draft.get("shop_id") != sid
                or draft.get("duration_seconds") not in (15, 30, 60)
                or type(draft.get("scenes")) is not list
                or not 1 <= len(draft["scenes"]) <= 12
                or len(json.dumps(draft, separators=(",", ":"))) > 64_000):
            return 400, {"error": "INVALID_REQUEST"}
        # RLS check before any service-role mutation, with an exact shop match.
        campaign = self.users.campaign(token, user_id, cid)
        if campaign is None or campaign.get("shop_id") != sid:
            return 404, {"error": "NOT_FOUND"}
        if not self.users.member(token, user_id, sid, write=True):
            return 403, {"error": "FORBIDDEN"}
        # Derive rather than accept a caller-provided idempotency key. A
        # response timeout does NOT authorize a browser POST replay.
        digest = hashlib.sha256(json.dumps(
            [sid, user_id, cid, approval, draft], sort_keys=True,
            separators=(",", ":"), ensure_ascii=True,
        ).encode()).hexdigest()
        # DB implementation MUST authenticate approved script/media revisions
        # and perform insert/claim/outbox/credit reservation transactionally.
        result = self.admin.create_feature4_intent({
            "shop_id": sid, "campaign_id": cid, "requested_by": user_id,
            "approval_id": approval, "draft": draft, "idempotency_key": digest,
            "preset": "feature4_reel_v1",
        })
        receipt = _receipt(result, sid)
        return (202 if receipt["status"] in ("QUEUED", "RUNNING") else 200), receipt

    def get(self, token, user_id, job_id):
        jid = _id(job_id)
        job = self.users.feature4_job(token, user_id, jid)
        if job is None:
            return 404, {"error": "NOT_FOUND"}
        sid = _id(job["shop_id"])
        if not self.users.member(token, user_id, sid, write=False):
            return 404, {"error": "NOT_FOUND"}
        receipt = _receipt(job, sid, jid)
        if receipt["status"] == "FAILED":
            receipt["error_code"] = str(job.get("error_code") or "RENDER_FAILED")[:70]
        return 200, receipt

    def download(self, token, user_id, job_id):
        jid = _id(job_id)
        job = self.users.feature4_job(token, user_id, jid)
        if job is None:
            return 404, {"error": "NOT_FOUND"}
        sid = _id(job["shop_id"])
        if not self.users.member(token, user_id, sid, write=False):
            return 404, {"error": "NOT_FOUND"}
        _receipt(job, sid, jid)
        if job["status"] != "SUCCEEDED" or not job.get("output_asset_id"):
            return 409, {"error": "OUTPUT_NOT_READY"}
        asset = self.users.asset(token, sid, job["output_asset_id"])
        if (type(asset) is not dict or asset.get("shop_id") != sid or
                asset.get("mime_type") != "video/mp4" or
                asset.get("storage_bucket") != "retailgrowth-media"):
            return 404, {"error": "OUTPUT_NOT_FOUND"}
        match = TENANT_MEDIA.fullmatch(asset.get("object_path") or "")
        if (match is None or match["shop"] != sid or match["job"] != jid):
            return 404, {"error": "OUTPUT_NOT_FOUND"}
        _id(match["lease"])
        url = self.users.sign_download(token, sid, asset["object_path"])
        # URL is produced ONLY by the same backend storage signing code, not
        # fetched from browser input or an external AI provider.
        return 200, {"shop_id": sid, "job_id": jid, "url": url}
