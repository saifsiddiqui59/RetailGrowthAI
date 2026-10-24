"""Worker-only upload boundary for an immutable, private RetailGrowthAI poster.

This file does not create jobs, grant download rights or publish images.
The future poster worker MUST hold a fresh fenced database claim before calling
upload_png, then atomically complete that same claim before exposing the asset.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request

from PIL import Image, UnidentifiedImageError

from admin_store import backend_headers
from private_media import BUCKET, PrivateMedia
from tenant_store import StorageUnavailable, canonical_uuid

# Exact, versioned poster presets used by the existing offline Pillow renderer.
FORMATS = {"square": (1080, 1080), "portrait": (1080, 1350)}
MAX_PNG_BYTES = 12 * 1024 * 1024
MIN_PNG_BYTES = 100
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def validate_output_png(output_file, format_name):
    """Decode the actual bytes, not the filename or untrusted Content-Type."""
    if format_name not in FORMATS:
        raise ValueError("unsupported poster format")
    path = Path(output_file)
    try:
        if path.is_symlink() or not path.is_file():
            raise StorageUnavailable("poster output must be a regular file")
        size = path.stat().st_size
        if not MIN_PNG_BYTES <= size <= MAX_PNG_BYTES:
            raise StorageUnavailable("poster output size out of bounds")
        # Read once, then validate and upload the same immutable byte snapshot.
        # Prevents a path replacement between Pillow validation and network I/O.
        data = path.read_bytes()
        if len(data) != size or not data.startswith(PNG_MAGIC):
            raise StorageUnavailable("poster output is not PNG")
        # verify() checks PNG structure, but does not fully decompress its pixels.
        with Image.open(BytesIO(data)) as image:
            if (image.format != "PNG" or image.size != FORMATS[format_name]
                    or image.mode != "RGB" or getattr(image, "n_frames", 1) != 1):
                raise StorageUnavailable("poster output does not match approved preset")
            image.verify()
        with Image.open(BytesIO(data)) as image:
            image.load()  # truncated/corrupt compressed payload must fail here
            if image.size != FORMATS[format_name] or image.mode != "RGB":
                raise StorageUnavailable("poster output decoded differently")
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError, SyntaxError,
            ValueError) as exc:
        if isinstance(exc, StorageUnavailable):
            raise
        raise StorageUnavailable("invalid private poster output") from exc
    return data


class PrivatePosterMedia(PrivateMedia):
    """Never overwrites a prior lease's output; uses worker-only credentials."""

    def upload_png(self, shop_id, poster_id, lease_token, output_file, *, format_name):
        sid = canonical_uuid(shop_id)
        pid = canonical_uuid(poster_id)
        token = canonical_uuid(lease_token)
        data = validate_output_png(output_file, format_name)
        # Every claim writes a distinct path; a stale worker cannot replace a
        # newer claim's private object. DB completion must separately check token.
        key = f"{sid}/posters/{pid}/{token}.png"
        url = self.origin + "/storage/v1/object/" + BUCKET + "/" + self._path(sid, key)
        try:
            request = Request(
                url, data=data, method="POST",
                headers={**backend_headers(self.secret),
                         "Content-Type": "image/png", "x-upsert": "false"},
            )
            with self.transport(request, timeout=60) as response:
                if response.status not in (200, 201):
                    raise StorageUnavailable("private poster upload was not accepted")
        except HTTPError as exc:
            # Storage 409 is not idempotent success. Existing bytes/rights cannot
            # be assumed to be equivalent, even for an identical lease key.
            raise StorageUnavailable("private poster output collision or denial") from exc
        except (URLError, OSError) as exc:
            raise StorageUnavailable("private poster upload unavailable") from exc
        return key
