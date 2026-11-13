"""Prepare genuine VoiceStudio PCM WAV for the existing Feature4 audio contract.

This is only a format adapter. It does not synthesize, grant media rights,
approve a transcript, persist audio, or authorize a render/publish action.
VoiceStudio itself remains the upstream speech generator.
"""
from __future__ import annotations

from hashlib import sha256
import io
import wave

from .feature2_voicestudio_adapter import (
    MAX_WAV_BYTES,
    VoiceStudioUnavailable,
    _validate_pcm_wav,
)

_ALLOWED_REEL_SECONDS = frozenset((15, 30, 60))


def fit_voiceover_to_reel(source_wav: bytes, *, reel_seconds: int) -> tuple[bytes, dict]:
    """Preserve every original PCM sample, pad silence to an exact F4 duration.

    Reject narration longer than the reel instead of truncating spoken words.
    The returned WAV is for a PRIVATE editor asset and still needs human review,
    authoritative tenant/rights rechecks and F4 audio/MP4 acceptance.
    """
    if type(reel_seconds) is not int or reel_seconds not in _ALLOWED_REEL_SECONDS:
        raise VoiceStudioUnavailable("Unsupported Feature4 narration duration")
    if type(source_wav) is not bytes:
        raise VoiceStudioUnavailable("Trusted original WAV bytes required")
    _validate_pcm_wav(source_wav)
    with wave.open(io.BytesIO(source_wav), "rb") as original:
        channels = original.getnchannels()
        sample_width = original.getsampwidth()
        sample_rate = original.getframerate()
        frames = original.getnframes()
        pcm = original.readframes(frames)
        if original.getcomptype() != "NONE" or channels not in (1, 2) or sample_width not in (1, 2, 3, 4):
            raise VoiceStudioUnavailable("Unsupported VoiceStudio PCM layout")
        expected_bytes = frames * channels * sample_width
        if len(pcm) != expected_bytes:
            raise VoiceStudioUnavailable("VoiceStudio PCM length mismatch")

    target_frames = reel_seconds * sample_rate
    if frames > target_frames:
        raise VoiceStudioUnavailable("Narration exceeds Feature4 reel; revise the script")
    padding_bytes = (target_frames - frames) * channels * sample_width
    if expected_bytes + padding_bytes + 44 > MAX_WAV_BYTES:
        raise VoiceStudioUnavailable("Narration would exceed private WAV size limit")

    output = io.BytesIO()
    with wave.open(output, "wb") as dest:
        dest.setnchannels(channels)
        dest.setsampwidth(sample_width)
        dest.setframerate(sample_rate)
        dest.writeframes(pcm + b"\x00" * padding_bytes)
    render_wav = output.getvalue()
    if len(render_wav) > MAX_WAV_BYTES:
        raise VoiceStudioUnavailable("Feature4 WAV exceeds private media cap")
    _validate_pcm_wav(render_wav)
    return render_wav, {
        "schema": "retailgrowth.feature2-voicestudio-f4-narration.v1",
        "source_audio_sha256": sha256(source_wav).hexdigest(),
        "render_audio_sha256": sha256(render_wav).hexdigest(),
        "spoken_frame_count": frames,
        "render_frame_count": target_frames,
        "sample_rate_hz": sample_rate,
        "channels": channels,
        "sample_width_bytes": sample_width,
        "spoken_duration_seconds": round(frames / sample_rate, 4),
        "render_duration_seconds": reel_seconds,
        "silence_padded": target_frames > frames,
        "source_model_inference_verified": False,
        "speech_words_verified": False,
        "rights_or_consent_granted": False,
        "approved_for_render_or_publish": False,
    }
