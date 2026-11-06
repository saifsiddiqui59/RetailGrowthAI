"""Feature #2 JWT/tenant-gated Azure Functions boundary.

Shared trends and protected shop drafts are deployed in RetailGrowthAI DEV.
All writes require server-side shop, media, and source checks and stay DRAFT.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from ai_agents.content_intelligence import RetailerProfile, create_content_draft
from ai_agents.schemas import CampaignBrief, ContractError
from ai_agents.providers import FoundryUnavailable
from ai_agents.trend_intelligence import recommendations
from security import AuthenticationError
from tenant_store import StorageUnavailable, canonical_uuid


class TrendFeatureAdapter:
    def __init__(self, verify_token, tenant_store, profile_reader=None,
                 snapshot_store=None, draft_store=None, clock=None, ai_service=None):
        self.verify_token = verify_token
        self.tenant_store = tenant_store
        self.profile_reader = profile_reader
        self.snapshot_store = snapshot_store
        self.draft_store = draft_store
        self.ai_service = ai_service
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def handle(self, method: str, shop_id: str, authorization: str,
               payload: dict | None = None, *, ai_mode=False) -> tuple[int, dict]:
        try:
            sid = canonical_uuid(shop_id)
            if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
                return 401, {"error": "UNAUTHORIZED"}
            token = authorization[7:].strip()
            if not token:
                return 401, {"error": "UNAUTHORIZED"}
            try:
                user_id = canonical_uuid(self.verify_token(token))
            except (AuthenticationError, ValueError, TypeError):
                return 401, {"error": "UNAUTHORIZED"}
            if method not in ("GET", "POST"):
                return 405, {"error": "METHOD_NOT_ALLOWED"}
            if not self.tenant_store.member(token, user_id, sid, write=method == "POST"):
                return 404, {"error": "NOT_FOUND"}
            # All dependencies intentionally fail closed pending coordinator review.
            if not self.profile_reader or not self.snapshot_store:
                return 503, {"error": "TREND_STORAGE_NOT_CONFIGURED"}
            profile_source = self.profile_reader(token, user_id, sid)
            if not isinstance(profile_source, dict) or profile_source.get("shop_id") != sid:
                return 404, {"error": "NOT_FOUND"}
            # A just-created business has city='' until onboarding is completed.
            # Never infer its location from the device, a model, or the national trend feed.
            city = profile_source.get("city")
            if not isinstance(city, str) or not city.strip():
                if method == "GET":
                    return 200, {
                        "shop_id": sid, "profile_required": True,
                        "recommendations": [], "sources": [], "complete": False,
                        "observed_at": None,
                    }
                return 422, {"error": "BUSINESS_PROFILE_INCOMPLETE"}
            retailer = RetailerProfile.from_authorized(profile_source)
            snapshot = self.snapshot_store.load("IN")
            if not isinstance(snapshot, dict):
                return 503, {"error": "TREND_SOURCES_UNAVAILABLE"}
            now = self.clock()
            matches = recommendations(snapshot, {
                "category": retailer.category, "city": retailer.city,
                "language": retailer.language, "products": list(retailer.products),
            }, now)
            if method == "GET":
                return 200, {
                    "shop_id": sid, "recommendations": matches,
                    "sources": snapshot.get("sources", []),
                    "complete": snapshot.get("complete", False),
                    "observed_at": snapshot.get("observed_at"),
                }
            if (not isinstance(payload, dict) or
                set(payload) not in ({"trend_id", "campaign"},
                                     {"trend_id", "campaign", "submission_id"})):
                return 400, {"error": "INVALID_REQUEST"}
            submission_id = payload.get("submission_id")
            if "submission_id" in payload:
                try:
                    canonical_uuid(submission_id)
                except (ValueError, TypeError):
                    return 400, {"error": "INVALID_REQUEST"}
            if not self.draft_store:
                return 503, {"error": "CONTENT_DRAFT_STORE_NOT_CONFIGURED"}
            target = payload["trend_id"]
            chosen = next((t for t in snapshot.get("trends", []) if t.get("trend_id") == target), None)
            if not chosen or not any(t["trend_id"] == target for t in matches):
                return 409, {"error": "TREND_UNAVAILABLE_OR_STALE"}
            brief = CampaignBrief.from_dict(payload["campaign"])
            if brief.shop_id != sid or not self.tenant_store.assets(token, sid, brief.media_asset_ids):
                return 403, {"error": "FORBIDDEN"}
            # Only deterministic approved-budget OFFLINE drafting here. The
            # existing live model and expensive jobs require coordinator gates.
            from uuid import uuid4
            campaign_id = str(uuid4())
            if ai_mode:
                if self.ai_service is None:
                    return 503, {"error": "AI_NOT_ENABLED_OR_NOT_APPROVED"}
                # Signed shop/actor and server-validated submission ID pin
                # the billable ledger request across a lost HTTP acknowledgement.
                # Replays get RG005 before network egress; never auto-retry.
                ai_kwargs = dict(
                    brief=brief, retailer=retailer, campaign_id=campaign_id,
                    now=now, trend=chosen, shop_id=sid, actor_id=user_id)
                if submission_id is not None:
                    ai_kwargs["request_id"] = submission_id
                draft = self.ai_service.draft(**ai_kwargs)
            else:
                draft = create_content_draft(brief, retailer, campaign_id=campaign_id,
                                             now=now, trend=chosen)
            # Non-sensitive correlation nonce for read-after-uncertain-POST.
            # Not a DB idempotency lock: clients MUST NOT replay a POST just
            # because Azure timed out before returning the insert acknowledgement.
            if submission_id is not None:
                draft["submission_id"] = submission_id
            if not self.tenant_store.member(token, user_id, sid, write=True):
                return 403, {"error": "FORBIDDEN"}
            draft_id = self.draft_store.save_draft(token, user_id, sid, draft)
            return 201, {"draft_id": canonical_uuid(draft_id), "shop_id": sid,
                         "status": "DRAFT", "campaign_id": campaign_id}
        except AuthenticationError:
            return 401, {"error": "UNAUTHORIZED"}
        except (ContractError, ValueError, TypeError, KeyError, AttributeError):
            return 400, {"error": "INVALID_REQUEST"}
        except PermissionError:
            return 403, {"error": "FORBIDDEN"}
        except StorageUnavailable:
            return 503, {"error": "TREND_STORAGE_UNAVAILABLE"}
        except FoundryUnavailable:
            return 503, {"error": "AI_MODEL_UNAVAILABLE"}

    def improve(self, shop_id: str, authorization: str,
                payload: dict | None, *, ai_mode=False) -> tuple[int, dict]:
        """Zero-paid-inference editorial preview. No trends, media or DB writes.

        Only authenticated OWNER/EDITOR, with server-read RLS business context.
        The request cannot supply or override an authorized business profile.
        """
        try:
            sid = canonical_uuid(shop_id)
            if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
                return 401, {"error": "UNAUTHORIZED"}
            token = authorization[7:].strip()
            if not token:
                return 401, {"error": "UNAUTHORIZED"}
            try:
                uid = canonical_uuid(self.verify_token(token))
            except (AuthenticationError, ValueError, TypeError):
                return 401, {"error": "UNAUTHORIZED"}
            if not self.tenant_store.member(token, uid, sid, write=True):
                return 403, {"error": "FORBIDDEN"}
            if self.profile_reader is None:
                return 503, {"error": "PROFILE_UNAVAILABLE"}
            if not isinstance(payload, dict) or set(payload) != {
                "original_prompt", "output_formats", "language"
            }:
                return 400, {"error": "INVALID_REQUEST"}
            row = self.profile_reader(token, uid, sid)
            if not isinstance(row, dict) or row.get("shop_id") != sid:
                return 404, {"error": "NOT_FOUND"}
            if not isinstance(row.get("city"), str) or not row["city"].strip():
                return 422, {"error": "BUSINESS_PROFILE_INCOMPLETE"}
            profile = RetailerProfile.from_authorized(row)
            if ai_mode:
                if self.ai_service is None:
                    return 503, {"error": "AI_NOT_ENABLED_OR_NOT_APPROVED"}
                result = self.ai_service.improve(
                    original_prompt=payload["original_prompt"], retailer=profile,
                    output_formats=payload["output_formats"],
                    language=payload["language"], shop_id=sid, actor_id=uid)
            else:
                from ai_agents.prompt_improver import improve_prompt
                result = improve_prompt(
                    payload["original_prompt"], profile,
                    output_formats=payload["output_formats"], language=payload["language"],
                )
            return 200, {"shop_id": sid, **result}
        except AuthenticationError:
            return 401, {"error": "UNAUTHORIZED"}
        except (ValueError, TypeError, KeyError, ContractError):
            return 400, {"error": "INVALID_REQUEST"}
        except PermissionError:
            return 403, {"error": "FORBIDDEN"}
        except StorageUnavailable:
            return 503, {"error": "PROFILE_UNAVAILABLE"}
        except FoundryUnavailable:
            return 503, {"error": "AI_MODEL_UNAVAILABLE"}

    def list_drafts(self, shop_id: str, authorization: str) -> tuple[int, dict]:
        """Read saved drafts with the *user's* RLS identity, even when RSS is down."""
        try:
            sid = canonical_uuid(shop_id)
            if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
                return 401, {"error": "UNAUTHORIZED"}
            token = authorization[7:].strip()
            if not token:
                return 401, {"error": "UNAUTHORIZED"}
            try:
                uid = canonical_uuid(self.verify_token(token))
            except (AuthenticationError, ValueError, TypeError):
                return 401, {"error": "UNAUTHORIZED"}
            if not self.tenant_store.member(token, uid, sid, write=False):
                return 404, {"error": "NOT_FOUND"}
            if not self.draft_store:
                return 503, {"error": "CONTENT_DRAFT_STORE_NOT_CONFIGURED"}
            rows = self.draft_store.list_drafts(token, sid, limit=5)
            return 200, {"shop_id": sid, "drafts": rows}
        except AuthenticationError:
            return 401, {"error": "UNAUTHORIZED"}
        except (ValueError, TypeError, KeyError):
            return 400, {"error": "INVALID_REQUEST"}
        except StorageUnavailable:
            return 503, {"error": "CONTENT_DRAFT_READ_UNAVAILABLE"}


