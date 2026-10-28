"""Feature2 WAV byte/duration and private source provenance, NOT speech approval.

Explicitly does NOT claim real human narration, lip sync or verified transcript
from a synthetic tone. A final Feature4 editor must separately confirm real
speaker identity, spoken words and licensed audio before publishing.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import io
import wave


class AudioEvidenceRejected(ValueError):
    pass


@dataclass(frozen=True)
class AudioEvidence:
    status: str
    shop_id: str
    campaign_id: str
    plan_sha256: str
    audio_sha256: str
    sample_rate_hz: int
    duration_seconds: float
    audio_codec: str = "PCM_S16LE"
    actual_human_speech_verified: bool = False
    words_audibly_match_script: bool = False
    lip_sync_verified: bool = False
    can_publish: bool = False
    can_dispatch_motion: bool = False
    gpu_enabled: bool = False


def inspect_private_narration_wav(
    *, bundle: dict, audio_original: bytes,
    signed_audio_record: dict, active_owner_or_editor_check,
) -> AudioEvidence:
    if not isinstance(bundle, dict) or not callable(active_owner_or_editor_check):
        raise AudioEvidenceRejected("Original creative and trusted active membership required")
    creative=bundle.get("creative_direction_v1")
    approval=bundle.get("approval_record")
    if not isinstance(creative, dict) or not isinstance(approval, dict):
        raise AudioEvidenceRejected("Reviewed creative source bundle required")
    shop=creative.get("shop_id")
    campaign=creative.get("campaign_id")
    digest=approval.get("plan_sha256")
    if (not isinstance(shop, str) or not isinstance(campaign, str) or
        not isinstance(digest, str) or len(digest)!=64 or
        approval.get("review_status")!="DRAFT" or
        approval.get("can_publish") is not False or
        approval.get("can_run_paid_motion") is not False or
        creative.get("duration_seconds") not in (15,30,60)):
        raise AudioEvidenceRejected("Only source-locked nonpublishable Reel drafts")
    if active_owner_or_editor_check(shop) is not True:
        raise AudioEvidenceRejected("Current same-shop audio source membership denied")
    if type(audio_original) is not bytes or not 100 <= len(audio_original) <= 18_000_000:
        raise AudioEvidenceRejected("Original bounded WAV bytes unavailable")
    checksum=sha256(audio_original).hexdigest()
    if (type(signed_audio_record) is not dict or
        signed_audio_record.get("shop_id") != shop or
        signed_audio_record.get("campaign_id") != campaign or
        signed_audio_record.get("creative_plan_sha256") != digest or
        signed_audio_record.get("original_audio_sha256") != checksum or
        signed_audio_record.get("private") is not True or
        signed_audio_record.get("commercial_use_allowed") is not True or
        signed_audio_record.get("revoked_at") is not None or
        signed_audio_record.get("mime") != "audio/wav" or
        signed_audio_record.get("rights_reviewed") is not True):
        raise AudioEvidenceRejected("Private licensed source WAV has no current plan/bytes approval")
    try:
        with wave.open(io.BytesIO(audio_original),"rb") as wav:
            frames=wav.getnframes()
            hz=wav.getframerate()
            channels=wav.getnchannels()
            sample_size=wav.getsampwidth()
            mode=wav.getcomptype()
            if (hz not in (16000,24000,44100,48000) or channels not in (1,2)
                or sample_size!=2 or mode!="NONE" or frames<=0):
                raise AudioEvidenceRejected("Only bounded uncompressed 16-bit PCM WAV accepted")
            duration=frames / hz
    except (EOFError, OSError, ValueError, wave.Error) as exc:
        raise AudioEvidenceRejected("Malformed or unsupported WAV container") from exc
    if duration > creative["duration_seconds"] or duration < 0.5:
        raise AudioEvidenceRejected("Audio playback duration does not fit approved Reel")
    audio_state=(creative.get("audio_sync") or {}).get("state")
    if audio_state not in (
        "ESTIMATED_PENDING_REAL_SPEECH_ALIGNMENT",
        "WORD_TIMES_MATCH_PENDING_AUDIO_PROVENANCE",
    ):
        raise AudioEvidenceRejected("Unverified audio state falsely claims prior speech proof")
    if active_owner_or_editor_check(shop) is not True:
        raise AudioEvidenceRejected("Current audio owner/editor revoked after media inspection")
    return AudioEvidence(
        status="ORIGINAL_PCM_AUDIO_BYTES_DURATION_VERIFIED_SPEECH_NOT_REVIEWED",
        shop_id=shop,campaign_id=campaign,plan_sha256=digest,
        audio_sha256=checksum,sample_rate_hz=hz,
        duration_seconds=round(duration,3),
    )
