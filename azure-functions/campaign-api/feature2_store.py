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



class Feature2PrivateAuditStore(Feature2PrivateVoiceStore):
    """F2-08/F2-12 signed-user *read-only* private workflow/audit backend.

    This is source-only, not an active route, migration, worker signer or human
    approval authority. Every call uses JWT-scoped PostgREST and current
    OWNER/EDITOR membership; no service role, public URL, customer script or
    model invocation. HMAC signatures are trusted ONLY when independently
    created by a reviewed reviewer/worker commit path, which is not installed.
    """

    _TABLES=frozenset((
        "feature2_private_trace_sources",
        "feature2_private_trace_events",
        "feature2_private_blind_scores",
        "feature2_private_blind_attestations",
    ))
    _READ_LIMIT=1_048_576

    def __init__(self,tenant_store,*,trace_secret=None,review_secret=None,
                 transport=None):
        super().__init__(tenant_store,transport=transport)
        # Zero-cost readonly source work never manufactures authoritative
        # HMAC keys. A missing approved key disables the signature verifier.
        if trace_secret is not None and (
                type(trace_secret) is not bytes or len(trace_secret)<32):
            raise ValueError("Approved trace secret must have at least 32 bytes")
        if review_secret is not None and (
                type(review_secret) is not bytes or len(review_secret)<32):
            raise ValueError("Approved independent review key requires 32 bytes")
        self.trace_secret=trace_secret
        self.review_secret=review_secret

    def _get_many(self,table,token,query,*,limit):
        import json
        from urllib.error import HTTPError,URLError
        from urllib.parse import urlencode
        from urllib.request import Request
        from security import AuthenticationError

        if table not in self._TABLES or type(limit) is not int or (
                limit not in (51,101)):
            raise ValueError("Unsupported bounded private audit query")
        if query.get("limit")!=str(limit):
            raise ValueError("Private audit query requires hard row cap")
        url=self.tenants.origin+"/rest/v1/"+table+"?"+urlencode(
            query,safe="(),.*")
        req=Request(url,method="GET",headers={
            "apikey":self.tenants.key,
            "Authorization":"Bearer "+token,
            "Accept":"application/json",
            "Cache-Control":"no-store",
        })
        try:
            with self.transport(req,timeout=8) as resp:
                raw=resp.read(self._READ_LIMIT+1)
                if len(raw)>self._READ_LIMIT:
                    raise StorageUnavailable("Unbounded private audit response")
                rows=json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401,403):
                raise AuthenticationError("Signed private audit read denied") from exc
            raise StorageUnavailable("Private audit read unavailable") from exc
        except (URLError,OSError,UnicodeError,ValueError) as exc:
            raise StorageUnavailable("Private audit read unavailable") from exc
        if type(rows) is not list or len(rows)>=limit:
            raise StorageUnavailable("Ambiguous or unbounded audit history")
        return rows

    def read_trace_source(self,token,actor,shop_id,campaign_id,workflow_id):
        from copy import deepcopy
        sid,cid=self._scope(token,actor,shop_id,campaign_id)
        wid=canonical_uuid(workflow_id)
        row=self._get("feature2_private_trace_sources",token,{
            "select":"shop_id,campaign_id,workflow_id,source_sha256,private,can_publish,revoked_at,revision",
            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
            "workflow_id":"eq."+wid,"limit":"2"})
        if row is None:
            return None
        if (type(row) is not dict or row.get("shop_id")!=sid or
            row.get("campaign_id")!=cid or row.get("workflow_id")!=wid or
            type(row.get("source_sha256")) is not str or
            not __import__("re").fullmatch("[a-f0-9]{64}",row["source_sha256"]) or
            row.get("private") is not True or
            row.get("can_publish") is not False or
            row.get("revoked_at") is not None or
            type(row.get("revision")) is not int or row["revision"]<0):
            raise StorageUnavailable("Private trace source modified or revoked")
        # Second read and role guard occur in Feature2PrivateTraceAdapter.
        return deepcopy(row)

    def read_private_trace_events(self,token,actor,shop_id,campaign_id,
                                  workflow_id):
        from copy import deepcopy
        sid,cid=self._scope(token,actor,shop_id,campaign_id)
        wid=canonical_uuid(workflow_id)
        rows=self._get_many("feature2_private_trace_events",token,{
            "select":"shop_id,campaign_id,workflow_id,sequence,event_json",
            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
            "workflow_id":"eq."+wid,"order":"sequence.asc","limit":"101"},
            limit=101)
        data=[]
        for idx,row in enumerate(rows,1):
            if (type(row) is not dict or
                row.get("shop_id")!=sid or row.get("campaign_id")!=cid or
                row.get("workflow_id")!=wid or
                type(row.get("sequence")) is not int or
                row["sequence"]!=idx or
                type(row.get("event_json")) is not dict or
                row["event_json"].get("shop_id")!=sid or
                row["event_json"].get("campaign_id")!=cid or
                row["event_json"].get("workflow_id")!=wid or
                row["event_json"].get("sequence")!=idx):
                raise StorageUnavailable("Private trace chain order or shop mismatch")
            data.append(deepcopy(row["event_json"]))
        self._scope(token,actor,sid,cid)
        return data

    def read_private_blind_history(self,token,actor,shop_id,campaign_id,
                                   experiment_id):
        from copy import deepcopy
        import re
        sid,cid=self._scope(token,actor,shop_id,campaign_id)
        if (type(experiment_id) is not str or
            not re.fullmatch("[A-Za-z0-9_-]{10,120}",experiment_id)):
            raise ValueError("Invalid private experiment identifier")
        rows=self._get_many("feature2_private_blind_scores",token,{
            "select":"shop_id,campaign_id,experiment_id,revision,review_record",
            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
            "experiment_id":"eq."+experiment_id,
            "order":"revision.asc","limit":"51"},limit=51)
        scores=[]
        for idx,row in enumerate(rows,1):
            if (type(row) is not dict or row.get("shop_id")!=sid or
                row.get("campaign_id")!=cid or
                row.get("experiment_id")!=experiment_id or
                type(row.get("revision")) is not int or
                row["revision"]!=idx or type(row.get("review_record")) is not dict or
                row["review_record"].get("shop_id")!=sid or
                row["review_record"].get("campaign_id")!=cid or
                row["review_record"].get("experiment_id")!=experiment_id or
                row["review_record"].get("revision")!=idx):
                raise StorageUnavailable("Private human A/B review sequence invalid")
            scores.append(deepcopy(row["review_record"]))
        self._scope(token,actor,sid,cid)
        return scores

    @staticmethod
    def _attestation_message(shop,campaign,experiment,revision,receipt,
                             candidates,score_record):
        import json
        return json.dumps({
            "shop_id":shop,"campaign_id":campaign,
            "experiment_id":experiment,"revision":revision,
            "receipt_digest":receipt,"candidate_digests":candidates,
            "review_record":score_record,
        },ensure_ascii=False,sort_keys=True,
           separators=(",",":")).encode("utf-8")

    def verify_signed_human_history(self,token,actor,shop_id,campaign_id,
                                    experiment_id,revision,receipt_digest,
                                    candidate_digests):
        """Cryptographic independent-review receipt check, not source creation.

        A backend reviewer service must previously sign the complete frozen
        review record with the separately provisioned approved secret. A
        tampered score, replayed revision or foreign shop cannot be certified
        merely by trusting a PostgREST row's claim that it was reviewed.
        """
        import hmac
        import re
        sid,cid=self._scope(token,actor,shop_id,campaign_id)
        if (self.review_secret is None or
            type(experiment_id) is not str or
            not re.fullmatch("[A-Za-z0-9_-]{10,120}",experiment_id) or
            type(revision) is not int or not 1<=revision<=50 or
            type(receipt_digest) is not str or
            not re.fullmatch("[a-f0-9]{64}",receipt_digest) or
            type(candidate_digests) is not dict or
            set(candidate_digests)!={"A","B"} or
            any(type(value) is not str or
                not re.fullmatch("[a-f0-9]{64}",value)
                for value in candidate_digests.values()) or
            candidate_digests["A"]==candidate_digests["B"]):
            return False
        row=self._get("feature2_private_blind_attestations",token,{
            "select":"shop_id,campaign_id,experiment_id,revision,receipt_digest,candidate_digests,review_record,server_mac,revoked_at",
            "shop_id":"eq."+sid,"campaign_id":"eq."+cid,
            "experiment_id":"eq."+experiment_id,
            "revision":"eq."+str(revision),"limit":"2"})
        if (type(row) is not dict or
            row.get("shop_id")!=sid or row.get("campaign_id")!=cid or
            row.get("experiment_id")!=experiment_id or
            row.get("revision")!=revision or
            row.get("receipt_digest")!=receipt_digest or
            row.get("candidate_digests")!=candidate_digests or
            row.get("revoked_at") is not None or
            type(row.get("review_record")) is not dict or
            row["review_record"].get("receipt_digest")!=receipt_digest or
            row["review_record"].get("human_scores") is None or
            row["review_record"].get("revision")!=revision or
            type(row.get("server_mac")) is not str or
            not re.fullmatch("[a-f0-9]{64}",row["server_mac"])):
            return False
        # Compare against the current signed persisted review record too:
        # validates the complete signed scores, not only opaque receipt hash.
        history=self.read_private_blind_history(
            token,actor,sid,cid,experiment_id)
        if revision>len(history) or history[revision-1]!=row["review_record"]:
            return False
        raw=self._attestation_message(
            sid,cid,experiment_id,revision,
            receipt_digest,candidate_digests,row["review_record"])
        expected=hmac.digest(self.review_secret,
            b"retailgrowth.feature2.human-history.v1\n"+raw,"sha256").hex()
        if not hmac.compare_digest(row["server_mac"],expected):
            return False
        self._scope(token,actor,sid,cid)
        return True
