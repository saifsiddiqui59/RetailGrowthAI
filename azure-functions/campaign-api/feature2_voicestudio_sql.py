"""Server-only PostgREST RPC adapter for VoiceStudio durable original-key jobs.

NO public HTTP route and NO SQL migration or cloud write is activated by this
module. The three dedicated RPCs must be independently reviewed/deployed first.
A signed JWT principal and live membership are mandatory in the SQL RPC body;
caller must derive actor_id from a VERIFIED token, never a browser field.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from uuid import UUID

from admin_store import backend_headers

_SHA = re.compile(r"^[0-9a-f]{64}$")
MAX_JSON = 32 * 1024
RPC = {
    "claim": "feature2_voicestudio_claim",
    "register": "feature2_voicestudio_register",
    "receipt": "feature2_voicestudio_receipt",
}


class VoiceStudioSqlDenied(ValueError):
    """No credentials or private backend response should escape to users."""


def _uuid4(value):
    try:
        return type(value) is str and str(UUID(value)) == value and UUID(value).version == 4
    except (TypeError, ValueError, AttributeError):
        return False


def _sha(value):
    return type(value) is str and _SHA.fullmatch(value) is not None


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise VoiceStudioSqlDenied("Private SQL RPC redirected")


class VoiceStudioSqlStore:
    """Original-key claim/registration/receipt adapter, not a DB migration."""

    def __init__(self, origin, secret, actor_id, *, transport=None):
        try:
            p = urlsplit(origin)
            valid = (
                type(origin) is str and p.scheme == "https"
                and p.hostname is not None
                and not p.username and not p.password and p.query == ""
                and p.fragment == "" and p.path in ("", "/")
                and p.port in (None, 443)
            )
        except (ValueError, TypeError):
            valid = False
        if not valid or not _uuid4(actor_id):
            raise VoiceStudioSqlDenied("Verified signed actor and private HTTPS origin required")
        self.origin = origin.rstrip("/")
        self.actor_id = actor_id
        self.headers = backend_headers(secret)
        self.sender = transport or build_opener(_NoRedirect()).open

    def _rpc(self, kind, body):
        if kind not in RPC:
            raise VoiceStudioSqlDenied("Unsupported trusted SQL call")
        path = RPC[kind]
        url = self.origin + "/rest/v1/rpc/" + path
        request = Request(url, method="POST", data=json.dumps(body).encode("utf-8"), headers={
            **self.headers, "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "return=representation",
        })
        try:
            with self.sender(request, timeout=12) as response:
                if (
                    response.status != 200
                    or response.geturl() != url
                    or response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                    != "application/json"
                ):
                    raise VoiceStudioSqlDenied("Unverified SQL RPC acknowledgement")
                raw = response.read(MAX_JSON + 1)
        except (HTTPError, URLError, OSError, TimeoutError):
            raise VoiceStudioSqlDenied("SQL voice job status is denied or uncertain") from None
        if not 1 <= len(raw) <= MAX_JSON:
            raise VoiceStudioSqlDenied("Invalid bounded SQL receipt")
        try:
            data = json.loads(raw)
        except (UnicodeError, ValueError):
            raise VoiceStudioSqlDenied("Malformed SQL receipt") from None
        if type(data) is not dict:
            raise VoiceStudioSqlDenied("SQL RPC did not return one receipt")
        return data

    def claim_once(self, shop_id, campaign_id, request_id, plan_sha256):
        if not all(_uuid4(v) for v in (shop_id, campaign_id, request_id)) or not _sha(plan_sha256):
            raise VoiceStudioSqlDenied("Invalid original voice job identity")
        result = self._rpc("claim", {
            "p_actor_id": self.actor_id,
            "p_shop_id": shop_id,
            "p_campaign_id": campaign_id,
            "p_request_id": request_id,
            "p_plan_sha256": plan_sha256,
        })
        if (
            result.get("shop_id") != shop_id
            or result.get("campaign_id") != campaign_id
            or result.get("request_id") != request_id
            or result.get("plan_sha256") != plan_sha256
            or result.get("status") != "CLAIMED_ONCE"
            or type(result.get("paid_inference_calls")) is not int
            or result["paid_inference_calls"] != 0
        ):
            raise VoiceStudioSqlDenied("Original-key SQL claim was not newly granted")
        return result

    def register_verified_private_pair(self, shop_id, campaign_id, request_id, claim, proof):
        if not all(_uuid4(v) for v in (shop_id, campaign_id, request_id)):
            raise VoiceStudioSqlDenied("Invalid private registration identity")
        if (
            type(claim) is not dict
            or claim.get("shop_id") != shop_id
            or claim.get("campaign_id") != campaign_id
            or claim.get("request_id") != request_id
            or claim.get("status") != "CLAIMED_ONCE"
            or not _sha(claim.get("plan_sha256"))
            or type(proof) is not dict
            or proof.get("original_object_key")
            != f"{shop_id}/voicestudio/{campaign_id}/{request_id}/original.wav"
            or proof.get("render_object_key")
            != f"{shop_id}/voicestudio/{campaign_id}/{request_id}/render.wav"
            or not all(_sha(proof.get(k)) for k in ("original_sha256", "render_sha256"))
            or not all(type(proof.get(k)) is int and 44 <= proof[k] <= 8 * 1024 * 1024
                       for k in ("original_bytes", "render_bytes"))
            or proof.get("requires_human_review") is not True
            or proof.get("publish_approved") is not False
        ):
            raise VoiceStudioSqlDenied("Unverified original-key private media evidence")
        result = self._rpc("register", {
            "p_actor_id": self.actor_id,
            "p_shop_id": shop_id, "p_campaign_id": campaign_id,
            "p_request_id": request_id,
            "p_plan_sha256": claim["plan_sha256"],
            "p_original_sha256": proof["original_sha256"],
            "p_render_sha256": proof["render_sha256"],
            "p_original_bytes": proof["original_bytes"],
            "p_render_bytes": proof["render_bytes"],
        })
        if (
            result.get("status") != "REGISTERED_PRIVATE_NEEDS_REVIEW"
            or result.get("shop_id") != shop_id
            or result.get("campaign_id") != campaign_id
            or result.get("request_id") != request_id
            or result.get("original_sha256") != proof["original_sha256"]
            or result.get("render_sha256") != proof["render_sha256"]
            or result.get("publish_approved") is not False
        ):
            raise VoiceStudioSqlDenied("Private registration CAS was not confirmed")
        return result

    def read_private_receipt(self, shop_id, campaign_id, request_id):
        if not all(_uuid4(v) for v in (shop_id, campaign_id, request_id)):
            raise VoiceStudioSqlDenied("Invalid private receipt identity")
        result = self._rpc("receipt", {
            "p_actor_id": self.actor_id,
            "p_shop_id": shop_id,
            "p_campaign_id": campaign_id,
            "p_request_id": request_id,
        })
        if (
            not _uuid4(result.get("audio_asset_id"))
            or result.get("shop_id") != shop_id
            or result.get("campaign_id") != campaign_id
            or result.get("request_id") != request_id
            or not all(_sha(result.get(k)) for k in ("plan_sha256", "original_sha256", "render_sha256"))
            or result.get("private") is not True
            or result.get("review_status") != "NEEDS_REVIEW"
            or result.get("commercial_rights_confirmed") is not True
            or result.get("publish_approved") is not False
        ):
            raise VoiceStudioSqlDenied("Untrusted private receipt or changed role")
        return result
