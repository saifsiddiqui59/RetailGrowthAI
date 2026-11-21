"""RLS-scoped Supabase PostgREST calls using the VERIFIED user's access token.

No service_role credentials are used. Response IDs and tenant roles are verified
server-side. HTTP errors never return raw PostgREST error bodies to clients.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
from uuid import UUID

from security import AuthenticationError


class StorageUnavailable(RuntimeError):
    pass


class SubscriptionDenied(PermissionError):
    """Server-authored SQLSTATE for expired/suspended plan or exhausted meter."""
    def __init__(self, code):
        self.code = code
        super().__init__("Subscription action unavailable")


def canonical_uuid(value):
    try:
        parsed = UUID(str(value))
        if str(parsed) != value:
            raise ValueError("noncanonical UUID")
        return str(parsed)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("invalid UUID") from exc


class _RejectRedirects(HTTPRedirectHandler):
    """Do not forward a verified user's JWT or Supabase API key after redirects."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_NO_REDIRECT_OPENER = build_opener(_RejectRedirects())


class TenantStore:
    def __init__(self, origin: str, publishable_key: str, transport=None):
        if (not isinstance(origin, str) or not isinstance(publishable_key, str)
                or not publishable_key
                or any(ord(ch) <= 32 or ord(ch) == 127 for ch in origin)
                or "\\" in origin):
            raise ValueError("Supabase HTTPS origin and publishable key required")
        try:
            parsed = urlsplit(origin)
            parsed.port  # reject a malformed explicit port
            valid = (origin.startswith("https://") and parsed.scheme == "https"
                     and bool(parsed.hostname) and parsed.username is None
                     and parsed.password is None and parsed.path in ("", "/")
                     and not parsed.query and not parsed.fragment
                     and parsed.geturl() == origin)
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("Supabase HTTPS origin and publishable key required")
        self.origin = origin.rstrip("/")
        self.key = publishable_key
        self.transport = transport if transport is not None else _NO_REDIRECT_OPENER.open

    def _request(self, table, token, *, query=None, method="GET", data=None):
        if table not in {"shop_memberships", "media_assets", "campaigns", "campaign_days", "render_jobs", "poster_drafts", "poster_jobs", "business_profiles", "shop_content_drafts", "feature3_gpu_jobs", "feature4_creative_plans",
                         "rpc/feature4_review_cpu_plan", "rpc/feature4_revoke_cpu_plan",
                         "feature4_cpu_render_jobs", "rpc/feature4_submit_cpu_render"}:
            raise ValueError("unsupported table")
        # Feature4 proposals are service-issued and immutable to browsers.
        # Only current JWT-based narrow review/revoke RPCs can mutate them.
        if table == "feature4_cpu_render_jobs" and method != "GET":
            raise ValueError("F4 CPU jobs are always read-only under JWT")
        if table == "rpc/feature4_submit_cpu_render" and method != "POST":
            raise ValueError("F4 CPU rendering requires authenticated POST")
        if table == "feature4_creative_plans" and method != "GET":
            raise ValueError("Feature4 creative plans are read-only via JWT")
        if table in ("rpc/feature4_review_cpu_plan",
                     "rpc/feature4_revoke_cpu_plan") and method != "POST":
            raise ValueError("Feature4 editorial RPCs require POST")
        # Browser-JWT job history/status is SELECT-only. Claim, finish,
        # financial and private-output writes remain service-role RPCs.
        if table == "feature3_gpu_jobs" and method != "GET":
            raise ValueError("Feature3 GPU history is read-only")
        if table == "shop_content_drafts" and method != "GET":
            raise ValueError("content drafts are only writable through the backend")
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
            try:
                if exc.code in (400, 402, 409, 429, 500):
                    try:
                        response_code = json.loads(exc.read(4096)).get("code")
                    except (ValueError, AttributeError, TypeError):
                        response_code = None
                    if response_code in ("RG001", "RG002"):
                        raise SubscriptionDenied(response_code) from exc
                if exc.code in (401, 403):
                    raise AuthenticationError("database denied user token") from exc
                raise StorageUnavailable("database request rejected") from exc
            finally:
                exc.close()
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

    def feature3_source_asset(self, token, shop_id, asset_id):
        """JWT/RLS-backed registration proof, never a blob rights grant."""
        sid, aid = canonical_uuid(shop_id), canonical_uuid(asset_id)
        rows = self._request("media_assets", token, query={
            "select": "id,shop_id,storage_bucket,object_path,mime_type,"
                      "source,license_name,license_url,attribution",
            "shop_id": "eq." + sid, "id": "eq." + aid, "limit": "2",
        })
        if not isinstance(rows, list) or len(rows) != 1:
            return None
        item = rows[0]
        if not isinstance(item, dict):
            return None
        extensions = {"image/png": ".png", "image/jpeg": ".jpg",
                      "image/webp": ".webp"}
        mime = item.get("mime_type")
        ext = extensions.get(mime) if isinstance(mime, str) else None
        # License provenance is not a rights approval. Reject malformed
        # authorities rather than accepting any string starting with https://.
        license_url = item.get("license_url")
        valid_license_url = False
        if (isinstance(license_url, str) and 0 < len(license_url) <= 500 and
                all(32 < ord(ch) < 127 for ch in license_url)):
            try:
                parsed = urlsplit(license_url)
                valid_license_url = (
                    parsed.scheme == "https" and bool(parsed.hostname) and
                    parsed.username is None and parsed.password is None
                )
            except ValueError:
                pass
        if not ext or item.get("id") != aid or item.get("shop_id") != sid or (
            item.get("storage_bucket") != "retailgrowth-media" or
            item.get("source") != "UPLOAD" or
            item.get("object_path") != f"{sid}/uploads/{aid}{ext}" or
            item.get("license_name") not in
                ("owned", "cc0", "royalty_free", "commercial") or
            not isinstance(item.get("attribution"), str) or
            len(item["attribution"].strip()) < 10 or
            (item["license_name"] != "owned" and not valid_license_url)
        ):
            return None
        return {"mime_type": item["mime_type"],
                "license_name": item["license_name"]}

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

    def feature3_gpu_jobs(self, token, shop_id):
        """Current JWT/RLS-visible image job list, never a paid claim."""
        sid = canonical_uuid(shop_id)
        rows = self._request("feature3_gpu_jobs", token, query={
            "select": "id,shop_id,status,created_at",
            "shop_id": "eq." + sid, "order": "created_at.desc", "limit": "21",
        })
        if not isinstance(rows, list) or len(rows) > 20:
            raise StorageUnavailable("malformed generated image history")
        checked = []
        for row in rows:
            if not isinstance(row, dict) or row.get("shop_id") != sid or (
                row.get("status") not in ("QUEUED", "RUNNING", "SUCCEEDED", "FAILED")
            ):
                raise StorageUnavailable("foreign or malformed generated image job")
            jid = canonical_uuid(row.get("id"))
            checked.append({"id": jid, "shop_id": sid, "status": row["status"]})
        return checked

    def feature3_gpu_job(self, token, shop_id, job_id):
        """User-JWT/RLS-backed generated job read, never a paid job claim."""
        sid, jid = canonical_uuid(shop_id), canonical_uuid(job_id)
        rows = self._request("feature3_gpu_jobs", token, query={
            "select": "id,shop_id,status,output_asset_id",
            "id": "eq." + jid, "shop_id": "eq." + sid, "limit": "2",
        })
        if not isinstance(rows, list) or len(rows) != 1:
            return None
        item = rows[0]
        if item.get("shop_id") != sid or item.get("id") != jid:
            return None
        if item.get("status") not in ("QUEUED","RUNNING","SUCCEEDED","FAILED"):
            return None
        return item

    def feature3_generated_asset(self, token, shop_id, job_id, asset_id):
        """Only the precise versioned private PNG object for this GPU job."""
        sid, jid, aid = map(canonical_uuid, (shop_id,job_id,asset_id))
        rows = self._request("media_assets", token, query={
            "select": "id,shop_id,storage_bucket,object_path,mime_type,source",
            "id": "eq." + aid, "shop_id": "eq." + sid, "limit": "2",
        })
        if not isinstance(rows, list) or len(rows)!=1:
            return None
        item=rows[0]
        expected_prefix=f"{sid}/feature3/gpu/{jid}/"
        key=item.get("object_path")
        if (item.get("id")!=aid or item.get("shop_id")!=sid or
            item.get("storage_bucket")!="retailgrowth-media" or
            item.get("source")!="GENERATED" or item.get("mime_type")!="image/png" or
            not isinstance(key,str) or not key.startswith(expected_prefix) or
            not re.fullmatch(r"[a-f0-9]{64}[.]png",key[len(expected_prefix):])):
            return None
        return {"object_path":key,"mime_type":"image/png"}

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


    def create_poster_draft(self, token, fields):
        """Invoke the rights-gated SQL RPC with the verified user's JWT.

        Never uses service_role. Null result is a deliberate DB authorization
        denial; missing RPC, schema or a transport error fails closed.
        """
        if not isinstance(fields, dict) or set(fields) != {
            "p_shop_id", "p_campaign_id", "p_day_id", "p_source_asset_id",
            "p_logo_asset_id", "p_template", "p_format", "p_business_name",
            "p_accent_color", "p_background_color", "p_offer_text",
        }:
            raise ValueError("invalid poster RPC fields")
        req = Request(
            self.origin + "/rest/v1/rpc/create_poster_draft",
            method="POST", data=json.dumps(fields).encode("utf-8"),
            headers={
                "apikey": self.key, "Authorization": "Bearer " + token,
                "Content-Type": "application/json", "Accept": "application/json",
            },
        )
        try:
            with self.transport(req, timeout=8) as response:
                value = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise AuthenticationError("poster draft rights denied") from exc
            raise StorageUnavailable("poster draft RPC unavailable") from exc
        except (URLError, OSError, json.JSONDecodeError) as exc:
            raise StorageUnavailable("poster draft unavailable") from exc
        if value is None:
            return None
        return canonical_uuid(value)

    def poster_draft(self, token, user_id, draft_id):
        """Read metadata only through shop RLS and current member verification."""
        pid = canonical_uuid(draft_id)
        found = self._request("poster_drafts", token, query={
            "select": "id,shop_id,campaign_id,day_id,status,template,format,"
                      "business_name,accent_color,background_color,offer_text,"
                      "source_asset_id,output_asset_id",
            "id": "eq." + pid, "limit": "1",
        })
        if len(found) != 1 or found[0].get("id") != pid:
            return None
        row = found[0]
        sid = canonical_uuid(row["shop_id"])
        if not self.member(token, user_id, sid):
            return None
        return row


    def posters_for_day(self, token, shop_id, campaign_id, day_id):
        """Return only RLS-visible, exact-campaign/day poster metadata and job IDs.

        Caller must verify current JWT user membership and campaign/day ownership.
        This method never returns object keys, signed links or storage credentials.
        """
        sid, cid, did = map(canonical_uuid, (shop_id, campaign_id, day_id))
        rows = self._request("poster_drafts", token, query={
            "select": "id,shop_id,campaign_id,day_id,status,revision,template,format,"
                      "business_name,accent_color,background_color,offer_text,"
                      "source_asset_id,output_asset_id",
            "shop_id": "eq." + sid, "campaign_id": "eq." + cid,
            "day_id": "eq." + did, "order": "created_at.desc", "limit": "21",
        })
        if not isinstance(rows, list) or len(rows) > 21 or any(
            row.get("shop_id") != sid or row.get("campaign_id") != cid or
            row.get("day_id") != did for row in rows
        ):
            raise StorageUnavailable("inconsistent private poster records")
        if not rows:
            return []
        ids = [canonical_uuid(row["id"]) for row in rows]
        if len(ids) != len(set(ids)):
            raise StorageUnavailable("duplicated private poster records")
        jobs = self._request("poster_jobs", token, query={
            "select": "id,shop_id,poster_id,status,output_asset_id",
            "shop_id": "eq." + sid,
            "poster_id": "in.(" + ",".join(ids) + ")",
            "limit": "21",
        })
        if not isinstance(jobs, list) or len(jobs) > 21 or any(
            job.get("shop_id") != sid or job.get("poster_id") not in ids for job in jobs
        ):
            raise StorageUnavailable("inconsistent private poster jobs")
        by_id = {}
        for job in jobs:
            pid = canonical_uuid(job["poster_id"])
            if pid in by_id:
                raise StorageUnavailable("multiple jobs for same poster revision")
            by_id[pid] = job
        return [{**row,
                 "job_id": by_id.get(row["id"], {}).get("id"),
                 "job_status": by_id.get(row["id"], {}).get("status")}
                for row in rows]


    def request_poster_job(self, token, poster_id):
        """User-JWT SQL render intent, atomically persisted with private outbox."""
        pid = canonical_uuid(poster_id)
        request = Request(
            self.origin + "/rest/v1/rpc/request_poster_job",
            data=json.dumps({"p_poster_id": pid}).encode("utf-8"),
            method="POST", headers={
                "apikey": self.key, "Authorization": "Bearer " + token,
                "Accept": "application/json", "Content-Type": "application/json",
            })
        try:
            with self.transport(request, timeout=8) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise AuthenticationError("poster render authorization denied") from exc
            raise StorageUnavailable("poster request rejected") from exc
        except (URLError, OSError, ValueError) as exc:
            raise StorageUnavailable("poster request unavailable") from exc
        return canonical_uuid(result) if result is not None else None

    def poster_job(self, token, user_id, job_id):
        jid = canonical_uuid(job_id)
        records = self._request("poster_jobs", token, query={
            "select": "id,shop_id,poster_id,status,output_asset_id,error_code",
            "id": "eq." + jid, "limit": "1",
        })
        if len(records) != 1 or records[0].get("id") != jid:
            return None
        job = records[0]
        if not self.member(token, user_id, job["shop_id"]):
            return None
        return job


    def select_poster_banner(self, token, poster_id, expected_instagram):
        """Optimistic reviewed selection, RLS subject checked within SQL RPC."""
        pid = canonical_uuid(poster_id)
        if not isinstance(expected_instagram, dict) or set(expected_instagram) != {
                "caption", "banner_asset_id", "reel"}:
            raise ValueError("complete expected saved Instagram draft required")
        request = Request(
            self.origin + "/rest/v1/rpc/select_poster_banner",
            method="POST", data=json.dumps({
                "p_poster_id": pid,
                "p_expected_instagram": expected_instagram,
            }).encode("utf-8"),
            headers={"apikey": self.key, "Authorization": "Bearer " + token,
                     "Content-Type": "application/json", "Accept": "application/json"})
        try:
            with self.transport(request, timeout=8) as response:
                value = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401,403):
                raise AuthenticationError("poster selection denied") from exc
            raise StorageUnavailable("poster selection unavailable") from exc
        except (URLError, OSError, ValueError) as exc:
            raise StorageUnavailable("poster selection unavailable") from exc
        if type(value) is not bool:
            raise StorageUnavailable("invalid poster selection response")
        return value


    def feature4_creative_plan(self, token, user_id, plan_id):
        """Read a previously service-issued F2 proposal via user JWT and RLS."""
        pid = canonical_uuid(plan_id)
        rows = self._request("feature4_creative_plans", token, query={
            "select": "id,shop_id,campaign_id,proposal,proposal_sha256,"
                      "media_asset_ids,state,approved_direction,review_sha256,"
                      "reviewed_by,reviewed_at,revoked_at",
            "id": "eq." + pid, "limit": "1",
        })
        if not isinstance(rows, list) or len(rows) > 1:
            raise StorageUnavailable("Feature4 review lookup ambiguous")
        if not rows:
            return None
        plan = rows[0]
        if (type(plan) is not dict or plan.get("id") != pid
                or not self.member(token, user_id, plan["shop_id"], write=False)):
            return None
        if plan.get("state") not in ("DRAFT", "APPROVED", "REVOKED"):
            raise StorageUnavailable("invalid creative plan state")
        return plan

    def feature4_review_cpu_plan(self, token, plan_id, expected_sha256):
        """Authenticated SQL approval; the DB re-locks media and actor rights."""
        pid = canonical_uuid(plan_id)
        if (type(expected_sha256) is not str or
                re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None):
            raise ValueError("immutable source review SHA required")
        result = self._request("rpc/feature4_review_cpu_plan", token,
                               method="POST", data={
                                   "p_plan_id": pid,
                                   "p_expected_source_sha256": expected_sha256,
                               })
        if result is not None and not isinstance(result, dict):
            raise StorageUnavailable("invalid Feature4 review SQL result")
        return result

    def feature4_revoke_cpu_plan(self, token, plan_id):
        """Only SQL-verified current OWNER can revoke an approved revision."""
        pid = canonical_uuid(plan_id)
        result = self._request("rpc/feature4_revoke_cpu_plan", token,
                               method="POST", data={"p_plan_id": pid})
        if type(result) is not bool:
            raise StorageUnavailable("invalid Feature4 revocation result")
        return result

    def feature4_submit_cpu_render(self, token, plan_id, expected_review_hash):
        """Pure user-JWT PostgREST RPC; DB alone locks editor/revision/quota/outbox.

        Browser must NOT supply its own storyboard, media URLs, job ID or
        service-role key. Idempotent replay requires fresh membership+rights.
        """
        pid = canonical_uuid(plan_id)
        if (type(expected_review_hash) is not str or
                re.fullmatch(r"[0-9a-f]{64}", expected_review_hash) is None):
            raise ValueError("Expected approved F2 revision SHA256")
        result = self._request("rpc/feature4_submit_cpu_render", token,
            method="POST", data={"p_plan_id": pid,
                                 "p_expected_review_hash": expected_review_hash})
        if result is not None and type(result) is not dict:
            raise StorageUnavailable("invalid CPU render transaction receipt")
        return result

    def feature4_job(self, token, user_id, job_id):
        """Current RLS-scoped v2 job; a foreign shop must read no row."""
        jid = canonical_uuid(job_id)
        rows = self._request("feature4_cpu_render_jobs", token, query={
            "select": "id,shop_id,campaign_id,plan_id,approved_review_sha256,status,output_asset_id,error_code",
            "id": "eq." + jid, "limit": "1",
        })
        if type(rows) is not list or len(rows) > 1:
            raise StorageUnavailable("ambiguous Feature4 CPU job")
        if not rows:
            return None
        row = rows[0]
        if (type(row) is not dict or row.get("id") != jid or
                not self.member(token, user_id, row["shop_id"], write=False)):
            return None
        return row

    def feature4_media(self, token, shop_id, asset_id):
        """Complete JWT/RLS media identity for current v2 rights and output."""
        sid, aid = canonical_uuid(shop_id), canonical_uuid(asset_id)
        rows = self._request("media_assets", token, query={
            "select": "id,shop_id,storage_bucket,object_path,mime_type,source,license_name",
            "shop_id": "eq." + sid, "id": "eq." + aid, "limit": "1",
        })
        if type(rows) is not list or len(rows) > 1:
            raise StorageUnavailable("ambiguous Feature4 media")
        if not rows:
            return None
        item = rows[0]
        if (type(item) is not dict or item.get("id") != aid
                or item.get("shop_id") != sid
                or item.get("storage_bucket") != "retailgrowth-media"
                or not isinstance(item.get("object_path"), str)
                or not item["object_path"].startswith(sid + "/")):
            return None
        return item
