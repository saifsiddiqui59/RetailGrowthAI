"""Server-only private Supabase WAV writer for VoiceStudio Feature2 jobs.

The caller must provide an authoritative, one-shot database claim and current
signed membership. This module performs no Auth or billing decisions, never
produces public URLs, and never retries an uncertain Storage acknowledgement.
"""
from __future__ import annotations

from hashlib import sha256
import io
import re
import struct
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from uuid import UUID
import wave

from admin_store import backend_headers

BUCKET = "retailgrowth-media"
MAX_WAV = 8 * 1024 * 1024
_HASH = re.compile(r"^[0-9a-f]{64}$")


class PrivateVoiceStorageDenied(ValueError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PrivateVoiceStorageDenied("Private voice storage redirect denied")


def _uuid(value):
    try:
        return type(value) is str and str(UUID(value)) == value and UUID(value).version == 4
    except (TypeError, ValueError, AttributeError):
        return False


def _wav(data):
    if type(data) is not bytes or not 44 <= len(data) <= MAX_WAV:
        raise PrivateVoiceStorageDenied("Invalid bounded private WAV")
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise PrivateVoiceStorageDenied("Invalid PCM WAVE header")
    # Deny hidden chunks, trailing data, and impossible frame geometry even
    # when a WAV decoder could ignore extra content after the RIFF envelope.
    if struct.unpack_from("<I", data, 4)[0] != len(data) - 8:
        raise PrivateVoiceStorageDenied("RIFF byte length does not match object")
    cursor = 12
    chunks = []
    while cursor < len(data):
        if len(data) - cursor < 8:
            raise PrivateVoiceStorageDenied("Truncated WAV chunk header")
        kind = data[cursor:cursor + 4]
        length = struct.unpack_from("<I", data, cursor + 4)[0]
        end = cursor + 8 + length
        padded_end = end + (length & 1)
        if end > len(data) or padded_end > len(data):
            raise PrivateVoiceStorageDenied("WAV chunk exceeds RIFF envelope")
        if length & 1 and data[end] != 0:
            raise PrivateVoiceStorageDenied("Nonzero WAV chunk padding")
        chunks.append((kind, length))
        cursor = padded_end
    if (cursor != len(data) or len(chunks) != 2 or chunks[0][0] != b"fmt "
            or chunks[1][0] != b"data" or chunks[0][1] not in (16, 18)):
        raise PrivateVoiceStorageDenied("Noncanonical private PCM WAV chunks")
    if struct.unpack_from("<H", data, 20)[0] != 1:
        raise PrivateVoiceStorageDenied("Only PCM private WAV accepted")
    if chunks[0][1] == 18 and struct.unpack_from("<H", data, 36)[0] != 0:
        raise PrivateVoiceStorageDenied("Unexpected PCM format extension")
    channels, rate, byte_rate, block_align, bits = struct.unpack_from("<HIIHH", data, 22)
    if (channels not in (1, 2) or bits != 16 or not 8000 <= rate <= 96000
            or block_align != channels * (bits // 8)
            or byte_rate != rate * block_align
            or chunks[1][1] == 0 or chunks[1][1] % block_align
            or chunks[1][1] // block_align > rate * 60):
        raise PrivateVoiceStorageDenied("Inconsistent private PCM frame geometry")
    try:
        with wave.open(io.BytesIO(data), "rb") as stream:
            channels, width, rate, frames = (stream.getnchannels(),
                                            stream.getsampwidth(),
                                            stream.getframerate(),
                                            stream.getnframes())
            if stream.getcomptype() != "NONE" or channels not in (1, 2) or width != 2 or not 8000 <= rate <= 96000 or not frames or frames / rate > 60:
                raise PrivateVoiceStorageDenied("Invalid private VoiceStudio audio profile")
            if len(stream.readframes(frames)) != frames * channels * width:
                raise PrivateVoiceStorageDenied("Truncated private VoiceStudio WAV")
    except (EOFError, wave.Error) as exc:
        raise PrivateVoiceStorageDenied("Malformed VoiceStudio WAV") from exc


class VoiceStudioPrivateStorage:
    """Private, no-upsert writer. Not an authenticated public API."""

    def __init__(self, origin, service_role_key, *, transport=None):
        try:
            parsed = urlsplit(origin)
            valid_origin = (type(origin) is str and parsed.scheme == "https"
                            and parsed.hostname is not None
                            and parsed.username is None and parsed.password is None
                            and parsed.path in ("", "/") and not parsed.query
                            and not parsed.fragment and parsed.port in (None, 443))
        except (ValueError, TypeError):
            valid_origin = False
        if not valid_origin:
            raise PrivateVoiceStorageDenied("Trusted Supabase HTTPS origin required")
        self.origin = origin.rstrip("/")
        self.headers = backend_headers(service_role_key)
        self.send = transport or build_opener(_NoRedirect()).open

    @staticmethod
    def paths(shop_id, campaign_id, request_id):
        if not all(_uuid(x) for x in (shop_id, campaign_id, request_id)):
            raise PrivateVoiceStorageDenied("Canonical v4 private job IDs required")
        parent = f"{shop_id}/voicestudio/{campaign_id}/{request_id}"
        return parent + "/original.wav", parent + "/render.wav"

    def _put(self, path, data):
        url = self.origin + "/storage/v1/object/" + BUCKET + "/" + quote(path, safe="/")
        req = Request(url, data=data, method="POST", headers={
            **self.headers, "Content-Type": "audio/wav", "x-upsert": "false",
        })
        try:
            with self.send(req, timeout=30) as response:
                if not 200 <= response.status < 300 or response.geturl() != url:
                    raise PrivateVoiceStorageDenied("Private WAV save not confirmed")
        except (HTTPError, URLError, OSError, TimeoutError):
            raise PrivateVoiceStorageDenied("Private WAV write failed or is uncertain") from None

    def _get_verified(self, path, expected_sha):
        """Read a known object with a trusted SHA. Never accept a raw browser path.

        The only public-facing callers must recheck current tenant membership,
        audio review/rights and claim state before and after this operation.
        """
        if type(expected_sha) is not str or not _HASH.fullmatch(expected_sha):
            raise PrivateVoiceStorageDenied("Original private digest required")
        url = self.origin + "/storage/v1/object/" + BUCKET + "/" + quote(path, safe="/")
        req = Request(url, method="GET", headers=self.headers)
        try:
            with self.send(req, timeout=30) as response:
                if response.status != 200 or response.geturl() != url:
                    raise PrivateVoiceStorageDenied("Private WAV readback not authorized")
                content = response.read(MAX_WAV + 1)
        except (HTTPError, URLError, OSError, TimeoutError):
            raise PrivateVoiceStorageDenied("Private WAV readback unavailable or uncertain") from None
        _wav(content)
        if sha256(content).hexdigest() != expected_sha:
            raise PrivateVoiceStorageDenied("Private WAV byte digest changed after upload")
        return content

    def _read_and_verify(self, path, expected_sha):
        # Used by the original-key SQL registration gate. No media returned.
        return len(self._get_verified(path, expected_sha))

    def read_verified_original(self, shop_id, campaign_id, request_id, original_sha):
        """Worker-only source for a tenant-authorized human audio review.

        Caller must obtain the current SQL review receipt and recheck RLS
        before/after I/O. The private original is never a signed public link.
        """
        original_path, _ = self.paths(shop_id, campaign_id, request_id)
        return self._get_verified(original_path, original_sha)

    def read_verified_render(self, shop_id, campaign_id, request_id, render_sha):
        """Worker-only Feature4 PCM source; approval must be checked elsewhere."""
        _, render_path = self.paths(shop_id, campaign_id, request_id)
        return self._get_verified(render_path, render_sha)

    def verify_pair(self, shop_id, campaign_id, request_id, original_sha, render_sha):
        """Verify both current private bytes before separately registered SQL receipt.

        Does not create a public signed URL, grant review or mark a job complete.
        """
        original_path, render_path = self.paths(shop_id, campaign_id, request_id)
        original_size = self._read_and_verify(original_path, original_sha)
        render_size = self._read_and_verify(render_path, render_sha)
        return {"status": "PRIVATE_WAV_READBACK_VERIFIED_NOT_REGISTERED",
                "shop_id": shop_id, "campaign_id": campaign_id,
                "request_id": request_id,
                "original_sha256": original_sha, "render_sha256": render_sha,
                "original_bytes": original_size, "render_bytes": render_size,
                "sql_original_key_claim_and_registration_still_required": True,
                "publish_approved": False}

    def write_private_audio(self, shop_id, campaign_id, request_id,
                            original, render_wav, original_sha, render_sha, claim):
        """One attempt per object; require a unique SQL claim first.

        A partial two-object write is a pending reconciliation case, NOT success.
        No retries or automatic cleanup of a potentially acknowledged object.
        """
        original_path, render_path = self.paths(shop_id, campaign_id, request_id)
        if (type(claim) is not dict or claim.get("status") != "CLAIMED_ONCE"
                or any(claim.get(k) != value for k, value in (
                    ("shop_id", shop_id), ("campaign_id", campaign_id),
                    ("request_id", request_id)))
                or not isinstance(original_sha, str) or not _HASH.fullmatch(original_sha)
                or not isinstance(render_sha, str) or not _HASH.fullmatch(render_sha)
                or type(original) is not bytes or type(render_wav) is not bytes
                or sha256(original).hexdigest() != original_sha
                or sha256(render_wav).hexdigest() != render_sha):
            raise PrivateVoiceStorageDenied("Unverified voice claim or media digests")
        _wav(original)
        _wav(render_wav)
        self._put(original_path, original)
        self._put(render_path, render_wav)
        return {"status": "PRIVATE_WAV_BYTES_WRITTEN_NOT_REGISTERED",
                "shop_id": shop_id, "campaign_id": campaign_id,
                "request_id": request_id,
                "original_object_key": original_path,
                "render_object_key": render_path,
                "original_sha256": original_sha, "render_sha256": render_sha,
                "readback_and_sql_registration_required": True,
                "publish_approved": False}
