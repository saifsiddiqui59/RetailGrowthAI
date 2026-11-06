"""Feature #2 storage: service-only shared data/writes and original JWT RLS reads.

No browser ever sees the service role key. Membership is checked by the API before
any tenant draft reads, and PostgREST independently enforces shop RLS.
"""
from __future__ import annotations

from datetime import datetime, timezone

from tenant_store import StorageUnavailable, canonical_uuid


class TrendSnapshotStore:
    def __init__(self, admin, *, clock=None):
        self.admin = admin
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self._claim = None

    def load(self, region: str):
        if region != "IN":
            raise ValueError("unsupported region")
        now = self.clock()
        if now.tzinfo is None:
            raise ValueError("aware clock required")
        result = self.admin.request("trend_snapshots", query={
            "select": "region,snapshot,expires_at",
            "region": "eq.IN", "expires_at": "gt." + now.astimezone(timezone.utc).isoformat(),
            "order": "utc_day.desc", "limit": "1",
        })
        if not isinstance(result, list) or len(result) > 1:
            raise StorageUnavailable("unexpected trend snapshot response")
        if not result:
            return None
        if result[0].get("region") != "IN" or not isinstance(result[0].get("snapshot"), dict):
            raise StorageUnavailable("invalid shared trend snapshot")
        return result[0]["snapshot"]

    def claim_day(self, region: str, day: str) -> bool:
        if region != "IN" or day != self.clock().astimezone(timezone.utc).date().isoformat():
            raise ValueError("invalid collection region or date")
        result = self.admin.request("rpc/feature2_claim_collection", method="POST",
                                    data={"p_region": region, "p_day": day})
        self._claim = (day, canonical_uuid(result)) if result else None
        return self._claim is not None

    def save(self, region: str, snapshot: dict):
        if region != "IN" or not isinstance(snapshot, dict):
            raise ValueError("invalid snapshot")
        if not self._claim:
            raise StorageUnavailable("trend claim missing")
        day, token = self._claim
        self._claim = None
        ok = self.admin.request("rpc/feature2_finish_collection", method="POST", data={
            "p_region": "IN", "p_day": day, "p_token": token, "p_snapshot": snapshot,
        })
        if ok is not True:
            raise StorageUnavailable("trend collection lease expired or lost")


def authorized_profile_reader(tenant_store):
    def read(token, user_id, shop_id):
        sid = canonical_uuid(shop_id)
        rows = tenant_store._request("business_profiles", token, query={
            "select": "shop_id,business_name,category,brand_voice,city,description",
            "shop_id": "eq." + sid, "limit": "1",
        })
        if not isinstance(rows, list) or len(rows) != 1 or rows[0].get("shop_id") != sid:
            return None
        row = rows[0]
        original_category = (row.get("category") or "").lower().strip()
        categories = {
            "clothing": ("fashion", "apparel", "boutique", "garment", "clothes", "clothing", "saree", "kurti"),
            "restaurant": ("restaurant", "cafe", "food", "hotel", "bakery", "dining"),
            "technology": ("technology", "software", "computer", "electronics", "it services"),
        }
        category = next((key for key, terms in categories.items()
                         if any(term in original_category for term in terms)), "general")
        # Product claims are NEVER inferred from free-form business description.
        # The currently versioned v1 onboarding schema has no product catalog.
        return {
            "shop_id": sid, "name": row.get("business_name", ""),
            "category": category, "city": row.get("city", ""),
            "brand_voice": row.get("brand_voice") or "helpful",
            "language": "en-IN", "products": [],
            "audience": "local customers", "objective": "awareness",
            "platforms": ["instagram", "linkedin"], "cta": "Contact the store",
        }
    return read