class PrivateVoiceStatusAdapter:
    """F2-19 signed, GET-only private job-status API boundary.

    The actual HTTP router and authenticated PostgREST readers must be wired
    and reviewed independently; this source class makes NO network/model call.
    Request UUIDs are *not* authorization. Never create/retry/bill a voice job.
    """

    def __init__(self, verify_token, tenant_store, *, plan_reader=None,
                 job_reader=None, private_audio_reader=None,
                 status_verifier=None):
        self.verify_token = verify_token
        self.tenant_store = tenant_store
        self.plan_reader = plan_reader
        self.job_reader = job_reader
        self.private_audio_reader = private_audio_reader
        # Runtime dependencies must be declared in the protected ZIP
        # allowlist before activation. The coordinator supplies this trusted
        # F2 status verifier ONLY after an independently approved package.
        self.status_verifier = status_verifier

    def get(self, shop_id, campaign_id, request_key, authorization):
        from copy import deepcopy
        # Deliberately NO new ai_agents import from the Functions runtime.
        # The permitted server service is injected after review.
        try:
            sid, cid, key = (canonical_uuid(v) for v in
                             (shop_id, campaign_id, request_key))
            if any(UUID(v).version != 4 for v in (sid,cid,key)):
                return 400, {"error":"INVALID_REQUEST"}
        except (ValueError, TypeError, AttributeError):
            return 400, {"error":"INVALID_REQUEST"}
        if (type(authorization) is not str or
            not authorization.startswith("Bearer ") or
            len(authorization)>8192 or
            any(c in authorization for c in "\r\n\x00")):
            return 401, {"error":"UNAUTHORIZED"}
        token = authorization[7:]
        if not token or token != token.strip():
            return 401, {"error":"UNAUTHORIZED"}
        try:
            actor = canonical_uuid(self.verify_token(token))
        except (AuthenticationError, ValueError, TypeError):
            return 401, {"error":"UNAUTHORIZED"}
        if not all(callable(v) for v in
                   (self.plan_reader,self.job_reader,self.private_audio_reader,
                    self.status_verifier)):
            return 503, {"error":"PRIVATE_VOICE_STATUS_UNAVAILABLE"}
        try:
            def editor(s,c):
                return (s==sid and c==cid and
                        self.tenant_store.member(token,actor,sid,write=True) is True)
            if not editor(sid,cid):
                return 404, {"error":"NOT_FOUND"}
            original=self.plan_reader(token,actor,sid,cid)
            if type(original) is not dict:
                return 404, {"error":"NOT_FOUND"}
            # Snapshot the first RLS plan so mutable shared readers cannot
            # replace source provenance during status/asset readback.
            receipt=self.status_verifier(
                shop_id=sid,campaign_id=cid,source_plan=deepcopy(original),
                request_key=key,authorize_current_editor=editor,
                read_current_plan=lambda s,c:self.plan_reader(token,actor,s,c),
                read_registered_job=lambda s,c,k:self.job_reader(token,actor,s,c,k),
                read_registered_private_asset=lambda s,c,a:
                    self.private_audio_reader(token,actor,s,c,a),
            )
            if not editor(sid,cid):
                return 404, {"error":"NOT_FOUND"}
            return 200,receipt
        except (ValueError, PermissionError):
            return 404, {"error":"NOT_FOUND"}
        except StorageUnavailable:
            return 503, {"error":"PRIVATE_VOICE_STATUS_UNAVAILABLE"}


