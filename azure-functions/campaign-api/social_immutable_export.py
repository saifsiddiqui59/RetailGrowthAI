"""Off-by-default, service-only copy-once media export for Instagram.

Not registered on HTTP/Azure queues and never publishes to a provider.
The injected DB authority MUST verify an active P2 external-send claim,
connected account scopes, quota, approved content/revision, reviewed rights,
and immutable source checksum. This module independently rehashes private
source bytes, creates a private service-owned export object with x-upsert=false,
reads it back, verifies digest equality, and signs only that exact object.
The signer token stays backend-only. An uncertain POST never retries blind.
"""
from __future__ import annotations

from hashlib import sha256
import hmac
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from admin_store import backend_headers
from social_providers import private_media_url, ProviderRejected
from tenant_store import canonical_uuid

_MAX_BYTES = 80 * 1024 * 1024
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_BUCKET = "retailgrowth-social-exports"


class ExportDenied(ValueError):
    """Safe fixed error only; never include signed URL, bytes or secrets."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _origin(value):
    try:
        if (not isinstance(value, str) or value != value.strip() or
                any(ord(c) <= 32 or ord(c) == 127 for c in value)):
            raise ValueError()
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.hostname or
                parsed.username or parsed.password or parsed.query or
                parsed.fragment or parsed.path not in ("", "/") or
                parsed.port not in (None, 443)):
            raise ValueError()
    except (TypeError, ValueError):
        raise ExportDenied("EXPORT_ORIGIN_INVALID") from None
    return value.rstrip("/")


def _uuid(value):
    try:
        return canonical_uuid(value)
    except (ValueError, TypeError, AttributeError):
        raise ExportDenied("EXPORT_ID_INVALID") from None


def _digest(value):
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        raise ExportDenied("EXPORT_DIGEST_REQUIRED")
    return value


def _private_bytes(source_path, private_root, expected):
    try:
        root = Path(private_root).resolve(strict=True)
        raw = Path(source_path)
        if raw.is_symlink():
            raise ExportDenied("EXPORT_SOURCE_PATH_INVALID")
        source = raw.resolve(strict=True)
        if source == root or root not in source.parents or not source.is_file():
            raise ExportDenied("EXPORT_SOURCE_PATH_INVALID")
        before = source.stat()
        if not 0 < before.st_size <= _MAX_BYTES:
            raise ExportDenied("EXPORT_SOURCE_SIZE_INVALID")
        data = source.read_bytes()
        after = source.stat()
        if (before.st_ino,before.st_dev,before.st_mtime_ns,before.st_size)!=(
                after.st_ino,after.st_dev,after.st_mtime_ns,after.st_size):
            raise ExportDenied("EXPORT_SOURCE_MUTATED")
        if not hmac.compare_digest(sha256(data).hexdigest(), expected):
            raise ExportDenied("EXPORT_SOURCE_HASH_MISMATCH")
        return data
    except ExportDenied:
        raise
    except (OSError, TypeError, ValueError):
        raise ExportDenied("EXPORT_SOURCE_UNAVAILABLE") from None


class ImmutableSocialExportWriter:
    def __init__(self, *, origin, service_key, claim_authority,
                 enabled=False, transport=None):
        if enabled is not True:
            raise ExportDenied("EXPORT_RELEASE_DISABLED")
        if claim_authority is None:
            raise ExportDenied("EXPORT_CLAIM_AUTHORITY_MISSING")
        self.origin = _origin(origin)
        try:
            self.headers = backend_headers(service_key)
        except (TypeError, ValueError):
            raise ExportDenied("EXPORT_BACKEND_KEY_INVALID") from None
        self.authority = claim_authority
        self.transport = transport or build_opener(_NoRedirect()).open

    def _request(self, url, *, method, data=None, headers=None, max_reply=8192):
        req = Request(url, data=data, method=method,
                      headers={**self.headers, **(headers or {})})
        try:
            with self.transport(req, timeout=45) as response:
                if (response.geturl() != url or response.status not in (200,201)):
                    raise ExportDenied("EXPORT_STORAGE_REJECTED")
                body = response.read(max_reply+1)
                if not isinstance(body, bytes) or len(body)>max_reply:
                    raise ExportDenied("EXPORT_STORAGE_REJECTED")
                return body
        except ExportDenied:
            raise
        except (HTTPError, URLError, OSError, TypeError, ValueError):
            raise ExportDenied("EXPORT_STORAGE_UNCERTAIN") from None

    def create_signed_export(self, *, shop_id, job_id, revision, source_sha256,
                             source_path, private_root, expires_seconds=7200):
        sid,jid = _uuid(shop_id),_uuid(job_id)
        sha = _digest(source_sha256)
        if (type(revision) is not int or not 1<=revision<=99999999 or
                type(expires_seconds) is not int or
                not 3600<=expires_seconds<=21600):
            raise ExportDenied("EXPORT_REQUEST_INVALID")
        if self.authority.allow_export(sid,jid,revision,sha) is not True:
            raise ExportDenied("EXPORT_CLAIM_DENIED")
        data = _private_bytes(source_path,private_root,sha)
        key = f"{sid}/video/{jid}/{revision}/{sha}.mp4"
        encoded = quote(key,safe="/")
        object_url = self.origin+f"/storage/v1/object/{_BUCKET}/"+encoded
        self._request(object_url,method="POST",data=data,max_reply=8192,
            headers={"Content-Type":"video/mp4","x-upsert":"false"})

        # A successful POST is not proof that the remote export retained the
        # right bytes. Check exact readback BEFORE issuing a signed URL.
        received = self._request(object_url,method="GET",max_reply=len(data))
        if len(received)!=len(data) or not hmac.compare_digest(
                sha256(received).hexdigest(),sha):
            raise ExportDenied("EXPORT_REMOTE_HASH_MISMATCH")
        if self.authority.allow_export(sid,jid,revision,sha) is not True:
            raise ExportDenied("EXPORT_CLAIM_REVOKED")
        sign_url = self.origin+f"/storage/v1/object/sign/{_BUCKET}/"+encoded
        raw = self._request(sign_url,method="POST",
              data=json.dumps({"expiresIn":expires_seconds}).encode("utf-8"),
              headers={"Content-Type":"application/json"},max_reply=8192)
        try:
            payload = json.loads(raw)
            relative = payload["signedURL"]
            expected = f"/object/sign/{_BUCKET}/"+encoded+"?"
            if (not isinstance(relative,str) or not relative.startswith(expected)
                    or len(relative)>3000):
                raise ValueError()
            signed = self.origin+"/storage/v1"+relative
            private_media_url(signed,self.origin)
        except (ValueError,KeyError,TypeError,ProviderRejected,UnicodeError):
            raise ExportDenied("EXPORT_SIGNED_URL_UNTRUSTED") from None
        # Not a provider publish receipt. Never return this to user/browser.
        return {"object_path":key,"source_sha256":sha,
                "signed_url":signed,"state":"IMMUTABLE_EXPORT_VERIFIED"}
