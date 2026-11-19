"""Offline regressions for the upstream VoiceStudio adapter; never run live TTS."""
import io
import json
import wave

import pytest

from ai_agents.feature2_voicestudio_adapter import VoiceStudioUnavailable, synthesize_voice_wav


def _wav():
    out = io.BytesIO()
    with wave.open(out, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(b"\x00\x00" * 160)
    return out.getvalue()


class FakeVoiceStudioReply(io.BytesIO):
    status = 200
    headers = {"Content-Type": "audio/wav"}

    def __init__(self, data, *, url="http://127.0.0.1:3900/v1/audio/speech", status=200,
                 content_type="audio/wav"):
        super().__init__(data)
        self.url = url
        self.status = status
        self.headers = {"Content-Type": content_type}

    def geturl(self):
        return self.url


def _call(**overrides):
    params = {
        "text": "Welcome to our shop.",
        "base_url": "http://127.0.0.1:3900",
        "api_key": "test-example-key-not-real",
        "voice": "alloy",
        "enabled": True,
        "commercial_model_verified": True,
        "transport": lambda req, timeout: FakeVoiceStudioReply(_wav()),
    }
    params.update(overrides)
    return synthesize_voice_wav(**params)


def test_pcm_wav_speech_returned_from_stub():
    seen = []
    def transport(req, timeout):
        seen.append((req, timeout))
        return FakeVoiceStudioReply(_wav())
    assert _call(transport=transport) == _wav()
    assert len(seen) == 1
    req, timeout = seen[0]
    assert req.get_method() == "POST"
    assert req.full_url == "http://127.0.0.1:3900/v1/audio/speech"
    assert req.get_header("Authorization") == "Bearer test-example-key-not-real"
    assert json.loads(req.data) == {
        "model": "tts-1", "voice": "alloy",
        "input": "Welcome to our shop.", "response_format": "wav",
    }
    assert timeout == 45


@pytest.mark.parametrize("config", [
    {"enabled": False},
    {"commercial_model_verified": False},
    {"api_key": ""},
    {"api_key": "short"},
    {"text": ""},
    {"text": "x" * 3001},
    {"voice": "../evil"},
    {"base_url": "http://example.com:3900"},
    {"base_url": "http://127.0.0.1:3900@evil.example:3900"},
    {"base_url": "file:///etc/passwd"},
    {"base_url": "http://127.0.0.1:3900/?api_key=secret"},
])
def test_denials_without_network(config):
    calls = []
    def transport(req, timeout):
        calls.append(req)
        raise AssertionError("must not contact upstream")
    with pytest.raises(VoiceStudioUnavailable):
        _call(**config, transport=transport)
    assert calls == []


@pytest.mark.parametrize("blob", [
    b"",
    b"not-wave",
    b"RIFF" + b"\x00" * 100,
    _wav()[:24],
    b"Z" * (8 * 1024 * 1024 + 1),
])
def test_malformed_or_oversized_response_denied(blob):
    with pytest.raises(VoiceStudioUnavailable):
        _call(transport=lambda req, timeout: FakeVoiceStudioReply(blob))


def test_upstream_error_is_redacted():
    from urllib.error import URLError
    def transport(req, timeout):
        raise URLError("secret in upstream exception")
    with pytest.raises(VoiceStudioUnavailable) as err:
        _call(transport=transport)
    assert "secret" not in str(err.value)


@pytest.mark.parametrize("reply", [
    {"status": 202},
    {"url": "https://attacker.example/v1/audio/speech"},
    {"content_type": "text/html"},
    {"content_type": ""},
])
def test_status_origin_and_mime_denied(reply):
    with pytest.raises(VoiceStudioUnavailable):
        _call(transport=lambda req, timeout: FakeVoiceStudioReply(_wav(), **reply))


def test_truncated_riff_data_denied_even_if_header_claims_longer():
    audio = _wav()
    with pytest.raises(VoiceStudioUnavailable):
        _call(transport=lambda req, timeout: FakeVoiceStudioReply(audio[:45]))
