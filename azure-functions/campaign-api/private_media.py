"""Worker-only private Supabase Storage I/O with tenant path and size limits."""
import json
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
        if media_file.stat().st_size > MAX_OUTPUT or media_file.stat().st_size < 100:
            raise StorageUnavailable("encoded media exceeds output limit")
        req = Request(
            self.origin + "/storage/v1/object/" + BUCKET + "/" + path,
            data=media_file.read_bytes(), method="POST",
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
