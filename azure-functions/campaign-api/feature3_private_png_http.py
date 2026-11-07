"""F3-08 private binary HTTP boundary, source-only until route review.

No caller-supplied rights, paths, storage URLs or user identity are accepted.
The injected reader must be constructed with backend-owned trusted pins and
fresh JWT/RLS dependencies. This module never creates an Azure route.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID
import struct
import zlib

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



def _valid_png(data):
    """Validate the complete PNG chunk envelope before exposing private bytes.

    Reject truncated, trailing, corrupted or polyglot output; decoding pixels
    remains the responsibility of the existing private reader.
    """
    if type(data) is not bytes or not 100 <= len(data) <= 25 * 1024 * 1024:
        return False
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    offset, seen_ihdr, seen_idat, ended_idat = 8, False, False, False
    seen_plte, color_type = False, None
    while offset + 12 <= len(data):
        size = struct.unpack_from(">I", data, offset)[0]
        end = offset + 12 + size
        if size > len(data) - offset - 12 or end > len(data):
            return False
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:end - 4]
        crc = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            return False
        if not seen_ihdr:
            if kind != b"IHDR" or size != 13:
                return False
            width, height = struct.unpack_from(">II", payload)
            if (not (0 < width <= 16384 and 0 < height <= 16384) or
                    width * height > 16_777_216 or
                    payload[8] not in (1, 2, 4, 8, 16) or
                    payload[9] not in (0, 2, 3, 4, 6) or
                    payload[10:] != b"\x00\x00\x00"):
                return False
            valid_depths = {0: (1, 2, 4, 8, 16), 2: (8, 16),
                            3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
            if payload[8] not in valid_depths[payload[9]]:
                return False
            color_type = payload[9]
            seen_ihdr = True
        elif kind == b"IHDR":
            return False
        if kind == b"PLTE":
            # Palette must be unique, precede pixel data, and be present for
            # indexed-color PNGs. Grayscale images cannot carry a palette.
            if (seen_plte or seen_idat or color_type in (0, 4) or
                    not 3 <= size <= 768 or size % 3):
                return False
            seen_plte = True
        if kind == b"IDAT":
            if color_type == 3 and not seen_plte:
                return False
            if ended_idat or size == 0:
                return False
            seen_idat = True
        elif seen_idat:
            ended_idat = True
        # Unknown critical chunks cannot be safely interpreted as PNG.
        if kind not in (b"IHDR", b"PLTE", b"IDAT", b"IEND") and not (kind[0] & 0x20):
            return False
        if kind == b"IEND":
            return (seen_idat and size == 0 and end == len(data) and
                    (color_type != 3 or seen_plte))
        offset = end
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
        if (not _valid_png(raw) or
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
