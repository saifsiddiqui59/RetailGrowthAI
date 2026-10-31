"""Real PCM test music, not streaming, borrowing or pretending to be speech."""
from pathlib import Path
import hashlib
import importlib.util
import json
import wave
def test_original_test_bed_5_seconds_is_real_pcm_and_not_licensed(tmp_path):
    script=Path(__file__).resolve().parents[1]/"test-fixtures/clothing-shop-pexels/generate-original-test-audio.py"
    spec=importlib.util.spec_from_file_location("feature2_original_test_audio",script)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original=tmp_path/"bed.wav"
    row=module.write_original_audio(original,5)
    with wave.open(str(original),"rb") as wav:
        assert wav.getnchannels()==1
        assert wav.getsampwidth()==2
        assert wav.getframerate()==48000
        assert wav.getnframes()==5*48000
    assert row["sha256"]==hashlib.sha256(original.read_bytes()).hexdigest()
    assert row["contains_real_speech"] is False
    assert row["commercial_music_license_reviewed"] is False
    assert row["can_publish"] is False
    assert not row["tenant_private_imported"]
    try:module.write_original_audio(original,5)
    except RuntimeError:pass
    else:raise AssertionError("Overwriting original WAV must fail")
