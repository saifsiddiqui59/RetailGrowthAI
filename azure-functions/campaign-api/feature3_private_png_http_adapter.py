"""F3-08 HTTP response boundary for authenticated private PNG bytes.

This is an adapter, not an Azure Functions route registration. A caller must
mount it behind the normal JWT-protected Function route and provide the
server-owned scoped reader factory. No browser-supplied rights are accepted.
"""
from __future__ import annotations

from uuid import UUID

from feature3_private_png_reader import PrivateGeneratedDownloadDenied

_MAX_PNG_BYTES = 25 * 1024 * 1024
_DENIED_HEADERS = {
    "Cache-Control": "no-store, private",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
}
_PNG_HEADERS = {
    **_DENIED_HEADERS,
    "Content-Type": "image/png",
    "Content-Disposition": 'attachment; filename="generated.png"',
    "X-Content-Type-Options": "nosniff",
}


def private_png_http_response(*, reader_factory, shop_id, job_id, bearer_token):
    """Return (status, immutable headers, body) without leaking denial details.

    JWT verification, active membership, current rights and byte integrity
    remain mandatory responsibilities of the trusted scoped reader. Never
    invoke this function with an untrusted fixture factory in hosted routes.
    """
    if not callable(reader_factory):
        raise ValueError("Trusted scoped reader factory required")
    try:
        # Reject malformed route scope before invoking any tenant reader.
        for scope in (shop_id, job_id):
            if type(scope) is not str or len(scope) != 36:
                raise PrivateGeneratedDownloadDenied("Unavailable")
            parsed = UUID(scope)
            if parsed.version != 4 or str(parsed) != scope:
                raise PrivateGeneratedDownloadDenied("Unavailable")
        if type(bearer_token) is not str or not bearer_token.startswith("Bearer "):
            raise PrivateGeneratedDownloadDenied("Unavailable")
        token = bearer_token[7:]
        if (not 12 <= len(token) <= 8192 or
                token.startswith(("sb_secret_", "sb_publishable_")) or
                any(ord(ch) < 33 or ord(ch) > 126 for ch in token) or
                any(ch in token for ch in (",", ";", '"', "\\"))):
            raise PrivateGeneratedDownloadDenied("Unavailable")
        # Reject malformed compact JWS framing before constructing any reader.
        # This is input hygiene only; the scoped reader MUST still verify the
        # cryptographic signature, issuer, audience, membership and rights.
        parts = token.split(".")
        if (len(parts) != 3 or any(not part for part in parts) or
                len(parts[0]) > 2048 or len(parts[1]) > 6144 or
                len(parts[2]) > 2048 or
                any(len(part) % 4 == 1 for part in parts) or
                any(any(not (ch.isascii() and (ch.isalnum() or ch in "-_"))
                        for ch in part) for part in parts)):
            raise PrivateGeneratedDownloadDenied("Unavailable")
        reader = reader_factory(shop_id, job_id)
        body = reader.read(user_token=token, shop_id=shop_id, job_id=job_id)
        if type(body) is not bytes or not 100 <= len(body) <= _MAX_PNG_BYTES or not body.startswith(bytes((137, 80, 78, 71, 13, 10, 26, 10))):
            raise PrivateGeneratedDownloadDenied("Unavailable")
        return 200, dict(_PNG_HEADERS), body
    except (PrivateGeneratedDownloadDenied, ValueError, TypeError, AttributeError):
        return 404, dict(_DENIED_HEADERS), b""
