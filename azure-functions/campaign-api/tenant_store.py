"""RLS-scoped Supabase PostgREST calls using the VERIFIED user's access token.

No service_role credentials are used. Response IDs and tenant roles are verified
server-side. HTTP errors never return raw PostgREST error bodies to clients.
"""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import UUID

from security import AuthenticationError


class StorageUnavailable(RuntimeError):
    pass


def canonical_uuid(value):
    try:
        parsed = UUID(str(value))
        if str(parsed) != value:
            raise ValueError("noncanonical UUID")
        return str(parsed)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("invalid UUID") from exc


class TenantStore:
    def __init__(self, origin: str, publishable_key: str, transport=None):
        if not origin.startswith("https://") or not publishable_key:
            raise ValueError("Supabase HTTPS origin and publishable key required")
        self.origin = origin.rstrip("/")
        self.key = publishable_key
        self.transport = transport or urlopen

    def _request(self, table, token, *, query=None, method="GET", data=None):
        if table not in {"shop_memberships", "media_assets", "campaigns", "campaign_days", "render_jobs"}:
            raise ValueError("unsupported table")
        url = self.origin + "/rest/v1/" + table
        if query:
            url += "?" + urlencode(query, safe="(),.*")
        headers = {
            "apikey": self.key, "Authorization": "Bearer " + token,
            "Accept": "application/json", "Content-Type": "application/json",
        }
        if method != "GET":
            headers["Prefer"] = "return=representation"
        raw = None if data is None else json.dumps(data).encode("utf-8")
        request = Request(url, headers=headers, method=method, data=raw)
        try:
            with self.transport(request, timeout=8) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise AuthenticationError("database denied user token") from exc
            raise StorageUnavailable("database request rejected") from exc
        except (URLError, OSError, json.JSONDecodeError) as exc:
            raise StorageUnavailable("database unavailable") from exc

    def member(self, token, user_id, shop_id, *, write=False):
        sid, uid = canonical_uuid(shop_id), canonical_uuid(user_id)
        results = self._request("shop_memberships", token, query={
            "select": "role", "shop_id": "eq." + sid, "user_id": "eq." + uid,
            "active": "eq.true", "limit": "1",
        })
        return bool(results) and results[0].get("role") in (
            ("OWNER", "EDITOR") if write else ("OWNER", "EDITOR", "VIEWER")
        )

    def assets(self, token, shop_id, asset_ids):
        sid = canonical_uuid(shop_id)
        if not asset_ids:
            return False
        ids = [canonical_uuid(i) for i in asset_ids]
        if len(ids) != len(set(ids)):
            return False
        found = self._request("media_assets", token, query={
            "select": "id", "shop_id": "eq." + sid,
            "id": "in.(" + ",".join(ids) + ")",
        })
        return {item["id"] for item in found} == set(ids)

    def campaign(self, token, user_id, campaign_id):
        cid = canonical_uuid(campaign_id)
        rows = self._request("campaigns", token, query={
            "select": "id,shop_id,status", "id": "eq." + cid, "limit": "1",
        })
        if len(rows) != 1:
            return None
        row = rows[0]
        sid = canonical_uuid(row["shop_id"])
        if row["id"] != cid or not self.member(token, user_id, sid):
            return None
        days = self._request("campaign_days", token, query={
            "select": "id,campaign_id,shop_id,day_index,scheduled_date,topic,linkedin,instagram,review_status",
            "campaign_id": "eq." + cid, "shop_id": "eq." + sid,
            "order": "day_index.asc",
        })
        if any(d["shop_id"] != sid or d["campaign_id"] != cid for d in days):
            raise StorageUnavailable("inconsistent tenant records")
        return {"id": cid, "shop_id": sid, "status": row["status"], "days": days}

    def save_pending(self, token, user_id, campaign_id, brief):
        rows = self._request("campaigns", token, method="POST", data={
            "id": campaign_id, "shop_id": brief.shop_id, "created_by": user_id,
            "brief": brief.brief, "duration_days": brief.duration_days,
            "start_date": brief.start_date.isoformat(), "timezone": brief.timezone,
            "language": brief.language, "platforms": list(brief.platforms),
            "offer": None if brief.offer is None else {
                "description": brief.offer.description,
                "valid_until": brief.offer.valid_until.isoformat(),
            },
            "status": "PLANNING",
            "media_asset_ids": list(brief.media_asset_ids),
        })
        if len(rows) != 1 or rows[0].get("id") != campaign_id:
            raise StorageUnavailable("campaign insert verification failed")

    def fail(self, token, campaign_id):
        self._request("campaigns", token, method="PATCH",
                      query={"id": "eq." + canonical_uuid(campaign_id)},
                      data={"status": "FAILED"})


    def render_job(self, token, user_id, job_id):
        jid = canonical_uuid(job_id)
        found = self._request("render_jobs", token, query={
            "select": "id,shop_id,status,output_asset_id,error_code",
            "id": "eq." + jid, "limit": "1",
        })
        if len(found) != 1 or found[0]["id"] != jid:
            return None
        item = found[0]
        if not self.member(token, user_id, item["shop_id"]):
            return None
        return item

    def asset(self, token, shop_id, asset_id):
        sid, aid = canonical_uuid(shop_id), canonical_uuid(asset_id)
        rows = self._request("media_assets", token, query={
            "select": "id,shop_id,storage_bucket,object_path,mime_type",
            "id": "eq." + aid, "shop_id": "eq." + sid, "limit": "1",
        })
        if len(rows) != 1 or rows[0]["shop_id"] != sid or rows[0]["id"] != aid:
            return None
        result = rows[0]
        if result["storage_bucket"] != "retailgrowth-media" or not result["object_path"].startswith(sid + "/"):
            return None
        return result

    def sign_download(self, token, shop_id, object_path):
        """Request a short-lived link with the real user's RLS-scoped JWT."""
        from urllib.parse import quote
        sid = canonical_uuid(shop_id)
        if (not isinstance(object_path, str) or not object_path.startswith(sid + "/")
                or ".." in object_path.split("/") or "\\" in object_path):
            raise ValueError("invalid private object path")
        prefix = "/object/sign/retailgrowth-media/" + quote(object_path, safe="/")
        req = Request(
            self.origin + "/storage/v1" + prefix, method="POST",
            data=b'{"expiresIn":60}',
            headers={"apikey": self.key, "Authorization": "Bearer " + token,
                     "Content-Type": "application/json"},
        )
        try:
            with self.transport(req, timeout=8) as response:
                result = json.loads(response.read().decode())
        except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
            raise StorageUnavailable("signed media authorization unavailable") from exc
        link = result.get("signedURL") if isinstance(result, dict) else None
        if not isinstance(link, str) or not link.startswith(prefix + "?token="):
            raise StorageUnavailable("invalid signed storage response")
        return self.origin + "/storage/v1" + link

    def save_day(self, token, shop_id, campaign_id, day_id, expected, changes):
        """RLS-authenticated RPC; false means stale, locked or revoked rights."""
        sid, cid, did = (canonical_uuid(x) for x in (shop_id, campaign_id, day_id))
        request = Request(
            self.origin + "/rest/v1/rpc/save_campaign_day",
            method="POST",
            data=json.dumps({
                "p_shop_id": sid, "p_campaign_id": cid, "p_day_id": did,
                "p_expected": expected, "p_changes": changes,
            }).encode("utf-8"),
            headers={
                "apikey": self.key, "Authorization": "Bearer " + token,
                "Content-Type": "application/json", "Accept": "application/json",
            },
        )
        try:
            with self.transport(request, timeout=8) as response:
                value = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise AuthenticationError("draft save denied") from exc
            raise StorageUnavailable("draft save rejected") from exc
        except (URLError, OSError, json.JSONDecodeError) as exc:
            raise StorageUnavailable("draft save unavailable") from exc
        if type(value) is not bool:
            raise StorageUnavailable("unexpected draft save response")
        return value
