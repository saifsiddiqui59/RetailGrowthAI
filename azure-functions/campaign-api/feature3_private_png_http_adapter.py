"""F3-08 HTTP response boundary for authenticated private PNG bytes.

This is an adapter, not an Azure Functions route registration. A caller must
mount it behind the normal JWT-protected Function route and provide the
server-owned scoped reader factory. No browser-supplied rights are accepted.
"""
from __future__ import annotations

from feature3_private_png_reader import PrivateGeneratedDownloadDenied

_DENIED_HEADERS = {"Cache-Control": "no-store, private", "Pragma": "no-cache"}
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
        if type(bearer_token) is not str or not bearer_token.startswith("Bearer "):
            raise PrivateGeneratedDownloadDenied("Unavailable")
        token = bearer_token[7:]
        if not token or token != token.strip() or " " in token:
            raise PrivateGeneratedDownloadDenied("Unavailable")
        reader = reader_factory(shop_id, job_id)
        body = reader.read(user_token=token, shop_id=shop_id, job_id=job_id)
        if type(body) is not bytes or len(body) < 100 or not body.startswith(bytes((137, 80, 78, 71, 13, 10, 26, 10))):
            raise PrivateGeneratedDownloadDenied("Unavailable")
        return 200, dict(_PNG_HEADERS), body
    except (PrivateGeneratedDownloadDenied, ValueError, TypeError, AttributeError):
        return 404, dict(_DENIED_HEADERS), b""