# ---------------------------------------------------------------------------
# Feature #2 independent signed-DEV endpoint adapters (source-only integration).
# This module is already included in the Functions ZIP. DO NOT import the
# optional speech/trace/reviewer workers at import-time: they are NOT on the
# protected runtime allowlist. The approved server composes and injects them.
# No adapter grants commercial rights, creates paid jobs or auto-approves.
# ---------------------------------------------------------------------------
def _feature2_private_scope(verify_token, tenant_store, shop, campaign, bearer):
    """Common verification for F2-owned reviewed/private routes.

    Returns (HTTP error, None) or (None, validated scoped identity). UUIDs,
    membership and JWT verification are server-side; browser input is never
    passed as a privileged PostgREST credential or rights assertion.
    """
    try:
        sid, cid = canonical_uuid(shop), canonical_uuid(campaign)
        if UUID(sid).version != 4 or UUID(cid).version != 4:
            return 400, None
    except (ValueError, TypeError, AttributeError):
        return 400, None
    if (type(bearer) is not str or not bearer.startswith("Bearer ") or
        len(bearer) > 8192 or any(c in bearer for c in "\r\n\x00")):
        return 401, None
    token = bearer[7:]
    if not token or token != token.strip():
        return 401, None
    try:
        actor = canonical_uuid(verify_token(token))
        if UUID(actor).version != 4:
            return 401, None
    except (ValueError, TypeError, AttributeError, AuthenticationError):
        return 401, None
    try:
        if tenant_store.member(token, actor, sid, write=True) is not True:
            return 404, None
    except (PermissionError, AuthenticationError):
        return 404, None
    except StorageUnavailable:
        return 503, None
    return None, (sid, cid, actor, token)


def _feature2_private_editor(members, token, actor, sid, cid):
    """Check member again; never treat a client ID as approval for a campaign."""
    try:
        return members.member(token, actor, sid, write=True) is True
    except (AuthenticationError, PermissionError):
        return False


