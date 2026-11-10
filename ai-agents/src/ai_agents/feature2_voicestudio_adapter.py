"""Minimal server-only adapter for the unmodified upstream VoiceStudio API.

VoiceStudio is deployed separately. This file does not bundle AGPL code,
download model weights, expose a browser route, or enable inference.
"""
from __future__ import annotations

import io
import json
import re
import wave
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

MAX_WAV_BYTES = 8 * 1024 * 1024
MAX_TEXT_CHARS = 3000
_TOKEN = re.compile(r"^[a-zA-Z0-9_.-]{1,64}$")


class VoiceStudioUnavailable(RuntimeError):
    """A denied or unavailable voice request; never includes credentials."""


def _speech_endpoint(base_url: str) -> str:
    try:
        parsed = urlsplit(base_url)
        hostname = parsed.hostname
        port = parsed.port
    except (TypeError, ValueError) as exc:
        raise VoiceStudioUnavailable("Invalid private VoiceStudio endpoint") from exc
    if (
        not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
        or port is None
        or not 1 <= port <= 65535
        or not (
            parsed.scheme == "https"
            or (parsed.scheme == "http" and hostname in ("127.0.0.1", "::1", "localhost"))
        )
    ):
        raise VoiceStudioUnavailable("VoiceStudio must use HTTPS or loopback with an explicit port")
    return base_url.rstrip("/") + "/v1/audio/speech"


def _validate_pcm_wav(data: bytes) -> None:
    if len(data) < 44 or not data.startswith(b"RIFF") or data[8:12] != b"WAVE":
        raise VoiceStudioUnavailable("VoiceStudio did not return a valid WAV")
    try:
        with wave.open(io.BytesIO(data), "rb") as stream:
            if (
                stream.getnchannels() not in (1, 2)
                or stream.getsampwidth() not in (1, 2, 3, 4)
                or not 8000 <= stream.getframerate() <= 96000
                or stream.getnframes() < 1
                or stream.getnframes() / stream.getframerate() > 180
            ):
                raise VoiceStudioUnavailable("VoiceStudio WAV exceeds audio policy")
    except (EOFError, wave.Error) as exc:
        raise VoiceStudioUnavailable("VoiceStudio returned malformed PCM WAV") from exc


def synthesize_voice_wav(
    *,
    text: str,
    base_url: str,
    api_key: str,
    voice: str,
    enabled: bool = False,
    commercial_model_verified: bool = False,
    transport=None,
) -> bytes:
    """Return one validated WAV, with no retry or persisted output.

    Backend caller must enforce live JWT/RLS, tenant media rights, licensed model,
    quota and one-shot job fencing BEFORE invoking this source-only adapter.
    A boolean here is not a legal licence, payment authorization or tenant check.
    """
    if not enabled or not commercial_model_verified:
        raise VoiceStudioUnavailable("VoiceStudio disabled pending verified commercial model approval")
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= MAX_TEXT_CHARS:
        raise VoiceStudioUnavailable("Invalid voiceover text")
    if not isinstance(voice, str) or not _TOKEN.fullmatch(voice):
        raise VoiceStudioUnavailable("Invalid server-selected voice")
    if not isinstance(api_key, str) or len(api_key) < 16:
        raise VoiceStudioUnavailable("Missing trusted VoiceStudio API credential")

    endpoint = _speech_endpoint(base_url)
    body = json.dumps({
        "model": "tts-1",
        "voice": voice,
        "input": text,
        "response_format": "wav",
    }).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    sender = transport if transport is not None else urlopen
    try:
        with sender(request, timeout=45) as response:
            blob = response.read(MAX_WAV_BYTES + 1)
    except (HTTPError, URLError, OSError, TimeoutError) as exc:
        raise VoiceStudioUnavailable("Private VoiceStudio speech request failed") from None

    if not isinstance(blob, bytes) or len(blob) > MAX_WAV_BYTES:
        raise VoiceStudioUnavailable("VoiceStudio audio response size denied")
    _validate_pcm_wav(blob)
    return blob
