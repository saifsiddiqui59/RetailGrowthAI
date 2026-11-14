"""Unregistered HTTP response boundary for private VoiceStudio original WAV review.

The root Azure Functions route is independently protected in PR #925. This
module deliberately does not register an endpoint or instantiate credentials.
"""
from __future__ import annotations

from feature2_voicestudio_review_audio import (
    VoiceStudioReviewDenied,
    read_current_voiceover_for_review,
)


def private_original_review_response(*, request, shop_id, campaign_id, request_id,
                                     verify_token, tenant_store, sql_store_factory,
                                     private_storage):
    """Return (status, headers, body) for a trusted Azure Functions adapter.

    All authentication and SQL/tenant checks are performed by the service.
    Never cache private bytes or expose storage paths, tokens or SQL details.
    """
    headers = {
        "Cache-Control": "no-store, private",
        "Pragma": "no-cache",
        "Vary": "Authorization",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'",
    }
    try:
        # Malformed HTTP request wrappers are unauthenticated, not provider outages.
        try:
            authorization = request.headers.get("Authorization")
        except (AttributeError, TypeError, ValueError, KeyError, IndexError):
            return 401, headers, b""
        if (type(authorization) is not str or not authorization.strip()\n                or any(ord(ch) < 32 or ord(ch) == 127 for ch in authorization)):
            return 401, headers, b""
        content = read_current_voiceover_for_review(
            shop_id=shop_id, campaign_id=campaign_id, request_id=request_id,
            authorization=authorization, verify_token=verify_token,
            tenant_store=tenant_store, sql_store_factory=sql_store_factory,
            private_storage=private_storage,
        )
        # Defense in depth: a faulty injected reader cannot stream an oversized
        # or non-RIFF response through this unregistered HTTP boundary.
        if (type(content) is not bytes or not 44 <= len(content) <= 8 * 1024 * 1024
                or content[:4] != b"RIFF" or content[8:12] != b"WAVE"
                or int.from_bytes(content[4:8], "little") != len(content) - 8):
            raise VoiceStudioReviewDenied("Private VoiceStudio review access denied")
        return 200, {**headers, "Content-Type": "audio/wav",
                     "Content-Length": str(len(content))}, content
    except VoiceStudioReviewDenied:
        return 404, headers, b""
    except Exception:
        # Provider failures must never disclose their diagnostic or audio.
        return 503, headers, b""