class Feature2PrivateTraceAdapter:
    """Read F2-12 HMAC-verified private stage projection, not the HMAC itself.

    The trusted server injects a verifier partially bound to its HMAC key.
    The user JWT is scoped to immutable workflow source and private RLS events.
    No new route is registered until the coordinator's package is reviewed.
    """

    def __init__(self, verify_token, tenant_store, *, source_reader=None,
                 event_reader=None, trace_verifier=None):
        self.verify_token, self.tenant_store = verify_token, tenant_store
        self.source_reader = source_reader
        self.event_reader = event_reader
        self.trace_verifier = trace_verifier

    def get(self, shop_id, campaign_id, workflow_id, source_sha256, authorization):
        from copy import deepcopy
        import re
        code, identity = _feature2_private_scope(
            self.verify_token, self.tenant_store, shop_id, campaign_id,
            authorization)
        if code is not None:
            return code, {"error":"UNAUTHORIZED" if code == 401 else
                          "PRIVATE_TRACE_UNAVAILABLE" if code == 503 else
                          "NOT_FOUND" if code == 404 else "INVALID_REQUEST"}
        sid, cid, actor, token = identity
        try:
            wid = canonical_uuid(workflow_id)
            if UUID(wid).version != 4 or type(source_sha256) is not str or (
                    re.fullmatch("[0-9a-f]{64}", source_sha256) is None):
                return 400, {"error":"INVALID_REQUEST"}
        except (ValueError, TypeError, AttributeError):
            return 400, {"error":"INVALID_REQUEST"}
        if not all(callable(f) for f in (
                self.source_reader, self.event_reader, self.trace_verifier)):
            return 503, {"error":"PRIVATE_TRACE_UNAVAILABLE"}
        try:
            first = self.source_reader(token, actor, sid, cid, wid)
            if (type(first) is not dict or
                first.get("shop_id") != sid or first.get("campaign_id") != cid or
                first.get("workflow_id") != wid or
                first.get("source_sha256") != source_sha256 or
                first.get("private") is not True or
                first.get("can_publish") is not False or
                first.get("revoked_at") is not None):
                return 404, {"error":"NOT_FOUND"}
            frozen = deepcopy(first)
            def current(s, c, w, digest):
                return (s, c, w, digest) == (sid, cid, wid, source_sha256) and (
                    _feature2_private_editor(self.tenant_store, token, actor, sid, cid)
                    and self.source_reader(token, actor, sid, cid, wid) == frozen)
            if not current(sid, cid, wid, source_sha256):
                return 404, {"error":"NOT_FOUND"}
            projection = self.trace_verifier(
                shop_id=sid, campaign_id=cid, workflow_id=wid,
                source_sha256=source_sha256, current_scope=current,
                read_private_events=lambda s,c,w:
                    self.event_reader(token, actor, s, c, w),
            )
            keys = {"schema", "shop_id", "campaign_id", "workflow_id",
                    "source_sha256", "events", "last_event_sha256", "private",
                    "all_steps_verified", "actual_model_inference_verified",
                    "can_publish"}
            if (type(projection) is not dict or set(projection) != keys or
                projection.get("schema") !=
                    "retailgrowth.feature2-private-trace-history.v1" or
                (projection.get("shop_id"), projection.get("campaign_id"),
                 projection.get("workflow_id"), projection.get("source_sha256"))
                    != (sid,cid,wid,source_sha256) or
                projection.get("private") is not True or
                projection.get("all_steps_verified") is not True or
                projection.get("actual_model_inference_verified") is not False or
                projection.get("can_publish") is not False or
                type(projection.get("events")) is not list or
                not 1 <= len(projection["events"]) <= 100 or
                any(type(e) is not dict or set(e) != {
                    "sequence","stage","status","evidence_class",
                    "failure_code","event_sha256","can_publish"}
                    for e in projection["events"])):
                return 404, {"error":"NOT_FOUND"}
            if not current(sid, cid, wid, source_sha256):
                return 404, {"error":"NOT_FOUND"}
            return 200, deepcopy(projection)
        except (ValueError, PermissionError, KeyError, TypeError):
            return 404, {"error":"NOT_FOUND"}
        except StorageUnavailable:
            return 503, {"error":"PRIVATE_TRACE_UNAVAILABLE"}