class TenantDraftStore:
    def __init__(self, admin, tenant_store=None):
        self.admin = admin
        self.tenant_store = tenant_store

    def list_drafts(self, token, shop_id, *, limit=5):
        sid = canonical_uuid(shop_id)
        if not 1 <= limit <= 5:
            raise ValueError("invalid limit")
        if self.tenant_store is None:
            raise StorageUnavailable("RLS draft reader unavailable")
        rows = self.tenant_store._request("shop_content_drafts", token, query={
            "select": "id,shop_id,trend_id,review_state,created_at,content",
            "shop_id": "eq." + sid, "order": "created_at.desc", "limit": str(limit),
        })
        if not isinstance(rows, list) or len(rows) > limit:
            raise StorageUnavailable("invalid draft response")
        result = []
        for row in rows:
            if not isinstance(row, dict) or row.get("shop_id") != sid or row.get("review_state") != "DRAFT":
                raise StorageUnavailable("draft tenant or approval state mismatch")
            content = row.get("content")
            if not isinstance(content, dict) or not isinstance(content.get("campaign"), dict) or (
                content["campaign"].get("shop_id") != sid
            ) or not isinstance(content.get("content_days"), list):
                raise StorageUnavailable("persisted draft contract mismatch")
            review = content.get("review")
            if not isinstance(review, dict) or review.get("status") != "DRAFT" or review.get("can_publish") is not False:
                raise StorageUnavailable("draft requires retailer approval")
            trend_id = row.get("trend_id")
            if not isinstance(trend_id, str) or len(trend_id) != 32:
                raise StorageUnavailable("invalid saved trend reference")
            result.append({"id": canonical_uuid(row["id"]), "shop_id": sid,
                           "trend_id": trend_id, "created_at": row.get("created_at"),
                           "review_state": "DRAFT", "content": content})
        return result

    def save_draft(self, token, user_id, shop_id, draft: dict):
        sid, uid = canonical_uuid(shop_id), canonical_uuid(user_id)
        content_days = draft.get("content_days") or []
        if not content_days or not content_days[0].get("trend_id"):
            raise ValueError("a selected verified trend is required")
        if draft["campaign"].get("shop_id") != sid:
            raise PermissionError("cross-tenant draft denied")
        result = self.admin.request("shop_content_drafts", method="POST", data={
            "shop_id": sid, "created_by": uid,
            "trend_id": content_days[0]["trend_id"],
            "content": draft,
        })
        if (not isinstance(result, list) or len(result) != 1 or
                result[0].get("shop_id") != sid or
                result[0].get("created_by") != uid):
            raise StorageUnavailable("draft insert acknowledgement invalid")
        return canonical_uuid(result[0]["id"])


