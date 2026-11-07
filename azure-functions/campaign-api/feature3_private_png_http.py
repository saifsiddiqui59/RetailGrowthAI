"""F3-08 private PNG HTTP boundary (source-only; no mounted Azure route).

Reuse the established Feature3PrivateBinaryHTTP verification instead of
maintaining a second, weaker PNG parser. The trusted reader must still perform
fresh signed JWT/RLS and independently reviewed rights checks before and after
each private Storage read. A synthetic reader is NOT a deployment grant.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from feature3_private_binary_http import Feature3PrivateBinaryHTTP


@dataclass(frozen=True)
class BinaryReply:
    status: int
    body: bytes
    headers: dict


def _opaque(status):
    return BinaryReply(status, b"", {
        "Cache-Control": "no-store, private",
        "Pragma": "no-cache",
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'",
        "Vary": "Authorization",
        "Content-Length": "0",
    })


def _canonical(value):
    if type(value) is not str:
        return False
    try:
        return UUID(value).version == 4 and str(UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def private_png_http(*, authorization, shop_id, job_id, reader_factory):
    """Serve only verified private binary receipts; never mint a Storage URL.

    The factory must come from a trusted server-side rights binding. This
    code does not register an endpoint or enable any disabled route.
    """
    if not _canonical(shop_id) or not _canonical(job_id):
        return _opaque(404)
    if type(authorization) is not str or len(authorization) > 8200:
        return _opaque(401)
    if not authorization.startswith("Bearer "):
        return _opaque(401)
    token = authorization[7:]
    if (not 12 <= len(token) <= 8192 or
            any(ord(ch) < 33 or ord(ch) > 126 for ch in token) or
            token.startswith(("sb_secret_", "sb_publishable_"))):
        return _opaque(401)
    if not callable(reader_factory):
        return _opaque(503)
    try:
        reader = reader_factory(shop_id, job_id)
        # Canonical existing handler owns receipt identity, immutable SHA,
        # PNG format/pixel validation, private-only flags and response headers.
        status, body, headers = Feature3PrivateBinaryHTTP(reader=reader).handle(
            method="GET", authorization=authorization,
            shop_id=shop_id, job_id=job_id)
    except Exception:
        return _opaque(503)
    if status != 200:
        # Preserve the inner denial reason/status without exposing any bytes,
        # object keys, Authorization tokens or source-specific headers.
        return _opaque(status)
    return BinaryReply(status, body, headers)