class Feature2PrivateWavAdapter:
    """F2-20 private, original WAV *binary* response (never a public URL).

    A real HTTP route must use the raw bytes response (not JSON.serialize),
    set the returned no-store headers and enforce the existing JWT boundary.
    All source, media, original WAV and editor verification is injected from
    trusted RLS + private blob service; no browser-supplied path is accepted.
    """

    def __init__(self, verify_token, tenant_store, *, plan_reader=None,
                 asset_reader=None, blob_reader=None, wav_verifier=None):
        self.verify_token, self.tenant_store = verify_token, tenant_store
        self.plan_reader, self.asset_reader = plan_reader, asset_reader
        self.blob_reader, self.wav_verifier = blob_reader, wav_verifier

    def get(self, shop_id, campaign_id, audio_asset_id,
            original_audio_sha256, authorization):
        from copy import deepcopy
        from hashlib import sha256
        import re
        code, identity = _feature2_private_scope(
            self.verify_token, self.tenant_store, shop_id, campaign_id,
            authorization)
        if code is not None:
            return code, {"error":"UNAUTHORIZED" if code == 401 else
                          "PRIVATE_AUDIO_UNAVAILABLE" if code == 503 else
                          "NOT_FOUND" if code == 404 else "INVALID_REQUEST"}
        sid, cid, actor, token = identity
        try:
            aid = canonical_uuid(audio_asset_id)
            if (UUID(aid).version != 4 or type(original_audio_sha256) is not str or
                not re.fullmatch("[0-9a-f]{64}",original_audio_sha256)):
                return 400, {"error":"INVALID_REQUEST"}
        except (ValueError, TypeError, AttributeError):
            return 400, {"error":"INVALID_REQUEST"}
        if not all(callable(f) for f in (
                self.plan_reader, self.asset_reader, self.blob_reader,
                self.wav_verifier)):
            return 503, {"error":"PRIVATE_AUDIO_UNAVAILABLE"}
        try:
            def editor(s,c):
                return ((s,c)==(sid,cid) and
                    _feature2_private_editor(self.tenant_store, token, actor, sid, cid))
            if not editor(sid,cid):
                return 404, {"error":"NOT_FOUND"}
            first=self.plan_reader(token,actor,sid,cid)
            if type(first) is not dict:
                return 404, {"error":"NOT_FOUND"}
            verified=self.wav_verifier(
                shop_id=sid,campaign_id=cid,source_plan=deepcopy(first),
                audio_asset_id=aid,requested_audio_sha256=original_audio_sha256,
                authorize_current_editor=editor,
                read_current_plan=lambda s,c:self.plan_reader(token,actor,s,c),
                read_registered_private_asset=lambda s,c,a:
                    self.asset_reader(token,actor,s,c,a),
                read_private_blob=lambda s,c,a:self.blob_reader(token,actor,s,c,a))
            if (type(verified) is not dict or
                verified.get("schema")!="retailgrowth.feature2-private-original-wav-read.v1" or
                verified.get("shop_id")!=sid or verified.get("campaign_id")!=cid or
                verified.get("asset_id")!=aid or
                verified.get("original_audio_sha256")!=original_audio_sha256 or
                verified.get("mime_type")!="audio/wav" or
                verified.get("private") is not True or
                verified.get("can_publish") is not False or
                verified.get("can_dispatch_motion") is not False or
                verified.get("human_listen_required") is not True or
                verified.get("commercial_rights_not_certified") is not True or
                type(verified.get("audio_bytes")) is not bytes or
                not 128 <= len(verified["audio_bytes"]) <= 20_000_000 or
                sha256(verified["audio_bytes"]).hexdigest()!=original_audio_sha256):
                return 404, {"error":"NOT_FOUND"}
            if not editor(sid,cid):
                return 404, {"error":"NOT_FOUND"}
            return 200, {
                "body":verified["audio_bytes"],
                "headers":{"Content-Type":"audio/wav",
                           "Cache-Control":"private, no-store",
                           "Pragma":"no-cache",
                           "X-Content-Type-Options":"nosniff",
                           "Content-Disposition":
                                'attachment; filename="original-'+aid+'.wav"'},
            }
        except (ValueError,PermissionError,TypeError,KeyError):
            return 404, {"error":"NOT_FOUND"}
        except StorageUnavailable:
            return 503, {"error":"PRIVATE_AUDIO_UNAVAILABLE"}


class Feature2BlindHistoryAdapter:
    """F2-08 independent-signed score history: review only, no autoapproval."""

    def __init__(self, verify_token, tenant_store, *, history_reader=None,
                 receipt_verifier=None, history_projector=None):
        self.verify_token, self.tenant_store = verify_token, tenant_store
        self.history_reader = history_reader
        self.receipt_verifier = receipt_verifier
        self.history_projector = history_projector

    def get(self, shop_id, campaign_id, experiment_id, authorization):
        import re
        code, identity = _feature2_private_scope(
            self.verify_token, self.tenant_store,
            shop_id, campaign_id, authorization)
        if code is not None:
            return code, {"error":"UNAUTHORIZED" if code == 401 else
                          "PRIVATE_HISTORY_UNAVAILABLE" if code == 503 else
                          "NOT_FOUND" if code == 404 else "INVALID_REQUEST"}
        sid, cid, actor, token = identity
        if type(experiment_id) is not str or not re.fullmatch(
                "[a-zA-Z0-9_-]{10,120}", experiment_id):
            return 400, {"error":"INVALID_REQUEST"}
        if not all(callable(f) for f in (
                self.history_reader, self.receipt_verifier, self.history_projector)):
            return 503, {"error":"PRIVATE_HISTORY_UNAVAILABLE"}
        try:
            def editor(s,c):
                return (s,c)==(sid,cid) and _feature2_private_editor(
                    self.tenant_store,token,actor,sid,cid)
            if not editor(sid,cid):
                return 404, {"error":"NOT_FOUND"}
            out=self.history_projector(
                shop_id=sid,campaign_id=cid,experiment_id=experiment_id,
                current_editor=editor,
                read_private_history=lambda s,c,e:
                    self.history_reader(token,actor,s,c,e),
                verify_signed_history_receipt=lambda s,c,e,n,sha,digests:
                    self.receipt_verifier(token,actor,s,c,e,n,sha,digests))
            if (type(out) is not dict or out.get("schema") !=
                "retailgrowth.feature2-private-blind-review-history.v1" or
                out.get("experiment_id")!=experiment_id or
                out.get("private") is not True or
                out.get("can_publish") is not False or
                out.get("paid_motion_permitted") is not False or
                out.get("source_quality_not_certified") is not True or
                type(out.get("records")) is not list):
                return 404, {"error":"NOT_FOUND"}
            if not editor(sid,cid):
                return 404, {"error":"NOT_FOUND"}
            return 200,out
        except (ValueError,PermissionError,TypeError,KeyError):
            return 404, {"error":"NOT_FOUND"}
        except StorageUnavailable:
            return 503, {"error":"PRIVATE_HISTORY_UNAVAILABLE"}


