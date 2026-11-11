"""Service-only VoiceStudio original PCM reader for authenticated human review.

No HTTP route or signed URL. The ORIGINAL audio can be heard by a current
retailer editor only while its SQL original-key review receipt and JWT/RLS
membership remain valid. It cannot approve, publish or render the asset.
"""
from __future__ import annotations

import re
from hashlib import sha256
from uuid import UUID

from security import AuthenticationError
from tenant_store import StorageUnavailable, canonical_uuid
from feature2_voicestudio_storage import PrivateVoiceStorageDenied, _wav

_SHA = re.compile(r"^[0-9a-f]{64}$")


class VoiceStudioReviewDenied(PermissionError):
    """Generic fail-closed private audio review denial (no leaked identifiers)."""


def _v4(value):
    try:
        return type(value) is str and str(UUID(value)) == value and UUID(value).version == 4
    except (ValueError, TypeError, AttributeError):
        return False


def _receipt(sql_reader, shop, campaign, request):
    result = sql_reader(shop, campaign, request)
    if (
        type(result) is not dict
        or not _v4(result.get("audio_asset_id"))
        or result.get("shop_id") != shop
        or result.get("campaign_id") != campaign
        or result.get("request_id") != request
        or result.get("private") is not True
        or result.get("review_status") != "NEEDS_REVIEW"
        or result.get("commercial_rights_confirmed") is not True
        or result.get("publish_approved") is not False
        or type(result.get("original_sha256")) is not str
        or _SHA.fullmatch(result["original_sha256"]) is None
        or type(result.get("render_sha256")) is not str
        or _SHA.fullmatch(result["render_sha256"]) is None
        or type(result.get("plan_sha256")) is not str
        or _SHA.fullmatch(result["plan_sha256"]) is None
    ):
        raise VoiceStudioReviewDenied("Private VoiceStudio review access denied")
    # Snapshot the SQL receipt: adapters may reuse/mutate the same dict during I/O.
    # A live reference would make post-read revocation comparisons ineffective.
    return dict(result)


def read_current_voiceover_for_review(
    *,
    shop_id, campaign_id, request_id, authorization,
    verify_token, tenant_store, sql_store_factory, private_storage,
):
    """Fetch original bytes for a *trusted* HTTP adapter (not a public method).

    Call only from a route that maps denials to non-disclosing 401/404/503
    responses and sets no-store. All readers are server-created, never
    supplied by client JSON. Re-read SQL and membership after private GET.
    """
    if not (all(_v4(x) for x in (shop_id, campaign_id, request_id))
            and isinstance(authorization, str)
            and authorization.startswith("Bearer ")
            and callable(verify_token)
            and callable(sql_store_factory)
            and callable(getattr(tenant_store, "member", None))
            and callable(getattr(private_storage, "read_verified_original", None))):
        raise VoiceStudioReviewDenied("Private VoiceStudio review access denied")
    token = authorization[7:]
    # Never normalize malformed Authorization headers into accepted credentials.
    if (token != token.strip() or any(ch.isspace() for ch in token)
            or not 8 <= len(token) <= 8192):
        raise VoiceStudioReviewDenied("Private VoiceStudio review access denied")
    try:
        user_id = canonical_uuid(verify_token(token))
        if tenant_store.member(token, user_id, shop_id, write=True) is not True:
            raise VoiceStudioReviewDenied("Private VoiceStudio review access denied")
        reader = sql_store_factory(user_id)
        sql_receipt = getattr(reader, "read_private_receipt", None)
        if not callable(sql_receipt):
            raise VoiceStudioReviewDenied("Private VoiceStudio review access denied")
        before = _receipt(sql_receipt, shop_id, campaign_id, request_id)
        content = private_storage.read_verified_original(
            shop_id, campaign_id, request_id, before["original_sha256"]
        )
        if (type(content) is not bytes or not 44 <= len(content) <= 8 * 1024 * 1024
                or sha256(content).hexdigest() != before["original_sha256"]):
            raise VoiceStudioReviewDenied("Private VoiceStudio review access denied")
        # wave.open accepts bytes beyond the declared RIFF envelope. Require
        # the full object to be exactly the RIFF payload, with no hidden tail.
        # This check must precede post-read authorization and byte disclosure.
        if (content[:4] != b"RIFF" or content[8:12] != b"WAVE"
                or int.from_bytes(content[4:8], "little") != len(content) - 8):
            raise VoiceStudioReviewDenied("Private VoiceStudio review access denied")
        _wav(content)
        # A role, claim, rights or reviewed plan could be revoked during I/O.
        if _receipt(sql_receipt, shop_id, campaign_id, request_id) != before:
            raise VoiceStudioReviewDenied("Private VoiceStudio review access denied")
        if canonical_uuid(verify_token(token)) != user_id:
            raise VoiceStudioReviewDenied("Private VoiceStudio review access denied")
        if not tenant_store.member(token, user_id, shop_id, write=True):
            raise VoiceStudioReviewDenied("Private VoiceStudio review access denied")
        return content
    except Exception:
        # Third-party JWT, SQL and Storage adapters can raise provider-specific
        # exceptions. Never leak their messages or accidentally return private
        # bytes when a security dependency fails. Do not retry uncertain I/O.
        raise VoiceStudioReviewDenied("Private VoiceStudio review access denied") from None
