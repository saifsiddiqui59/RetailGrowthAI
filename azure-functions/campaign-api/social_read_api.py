"""Read-only Part 2 tenant-scoped HTTP surface; disabled by default in Azure.

Uses the authenticated user's token for PostgREST RLS; neither client secrets
nor provider access tokens are ever loaded, returned or logged.
"""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

from security import AuthenticationError
from tenant_store import StorageUnavailable, canonical_uuid


class _NoRedirect(HTTPRedirectHandler):
    """Never send the retailer JWT to another host after a redirect."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_FIELDS = {
    "accounts": ("social_accounts",
                 "id,shop_id,provider,provider_account_id,display_name,connection_status,connected_at"),
    "jobs": ("social_publish_jobs",
             "id,shop_id,social_account_id,campaign_day_id,provider,revision,caption,media_asset_id,status,scheduled_at,timezone,remote_post_id,attempts,last_error_code"),
    "audit": ("social_publish_audit",
              "id,shop_id,job_id,actor_user_id,event_code,recorded_at"),
    "days": ("campaign_days",
             "id,shop_id,campaign_id,day_index,scheduled_date,topic,review_status,linkedin"),
}


class SocialReadStore:
    def __init__(self, origin, publishable_key, transport=None):
        uri = urlsplit(origin) if isinstance(origin, str) else None
        if (uri is None or uri.scheme != "https" or not uri.hostname
                or uri.username or uri.password or uri.query or uri.fragment
                or uri.path not in ("", "/") or uri.port not in (None, 443)):
            raise ValueError("one HTTPS Supabase origin required")
        if not publishable_key:
            raise ValueError("publishable key required")
        self.origin = origin.rstrip("/")
        self.key = publishable_key
        self.transport = transport or build_opener(_NoRedirect()).open

    def list_rows(self, token, shop_id, resource):
        # Fixed table/field mapping; no caller-controlled query columns or order.
        table, fields = _FIELDS[resource]
        sid = canonical_uuid(shop_id)
        uri = self.origin + "/rest/v1/" + table + "?" + urlencode({
            "select": fields, "shop_id": "eq." + sid,
            "order": "id.asc", "limit": "100",
        })
        req = Request(uri, method="GET", headers={
            "apikey": self.key,
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
        })
        try:
            with self.transport(req, timeout=8) as res:
                if res.geturl() != req.full_url:
                    raise StorageUnavailable("unexpected social read redirect")
                payload = res.read(1048577)
                if len(payload) > 1048576:
                    raise StorageUnavailable("oversized tenant read")
                rows = json.loads(payload.decode("utf-8"))
        except HTTPError as err:
            if err.code in (401, 403):
                raise AuthenticationError("RLS denied social read") from err
            raise StorageUnavailable("social store unavailable") from err
        except (URLError, OSError, UnicodeDecodeError, json.JSONDecodeError) as err:
            raise StorageUnavailable("social store unavailable") from err
        if (not isinstance(rows, list) or len(rows) > 100
                or any(not isinstance(row, dict) or row.get("shop_id") != sid for row in rows)):
            raise StorageUnavailable("untrusted social response scope")
        return rows


class SocialReadAPI:
    def __init__(self, verify_token, tenant_store, social_store):
        self.verify_token = verify_token
        self.tenant_store = tenant_store
        self.social_store = social_store

    def handle(self, method, resource, authorization, shop_id):
        try:
            if method != "GET" or resource not in _FIELDS:
                return 404, {"error": "NOT_FOUND"}
            if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
                raise AuthenticationError("Bearer token required")
            token = authorization[7:].strip()
            user_id = self.verify_token(token)
            sid = canonical_uuid(shop_id)
            if not self.tenant_store.member(token, user_id, sid):
                return 403, {"error": "FORBIDDEN"}
            rows = self.social_store.list_rows(token, sid, resource)
            # Defense in depth: credentials and ciphertext not allowed in response.
            safe_keys = set(_FIELDS[resource][1].split(","))
            sanitized = [{k: row[k] for k in safe_keys if k in row} for row in rows]
            if resource == "jobs":
                for job in sanitized:
                    code = job.get("last_error_code")
                    if code is not None and (not isinstance(code, str)
                            or re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code) is None):
                        job.pop("last_error_code", None)
                    attempts = job.get("attempts")
                    if attempts is not None and (type(attempts) is not int
                            or not 0 <= attempts <= 5):
                        job.pop("attempts", None)
            if resource == "audit":
                for event in sanitized:
                    name = event.get("event_code")
                    if (not isinstance(name, str) or
                            re.fullmatch(r"[A-Z][A-Z0-9_]{0,79}", name) is None):
                        raise StorageUnavailable("invalid audit event")
            return 200, {resource: sanitized}
        except AuthenticationError:
            return 401, {"error": "UNAUTHORIZED"}
        except (TypeError, ValueError):
            return 400, {"error": "INVALID_REQUEST"}
        except (StorageUnavailable, KeyError):
            return 503, {"error": "SERVICE_UNAVAILABLE"}
