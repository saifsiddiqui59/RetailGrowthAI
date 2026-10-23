"""Fail-closed worker-only Wan output importer, OFF in production.

Provider URL never goes to a customer. Follow NO redirects. Validate media
before uploading to existing private RetailGrowthAI tenant storage. The
caller must already hold a DB-fenced valid premium task and cost reservation.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, build_opener, HTTPRedirectHandler

from tenant_store import canonical_uuid, StorageUnavailable

MAX_BYTES = 80 * 1024 * 1024
# Reviewed examples in Alibaba Model Studio Wan API docs (Singapore/Beijing).
HOST_PATTERN = re.compile(
    r"^dashscope-(?:result-)?[a-z0-9-]{1,30}\.oss-(?:accelerate|[a-z0-9-]{2,35})\.aliyuncs\.com$"
)


class PremiumImportError(RuntimeError):
    """Sanitized; never logs third-party signed URLs or tenant prompt data."""


def validate_vendor_video_url(url):
    if not isinstance(url, str) or len(url) > 2048:
        raise PremiumImportError("Invalid private provider media reference")
    try:
        parsed = urlparse(url)
        valid = (parsed.scheme == "https" and bool(parsed.hostname) and
                 HOST_PATTERN.fullmatch(parsed.hostname) is not None and
                 parsed.port in (None, 443) and
                 not parsed.username and not parsed.password and
                 not parsed.fragment and parsed.path.lower().endswith(".mp4") and
                 len(parsed.path) <= 500 and
                 not any(x in parsed.path.lower() for x in ("%2f", "%5c", "..")) and
                 bool(parse_qs(parsed.query).get("Expires") or
                      parse_qs(parsed.query).get("expires")))
    except ValueError:
        valid = False
    if not valid:
        raise PremiumImportError("Untrusted provider media origin")
    return url


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never follow a signed URL to a private IP, local metadata server or
        # unreviewed secondary host, even if Alibaba changes its CDN.
        return None


def fetch_signed_video(url, output, *, opener=None):
    validate_vendor_video_url(url)
    opener = opener or build_opener(NoRedirect())
    req = Request(url, headers={"Accept": "video/mp4,application/octet-stream"},
                  method="GET")
    try:
        with opener.open(req, timeout=60) as response:
            if response.status != 200:
                raise PremiumImportError("Provider download unavailable")
            content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            if content_type not in ("video/mp4", "application/octet-stream", ""):
                raise PremiumImportError("Unexpected provider content type")
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isdigit() or int(length) > MAX_BYTES):
                raise PremiumImportError("Provider video exceeds media limit")
            total = 0
            with open(output, "wb") as file:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise PremiumImportError("Provider video exceeds media limit")
                    file.write(chunk)
    except (HTTPError, URLError, OSError) as exc:
        raise PremiumImportError("Provider download failed") from exc
    if total < 1024:
        raise PremiumImportError("Provider video is empty")
    with open(output, "rb") as file:
        if file.read(12)[4:8] != b"ftyp":
            raise PremiumImportError("Provider output is not MP4")
    return total


def probe_mp4(path):
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams",
             "-of", "json", str(path)], capture_output=True, text=True,
            timeout=30, check=True
        )
        return json.loads(proc.stdout)
    except (OSError, ValueError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        raise PremiumImportError("Provider output could not be verified") from exc


def verify_video(metadata, *, expected_seconds):
    try:
        seconds = float(metadata["format"]["duration"])
        streams = metadata["streams"]
        video = [s for s in streams if s.get("codec_type") == "video"]
        if len(video) != 1 or video[0]["codec_name"] != "h264":
            raise ValueError("invalid video codec")
        width, height = int(video[0]["width"]), int(video[0]["height"])
        if not (240 <= width <= 1920 and 240 <= height <= 1920 and
                width % 2 == 0 and height % 2 == 0):
            raise ValueError("invalid video dimensions")
        if not (2 <= expected_seconds <= 15 and
                expected_seconds - 1.5 <= seconds <= expected_seconds + 1.5):
            raise ValueError("duration mismatch")
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise PremiumImportError("Provider media failed codec/duration validation") from exc


def import_to_private_storage(*, provider_url, shop_id, job_id, lease_token,
                              expected_seconds, media, store, opener=None,
                              probe=probe_mp4):
    """Import under existing private bucket; finalize only via DB-fenced CAS.

    The caller never supplies browser input here. A DB worker must map the
    claim's shop_id/job_id/lease_token to this invocation, and store.finalize
    must atomically check the current lease and persist output media metadata.
    """
    sid, jid, token = (canonical_uuid(x) for x in
                       (shop_id, job_id, lease_token))
    validate_vendor_video_url(provider_url)
    with tempfile.TemporaryDirectory(prefix="rgai-premium-") as directory:
        target = Path(directory) / "provider-clip.mp4"
        fetch_signed_video(provider_url, target, opener=opener)
        verify_video(probe(target), expected_seconds=expected_seconds)
        # PrivateMedia.upload disables overwriting old output and strictly
        # scopes to sid/renders/jid/token.mp4 in retailgrowth-media bucket.
        private_path = media.upload(sid, jid, target, lease_token=token)
        if not isinstance(private_path, str) or not private_path.startswith(
            sid + "/renders/" + jid + "/" + token
        ):
            raise PremiumImportError("Private media receipt mismatch")
        result = store.finalize(jid, sid, token, private_path)
        if not isinstance(result, dict) or result.get("status") != "SUCCEEDED":
            raise PremiumImportError("Lease-fenced private completion failed")
        output_id = canonical_uuid(result.get("output_asset_id"))
        return {"job_id": jid, "status": "SUCCEEDED",
                "output_asset_id": output_id}