class Feature2ReviewedDraftAdapter:
    """F2-03/F2-31 signed human-reviewed prompt draft CAS, never publish.

    Browser supplies *identifiers only*. All prompt text, reviewer evidence,
    current draft, and write-CAS are fetched from trusted JWT/RLS readers.
    No POST retry, paid model, browser-asserted approval, or provider egress.
    """

    def __init__(self, verify_token, tenant_store, *, draft_reader=None,
                 proposal_reader=None, decision_verifier=None, draft_saver=None,
                 reviewed_draft_commit=None):
        self.verify_token, self.tenant_store = verify_token, tenant_store
        self.draft_reader, self.proposal_reader = draft_reader, proposal_reader
        self.decision_verifier, self.draft_saver = decision_verifier, draft_saver
        self.reviewed_draft_commit = reviewed_draft_commit

    def post(self, shop_id, campaign_id, authorization, payload):
        import re
        code, identity = _feature2_private_scope(
            self.verify_token,self.tenant_store,
            shop_id,campaign_id,authorization)
        if code is not None:
            return code, {"error":"UNAUTHORIZED" if code == 401 else
                          "REVIEW_STORE_UNAVAILABLE" if code == 503 else
                          "NOT_FOUND" if code == 404 else "INVALID_REQUEST"}
        sid,cid,actor,token=identity
        expected={"schema","shop_id","campaign_id","creative_plan_sha256",
                  "proposal_id","source_revision","review_event_id","request_id",
                  "requires_independently_signed_human_review",
                  "requires_backend_compare_and_swap","allow_publish",
                  "allow_paid_motion"}
        if type(payload) is not dict or set(payload)!=expected:
            return 400, {"error":"INVALID_REQUEST"}
        try:
            proposal_id=canonical_uuid(payload["proposal_id"])
            review_id=canonical_uuid(payload["review_event_id"])
            request_id=canonical_uuid(payload["request_id"])
            if any(UUID(v).version!=4 for v in
                   (proposal_id,review_id,request_id)):
                return 400, {"error":"INVALID_REQUEST"}
        except (ValueError,TypeError,AttributeError):
            return 400, {"error":"INVALID_REQUEST"}
        if (payload["schema"]!="retailgrowth.feature2-reviewed-draft-request.v1" or
            payload["shop_id"]!=sid or payload["campaign_id"]!=cid or
            type(payload["creative_plan_sha256"]) is not str or
            not re.fullmatch("[0-9a-f]{64}",payload["creative_plan_sha256"]) or
            type(payload["source_revision"]) is not int or
            not 0<=payload["source_revision"]<100000 or
            payload["requires_independently_signed_human_review"] is not True or
            payload["requires_backend_compare_and_swap"] is not True or
            payload["allow_publish"] is not False or
            payload["allow_paid_motion"] is not False):
            return 400, {"error":"INVALID_REQUEST"}
        if not all(callable(f) for f in (
            self.draft_reader,self.proposal_reader,self.decision_verifier,
            self.draft_saver,self.reviewed_draft_commit)):
            return 503, {"error":"REVIEW_STORE_UNAVAILABLE"}
        try:
            def editor(s,c):
                return (s,c)==(sid,cid) and _feature2_private_editor(
                    self.tenant_store,token,actor,sid,cid)
            if not editor(sid,cid):
                return 404, {"error":"NOT_FOUND"}
            # The proposal's immutable plan SHA is verified against a trusted
            # source row, NOT only the browser's repeated digest.
            pending=self.proposal_reader(token,actor,sid,cid,proposal_id)
            if (type(pending) is not dict or
                pending.get("shop_id")!=sid or pending.get("campaign_id")!=cid or
                pending.get("proposal_id")!=proposal_id or
                pending.get("creative_plan_sha256")!=
                    payload["creative_plan_sha256"] or
                type(pending.get("original_prompt")) is not str or
                type(pending.get("improved_prompt")) is not str):
                return 404, {"error":"NOT_FOUND"}
            result=self.reviewed_draft_commit(
                shop_id=sid,campaign_id=cid,proposal_id=proposal_id,
                review_event_id=review_id,
                expected_revision=payload["source_revision"],
                original_prompt=pending["original_prompt"],
                improved_prompt=pending["improved_prompt"],
                current_editor=editor,
                read_current_draft=lambda s,c:self.draft_reader(token,actor,s,c),
                read_staged_proposal=lambda s,c,p:
                    self.proposal_reader(token,actor,s,c,p),
                verify_signed_editor_decision=lambda s,c,p,e,rev,original,proposed:
                    self.decision_verifier(token,actor,s,c,p,e,rev,original,proposed),
                save_draft_cas=lambda s,c,p,rev,e,data:self.draft_saver(
                    token,actor,s,c,p,rev,e,request_id,data))
            if (type(result) is not dict or
                result.get("schema")!="retailgrowth.feature2-reviewed-prompt-draft.v1" or
                result.get("shop_id")!=sid or result.get("campaign_id")!=cid or
                result.get("proposal_id")!=proposal_id or
                result.get("review_event_id")!=review_id or
                result.get("source_revision")!=payload["source_revision"] or
                type(result.get("revision")) is not int or
                result["revision"]!=payload["source_revision"]+1 or
                result.get("review_status")!="DRAFT" or
                result.get("private") is not True or
                result.get("can_publish") is not False or
                result.get("can_dispatch_paid_motion") is not False or
                result.get("requires_fresh_media_rights") is not True or
                result.get("requires_new_copy_fact_review") is not True):
                return 404, {"error":"NOT_FOUND"}
            if not editor(sid,cid):
                return 404, {"error":"NOT_FOUND"}
            return 201,result
        except (ValueError,PermissionError,TypeError,KeyError):
            return 404, {"error":"NOT_FOUND"}
        except StorageUnavailable:
            return 503, {"error":"REVIEW_STORE_UNAVAILABLE"}


