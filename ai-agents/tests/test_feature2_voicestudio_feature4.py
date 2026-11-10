"""CPU-only byte-exact upstream VoiceStudio-to-Feature4 narration tests."""
import io
import wave

import pytest

from ai_agents.feature2_voicestudio_adapter import (
    MAX_WAV_BYTES,
    VoiceStudioUnavailable,
    synthesize_voice_wav,
)
from ai_agents.feature2_voicestudio_feature4 import fit_voiceover_to_reel


def original_pcm(*, frames=8000, rate=16000, channels=1):
    out = io.BytesIO()
    with wave.open(out, "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(b"\x01\x02" * channels * frames)
    return out.getvalue()


class Reply(io.BytesIO):
    status = 200
    headers = {"Content-Type": "audio/wav"}

    def geturl(self):
        return "http://127.0.0.1:3900/v1/audio/speech"


@pytest.mark.parametrize("seconds", (15, 30, 60))
def test_actual_original_voice_samples_preserved_with_silence_padding(seconds):
    source = original_pcm(channels=2)
    padded, proof = fit_voiceover_to_reel(source, reel_seconds=seconds)
    with wave.open(io.BytesIO(source), "rb") as a, wave.open(io.BytesIO(padded), "rb") as b:
        original = a.readframes(a.getnframes())
        whole = b.readframes(b.getnframes())
        assert b.getnframes() == seconds * 16000
        assert whole[:len(original)] == original
        assert whole[len(original):] == b"\x00" * (len(whole) - len(original))
        assert b.getnchannels() == 2
    assert proof["spoken_frame_count"] == 8000
    assert proof["silence_padded"] is True
    assert proof["approved_for_render_or_publish"] is False
    assert proof["source_model_inference_verified"] is False


def test_integration_stub_upstream_speech_to_feature4_private_wav():
    original = original_pcm(frames=16000)
    wav_bytes = synthesize_voice_wav(
        text="A fictional test boutique offers tailoring tips.",
        base_url="http://127.0.0.1:3900",
        api_key="not-real-test-credential",
        voice="alloy",
        enabled=True,
        commercial_model_verified=True,
        transport=lambda req, timeout: Reply(original),
    )
    render_bytes, proof = fit_voiceover_to_reel(wav_bytes, reel_seconds=30)
    assert proof["source_audio_sha256"] != proof["render_audio_sha256"]
    assert proof["render_duration_seconds"] == 30
    assert len(render_bytes) > len(wav_bytes)


def test_already_full_length_is_not_trimmed_or_extended():
    source = original_pcm(frames=16000 * 15)
    rendered, proof = fit_voiceover_to_reel(source, reel_seconds=15)
    assert proof["spoken_duration_seconds"] == 15
    assert proof["silence_padded"] is False
    assert rendered == source


@pytest.mark.parametrize("bad", [True, 0, 1, 29, 31, 90, "30", None])
def test_unsupported_timeline_is_denied(bad):
    with pytest.raises(VoiceStudioUnavailable):
        fit_voiceover_to_reel(original_pcm(), reel_seconds=bad)


def test_overlong_narration_denied_instead_of_cutting_off_words():
    source = original_pcm(frames=16001 * 15)
    with pytest.raises(VoiceStudioUnavailable, match="exceeds Feature4"):
        fit_voiceover_to_reel(source, reel_seconds=15)


def test_untrusted_wav_bytes_denied():
    for value in ("filename.wav", None, bytearray(original_pcm()), b"not wav", b""):
        with pytest.raises(VoiceStudioUnavailable):
            fit_voiceover_to_reel(value, reel_seconds=30)


def test_padding_size_limit_denied():
    source = original_pcm(frames=100, rate=96000, channels=2)
    with pytest.raises(VoiceStudioUnavailable, match="size"):
        fit_voiceover_to_reel(source, reel_seconds=60)
