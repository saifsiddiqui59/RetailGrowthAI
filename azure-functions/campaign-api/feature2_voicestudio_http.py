"""Feature2 signed API boundary for existing upstream VoiceStudio private jobs.

SOURCE ONLY, NOT ROUTED OR ENABLED. A real Azure Functions route and SQL
migration both require separate security review. This file never trusts actor,
shop access, provider URL, voice/model or rights from browser input.
"""
from __future__ import annotations

from uuid import UUID

from ai_agents.feature2_voicestudio_registration import run_verified_private_voice_job
from ai_agents.feature2_voicestudio_adapter import VoiceStudioUnavailable
from security import AuthenticationError
from tenant_store import StorageUnavailable, canonical_uuid
from feature2_voicestudio_sql import VoiceStudioSqlDenied
from feature2_voicestudio_storage import PrivateVoiceStorageDenied


def _asset_id(value):
    try:
        return (type(value) is str and canonical_uuid(value) == value
                and UUID(value).version == 4)
    except (ValueError, TypeError, AttributeError):
        return False


class VoiceStudioSignedAPI:
    def __init__(
        self, verify_token, tenant_store, sql_store_factory, storage,
        *, base_url, api_key, enabled=False, commercial_model_verified=False,
        worker=run_verified_private_voice_job, transport=None,
    ):
        self.verify_token = verify_token
        self.tenant_store = tenant_store
        self.sql_store_factory = sql_store_factory
        self.storage = storage
        self.base_url = base_url
        self.api_key = api_key
        self.enabled = enabled
        self.commercial_model_verified = commercial_model_verified
        self.worker = worker
        self.transport = transport

    def generate(self, shop_id, authorization, body):
        """Only {campaign_id,request_id} is accepted from a JWT-authenticated editor.

        The trusted SQL plan picks the exact approved script, voice and duration.
        No body-supplied actor, approval status, model, URL, script or media path.
        """
        try:
            sid = canonical_uuid(shop_id)
            if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
                return 401, {"error": "UNAUTHORIZED"}
            token = authorization[7:].strip()
            if not token:
                return 401, {"error": "UNAUTHORIZED"}
            uid = canonical_uuid(self.verify_token(token))
            if type(body) is not dict or set(body) != {"campaign_id", "request_id"}:
                return 400, {"error": "INVALID_REQUEST"}
            cid = canonical_uuid(body["campaign_id"])
            request_id = canonical_uuid(body["request_id"])
            if not self.tenant_store.member(token, uid, sid, write=True):
                return 404, {"error": "NOT_FOUND"}
            if self.enabled is not True or self.commercial_model_verified is not True:
                return 503, {"error": "VOICESTUDIO_NOT_LICENSED_OR_ENABLED"}
            if not callable(self.sql_store_factory) or self.storage is None:
                return 503, {"error": "VOICE_PRIVATE_DB_NOT_CONFIGURED"}
            sql = self.sql_store_factory(uid)
            if not all(callable(getattr(sql, name, None)) for name in (
                "read_current_plan", "claim_once", "register_verified_private_pair",
                "read_private_receipt",
            )):
                return 503, {"error": "VOICE_PRIVATE_DB_NOT_CONFIGURED"}
            plan = sql.read_current_plan(sid, cid)
            if not isinstance(plan, dict) or plan.get("shop_id") != sid or plan.get("campaign_id") != cid:
                return 404, {"error": "NOT_FOUND"}
            result = self.worker(
                shop_id=sid, campaign_id=cid, request_id=request_id,
                voice=plan["voice"], reel_seconds=plan["duration_seconds"],
                base_url=self.base_url, api_key=self.api_key,
                storage=self.storage,
                read_current_plan=sql.read_current_plan,
                claim_once=sql.claim_once,
                register_verified_private_pair=sql.register_verified_private_pair,
                read_private_receipt=sql.read_private_receipt,
                enabled=True, commercial_model_verified=True,
                transport=self.transport,
            )
            # Signed membership is not a one-time permission; recheck even
            # after successful private write before revealing an asset ID.
            if not self.tenant_store.member(token, uid, sid, write=True):
                return 403, {"error": "VOICE_ACCESS_REVOKED"}
            if (
                not isinstance(result, dict)
                or result.get("shop_id") != sid
                or result.get("campaign_id") != cid
                or result.get("request_id") != request_id
                or result.get("review_status") != "NEEDS_REVIEW"
                or result.get("approved_to_render_or_publish") is not False
                or result.get("private_audio_url") is not None
                or not _asset_id(result.get("audio_asset_id"))
            ):
                return 503, {"error": "VOICE_PRIVATE_REVIEW_UNVERIFIED"}
            return 202, {
                "schema": "retailgrowth.feature2-private-voice-job-http.v1",
                "shop_id": sid, "campaign_id": cid,
                "request_id": request_id,
                "audio_asset_id": result["audio_asset_id"],
                "review_status": "NEEDS_REVIEW",
                "approved_to_render_or_publish": False,
                "private_audio_url": None,
                "replay_on_timeout": False,
            }
        except (AuthenticationError,):
            return 401, {"error": "UNAUTHORIZED"}
        except (VoiceStudioUnavailable, VoiceStudioSqlDenied, PrivateVoiceStorageDenied,
                StorageUnavailable, TimeoutError, OSError):
            return 503, {"error": "VOICE_STUDIO_UNAVAILABLE"}
        except (ValueError, TypeError, KeyError):
            return 400, {"error": "INVALID_REQUEST"}
