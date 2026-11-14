"""VoiceStudio's existing OpenAI-compatible ASR API -> Feature7 word timing.

No new speech model. Calls upstream /v1/audio/transcriptions privately using
an already authorized WAV; caller owns current JWT/RLS, rights, model licensing,
job fencing and downstream HMAC signing. OFF by default, no automatic retries.
"""
from __future__ import annotations

from hashlib import sha256
import io
import json
import math
import re
import wave
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

MAX_WAV = 8 * 1024 * 1024
MAX_JSON = 512 * 1024
MAX_WAV_METADATA = 1024 * 1024
_SHA = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_LANGUAGES = frozenset(("en", "hi", "mr"))
# Direction overrides and isolates can visually spoof review/caption text.
_BIDI_CONTROLS = frozenset((0x061C, 0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A)))


def _unsafe_text(value):
    return any(ord(ch) < 32 or 0x7F <= ord(ch) <= 0x9F or 0xD800 <= ord(ch) <= 0xDFFF
               or ord(ch) in _BIDI_CONTROLS or ord(ch) in (0x2028, 0x2029, 0xFEFF)
               for ch in value)


class VoiceStudioTranscriptionDenied(ValueError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise VoiceStudioTranscriptionDenied("VoiceStudio ASR redirect denied")


def _endpoint(base_url):
    if (type(base_url) is not str or not base_url.isascii()
            or any(ord(ch) <= 32 or ord(ch) >= 127 or ord(ch) == 92 for ch in base_url)):
        raise VoiceStudioTranscriptionDenied("Trusted canonical ASR endpoint required")
    try:
        p = urlsplit(base_url)
        host, port = p.hostname, p.port
    except ValueError as exc:
        raise VoiceStudioTranscriptionDenied("Invalid ASR endpoint") from exc
    if (not host or port is None or not 1 <= port <= 65535
            or p.username or p.password or p.query or p.fragment
            or p.path not in ("", "/")
            or not (p.scheme == "https" or
                    (p.scheme == "http" and host in ("127.0.0.1", "localhost", "::1")))):
        raise VoiceStudioTranscriptionDenied("Only trusted private HTTPS or loopback ASR permitted")
    return base_url.rstrip("/") + "/v1/audio/transcriptions"


def _checked_wav(wav_bytes):
    if (type(wav_bytes) is not bytes or not 44 <= len(wav_bytes) <= MAX_WAV
            or wav_bytes[:4] != b"RIFF" or wav_bytes[8:12] != b"WAVE"):
        raise VoiceStudioTranscriptionDenied("Bounded original WAV required")
    # Reject trailing bytes and truncated RIFF declarations before invoking ASR.
    # The signed digest must identify exactly one canonical original WAV object.
    if int.from_bytes(wav_bytes[4:8], "little") + 8 != len(wav_bytes):
        raise VoiceStudioTranscriptionDenied("WAV RIFF length mismatch")
    # Python's wave decoder can ignore trailing RIFF chunks. The downstream
    # signed-media gate forbids them, so reject before sending private bytes
    # to VoiceStudio as well. Do not interpret a second fmt/data as audio.
    offset = 12
    seen_fmt = seen_data = False
    pcm_block_align = None
    chunks = 0
    metadata_bytes = 0
    while offset + 8 <= len(wav_bytes):
        chunks += 1
        if chunks > 128 or seen_data:
            raise VoiceStudioTranscriptionDenied("Ambiguous WAV chunk layout")
        ident = wav_bytes[offset:offset + 4]
        if any(c < 32 or c > 126 for c in ident):
            raise VoiceStudioTranscriptionDenied("Invalid WAV chunk identifier")
        length = int.from_bytes(wav_bytes[offset + 4:offset + 8], "little")
        end = offset + 8 + length
        if end > len(wav_bytes) or (length % 2 and
                                    (end >= len(wav_bytes) or wav_bytes[end] != 0)):
            raise VoiceStudioTranscriptionDenied("Invalid WAV chunk boundary")
        if ident != b"data":
            metadata_bytes += 8 + length + length % 2
            if metadata_bytes > MAX_WAV_METADATA:
                raise VoiceStudioTranscriptionDenied("WAV metadata exceeds limit")
        if ident == b"fmt ":
            if seen_fmt or seen_data:
                raise VoiceStudioTranscriptionDenied("Duplicate WAV format")
            # Match the trusted signed-media PCM gate exactly: Python's wave
            # decoder does not validate every declared byte-rate/alignment field.
            # A digest of inconsistent fmt bytes must never reach private ASR.
            if length not in (16, 18) or (length == 18 and wav_bytes[offset + 24:offset + 26] != bytes(2)):
                raise VoiceStudioTranscriptionDenied("Unsupported PCM format metadata")
            fmt = wav_bytes[offset + 8:offset + 24]
            codec = int.from_bytes(fmt[0:2], "little")
            channels = int.from_bytes(fmt[2:4], "little")
            rate = int.from_bytes(fmt[4:8], "little")
            byte_rate = int.from_bytes(fmt[8:12], "little")
            block_align = int.from_bytes(fmt[12:14], "little")
            bits = int.from_bytes(fmt[14:16], "little")
            if (codec != 1 or channels not in (1, 2) or not 8000 <= rate <= 48000
                    or bits != 16 or block_align != channels * 2
                    or byte_rate != rate * block_align):
                raise VoiceStudioTranscriptionDenied("Inconsistent original PCM format")
            pcm_block_align = block_align
            seen_fmt = True
        elif ident == b"data":
            if not seen_fmt or length == 0 or length % pcm_block_align:
                raise VoiceStudioTranscriptionDenied("Missing WAV format or samples")
            seen_data = True
        offset = end + length % 2
    if offset != len(wav_bytes) or not seen_fmt or not seen_data:
        raise VoiceStudioTranscriptionDenied("Incomplete WAV chunk layout")
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as stream:
            rate, frames = stream.getframerate(), stream.getnframes()
            # Validate the sample rate before dividing; malformed WAV headers
            # must fail closed with the domain exception, not ZeroDivisionError.
            if (not 8000 <= rate <= 96000 or not 0 < frames / rate <= 180
                    or stream.getnchannels() not in (1, 2)
                    or stream.getsampwidth() != 2 or stream.getcomptype() != "NONE"):
                raise VoiceStudioTranscriptionDenied("Unapproved WAV codec/duration")
            if len(stream.readframes(frames)) != frames * stream.getnchannels() * 2:
                raise VoiceStudioTranscriptionDenied("Truncated original WAV")
            return frames / rate
    except (EOFError, wave.Error) as exc:
        raise VoiceStudioTranscriptionDenied("Unparseable original WAV") from exc


def _body(audio, language, boundary):
    fields = [
        ("model", "whisper-1"),
        ("response_format", "verbose_json"),
        ("timestamp_granularities[]", "word"),
    ]
    if language:
        fields.append(("language", language))
    result = bytearray()
    for name, value in fields:
        result.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode("ascii"))
    result.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"private.wav\"\r\nContent-Type: audio/wav\r\n\r\n".encode("ascii"))
    result.extend(audio)
    result.extend(f"\r\n--{boundary}--\r\n".encode("ascii"))
    return bytes(result)


