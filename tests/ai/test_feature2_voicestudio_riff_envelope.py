"""F2 private WAV envelope regression: malformed RIFF must never reach storage."""
from __future__ import annotations

import io
from pathlib import Path
import sys
import wave

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "azure-functions" / "campaign-api"))

from feature2_voicestudio_storage import _wav, PrivateVoiceStorageDenied  # noqa: E402


def _pcm():
    output = io.BytesIO()
    with wave.open(output, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(b"\\x00\\x01" * 160)
    return output.getvalue()


def test_exact_riff_envelope_is_accepted():
    assert _wav(_pcm()) is None


@pytest.mark.parametrize("mutation", ["trailing", "short_claim", "long_claim"])
def test_inconsistent_riff_envelope_denied(mutation):
    valid = _pcm()
    if mutation == "trailing":
        malformed = valid + b"hidden-tail"
    elif mutation == "short_claim":
        malformed = valid[:4] + (len(valid) - 12).to_bytes(4, "little") + valid[8:]
    else:
        malformed = valid[:4] + (len(valid) + 20).to_bytes(4, "little") + valid[8:]
    with pytest.raises(PrivateVoiceStorageDenied, match="RIFF envelope"):
        _wav(malformed)