# Signed-user, read-only, unactivated Feature2 voice persistence readers.
# This uses ordinary authenticated PostgREST, never service_role/anonymous.
# Requires review of ai-agents/sql/feature2_private_voice_REVIEW_ONLY.sql
# before HTTP routes or hosted migrations may be enabled.
class Feature2PrivateVoiceStore:
    """F2-19/F2-20 private original plan/job/WAV registered provenance.

    Only the server constructs this object, after verifying the actual
    Supabase JWT. Every read has a fresh member check AND Postgres RLS.
    The source adapter performs its own second read/role/lease checks.
    No job creation, inference, billing, external URL or public object GET.
    """

    _TABLES = frozenset((
        "feature2_private_voice_plans",
        "feature2_private_voice_jobs",
        "feature2_private_voice_assets",
    ))
    _BUCKET = "feature2-private-voice"
    _MAX_WAV_BYTES = 20_000_000

    def __init__(self, tenant_store, transport=None):
        from urllib.request import build_opener, HTTPRedirectHandler

        class _DenyRedirects(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, url):
                return None

        if (not hasattr(tenant_store, "member") or
            not hasattr(tenant_store, "origin") or
            not hasattr(tenant_store, "key") or
            not tenant_store.origin.startswith("https://") or
            not tenant_store.key):
            raise ValueError("Verified Supabase tenant store required")
        self.tenants = tenant_store
        # Standard urlopen automatically follows redirects (and can leak a
        # user's Authorization header). The default transport refuses them.
        self.transport = transport or build_opener(_DenyRedirects()).open

    def _scope(self, token, actor, shop_id, campaign_id):
        from security import AuthenticationError
        sid, cid, uid = (
            canonical_uuid(shop_id),canonical_uuid(campaign_id),
            canonical_uuid(actor))
        if (not isinstance(token,str) or not token or len(token)>8192 or
            token!=token.strip() or any(x in token for x in "\r\n\x00")):
            raise AuthenticationError("Current signed session required")
        if self.tenants.member(token,uid,sid,write=True) is not True:
            raise PermissionError("Current owner/editor membership required")
        return sid,cid

    def _get(self, table, token, query):
        import json
        from urllib.error import HTTPError, URLError
        from urllib.parse import urlencode
        from urllib.request import Request
        from security import AuthenticationError

        if table not in self._TABLES:
            raise ValueError("Unsupported private Feature2 read")
        url=(self.tenants.origin+"/rest/v1/"+table+"?"+
             urlencode(query,safe="(),.*"))
        req=Request(url,method="GET",headers={
            "apikey":self.tenants.key,
            "Authorization":"Bearer "+token,
            "Accept":"application/json",
        })
        try:
            with self.transport(req,timeout=8) as resp:
                # Avoid unlimited JSON from a compromised/proxied endpoint.
                body=resp.read(262_145)
                if len(body)>262_144:
                    raise StorageUnavailable("Unbounded private metadata")
                rows=json.loads(body.decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401,403):
                raise AuthenticationError("Private record auth denied") from exc
            raise StorageUnavailable("Private Feature2 record unavailable") from exc
        except (URLError,OSError,UnicodeError,ValueError) as exc:
            raise StorageUnavailable("Private Feature2 record unavailable") from exc
        if type(rows) is not list or len(rows)>1:
            raise StorageUnavailable("Ambiguous private voice rows")
        return rows[0] if rows else None

    def read_current_plan(self, token, actor, shop_id, campaign_id):
        from copy import deepcopy
        sid,cid=self._scope(token,actor,shop_id,campaign_id)
        row=self._get("feature2_private_voice_plans",token,{
            "select":"shop_id,campaign_id,source_plan,private,revoked_at",
            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,"limit":"2"})
        if row is None:
            return None
        if (type(row) is not dict or
            row.get("shop_id")!=sid or row.get("campaign_id")!=cid or
            row.get("private") is not True or
            row.get("revoked_at") is not None or
            type(row.get("source_plan")) is not dict):
            raise StorageUnavailable("Invalid or revoked private source")
        result=deepcopy(row["source_plan"])
        if (type(result.get("creative_direction_v1")) is not dict or
            result["creative_direction_v1"].get("shop_id")!=sid or
            result["creative_direction_v1"].get("campaign_id")!=cid or
            type(result.get("approval_record")) is not dict or
            result["approval_record"].get("can_publish") is not False):
            raise StorageUnavailable("Voice source is not shop-private draft")
        return result

    def read_registered_job(self, token, actor, shop_id, campaign_id,
                            request_key):
        from copy import deepcopy
        sid,cid=self._scope(token,actor,shop_id,campaign_id)
        key=canonical_uuid(request_key)
        row=self._get("feature2_private_voice_jobs",token,{
            "select":"shop_id,campaign_id,request_key,job_receipt,revoked_at",
            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
            "request_key":"eq."+key,"limit":"2"})
        if row is None:
            return None
        if (type(row) is not dict or row.get("shop_id")!=sid or
            row.get("campaign_id")!=cid or row.get("request_key")!=key or
            row.get("revoked_at") is not None or
            type(row.get("job_receipt")) is not dict):
            raise StorageUnavailable("Invalid private voice job record")
        receipt=deepcopy(row["job_receipt"])
        if (receipt.get("shop_id")!=sid or receipt.get("campaign_id")!=cid or
            receipt.get("request_key")!=key or
            receipt.get("private") is not True or
            receipt.get("can_publish") is not False):
            raise StorageUnavailable("Voice job tenant/status mismatch")
        return receipt

    def _registered_asset_row(self, token, actor, shop_id, campaign_id, asset_id):
        sid,cid=self._scope(token,actor,shop_id,campaign_id)
        aid=canonical_uuid(asset_id)
        row=self._get("feature2_private_voice_assets",token,{
            "select":"shop_id,campaign_id,audio_asset_id,object_path,asset_receipt,revoked_at",
            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
            "audio_asset_id":"eq."+aid,"limit":"2"})
        if row is None:
            return None
        expected=sid+"/"+cid+"/"+aid+".wav"
        if (type(row) is not dict or
            row.get("shop_id")!=sid or row.get("campaign_id")!=cid or
            row.get("audio_asset_id")!=aid or
            row.get("object_path")!=expected or
            row.get("revoked_at") is not None or
            type(row.get("asset_receipt")) is not dict):
            raise StorageUnavailable("Private WAV registry mismatch")
        data=row["asset_receipt"]
        if (data.get("shop_id")!=sid or data.get("campaign_id")!=cid or
            data.get("audio_asset_id")!=aid or data.get("private") is not True or
            data.get("mime_type")!="audio/wav" or
            data.get("can_publish") is not False or
            data.get("revoked_at") is not None):
            raise StorageUnavailable("Private WAV metadata denied")
        return row

    def read_registered_private_asset(self,token,actor,shop_id,campaign_id,
                                      asset_id):
        from copy import deepcopy
        row=self._registered_asset_row(token,actor,shop_id,campaign_id,asset_id)
        return deepcopy(row["asset_receipt"]) if row is not None else None

    def read_private_blob(self,token,actor,shop_id,campaign_id,asset_id):
        """Returns no more than 20 MB of original registered WAV bytes.

        No service_role credentials, signed/public URL or Storage redirect.
        Metadata is checked twice; the source-level WAV reader additionally
        compares actual original bytes SHA, PCM duration and current role.
        """
        from urllib.error import HTTPError, URLError
        from urllib.request import Request
        from security import AuthenticationError

        row=self._registered_asset_row(token,actor,shop_id,campaign_id,asset_id)
        if row is None:
            raise PermissionError("Original private WAV unavailable")
        uri=(self.tenants.origin+"/storage/v1/object/authenticated/"+
             self._BUCKET+"/"+row["object_path"])
        request=Request(uri,method="GET",headers={
            "apikey":self.tenants.key,
            "Authorization":"Bearer "+token,
            "Accept":"audio/wav",
            "Cache-Control":"no-store",
        })
        try:
            with self.transport(request,timeout=8) as resp:
                if (resp.headers.get("Content-Encoding") not in (None,"identity") or
                    resp.headers.get("Content-Type","").split(";")[0].strip() not in
                        ("audio/wav","audio/x-wav","application/octet-stream")):
                    raise StorageUnavailable("Unexpected private WAV response")
                raw=resp.read(self._MAX_WAV_BYTES+1)
        except HTTPError as exc:
            if exc.code in (401,403):
                raise AuthenticationError("Private WAV auth denied") from exc
            raise StorageUnavailable("Original WAV unavailable") from exc
        except (URLError,OSError) as exc:
            raise StorageUnavailable("Original WAV unavailable") from exc
        if type(raw) is not bytes or not 128<=len(raw)<=self._MAX_WAV_BYTES:
            raise StorageUnavailable("Private WAV size invalid")
        if self._registered_asset_row(token,actor,shop_id,campaign_id,asset_id)!=row:
            raise PermissionError("Private WAV registry changed during read")
        return raw
