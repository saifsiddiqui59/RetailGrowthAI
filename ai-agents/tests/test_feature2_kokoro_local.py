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
def test_missing_operator_cache_is_denied_without_raw_path_exception(tmp_path):
    # An absent/unmounted operator cache must produce a controlled denial,
    # never a FileNotFoundError that bubbles into the speech worker.
    missing = tmp_path / "operator-cache-not-provisioned"
    with pytest.raises(LocalSpeechUnavailable, match="Trusted speech cache required"):
        verify_cache(missing)


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


def test_operator_asset_provisioner_has_pinned_cache_and_safe_cli():
    import json
    from pathlib import Path
    import shutil
    import subprocess
    script=Path(__file__).resolve().parents[1]/'test-fixtures/retailer-voice/provision-pinned-kokoro-models.sh'
    pins=Path(__file__).resolve().parents[1]/'oss/kokoro-onnx/pinned-sources.json'
    source=script.read_text(encoding='utf-8')
    manifest=json.loads(pins.read_text(encoding='utf-8'))
    for original in manifest['assets']:
        assert original['name'] in source
        assert original['sha256'] in source
        assert str(original['bytes']) in source
    assert 'sha256sum --check --status' in source
    assert 'mv -n --' in source
    assert '--proto' in source and '--tlsv1.2' in source
    if shutil.which('bash'):
        assert subprocess.run(['bash','-n',str(script)],capture_output=True).returncode==0
        invalid=subprocess.run(['bash',str(script),'relative-path'],capture_output=True,timeout=5)
        assert invalid.returncode==2


def test_cpu_slot_is_acquired_before_any_140mb_weight_hash_or_model_load(monkeypatch):
    # A busy worker must reject before hashing large ONNX weights or loading
    # another runtime. This is an injected gate, NOT genuine neural inference.
    from ai_agents import feature2_kokoro_local as local
    events=[]
    class Busy:
        def acquire(self,timeout):
            events.append(("slot",timeout))
            return False
        def release(self):
            raise AssertionError("busy slot was never held")
    def never(*args,**kwargs):
        raise AssertionError("Expensive model/file IO occurred before CPU lease")
    monkeypatch.setattr(local,"_cpu_gate",Busy())
    monkeypatch.setattr(local,"verify_cache",never)
    monkeypatch.setattr(local,"_session",never)
    monkeypatch.setenv("RETAIL_FEATURE2_KOKORO_CPU_ENABLED","true")
    with pytest.raises(LocalSpeechUnavailable,match="busy"):
        synthesize_local(text="Diwali preview",cache_dir="/operator-pinned-cache")
    assert events==[("slot",5)]

def test_busy_slot_keeps_original_model_output_unavailable(monkeypatch):
    from ai_agents import feature2_kokoro_local as local
    class Busy:
        def acquire(self,timeout):return False
        def release(self):raise AssertionError("Never acquired")
    monkeypatch.setattr(local,"_cpu_gate",Busy())
    with pytest.raises(LocalSpeechUnavailable,match="busy"):
        synthesize_local(text="Kurtis for Diwali",engine=SimulatedEngine(),
                         trusted_for_tests=True)

def test_cpu_slot_released_after_failed_pcm_conversion(monkeypatch):
    from ai_agents import feature2_kokoro_local as local
    events=[]
    class Gate:
        def acquire(self,timeout):events.append("acquire");return True
        def release(self):events.append("release")
    class WrongEngine:
        def create(self,*args,**kwargs):return [], 24000
    monkeypatch.setattr(local,"_cpu_gate",Gate())
    with pytest.raises(LocalSpeechUnavailable):
        synthesize_local(text="Diwali",engine=WrongEngine(),trusted_for_tests=True)
    assert events==["acquire","release"]

def test_worker_session_cache_is_bounded_to_one_immutable_operator_root(monkeypatch,tmp_path):
    from ai_agents import feature2_kokoro_local as local
    local._loaded.clear()
    loads=[]
    def fake_load(path):
        loads.append(str(path))
        return object()
    monkeypatch.setattr(local,"_load_kokoro",fake_load)
    try:
        first=local._session(tmp_path/"first")
        assert local._session(tmp_path/"first") is first
        local._session(tmp_path/"second")
        assert len(local._loaded)==1
        assert len(loads)==2
        assert next(iter(local._loaded))[0].endswith("second")
    finally:
        local._loaded.clear()

