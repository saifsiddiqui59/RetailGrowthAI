"""Fail-closed internal Wan output importer (source only; no live trigger).

Do not call this until the provider task succeeded AND the premium DB attempt
token is still current. The resulting object is private and must be registered
by a reviewed premium-specific CAS completion RPC before any user download.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

MAX_VIDEO_BYTES = 80 * 1024 * 1024
MAX_SECONDS = 30


class PremiumImportRejected(RuntimeError):
    """Sanitized import failure (no provider URL, query token or tenant data)."""


class _ForbidRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PremiumImportRejected("Provider redirect not allowed")


def _validated_provider_url(source: str, allowed_hosts: tuple[str, ...]):
    if not allowed_hosts:
        raise PremiumImportRejected("No approved provider download hosts")
    if not isinstance(source, str) or len(source) > 4096:
        raise PremiumImportRejected("Provider result URL invalid")
    parts = urlsplit(source)
    if (parts.scheme != "https" or not parts.hostname or parts.username
        or parts.password or parts.port or parts.fragment
        or parts.hostname.lower() not in allowed_hosts
        or any(not re.fullmatch(r"[a-z0-9.-]{1,253}", host)
               for host in allowed_hosts)
        or not parts.path or ".." in parts.path or "%2f" in parts.path.lower()):
        raise PremiumImportRejected("Provider output origin not approved")
    return source


def _bounded_fetch(url: str):
    """One HTTPS request; redirects disabled to avoid cross-host SSRF."""
    request = Request(url, headers={"Accept": "video/mp4"}, method="GET")
    try:
        with build_opener(_ForbidRedirect()).open(request, timeout=30) as response:
            if response.status != 200:
                raise PremiumImportRejected("Provider download refused")
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if mime not in ("video/mp4", "application/octet-stream"):
                raise PremiumImportRejected("Provider result has wrong content type")
            blob = response.read(MAX_VIDEO_BYTES + 1)
    except PremiumImportRejected:
        raise
    except (OSError, ValueError) as exc:
        raise PremiumImportRejected("Provider video fetch unavailable") from exc
    if not blob or len(blob) > MAX_VIDEO_BYTES:
        raise PremiumImportRejected("Provider video exceeds private output limit")
    return blob


def _probe_mp4(path: Path):
    """OS ffprobe is used for a real downloaded file, never accepts shell text."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams",
             "-of", "json", str(path)],
            capture_output=True, text=True, check=True, timeout=20,
        )
        if len(result.stdout) > 200_000:
            raise PremiumImportRejected("Unexpected ffprobe output")
        return json.loads(result.stdout)
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        raise PremiumImportRejected("Generated MP4 failed validation") from exc


def _check_video(info: dict):
    try:
        streams = info["streams"]
        videos = [s for s in streams if s.get("codec_type") == "video"]
        if len(videos) != 1 or videos[0]["codec_name"] != "h264":
            raise ValueError("Video must be a single H264 stream")
        width, height = int(videos[0]["width"]), int(videos[0]["height"])
        duration = float(info["format"]["duration"])
        if not 0.5 <= duration <= MAX_SECONDS + 0.5:
            raise ValueError("Invalid output duration")
        if not (240 <= width <= 4096 and 240 <= height <= 4096):
            raise ValueError("Invalid output video dimensions")
        if any(s.get("codec_type") not in ("video", "audio")
               for s in streams):
            raise ValueError("Unsupported attachment streams")
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise PremiumImportRejected("Generated MP4 metadata invalid") from exc
    return {"duration_seconds": duration, "width": width, "height": height,
            "codec": "h264"}


def import_premium_video(*, shop_id, job_id, lease_token,
                         source_url, allowed_hosts, private_media,
                         fetch=_bounded_fetch, probe=_probe_mp4):
    """Import one allowed result. No DB status mutations or public link here.

    `allowed_hosts` must come from reviewed server environment, NEVER request
    payload. Lease and shop are validated by PrivateMedia.upload and separately
    in premium DB CAS before success. Do not call in customer HTTP request.
    """
    safe_url = _validated_provider_url(source_url, tuple(allowed_hosts))
    try:
        data = fetch(safe_url)
    except PremiumImportRejected:
        raise
    except Exception as exc:
        raise PremiumImportRejected("Provider fetch failed") from exc
    if not isinstance(data, bytes) or not 100 <= len(data) <= MAX_VIDEO_BYTES:
        raise PremiumImportRejected("Provider output has invalid length")
    # MP4 ftyp box must start at byte offset 4 for standard progressive MP4.
    if data[4:8] != b"ftyp":
        raise PremiumImportRejected("Provider output is not an MP4")
    with TemporaryDirectory(prefix="rgai-premium-") as scratch:
        dest = Path(scratch) / "provider.mp4"
        dest.write_bytes(data)
        metadata = _check_video(probe(dest))
        try:
            key = private_media.upload(shop_id, job_id, dest, lease_token=lease_token)
        except Exception as exc:
            raise PremiumImportRejected("Private media upload failed") from exc
    if not isinstance(key, str) or not key.startswith(shop_id + "/"):
        raise PremiumImportRejected("Private media upload identity mismatch")
    return {"object_path": key, "media": metadata}
