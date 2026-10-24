"""Part 2 service-only, hash-pinned read of a Part 1-generated MP4.

NOT a public API, upload authorization or active social worker. The reviewed
job/media revision and expected SHA-256 must be supplied by a separate,
server-only database authority. Never trust a browser path, host or digest.
Meta URL publication also needs an immutable serving copy: private objects
remain mutable under existing Part 1 tenant Storage policies.
"""
from __future__ import annotations

from hashlib import sha256
import hmac
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from admin_store import backend_headers
from tenant_store import canonical_uuid

_MAX_FILE = 80 * 1024 * 1024
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


class SocialVideoDownloadDenied(ValueError):
    """Only a sanitized code; no URL, media path, credentials or response body."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _origin(value):
    try:
        if not isinstance(value, str) or value != value.strip():
            raise ValueError()
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.hostname
                or not parsed.hostname.endswith(".supabase.co")
                or parsed.port not in (None, 443)
                or parsed.path not in ("", "/") or parsed.query
                or parsed.fragment or parsed.username or parsed.password):
            raise ValueError()
        return value.rstrip("/")
    except ValueError:
        raise SocialVideoDownloadDenied("VIDEO_ORIGIN_INVALID") from None


def _render_object(shop_id, object_path):
    try:
        sid = canonical_uuid(shop_id)
        if not isinstance(object_path, str) or len(object_path) > 400:
            raise ValueError()
        # The Part 1 backend creates <shop>/renders/<render-job>.mp4
        # or <shop>/renders/<render-job>/<lease-token>.mp4.
        if not re.fullmatch(
            re.escape(sid) + r"/renders/" + _UUID + r"(?:/" + _UUID + r")?\.mp4",
            object_path,
        ):
            raise ValueError()
        return quote(object_path, safe="/")
    except (TypeError, ValueError):
        raise SocialVideoDownloadDenied("VIDEO_PATH_INVALID") from None


class SocialPrivateRenderReader:
    """Read-only bounded service-role downloader with no redirects or upserts."""

    def __init__(self, origin, service_role_key, *, transport=None):
        self.origin = _origin(origin)
        if not isinstance(service_role_key, str) or not service_role_key:
            raise SocialVideoDownloadDenied("VIDEO_SERVICE_CREDENTIAL_MISSING")
        self._headers = backend_headers(service_role_key)
        self._opener = transport or build_opener(_NoRedirect()).open

    def download(self, *, shop_id, object_path, destination, private_root,
                 expected_sha256):
        if not isinstance(expected_sha256, str) or not _SHA.fullmatch(expected_sha256):
            raise SocialVideoDownloadDenied("VIDEO_DIGEST_REQUIRED")
        encoded = _render_object(shop_id, object_path)
        target = Path(destination)
        try:
            root = Path(private_root).resolve(strict=True)
            parent = target.parent.resolve(strict=True)
            if (parent != root and root not in parent.parents) or target.is_symlink():
                raise SocialVideoDownloadDenied("VIDEO_SCRATCH_PATH_INVALID")
            if not root.is_dir() or not parent.is_dir():
                raise SocialVideoDownloadDenied("VIDEO_SCRATCH_PATH_INVALID")
        except (OSError, RuntimeError):
            raise SocialVideoDownloadDenied("VIDEO_SCRATCH_PATH_INVALID") from None

        url = self.origin + "/storage/v1/object/retailgrowth-media/" + encoded
        req = Request(url, method="GET", headers={
            **self._headers, "Accept-Encoding": "identity"})
        created = False
        count = 0
        digest = sha256()
        try:
            with self._opener(req, timeout=45) as response:
                if (response.status != 200 or response.geturl() != req.full_url
                        or response.headers.get("Content-Encoding", "identity") != "identity"):
                    raise SocialVideoDownloadDenied("VIDEO_PRIVATE_FETCH_REJECTED")
                # Exclusive create, restrictive permissions: never follow a
                # pre-existing symlink or overwrite any previous scratch file.
                fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                created = True
                with os.fdopen(fd, "wb") as dest:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        if not isinstance(chunk, bytes):
                            raise SocialVideoDownloadDenied("VIDEO_PRIVATE_FETCH_REJECTED")
                        count += len(chunk)
                        if count > _MAX_FILE:
                            raise SocialVideoDownloadDenied("VIDEO_MEDIA_TOO_LARGE")
                        digest.update(chunk)
                        dest.write(chunk)
            if count == 0 or not hmac.compare_digest(digest.hexdigest(), expected_sha256):
                raise SocialVideoDownloadDenied("VIDEO_DIGEST_MISMATCH")
            return {"source_sha256": digest.hexdigest(),
                    "size_bytes": count, "path": target}
        except SocialVideoDownloadDenied:
            raise
        except (HTTPError, URLError, OSError, ValueError, TypeError):
            raise SocialVideoDownloadDenied("VIDEO_PRIVATE_FETCH_UNAVAILABLE") from None
        finally:
            if created and (count == 0 or not hmac.compare_digest(
                    digest.hexdigest(), expected_sha256)):
                target.unlink(missing_ok=True)
