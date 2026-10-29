"""Opt-in Azure Speech neural TTS for a trusted Feature2 approved script.

Source-only: no routes, Azure resource, quota or storage are provisioned here.
Caller MUST provide current signed OWNER/EDITOR + active subscription checks,
durable reserve/reconciliation, and a trusted private-storage writer. Neither
client selection nor an in-memory test callback confers production authority.
No retries after a potentially charged provider call; no public signed URL.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_UP
from hashlib import sha256
import io
import os
import re
import uuid
import wave
from urllib.request import Request, build_opener, HTTPRedirectHandler
from xml.sax.saxutils import escape

# Source: Microsoft official supported Speech TTS locales and neural voices.
# At deployment, check actual selected Speech resource's /voices/list; these
# published names are not proof of region-specific voice availability.
VOICES = (
    ("en-IN-NeerjaNeural", "en-IN", "English (India)", "Neerja", "Female"),
    ("en-IN-PrabhatNeural", "en-IN", "English (India)", "Prabhat", "Male"),
    ("hi-IN-SwaraNeural", "hi-IN", "Hindi", "Swara", "Female"),
    ("hi-IN-MadhurNeural", "hi-IN", "Hindi", "Madhur", "Male"),
    ("mr-IN-AarohiNeural", "mr-IN", "Marathi", "Aarohi", "Female"),
    ("mr-IN-ManoharNeural", "mr-IN", "Marathi", "Manohar", "Male"),
)
_VOICES = {v[0]: v for v in VOICES}
_RATES = {"normal": "+0%", "slow": "-10%", "fast": "+10%"}
_UUID = re.compile(r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_REGION = re.compile(r"^[a-z0-9]{2,30}$")
_MAX_WAV_BYTES = 6_000_000


class SpeechRejected(ValueError):
    """Invalid rights/voice/content, or uncertain/failed real provider call."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SpeechRejected("Azure Speech redirect not permitted")


def catalog():
    """Client-safe fixed voices, not a live Azure availability claim."""
    return [{"id": v[0], "locale": v[1], "language": v[2],
             "label": v[3], "gender": v[4], "preview_requires_explicit_consent": True}
            for v in VOICES]