def transcribe_private_voice(
    *, original_wav, source_sha256, base_url, api_key,
    language=None, enabled=False, commercial_model_verified=False,
    transport=None,
):
    """Return unsignable *review-only* words, not an approved F7 transcript."""
    if enabled is not True or commercial_model_verified is not True:
        raise VoiceStudioTranscriptionDenied("VoiceStudio ASR model not enabled/verified")
    if language is not None and (type(language) is not str or language not in _ALLOWED_LANGUAGES):
        raise VoiceStudioTranscriptionDenied("Unsupported ASR locale")
    if (type(api_key) is not str or not 16 <= len(api_key) <= 4096
            or not api_key.isascii() or any(ord(ch) <= 32 or ord(ch) >= 127 for ch in api_key)):
        raise VoiceStudioTranscriptionDenied("Private ASR credential required")
    if type(source_sha256) is not str or not _SHA.fullmatch(source_sha256):
        raise VoiceStudioTranscriptionDenied("Trusted original audio digest required")
    seconds = _checked_wav(original_wav)
    if sha256(original_wav).hexdigest() != source_sha256:
        raise VoiceStudioTranscriptionDenied("Original audio digest does not match trusted source")
    endpoint = _endpoint(base_url)
    # The body cannot be influenced by an untrusted filename/path/model id.
    boundary = "RetailGrowthASRWavBoundary"
    req = Request(endpoint, method="POST", data=_body(original_wav, language, boundary), headers={
        "Authorization": "Bearer " + api_key,
        "Content-Type": "multipart/form-data; boundary=" + boundary,
        "Accept": "application/json",
    })
    sender = transport or build_opener(_NoRedirect()).open
    try:
        with sender(req, timeout=60) as response:
            if (response.status != 200 or response.geturl() != endpoint or
                    response.headers.get("Content-Type", "").split(";", 1)[0].lower() != "application/json"):
                raise VoiceStudioTranscriptionDenied("Untrusted ASR response")
            raw = response.read(MAX_JSON + 1)
    except (HTTPError, URLError, OSError, TimeoutError):
        raise VoiceStudioTranscriptionDenied("Private VoiceStudio ASR request failed") from None
    # A private transport must return bounded wire bytes, never a decoded or
    # attacker-supplied Python object that bypasses the HTTP JSON byte contract.
    if type(raw) is not bytes:
        raise VoiceStudioTranscriptionDenied("ASR response must be raw JSON bytes")
    if len(raw) > MAX_JSON:
        raise VoiceStudioTranscriptionDenied("ASR response exceeds limit")
    # Reject ambiguous JSON keys at every depth. Different JSON consumers may
    # choose first/last values for duplicate timing, word or tenant fields.
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise VoiceStudioTranscriptionDenied("Duplicate ASR JSON field")
            result[key] = value
        return result
    try:
        parsed = json.loads(raw, object_pairs_hook=unique_object,
                            parse_constant=lambda value: (_ for _ in ()).throw(
                                VoiceStudioTranscriptionDenied("Non-finite ASR JSON number")))
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise VoiceStudioTranscriptionDenied("Malformed ASR result") from exc
    if type(parsed) is not dict or parsed.get("task") != "transcribe":
        raise VoiceStudioTranscriptionDenied("Incorrect ASR response type")
    words = parsed.get("words")
    if not isinstance(words, list) or not 1 <= len(words) <= 2000:
        raise VoiceStudioTranscriptionDenied("Real word timestamps required")
    validated = []
    previous_end = 0.0
    for item in words:
        if type(item) is not dict:
            raise VoiceStudioTranscriptionDenied("Invalid ASR word item")
        start, end, word = item.get("start"), item.get("end"), item.get("word")
        if (type(start) not in (int, float) or type(end) not in (int, float)
                or not math.isfinite(start) or not math.isfinite(end)
                or start < previous_end - .01 or start < 0 or end <= start
                or end > seconds + .1 or not isinstance(word, str)
                or not 1 <= len(word.strip()) <= 120
                or _unsafe_text(word)):
            raise VoiceStudioTranscriptionDenied("ASR words are unaligned or invalid")
        # Validate the canonical millisecond clock used by signed receipts:
        # sub-ms words may collapse or overlap after upstream float checks.
        canonical_start, canonical_end = round(start, 3), round(end, 3)
        if (canonical_end <= canonical_start or
                (validated and canonical_start < validated[-1]["end"])):
            raise VoiceStudioTranscriptionDenied("ASR timestamps collapse after canonicalization")
        validated.append({"start": canonical_start, "end": canonical_end,
                          "word": word.strip()})
        previous_end = end
    transcript = parsed.get("text")
    if (type(transcript) is not str or not transcript.strip() or len(transcript) > 12000
            or _unsafe_text(transcript)):
        raise VoiceStudioTranscriptionDenied("Missing ASR transcript text")
    reported_language = parsed.get("language")
    if type(reported_language) is not str or reported_language not in _ALLOWED_LANGUAGES:
        raise VoiceStudioTranscriptionDenied("Invalid ASR language report")
    if language and reported_language != language:
        raise VoiceStudioTranscriptionDenied("Unexpected transcription language")
    return {
        "schema": "retailgrowth.feature7-voicestudio-asr-review.v1",
        "audio_sha256": source_sha256,
        "language": reported_language,
        "words": validated,
        "text": transcript.strip(),
        "word_timings_present": True,
        "model_revision_verified_by_worker": False,
        "approved": False,
        "renderable": False,
        "requires_original_private_audio_and_current_tenant_recheck": True,
        "requires_feature7_signed_evidence": True,
    }
