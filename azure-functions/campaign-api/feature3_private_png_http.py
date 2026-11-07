"""F3-08 private binary HTTP boundary, source-only until route review.

No caller-supplied rights, paths, storage URLs or user identity are accepted.
The injected reader must be constructed with backend-owned trusted pins and
fresh JWT/RLS dependencies. This module never creates an Azure route.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from feature3_private_png_reader import PrivateGeneratedDownloadDenied
from tenant_store import StorageUnavailable


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
    """Return an opaque binary response; caller must mount behind auth=None.

    reader_factory(shop, job) is a trusted server-side dependency, not a
    request-selected factory. Its reader must revalidate rights after IO.
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
        result = reader.read(user_token=token, shop_id=shop_id, job_id=job_id)
        raw = result["image_bytes"]
        if (type(raw) is not bytes or not 100 <= len(raw) <= 25 * 1024 * 1024 or
                result.get("mime_type") != "image/png" or
                result.get("shop_id") != shop_id or
                result.get("job_id") != job_id or
                result.get("private") is not True or
                result.get("signed_url_issued") is not False):
            return _opaque(404)
    except PrivateGeneratedDownloadDenied:
        return _opaque(404)
    except (StorageUnavailable, OSError):
        return _opaque(503)
    except Exception:
        return _opaque(503)
    return BinaryReply(200, raw, {
        "Content-Type": "image/png",
        "Content-Length": str(len(raw)),
        "Content-Disposition": "attachment; filename=\"private-poster.png\"",
        "Cache-Control": "no-store, private",
        "Pragma": "no-cache",
        "X-Content-Type-Options": "nosniff",
    })