class Feature2LocalCpuReservationAdapter:
    """F2-21: JWT-scoped, once-only, CPU-only local voice budget reservation.

    This is NOT a synthesis or queue-dispatch endpoint. The trusted injected
    reserve_validator enforces the server quota, exact source SHA, writer CAS,
    lease fencing and zero paid fallback. The server must supply a real atomic
    budget/unique-job transaction; no browser flags authorize spend.
    """

    def __init__(self, verify_token, tenant_store, *, plan_reader=None,
                 quota_reader=None, atomic_reserver=None,
                 reserve_validator=None, server_clock_ms=None):
        self.verify_token, self.tenant_store = verify_token, tenant_store
        self.plan_reader, self.quota_reader = plan_reader, quota_reader
        self.atomic_reserver = atomic_reserver
        self.reserve_validator, self.server_clock_ms = (
            reserve_validator, server_clock_ms)

    def post(self, shop_id, campaign_id, authorization, payload):
        from copy import deepcopy
        import re
        code, identity=_feature2_private_scope(
            self.verify_token,self.tenant_store,shop_id,campaign_id,authorization)
        if code is not None:
            return code, {"error":"UNAUTHORIZED" if code==401 else
                          "CPU_RESERVATION_UNAVAILABLE" if code==503 else
                          "NOT_FOUND" if code==404 else "INVALID_REQUEST"}
        sid,cid,actor,token=identity
        keys={"schema","shop_id","campaign_id","creative_plan_sha256",
              "voice_id","language","speed","preview","provider",
              "request_key","needs_current_server_signed_grants",
              "may_auto_invoke_azure","estimated_paid_cost_usd"}
        if type(payload) is not dict or set(payload)!=keys:
            return 400, {"error":"INVALID_REQUEST"}
        try:
            job_key=canonical_uuid(payload["request_key"])
            if UUID(job_key).version!=4:
                return 400, {"error":"INVALID_REQUEST"}
        except (ValueError,TypeError,AttributeError):
            return 400, {"error":"INVALID_REQUEST"}
        if (payload["schema"]!="retailgrowth.feature2-local-voice-job.v1" or
            payload["shop_id"]!=sid or payload["campaign_id"]!=cid or
            type(payload["creative_plan_sha256"]) is not str or
            not re.fullmatch("[a-f0-9]{64}",payload["creative_plan_sha256"]) or
            payload["provider"]!="kokoro-onnx" or
            type(payload["voice_id"]) is not str or
            type(payload["language"]) is not str or
            type(payload["speed"]) is not str or
            type(payload["preview"]) is not bool or
            payload["needs_current_server_signed_grants"] is not True or
            payload["may_auto_invoke_azure"] is not False or
            type(payload["estimated_paid_cost_usd"]) not in (int,float) or
            payload["estimated_paid_cost_usd"]!=0):
            return 400, {"error":"INVALID_REQUEST"}
        if not all(callable(f) for f in
                (self.plan_reader,self.quota_reader,self.atomic_reserver,
                 self.reserve_validator,self.server_clock_ms)):
            return 503, {"error":"CPU_RESERVATION_UNAVAILABLE"}
        try:
            def editor(s,c):
                return (s,c)==(sid,cid) and _feature2_private_editor(
                    self.tenant_store,token,actor,sid,cid)
            if not editor(sid,cid):
                return 404, {"error":"NOT_FOUND"}
            current=self.plan_reader(token,actor,sid,cid)
            if (type(current) is not dict or
                type(current.get("approval_record")) is not dict or
                current["approval_record"].get("plan_sha256")!=
                    payload["creative_plan_sha256"]):
                return 404, {"error":"NOT_FOUND"}
            receipt=self.reserve_validator(
                shop_id=sid,campaign_id=cid,source_plan=deepcopy(current),
                voice_id=payload["voice_id"],lang=payload["language"],
                speed=payload["speed"],job_key=job_key,
                now_ms=self.server_clock_ms(),
                authorize_current_editor=editor,
                read_current_plan=lambda s,c:self.plan_reader(token,actor,s,c),
                read_authoritative_quota=lambda s,c:
                    self.quota_reader(token,actor,s,c),
                reserve_atomic_once=lambda s,c,key,req,revision,cpu,record:
                    self.atomic_reserver(token,actor,s,c,key,req,revision,cpu,record))
            if (type(receipt) is not dict or
                receipt.get("schema")!="retailgrowth.feature2-local-cpu-reservation.v1" or
                receipt.get("shop_id")!=sid or receipt.get("campaign_id")!=cid or
                receipt.get("creative_plan_sha256")!=payload["creative_plan_sha256"] or
                receipt.get("job_key")!=job_key or
                receipt.get("provider")!="kokoro-onnx" or
                receipt.get("private") is not True or
                receipt.get("can_publish") is not False or
                receipt.get("paid_api_calls")!=0 or
                type(receipt.get("paid_api_calls")) is not int or
                receipt.get("real_model_inference_observed") is not False or
                receipt.get("reservation_is_not_worker_completion") is not True):
                return 404, {"error":"NOT_FOUND"}
            if not editor(sid,cid):
                return 404, {"error":"NOT_FOUND"}
            return 202,receipt
        except (ValueError,PermissionError,KeyError,TypeError):
            return 404, {"error":"NOT_FOUND"}
        except StorageUnavailable:
            return 503, {"error":"CPU_RESERVATION_UNAVAILABLE"}


