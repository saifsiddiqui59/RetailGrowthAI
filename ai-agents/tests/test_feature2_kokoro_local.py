import io, wave
from hashlib import sha256
import pytest
from ai_agents.feature2_kokoro_local import (
    synthesize_local,verify_cache,MODEL_NAME,VOICES_NAME,
    LocalSpeechUnavailable, SUPPORTED_VOICES
)
class SimulatedEngine:
    def create(self,text,voice,speed,lang):
        assert text and voice in SUPPORTED_VOICES
        assert speed>0 and lang==SUPPORTED_VOICES[voice]
        np=pytest.importorskip('numpy',reason='NumPy is installed only in approved Kokoro runtime')
        return np.sin(2*np.pi*220*np.arange(24000)/24000).astype(np.float32)*0.15,24000

def test_source_only_mocked_input_is_labeled_test_only_and_pcm_bytes_are_real():
    out=synthesize_local(text="Diwali collection at Thread and Loom!",
        engine=SimulatedEngine(),trusted_for_tests=True)
    assert out["test_only"] is True and out["actual_inference_verified"] is False
    assert out["duration_seconds"]==1
    assert out["audio_sha256"]==sha256(out["audio_wav"]).hexdigest()
    with wave.open(io.BytesIO(out["audio_wav"]),"rb") as w:
        assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(24000,1,2)
        assert w.getnframes()==24000
    assert out["word_timestamps"] is None
@pytest.mark.parametrize("bad",[
    {"lang":"hi-in"},{"lang":"mr-in"},{"voice_id":"hi-IN-SwaraNeural"},
    {"voice_id":"bm_george","lang":"en-us"},{"speed":"hyper"},
    {"text":"<prosody>NO</prosody>"},{"text":""},
])
def test_unsupported_language_voice_and_injection_never_use_engine(bad):
    with pytest.raises(LocalSpeechUnavailable):
        synthesize_local(engine=SimulatedEngine(),
            trusted_for_tests=True,**{"text":"Diwali offer",**bad})
def test_real_inference_never_uses_mock_engine():
    with pytest.raises(LocalSpeechUnavailable):
        synthesize_local(text="Hello",engine=SimulatedEngine())
def test_real_runtime_disabled_no_weight_or_network(monkeypatch):
    monkeypatch.delenv("RETAIL_FEATURE2_KOKORO_CPU_ENABLED",raising=False)
    with pytest.raises(LocalSpeechUnavailable,match="disabled"):
        synthesize_local(text="Hello")
def test_wrong_local_weights_are_denied_before_inference(tmp_path):
    (tmp_path/MODEL_NAME).write_bytes(b"fake-onxx")
    (tmp_path/VOICES_NAME).write_bytes(b"fake-voices")
    with pytest.raises(LocalSpeechUnavailable):
        verify_cache(tmp_path)
def test_pure_provenance_hash_verification_fixture(tmp_path):
    model=b"local fake test tensor"
    voice=b"local fake test voice"
    (tmp_path/MODEL_NAME).write_bytes(model)
    (tmp_path/VOICES_NAME).write_bytes(voice)
    path=verify_cache(tmp_path,model_sha=sha256(model).hexdigest(),
        voice_sha=sha256(voice).hexdigest(),
        model_size=len(model),voice_size=len(voice))
    assert path==tmp_path
    with pytest.raises(LocalSpeechUnavailable):
        verify_cache(tmp_path)
