"""Tenant-safe, optimistic edit of an already generated DRAFT campaign day.

An editor may change only the text and reel metadata. Day/tenant identity,
review state, schedule, and asset permissions are never taken from the browser.
The database RPC rechecks active membership and parent state atomically.
"""
from ai_agents.schemas import validate_campaign
from tenant_store import canonical_uuid, StorageUnavailable


class DraftAPI:
    def __init__(self, store):
        self.store = store

    def save(self, token, user_id, campaign_id, day_id, body):
        cid, did = canonical_uuid(campaign_id), canonical_uuid(day_id)
        if not isinstance(body, dict) or set(body) != {"topic", "linkedin", "instagram"}:
            return 400, {"error": "INVALID_REQUEST"}
        campaign = self.store.campaign(token, user_id, cid)
        if campaign is None:
            return 404, {"error": "NOT_FOUND"}
        if campaign["status"] != "DRAFT":
            return 409, {"error": "CAMPAIGN_NOT_DRAFT"}
        matching = [day for day in campaign["days"] if day["id"] == did]
        if len(matching) != 1:
            return 404, {"error": "NOT_FOUND"}
        old = matching[0]
        sid = canonical_uuid(campaign["shop_id"])
        if not self.store.member(token, user_id, sid, write=True):
            return 403, {"error": "FORBIDDEN"}

        replacement = {**old, **body}
        candidate = {**campaign, "days": [
            replacement if item["id"] == did else item for item in campaign["days"]
        ]}
        validate_campaign(candidate)
        reel = replacement["instagram"]["reel"]
        assets = [shot["asset_id"] for shot in reel["storyboard"]]
        if reel["music_asset_id"] is not None:
            assets.append(reel["music_asset_id"])
        if replacement["instagram"]["banner_asset_id"] is not None:
            assets.append(replacement["instagram"]["banner_asset_id"])
        # An asset ID is a reference, never proof of ownership or rights.
        if not self.store.assets(token, sid, list(dict.fromkeys(assets))):
            return 403, {"error": "ASSET_ACCESS_DENIED"}

        old_fields = {field: old[field] for field in body}
        if not self.store.save_day(token, sid, cid, did, old_fields, body):
            return 409, {"error": "EDIT_CONFLICT"}
        refreshed = self.store.campaign(token, user_id, cid)
        if refreshed is None:
            raise StorageUnavailable("saved day inaccessible")
        saved = [day for day in refreshed["days"] if day["id"] == did]
        if len(saved) != 1:
            raise StorageUnavailable("saved day missing")
        return 200, {"day": saved[0]}
