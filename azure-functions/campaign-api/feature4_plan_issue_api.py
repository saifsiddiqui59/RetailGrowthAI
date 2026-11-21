"""Server-owned saved F2 campaign -> draft Feature4 review issuance.

Browser sends ONLY a saved day UUID. Every campaign scene/media/text is
re-fetched using the verified user's JWT under current RLS; media source and
private owned rights are enforced before inserting a source-only DRAFT via
service_role. The separate explicit SQL review must happen before any render.
No AI provider, billing, queue dispatch or approval occurs here.
"""
from tenant_store import canonical_uuid, StorageUnavailable
from feature2_saved_campaign_proposal import saved_campaign_creative_proposal


class Feature4PlanIssueAPI:
    def __init__(self, users, admin):
        if admin is None:
            raise ValueError("Feature4 source issuance requires backend database")
        self.users, self.admin = users, admin

    def create(self, token, user_id, campaign_id, body):
        cid = canonical_uuid(campaign_id)
        if type(body) is not dict or set(body) != {"day_id"}:
            return 400, {"error": "INVALID_REQUEST"}
        did = canonical_uuid(body["day_id"])
        campaign = self.users.campaign(token, user_id, cid)
        if campaign is None:
            return 404, {"error": "NOT_FOUND"}
        sid = canonical_uuid(campaign["shop_id"])
        if not self.users.member(token, user_id, sid, write=True):
            return 403, {"error": "FORBIDDEN"}
        # Validate only server-fetched source; never accept a copy, offer,
        # media rights flag, reviewer, digest or plan ID from the POST.
        days = [d for d in campaign.get("days", []) if d.get("id") == did]
        if len(days) != 1 or not isinstance(days[0], dict):
            return 404, {"error": "NOT_FOUND"}
        reel = days[0].get("instagram", {}).get("reel", {})
        if type(reel) is not dict or type(reel.get("storyboard")) is not list:
            return 409, {"error": "SOURCE_DRAFT_NOT_READY"}
        # A bare read result from another shop/unsupported source can never
        # be promoted; current owner-held license claims still need review.
        ids = []
        for scene in reel["storyboard"]:
            if type(scene) is not dict:
                return 409, {"error": "SOURCE_DRAFT_NOT_READY"}
            try:
                ids.append(canonical_uuid(scene["asset_id"]))
            except (KeyError, ValueError):
                return 409, {"error": "SOURCE_DRAFT_NOT_READY"}
        ids = list(dict.fromkeys(ids))
        if not 1 <= len(ids) <= 12:
            return 409, {"error": "SOURCE_DRAFT_NOT_READY"}
        records = self.users._request("media_assets", token, query={
            "select": "id,shop_id,storage_bucket,object_path,mime_type,source,license_name",
            "shop_id": "eq." + sid,
            "id": "in.(" + ",".join(ids) + ")",
            "limit": "13",
        })
        if (type(records) is not list or len(records) != len(ids)
                or {r.get("id") for r in records} != set(ids)):
            return 403, {"error": "ASSET_ACCESS_DENIED"}
        try:
            prepared = saved_campaign_creative_proposal(campaign, did, records)
        except (ValueError, TypeError, KeyError):
            return 409, {"error": "SOURCE_DRAFT_NOT_READY"}
        digest = prepared["proposal_sha256"]
        # Unique (shop_id,proposal_sha256) allows safe read-back after an
        # uncertain write; NEVER auto-repeat a blind service-role INSERT.
        query = {"select": "id,shop_id,campaign_id,proposal_sha256,state",
                 "shop_id": "eq." + sid,
                 "proposal_sha256": "eq." + digest, "limit": "2"}
        rows = self.admin.request("feature4_creative_plans", query=query)
        if type(rows) is not list or len(rows) > 1:
            raise StorageUnavailable("ambiguous previously issued F2 plan")
        if not rows:
            try:
                rows = self.admin.request("feature4_creative_plans",
                    method="POST", data={
                        "shop_id": sid, "campaign_id": cid,
                        "issued_by": user_id,
                        "proposal": prepared["proposal"],
                        "proposal_sha256": digest,
                        "media_asset_ids": prepared["media_asset_ids"],
                        "state": "DRAFT",
                    })
            except StorageUnavailable:
                # A lost HTTP ACK may already have committed the row. Read
                # idempotency key once, but do not submit a second INSERT.
                rows = self.admin.request("feature4_creative_plans", query=query)
        if type(rows) is not list or len(rows) != 1:
            raise StorageUnavailable("unconfirmed F2 proposal insertion")
        row = rows[0]
        if (type(row) is not dict or row.get("shop_id") != sid
                or row.get("campaign_id") != cid or
                row.get("proposal_sha256") != digest or
                row.get("state") not in ("DRAFT", "APPROVED")):
            return 409, {"error": "CREATIVE_REVISION_NOT_CURRENT"}
        return (201 if row["state"] == "DRAFT" else 200), {
            "plan_id": canonical_uuid(row["id"]), "shop_id": sid,
            "campaign_id": cid, "status": row["state"],
            "proposal_sha256": digest,
        }