def _text(value, label, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise SpeechRejected("Invalid " + label)
    if any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise SpeechRejected("Unsafe " + label)
    return value.strip()


def _plan(plan, *, shop_id, campaign_id):
    if (not isinstance(plan, dict) or
        not {"creative_direction_v1", "approval_record"}.issubset(plan) or
        set(plan) - {"creative_direction_v1", "approval_record", "motion_direction_v1"}):
        raise SpeechRejected("Trusted Feature2 creative source required")
    creative, review = plan["creative_direction_v1"], plan["approval_record"]
    if not isinstance(creative, dict) or not isinstance(review, dict):
        raise SpeechRejected("Missing trusted creative/review")
    if (not isinstance(shop_id, str) or not _UUID.fullmatch(shop_id) or
        not isinstance(campaign_id, str) or not _UUID.fullmatch(campaign_id) or
        creative.get("shop_id") != shop_id or creative.get("campaign_id") != campaign_id or
        creative.get("contract") != "creative_direction_v1" or
        creative.get("duration_seconds") not in (15, 30, 60) or
        type(creative.get("duration_seconds")) is not int or
        review.get("review_status") != "DRAFT" or
        review.get("approved") is not False or
        review.get("can_publish") is not False or
        review.get("can_run_paid_motion") is not False or
        not isinstance(review.get("plan_sha256"), str) or
        not _SHA.fullmatch(review["plan_sha256"])):
        raise SpeechRejected("Unreviewed or foreign Feature2 plan")
    script = _text(creative.get("voiceover_script"), "trusted voiceover script", 1800)
    if "<" in script or ">" in script:  # SSML instructions must not enter from copy.
        raise SpeechRejected("Script contains markup")
    return creative, review, script


def _money(value, *, maximum):
    try:
        amount = Decimal(str(value))
    except (TypeError, InvalidOperation) as exc:
        raise SpeechRejected("Unverified TTS price/cap") from exc
    if not amount.is_finite() or amount <= 0 or amount > Decimal(str(maximum)):
        raise SpeechRejected("Unverified TTS price/cap")
    return amount


def _wav(bytes_, max_seconds):
    if type(bytes_) is not bytes or not 100 <= len(bytes_) <= _MAX_WAV_BYTES:
        raise SpeechRejected("Untrusted Azure Speech audio bytes")
    try:
        with wave.open(io.BytesIO(bytes_), "rb") as reader:
            if (reader.getnchannels() != 1 or reader.getsampwidth() != 2 or
                reader.getframerate() != 24000 or reader.getcomptype() != "NONE" or
                reader.getnframes() <= 0):
                raise SpeechRejected("Unsupported Azure PCM speech format")
            seconds = reader.getnframes() / reader.getframerate()
            if seconds < 0.2 or seconds > max_seconds:
                raise SpeechRejected("Generated narration does not fit shot/reel")
            # Consume frames to catch truncated/malformed RIFF/WAVE data.
            if len(reader.readframes(reader.getnframes())) != reader.getnframes() * 2:
                raise SpeechRejected("Truncated PCM media")
    except (EOFError, OSError, ValueError, wave.Error) as exc:
        raise SpeechRejected("Invalid WAV container") from exc
    return round(seconds, 3)


def _azure_transport(url, headers, body):
    """No redirects, bounded HTTPS response; called once only after reserve."""
    request = Request(url, data=body, headers=headers, method="POST")
    with build_opener(_NoRedirect()).open(request, timeout=18) as response:
        if response.geturl() != url or response.status != 200:
            raise SpeechRejected("Speech provider did not return an approved response")
        if "audio" not in response.headers.get("Content-Type", "").lower():
            # Azure formats may use application/octet-stream; RIFF validation
            # is the real output check, so permit the official binary type.
            if "octet-stream" not in response.headers.get("Content-Type", "").lower():
                raise SpeechRejected("Unexpected Speech provider content type")
        return response.read(_MAX_WAV_BYTES + 1)


@dataclass(frozen=True)
class VoiceRequest:
    shop_id: str
    campaign_id: str
    voice_id: str
    language: str
    speed: str
    preview: bool
    user_confirmed_charge: bool
    idempotency_key: str


class AzureSpeechNarration:
    """Trusted orchestration only; no HTTP routes or automatic retries."""

    def __init__(self, *, region, api_key, usd_per_million_characters,
                 approved_max_cost_usd, authorize_current_editor,
                 read_authoritative_plan, reserve_once, write_private_original,
                 reconcile_reserved_cost, transport=None):
        if not isinstance(region, str) or not _REGION.fullmatch(region):
            raise SpeechRejected("Invalid Azure Speech region")
        if not isinstance(api_key, str) or len(api_key) < 12:
            raise SpeechRejected("Missing server-only Azure Speech key")
        for callback in (authorize_current_editor, read_authoritative_plan, reserve_once,
                         write_private_original, reconcile_reserved_cost):
            if not callable(callback):
                raise SpeechRejected("Trusted tenant billing/storage callbacks required")
        self.region = region
        self._api_key = api_key
        self._rate = _money(usd_per_million_characters, maximum="10000")
        self._cap = _money(approved_max_cost_usd, maximum="0.25")
        self._authorize = authorize_current_editor
        self._read_plan = read_authoritative_plan
        self._reserve = reserve_once
        self._write = write_private_original
        self._reconcile = reconcile_reserved_cost
        self._transport = transport or _azure_transport

    def synthesize(self, *, plan: dict, request: VoiceRequest) -> dict:
        if os.environ.get("RETAIL_FEATURE2_AZURE_SPEECH_ENABLED") != "true":
            raise SpeechRejected("Azure Speech voiceover disabled")
        if not isinstance(request, VoiceRequest):
            raise SpeechRejected("Trusted voice request required")
        creative, review, script = _plan(plan, shop_id=request.shop_id,
                                          campaign_id=request.campaign_id)
        selected = _VOICES.get(request.voice_id)
        if (not selected or request.language != selected[1] or
            request.speed not in _RATES or type(request.preview) is not bool or
            request.user_confirmed_charge is not True or
            type(request.idempotency_key) is not str or
            not _UUID.fullmatch(request.idempotency_key)):
            raise SpeechRejected("Voice selection or explicit approval invalid")
        if self._authorize(request.shop_id, request.campaign_id) is not True:
            raise SpeechRejected("Active signed editor and subscription required")
        if self._read_plan(request.shop_id, request.campaign_id) != plan:
            raise SpeechRejected("Current authoritative draft script or revision differs")
        # Preview is intentionally billable: never auto-play preview on dropdown.
        # Fixed-length excerpt comes only from the same source-locked script.
        spoken = script[:90].rsplit(" ", 1)[0] if request.preview and len(script) > 90 else script
        spoken = _text(spoken, "voiceover", 1800)
        if any(ord(c) < 32 and c not in "\n\t" for c in spoken):
            raise SpeechRejected("Invalid script")
        planned_limit = 9 if request.preview else creative["duration_seconds"]
        ssml = (
            '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            'xml:lang="' + selected[1] + '"><voice name="' + selected[0] +
            '"><prosody rate="' + _RATES[request.speed] + '">' +
            escape(spoken, {'"': '&quot;', "'": '&apos;'}) +
            '</prosody></voice></speak>'
        ).encode("utf-8")
        if len(ssml) > 6000:
            raise SpeechRejected("Speech request exceeds safe limit")
        max_charge = (Decimal(len(spoken)) * self._rate / Decimal(1_000_000)
                      ).quantize(Decimal("0.000001"), rounding=ROUND_UP)
        if max_charge <= 0 or max_charge > self._cap:
            raise SpeechRejected("No approved TTS rate/cap for this request")
        # The backend store must atomically reserve (tenant, campaign, plan
        # digest, idempotency_key) ONCE; repeat/uncertain attempts fail CLOSED.
        grant = self._reserve(request.shop_id, request.campaign_id,
                              review["plan_sha256"], request.idempotency_key,
                              float(max_charge), len(spoken), request.preview)
        if not isinstance(grant, str) or len(grant) < 8:
            raise SpeechRejected("Durable once-only TTS budget was not reserved")
        url = "https://" + self.region + ".tts.speech.microsoft.com/cognitiveservices/v1"
        headers = {"Content-Type": "application/ssml+xml",
                   "X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm",
                   "Ocp-Apim-Subscription-Key": self._api_key,
                   "User-Agent": "RetailGrowthAI-Feature2-TTS/1.0"}
        # A provider can charge before our client sees the response. Unknown
        # acknowledgements remain HELD, never automatically refunded/retried.
        try:
            audio = self._transport(url, headers, ssml)
            seconds = _wav(audio, planned_limit)
            if self._authorize(request.shop_id, request.campaign_id) is not True:
                raise SpeechRejected("Tenant editor revoked before private save")
            if self._read_plan(request.shop_id, request.campaign_id) != plan:
                raise SpeechRejected("Creative script changed before private save")
            receipt = {"shop_id": request.shop_id,
                       "campaign_id": request.campaign_id,
                       "plan_sha256": review["plan_sha256"],
                       "voice_id": selected[0], "language": selected[1],
                       "preview": request.preview,
                       "audio_sha256": sha256(audio).hexdigest(),
                       "mime_type": "audio/wav", "duration_seconds": seconds,
                       "source": "AZURE_SPEECH_TTS", "private": True,
                       "rights_status": "GENERATED_SPEECH_REVIEW_REQUIRED",
                       "human_speech_verified": False,
                       "word_alignment_verified": False,
                       "can_publish": False}
            result = self._write(request.shop_id, request.campaign_id, grant,
                                 audio, dict(receipt))
            if (not isinstance(result, dict) or
                result.get("shop_id") != request.shop_id or
                result.get("campaign_id") != request.campaign_id or
                result.get("audio_sha256") != receipt["audio_sha256"] or
                result.get("private") is not True or
                not isinstance(result.get("asset_id"), str) or
                not _UUID.fullmatch(result["asset_id"])):
                raise SpeechRejected("Trusted private media persistence failed")
            # Treat provider charge as maximum until verified actual bill; the
            # rate supplied by ops is a ceiling, not a fabricated invoice.
            self._reconcile(grant, "HELD_ESTIMATE_PROVIDER_BILL_UNVERIFIED",
                            float(max_charge))
            return {**receipt, "asset_id": result["asset_id"],
                    "cost_reservation": "HELD_ESTIMATE_PROVIDER_BILL_UNVERIFIED",
                    "estimated_max_cost_usd": float(max_charge),
                    "private_download_url": None}
        except Exception as exc:
            # No reattempt, no refund. Caller reconciles unknown provider cost
            # using existing budget ledger and recorded grant ID out-of-band.
            raise SpeechRejected("Speech synthesis/persistence unverified: do not retry") from exc
