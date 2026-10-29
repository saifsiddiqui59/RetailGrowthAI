"""Feature2 actual CPU Kokoro ONNX inference, reusing upstream Kokoro.create.

thewh1teagle/kokoro-onnx MIT 0.6.1 pinned at
3596b26764286a7de9d90c363e988d50578918e5. Model Kokoro-82M Apache-2.0.
Real inference is conditional on immutable official downloaded model+voice bytes
in a trusted local operator cache. NEVER silently download during requests.
No user JWT, public asset URL, global speech server or paid provider fallback.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import os
import re
import threading
import time
import wave
from array import array

MODEL_NAME="kokoro-v1.0.int8.onnx"
MODEL_SIZE=114119327
MODEL_SHA="ae315a79b623f244700e4afb9246c46a26066782e049ba174bf3ba433970ee9c"
VOICES_NAME="voices-v1.0.bin"
VOICES_SIZE=28214398
VOICES_SHA="bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d"
SOURCE_REVISION="3596b26764286a7de9d90c363e988d50578918e5"
RELEASE="model-files-v1.1"
# V1.0 English model. These are actual upstream voice keys, NOT en-IN/hi-IN/mr-IN.
SUPPORTED_VOICES={
    "af_heart":"en-us", "af_sarah":"en-us", "am_adam":"en-us",
    "am_michael":"en-us", "bf_emma":"en-gb", "bf_isabella":"en-gb",
    "bm_george":"en-gb", "bm_lewis":"en-gb",
}
SPEEDS={"slow":0.9,"normal":1.0,"fast":1.1}
_TEXT=re.compile(r"^[^\x00-\x08\x0b-\x1f\x7f<>]{1,1400}$")
_lock=threading.Lock()
_cpu_gate=threading.BoundedSemaphore(1)  # bounded CPU worker, no parallel model storms
_loaded={}  # worker-local session reused; path+digest bound; no shared user state.

class LocalSpeechUnavailable(ValueError):
    pass

def _file_proof(path:Path,expected_name,expected_bytes,expected_sha):
    if not path.is_file() or path.is_symlink() or path.name!=expected_name:
        raise LocalSpeechUnavailable("Pinned local model original unavailable")
    if path.stat().st_size!=expected_bytes:
        raise LocalSpeechUnavailable("Pinned ONNX/voice size mismatch")
    h=__import__("hashlib").sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            h.update(chunk)
    if h.hexdigest()!=expected_sha:
        raise LocalSpeechUnavailable("Pinned ONNX/voice digest mismatch")
    return h.hexdigest()

def verify_cache(cache_dir, *, model_sha=MODEL_SHA, voice_sha=VOICES_SHA,
                 model_size=MODEL_SIZE, voice_size=VOICES_SIZE):
    """Dev override values used only for pure hash fixture tests.

    Real generate() NEVER forwards alternative identities or a model path
    supplied by the browser. Cache directory is trusted operator config.
    """
    if not isinstance(cache_dir,(str,Path)) or not str(cache_dir):
        raise LocalSpeechUnavailable("Trusted speech cache required")
    root=Path(cache_dir).resolve(strict=True)
    if not root.is_dir():
        raise LocalSpeechUnavailable("Trusted speech cache required")
    _file_proof(root/MODEL_NAME,MODEL_NAME,model_size,model_sha)
    _file_proof(root/VOICES_NAME,VOICES_NAME,voice_size,voice_sha)
    return root

def _load_kokoro(path):
    try:
        from kokoro_onnx import Kokoro  # Actual upstream inference implementation
    except (ImportError, OSError) as exc:
        raise LocalSpeechUnavailable("Approved kokoro-onnx CPU package not installed") from exc
    old=os.environ.get("ONNX_PROVIDER")
    if old not in (None,"CPUExecutionProvider"):
        raise LocalSpeechUnavailable("Kokoro CPU-only execution required")
    os.environ["ONNX_PROVIDER"]="CPUExecutionProvider"
    try:
        kokoro=Kokoro(str(path/MODEL_NAME),str(path/VOICES_NAME))
        providers=kokoro.sess.get_providers()
        if providers!=["CPUExecutionProvider"]:
            raise LocalSpeechUnavailable("ONNX session is not CPU-only")
        return kokoro
    except LocalSpeechUnavailable:
        raise
    except Exception as exc:
        raise LocalSpeechUnavailable("Verified offline Kokoro model cannot load") from exc
    finally:
        if old is None:
            os.environ.pop("ONNX_PROVIDER",None)
        else:
            os.environ["ONNX_PROVIDER"]=old

def _session(root):
    with _lock:
        key=(str(root),MODEL_SHA,VOICES_SHA)
        if key not in _loaded:
            candidate=_load_kokoro(root)
            # A worker must never accumulate 100 MB+ model sessions every
            # time the trusted operator switches its immutable model cache.
            _loaded.clear()
            _loaded[key]=candidate
        return _loaded[key]

def _riff_wav(samples,rate):
    """Convert actual numpy float32/float64 upstream samples to portable PCM16."""
    if type(rate) is not int or rate!=24000:
        raise LocalSpeechUnavailable("Unsupported Kokoro sample rate")
    try:
        import numpy as np
        pcm=np.asarray(samples,dtype=np.float32)
        if (pcm.ndim!=1 or len(pcm)<rate//10 or len(pcm)>rate*65 or
            not np.isfinite(pcm).all() or np.max(np.abs(pcm))>1.0001):
            raise LocalSpeechUnavailable("Unexpected Kokoro PCM samples")
        if np.max(np.abs(pcm))<0.0003:
            raise LocalSpeechUnavailable("Kokoro output is near silent")
        pcm16=np.clip(np.rint(pcm*32767),-32768,32767).astype("<i2").tobytes()
    except (TypeError,ValueError) as exc:
        raise LocalSpeechUnavailable("Kokoro samples invalid") from exc
    out=BytesIO()
    with wave.open(out,"wb") as handle:
        handle.setnchannels(1);handle.setsampwidth(2);handle.setframerate(rate)
        handle.writeframes(pcm16)
    return out.getvalue(),round(len(pcm16)/(rate*2),4)

def synthesize_local(*,text,voice_id="af_heart",lang="en-us",
                     speed="normal",cache_dir=None,engine=None,
                     trusted_for_tests=False):
    """Actual upstream Kokoro.create, auditable local WAV bytes.

    engine injection is ONLY for tests. Genuine caller must use verified model
    cache and real upstream package. Synthetic test result is marked TEST_ONLY.
    """
    if (type(text) is not str or not _TEXT.fullmatch(text.strip()) or
        len(text.strip())>1400 or type(voice_id) is not str or
        SUPPORTED_VOICES.get(voice_id)!=lang or speed not in SPEEDS):
        raise LocalSpeechUnavailable("Unsupported text/voice/language/speed")
    if engine is not None and trusted_for_tests is not True:
        raise LocalSpeechUnavailable("Only approved upstream CPU engine may be used")
    if engine is None:
        if os.getenv("RETAIL_FEATURE2_KOKORO_CPU_ENABLED")!="true":
            raise LocalSpeechUnavailable("Local Kokoro disabled by operator")
        if not isinstance(cache_dir,(str,Path)) or not str(cache_dir):
            raise LocalSpeechUnavailable("Operator configured local cache required")
    started=time.perf_counter()
    # Include disk integrity checks and ONNX session initialization inside
    # the ONE active CPU lease. Otherwise concurrent requests can all hash
    # 140 MB weights and/or start model sessions before acquiring the gate.
    if not _cpu_gate.acquire(timeout=5):
        raise LocalSpeechUnavailable("Kokoro CPU worker busy; inspect existing job before retry")
    try:
        if engine is None:
            root=verify_cache(cache_dir)
            engine=_session(root)
            if voice_id not in engine.get_voices():
                raise LocalSpeechUnavailable("Voice absent in actual Kokoro style pack")
        samples,rate=engine.create(text.strip(),voice=voice_id,
                                   speed=SPEEDS[speed],lang=lang)
        data,duration=_riff_wav(samples,rate)
    except LocalSpeechUnavailable:
        raise
    except Exception as exc:
        raise LocalSpeechUnavailable("Kokoro CPU synthesis failed (no fallback charged)") from exc
    finally:
        _cpu_gate.release()
    if duration>60:
        raise LocalSpeechUnavailable("Generated audio is longer than supported Reel")
    return {
        "schema":"retailgrowth.feature2-kokoro-original-audio.v1",
        "provider":"kokoro-onnx", "model":"Kokoro-82M-v1.0-int8",
        "upstream_revision":SOURCE_REVISION,"voice_id":voice_id,
        "language":lang,"speed":speed,
        "audio_sha256":sha256(data).hexdigest(),"audio_wav":data,
        "duration_seconds":duration,"sample_rate_hz":rate,
        "cpu_elapsed_seconds":round(time.perf_counter()-started,4),
        "actual_inference_verified":trusted_for_tests is not True,
        "test_only":trusted_for_tests is True,
        "word_timestamps":None,"speech_transcript_verified":False,
        "approved_to_publish":False,"paid_calls":0,
    }


# A measurement harness only. No synthetic timer or mock voice can be labeled
# real; operation still requires operator-pinned local ONNX weight verification.
# RSS is a *process high-water mark*, not model-only or instance peak memory.
def run_cpu_kokoro_benchmark(*,cache_dir,voice_id="af_heart",
                             lang="en-us",repeats=2,
                             synthesize=None,trusted_for_tests=False):
    """Measure real local CPU inference, including cold verified weight load.

    Use only a fixed fictional-business script. Do not benchmark customer
    scripts, log the generated WAV, assume electricity/VM is free, or dispatch
    paid Azure/remote model calls. The optional injected runner is TEST ONLY.
    """
    if (type(repeats) is not int or not 1<=repeats<=3 or
        type(cache_dir) not in (str,Path) or not str(cache_dir) or
        type(voice_id) is not str or SUPPORTED_VOICES.get(voice_id)!=lang or
        type(trusted_for_tests) is not bool or
        (synthesize is not None and
         (trusted_for_tests is not True or not callable(synthesize))) or
        (trusted_for_tests and synthesize is None)):
        raise LocalSpeechUnavailable("Trusted bounded Kokoro benchmark required")
    if not trusted_for_tests and os.getenv("RETAIL_FEATURE2_KOKORO_CPU_ENABLED")!="true":
        raise LocalSpeechUnavailable("Local benchmark disabled by operator")
    # Original fixed synthetic voice benchmark, never a customer promotion.
    phrase="Thread and Loom Studio shares helpful garment styling ideas."
    try:
        import resource
        def rss_kib():
            value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            return int(value/1024) if __import__("sys").platform=="darwin" else int(value)
    except ImportError:
        def rss_kib():
            return None

    before=rss_kib()
    observations=[]
    engine=synthesize if trusted_for_tests else synthesize_local
    for _ in range(repeats):
        wall_start=time.perf_counter()
        cpu_start=time.process_time()
        audio=engine(text=phrase,voice_id=voice_id,lang=lang,speed="normal",
                     cache_dir=cache_dir)
        wall=time.perf_counter()-wall_start
        cpu=time.process_time()-cpu_start
        if (type(audio) is not dict or
            audio.get("schema")!="retailgrowth.feature2-kokoro-original-audio.v1" or
            audio.get("provider")!="kokoro-onnx" or
            audio.get("model")!="Kokoro-82M-v1.0-int8" or
            audio.get("upstream_revision")!=SOURCE_REVISION or
            audio.get("voice_id")!=voice_id or audio.get("language")!=lang or
            audio.get("sample_rate_hz")!=24000 or
            audio.get("paid_calls")!=0 or
            audio.get("test_only") is not trusted_for_tests or
            audio.get("actual_inference_verified") is not (not trusted_for_tests) or
            type(audio.get("audio_wav")) is not bytes or
            type(audio.get("audio_sha256")) is not str or
            sha256(audio["audio_wav"]).hexdigest()!=audio["audio_sha256"] or
            type(audio.get("duration_seconds")) not in (float,int) or
            not 0.1<=audio["duration_seconds"]<=60 or
            not audio["audio_wav"].startswith(b"RIFF") or
            audio["audio_wav"][8:12]!=b"WAVE"):
            raise LocalSpeechUnavailable("Benchmark source/audio provenance invalid")
        observations.append({
            "wall_seconds":round(wall,4),
            "process_cpu_seconds":round(cpu,4),
            "audio_seconds":audio["duration_seconds"],
            "real_time_factor":round(wall/audio["duration_seconds"],4),
            "process_high_water_rss_kib":rss_kib(),
        })
    after=rss_kib()
    return {
        "schema":"retailgrowth.feature2-cpu-benchmark.v1",
        "engine":"kokoro-onnx",
        "model":"Kokoro-82M-v1.0-int8",
        "upstream_revision":SOURCE_REVISION,
        "voice_id":voice_id,"language":lang,"sample_count":repeats,
        "observations":observations,
        "process_hwm_rss_before_kib":before,
        "process_hwm_rss_after_kib":after,
        "rss_is_process_high_water_only":True,
        "cold_start_includes_pinned_weight_hash":not trusted_for_tests,
        "real_model_inference_verified":not trusted_for_tests,
        "test_only":trusted_for_tests,
        "billable_provider_calls":0,
        "cloud_vm_or_electricity_cost_estimate_usd":None,
        "service_cost_is_not_certified_free":True,
        "verified_speech_quality":False,
        "can_publish":False,
    }
