"""Worker-only private Supabase Storage I/O with tenant path and size limits."""
import json
import os
import stat
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from tenant_store import StorageUnavailable, canonical_uuid
from admin_store import backend_headers

MAX_INPUT = 25 * 1024 * 1024
MAX_OUTPUT = 80 * 1024 * 1024
BUCKET = "retailgrowth-media"


class PrivateMedia:
    def __init__(self, origin, service_role_key, transport=None):
        if not origin.startswith("https://") or not service_role_key:
            raise ValueError("private backend storage credentials required")
        self.origin = origin.rstrip("/")
        self.secret = service_role_key
        self.transport = transport or urlopen

    def _path(self, shop_id, key):
        sid = canonical_uuid(shop_id)
        if (not isinstance(key, str) or not key.startswith(sid + "/")
                or "\\" in key or ".." in key.split("/") or "//" in key):
            raise StorageUnavailable("storage path outside tenant")
        return quote(key, safe="/")

    def download(self, shop_id, key, destination):
        path = self._path(shop_id, key)
        req = Request(self.origin + "/storage/v1/object/" + BUCKET + "/" + path,
                      headers=backend_headers(self.secret))
        try:
            with self.transport(req, timeout=30) as response:
                data = response.read(MAX_INPUT + 1)
        except (HTTPError, URLError, OSError) as exc:
            raise StorageUnavailable("private media fetch failed") from exc
        if not data or len(data) > MAX_INPUT:
            raise StorageUnavailable("media exceeds input limit")
        target = Path(destination)
        target.write_bytes(data)
        return target

    def upload(self, shop_id, job_id, media_file, *, lease_token=None):
        sid, jid = canonical_uuid(shop_id), canonical_uuid(job_id)
        token = canonical_uuid(lease_token) if lease_token is not None else None
        key = sid + "/renders/" + jid + ("/" + token if token else "") + ".mp4"
        path = self._path(sid, key)
        media_file = Path(media_file)
        # Open one non-following descriptor and upload ONLY those captured bytes.
        # A native renderer can race the path after an initial Path.stat();
        # the old stat()->read_bytes() sequence could disclose swapped content
        # before a later upload checksum caught the race.
        try:
            fd = os.open(media_file, os.O_RDONLY |
                         getattr(os, "O_NOFOLLOW", 0) |
                         getattr(os, "O_NONBLOCK", 0))
            with os.fdopen(fd, "rb") as reader:
                before = os.fstat(reader.fileno())
                if (not stat.S_ISREG(before.st_mode) or
                        not 100 <= before.st_size <= MAX_OUTPUT):
                    raise StorageUnavailable("encoded media must be bounded regular file")
                data = reader.read(MAX_OUTPUT + 1)
                after = os.fstat(reader.fileno())
                current = os.lstat(media_file)
                identity = lambda s: (
                    s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
                if (not stat.S_ISREG(current.st_mode) or
                        len(data) != before.st_size or
                        identity(before) != identity(after) or
                        identity(after) != identity(current)):
                    raise StorageUnavailable("encoded media file changed during upload staging")
        except (OSError, ValueError) as exc:
            raise StorageUnavailable("unsafe encoded media source") from exc
        req = Request(
            self.origin + "/storage/v1/object/" + BUCKET + "/" + path,
            data=data, method="POST",
            headers={**backend_headers(self.secret),
                     "Content-Type": "video/mp4", "x-upsert": "false"},
        )
        try:
            with self.transport(req, timeout=60) as response:
                if not 200 <= response.status < 300:
                    raise StorageUnavailable("private media upload rejected")
        except HTTPError as exc:
            # A preexisting object is not proven to be our rendered output.
            raise StorageUnavailable("private output collision requires verification") from exc
        except (URLError, OSError) as exc:
            raise StorageUnavailable("private media upload unavailable") from exc
        return key


    def verify_uploaded_mp4(self, shop_id, key, expected_sha256):
        """Read back the private remote object before registering output SHA.

        A successful POST alone does not attest that cloud bytes match the
        verified local H264/AAC result. Never follow a privileged HTTP redirect.
        """
        import hashlib
        import re
        from admin_store import _DenyRedirects
        from urllib.request import build_opener
        if (not isinstance(expected_sha256, str) or
                re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None):
            raise StorageUnavailable("invalid private output checksum")
        path = self._path(shop_id, key)
        client = build_opener(_DenyRedirects()).open if self.transport is urlopen else self.transport
        request = Request(
            self.origin + "/storage/v1/object/" + BUCKET + "/" + path,
            headers=backend_headers(self.secret))
        digest = hashlib.sha256()
        total = 0
        try:
            with client(request, timeout=60) as response:
                if response.status != 200:
                    raise StorageUnavailable("private output readback rejected")
                while True:
                    block = response.read(min(1024 * 1024, MAX_OUTPUT + 1 - total))
                    if not block:
                        break
                    total += len(block)
                    if total > MAX_OUTPUT:
                        raise StorageUnavailable("private output readback exceeded limit")
                    digest.update(block)
        except (HTTPError, URLError, OSError) as exc:
            raise StorageUnavailable("private output readback unavailable") from exc
        if total < 1024 or digest.hexdigest() != expected_sha256:
            raise StorageUnavailable("uploaded private MP4 checksum mismatch")
        return True