class Feature2PrivateMp3UploadAdapter:
    """F2-29: save original MP3 + derived WAV as two PRIVATE pending assets.

    Incoming bytes must reach this boundary over an authenticated body;
    MIME, FFmpeg executable, plan and storage writer are server-selected.
    No caller path/FFmpeg args or browser-declared rights can be supplied.
    The source verifier is injected only when the independently reviewed
    CPU FFmpeg worker + durable atomic two-asset writer are configured.
    """

    def __init__(self, verify_token, tenant_store, *, plan_reader=None,
                 dual_asset_writer=None, mp3_verifier=None,
                 operator_ffmpeg_path=None):
        self.verify_token, self.tenant_store = verify_token, tenant_store
        self.plan_reader,self.dual_asset_writer = plan_reader,dual_asset_writer
        self.mp3_verifier,self.operator_ffmpeg_path=(
            mp3_verifier,operator_ffmpeg_path)

    def post(self, shop_id, campaign_id, authorization, *,
             original_mp3, content_type):
        from copy import deepcopy
        from hashlib import sha256
        code,identity=_feature2_private_scope(
            self.verify_token,self.tenant_store,shop_id,campaign_id,authorization)
        if code is not None:
            return code, {"error":"UNAUTHORIZED" if code==401 else
                          "PRIVATE_UPLOAD_UNAVAILABLE" if code==503 else
                          "NOT_FOUND" if code==404 else "INVALID_REQUEST"}
        sid,cid,actor,token=identity
        if (content_type!="audio/mpeg" or type(original_mp3) is not bytes or
            not 128<=len(original_mp3)<=20_000_000):
            return 400, {"error":"INVALID_REQUEST"}
        if (not all(callable(f) for f in
                    (self.plan_reader,self.dual_asset_writer,self.mp3_verifier))
            or not self.operator_ffmpeg_path):
            return 503, {"error":"PRIVATE_UPLOAD_UNAVAILABLE"}
        try:
            def editor(s,c):
                return (s,c)==(sid,cid) and _feature2_private_editor(
                    self.tenant_store,token,actor,sid,cid)
            if not editor(sid,cid):
                return 404, {"error":"NOT_FOUND"}
            current=self.plan_reader(token,actor,sid,cid)
            if type(current) is not dict:
                return 404, {"error":"NOT_FOUND"}
            verified=self.mp3_verifier(
                shop_id=sid,campaign_id=cid,plan=deepcopy(current),
                original_mp3=original_mp3,
                operator_ffmpeg_path=self.operator_ffmpeg_path,
                authenticated_editor=editor,
                read_authoritative_plan=lambda s,c:self.plan_reader(token,actor,s,c),
                store_both_private_pending=lambda s,c,mp3,wav,envelope:
                    self.dual_asset_writer(token,actor,s,c,mp3,wav,envelope),
                client_declared_rights=None)
            if (type(verified) is not dict or
                verified.get("schema")!="retailgrowth.feature2-uploaded-mp3-pending.v1" or
                verified.get("shop_id")!=sid or verified.get("campaign_id")!=cid or
                verified.get("original_mp3_sha256")!=sha256(original_mp3).hexdigest() or
                verified.get("source_mime_type")!="audio/mpeg" or
                verified.get("derived_mime_type")!="audio/wav" or
                verified.get("private") is not True or
                verified.get("can_publish") is not False or
                verified.get("can_dispatch_motion") is not False or
                verified.get("review_state")!="PENDING_RIGHTS_AND_SPEECH_REVIEW" or
                verified.get("original_media_rights_verified") is not False or
                verified.get("human_speech_alignment_verified") is not False or
                verified.get("original_wav_is_registered_feature7_source") is not False or
                verified.get("private_download_url") is not None or
                verified.get("billing")!="NONE" or
                type(verified.get("paid_calls")) is not int or
                verified["paid_calls"]!=0 or
                type(verified.get("asset_id")) is not str or
                type(verified.get("derived_wav_asset_id")) is not str or
                verified["asset_id"]==verified["derived_wav_asset_id"]):
                return 404, {"error":"NOT_FOUND"}
            if not editor(sid,cid):
                return 404, {"error":"NOT_FOUND"}
            # Return bounded signed-source registration ONLY, never private
            # decoded WAV, original MP3 bytes or any public download URL.
            return 201, {"schema":verified["schema"],
                "shop_id":sid,"campaign_id":cid,
                "asset_id":verified["asset_id"],
                "derived_wav_asset_id":verified["derived_wav_asset_id"],
                "original_mp3_sha256":verified["original_mp3_sha256"],
                "derived_wav_sha256":verified["derived_wav_sha256"],
                "review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
                "private":True,"can_publish":False,"paid_calls":0}
        except (ValueError,PermissionError,KeyError,TypeError):
            return 404, {"error":"NOT_FOUND"}
        except StorageUnavailable:
            return 503, {"error":"PRIVATE_UPLOAD_UNAVAILABLE"}