def test_cpu_onnx_provider_list_must_be_exclusively_cpu(monkeypatch,tmp_path):
    from ai_agents import feature2_kokoro_local as local
    import sys
    from types import SimpleNamespace
    old=__import__("os").environ.get("ONNX_PROVIDER")
    class Unapproved:
        def __init__(self,*args):self.sess=self
        def get_providers(self):return ["CUDAExecutionProvider","CPUExecutionProvider"]
    monkeypatch.setitem(sys.modules,"kokoro_onnx",SimpleNamespace(Kokoro=Unapproved))
    monkeypatch.delenv("ONNX_PROVIDER",raising=False)
    with pytest.raises(LocalSpeechUnavailable,match="CPU-only"):
        local._load_kokoro(tmp_path)
    assert "ONNX_PROVIDER" not in __import__("os").environ
    class OnlyCPU(Unapproved):
        def get_providers(self):return ["CPUExecutionProvider"]
    monkeypatch.setitem(sys.modules,"kokoro_onnx",SimpleNamespace(Kokoro=OnlyCPU))
    assert local._load_kokoro(tmp_path).sess.get_providers()==["CPUExecutionProvider"]
    assert "ONNX_PROVIDER" not in __import__("os").environ
    if old is not None:
        monkeypatch.setenv("ONNX_PROVIDER",old)


from ai_agents.feature2_kokoro_local import run_cpu_kokoro_benchmark

def test_cpu_benchmark_is_accurately_labeled_injected_sine_test_not_real():
    calls=[]
    def injected(**kwargs):
        calls.append(kwargs)
        return synthesize_local(
            text=kwargs["text"],voice_id=kwargs["voice_id"],
            lang=kwargs["lang"],speed=kwargs["speed"],
            engine=SimulatedEngine(),trusted_for_tests=True)
    results=run_cpu_kokoro_benchmark(
        cache_dir="/synthetic-test-cache-never-loaded",repeats=2,
        synthesize=injected,trusted_for_tests=True)
    assert len(calls)==2
    assert all(c["text"].startswith("Thread and Loom") for c in calls)
    assert results["sample_count"]==2
    assert results["real_model_inference_verified"] is False
    assert results["cold_start_includes_pinned_weight_hash"] is False
    assert results["test_only"] is True
    assert results["service_cost_is_not_certified_free"] is True
    assert results["cloud_vm_or_electricity_cost_estimate_usd"] is None
    assert results["billable_provider_calls"]==0
    assert results["verified_speech_quality"] is False
    assert not results["can_publish"]
    assert all(x["audio_seconds"]==1.0 and x["real_time_factor"]>=0
               and x["process_cpu_seconds"]>=0
               for x in results["observations"])
    assert "audio_wav" not in str(results)
    assert "Thread and Loom" not in str(results)

@pytest.mark.parametrize("changes",[
    {"repeats":0},{"repeats":4},{"repeats":True},
    {"voice_id":"hi-IN-SwaraNeural"},{"lang":"mr-IN"},
    {"voice_id":"bm_george","lang":"en-us"},
    {"cache_dir":""},{"trusted_for_tests":False},
])
def test_cpu_benchmark_rejects_untrusted_runtime_or_unbounded_inference(changes):
    attempts=[]
    def mock(**kwargs):
        attempts.append(1)
        raise AssertionError("No inference may occur")
    args={"cache_dir":"/only-test-placeholder","repeats":1,
          "synthesize":mock,"trusted_for_tests":True}
    args.update(changes)
    with pytest.raises(LocalSpeechUnavailable):
        run_cpu_kokoro_benchmark(**args)
    assert attempts==[]

def test_cpu_benchmark_rejects_fabricated_actual_voice_proof():
    def pretend(**kwargs):
        record=synthesize_local(
            text=kwargs["text"],voice_id=kwargs["voice_id"],
            lang=kwargs["lang"],engine=SimulatedEngine(),trusted_for_tests=True)
        record["actual_inference_verified"]=True
        record["test_only"]=False
        return record
    with pytest.raises(LocalSpeechUnavailable,match="provenance"):
        run_cpu_kokoro_benchmark(cache_dir="/test",repeats=1,
            synthesize=pretend,trusted_for_tests=True)

def test_cpu_benchmark_disabled_operator_does_not_load_models(monkeypatch,tmp_path):
    monkeypatch.delenv("RETAIL_FEATURE2_KOKORO_CPU_ENABLED",raising=False)
    with pytest.raises(LocalSpeechUnavailable,match="disabled"):
        run_cpu_kokoro_benchmark(cache_dir=tmp_path)


def test_operator_cpu_benchmark_cli_no_customer_prompt_or_synthetic_positive(monkeypatch,tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    cli=Path(__file__).resolve().parents[1]/"test-fixtures/retailer-voice/benchmark-pinned-kokoro-cpu.py"
    assert cli.is_file()
    relative=subprocess.run([sys.executable,str(cli),"--cache-dir","relative"],
                            capture_output=True,text=True,timeout=10)
    assert relative.returncode==2
    assert relative.stdout==""
    assert "absolute" in relative.stderr
    monkeypatch.delenv("RETAIL_FEATURE2_KOKORO_CPU_ENABLED",raising=False)
    offline=subprocess.run([sys.executable,str(cli),"--cache-dir",str(tmp_path)],
                           capture_output=True,text=True,timeout=10,
                           env={k:v for k,v in __import__("os").environ.items()
                                if k!="RETAIL_FEATURE2_KOKORO_CPU_ENABLED"})
    assert offline.returncode==2
    assert offline.stdout==""
    assert "no positive proof" in offline.stderr
