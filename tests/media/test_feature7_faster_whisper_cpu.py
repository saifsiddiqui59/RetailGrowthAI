"""Feature7 Faster-Whisper REAL API adapter tests; no fake ASR is production.

The pure model driver actually calls upstream WhisperModel(..).transcribe,
not a hand-made recognizer. Only a TEST-LOCAL Python module object replaces
faster_whisper during offline CI to assert the API contract; independent
accuracy is NOT accepted without actual pinned weights, commercial rights,
human reference speech and benchmark.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
WORKER=ROOT/"video-engine"/"feature7"/"faster_whisper_cpu.py"
SPEC=importlib.util.spec_from_file_location("feature7_faster_whisper_cpu",WORKER)
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

REVISION="536b0662742c02347bc0e980a01041f333bce120"


class Word:
    def __init__(self,word,start,end):
        self.word=word
        self.start=start
        self.end=end


class Segment:
    def __init__(self,words):
        self.words=words


class OfflineFasterWhisperCpuTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="f7-real-asr-api-")
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.model=self.base/"local_model"
        self.model.mkdir()
        hashes={}
        for name,data in (
            ("config.json",b'{"model_type":"whisper"}'),
            ("model.bin",b"TEST_ONLY_NO_NEURAL_WEIGHTS"),
            ("tokenizer.json",b'{"dummy":true}')
        ):
            p=self.model/name
            p.write_bytes(data)
            hashes[name]=hashlib.sha256(data).hexdigest()
        self.manifest=self.base/"manifest.json"
        self.manifest.write_text(json.dumps({
            "version":"feature7_faster_whisper_model_manifest_v1",
            "model_project":"Systran/faster-whisper-small",
            "model_revision":REVISION,
            "commercial_rights_reviewed":True,
            "files":hashes
        }))
        self.wav=self.base/"speech.wav"
        self.wav.write_bytes(b"RIFF"+b"\0"*64)
        self.output=self.base/"words.json"
        self.env=patch.dict(os.environ,{
            "HF_HUB_OFFLINE":"1",
            "TRANSFORMERS_OFFLINE":"1",
            "CUDA_VISIBLE_DEVICES":""
        })
        self.env.start()
        self.addCleanup(self.env.stop)

    def arguments(self,**overrides):
        return {**dict(wav_path=str(self.wav),model_dir=str(self.model),
          manifest_path=str(self.manifest),
          output_path=str(self.output),audio_duration=10.0,
          language="en",threads=2),**overrides}

    def test_upstream_api_called_on_cpu_with_real_word_timestamp_flag(self):
        calls={}
        class WhisperModelDouble:
            def __init__(self,local_path,**kwargs):
                calls["path"]=local_path
                calls["init"]=kwargs
            def transcribe(self,wav,**kwargs):
                calls["wav"]=wav
                calls["options"]=kwargs
                return iter([Segment([
                    Word("Welcome",0.5,0.9),
                    Word("to",1.0,1.19),
                    Word("our",1.25,1.5),
                    Word("shop",1.6,1.9)
                ])]),types.SimpleNamespace(language="en")
        with patch.dict(sys.modules,{
            "faster_whisper":types.SimpleNamespace(WhisperModel=WhisperModelDouble)
        }):
            actual=mod.infer_audio(**self.arguments())
        self.assertEqual(calls["path"],str(self.model))
        self.assertEqual(calls["init"]["device"],"cpu")
        self.assertEqual(calls["init"]["compute_type"],"int8")
        self.assertTrue(calls["init"]["local_files_only"])
        self.assertTrue(calls["options"]["word_timestamps"])
        self.assertFalse(calls["options"]["vad_filter"])
        self.assertEqual(calls["options"]["task"],"transcribe")
        self.assertEqual(calls["options"]["language"],"en")
        self.assertEqual(calls["wav"],str(self.wav))
        self.assertEqual(actual["segments"][0]["words"][1]["word"],"to")
        self.assertTrue(actual["word_timestamps_from_actual_model"])
        self.assertEqual(actual["verified_input_sha256"],
                         hashlib.sha256(self.wav.read_bytes()).hexdigest())
        self.assertIsInstance(actual["actual_decode_wall_seconds"],float)
        self.assertFalse(actual["word_accuracy_benchmarked"])
        self.assertFalse(actual["approved"])
        self.assertEqual(json.loads(self.output.read_text())["engine"],
                         "SYSTRAN/faster-whisper")
        self.assertEqual(self.output.stat().st_mode&0o777,0o600)

    def test_empty_wrong_or_unaligned_words_fail_without_output(self):
        scenarios=[
          [], [Segment(None)], [Segment([Word("x",1,1)])],
          [Segment([Word("x",1,1.2),Word("y",.1,.3)])],
          [Segment([Word("x",9.8,12)])],
          [Segment([Word("x",None,2)])],
          [Segment([Word("x",1.2,float("nan"))])],
          [Segment([Word("X"*81,0,1)])]
        ]
        for scenario in scenarios:
            with self.subTest(scenario=str(scenario)[:50]):
                self.assertRaises(mod.LocalFasterWhisperError,
                  mod.normalize_actual_words,scenario,audio_duration=10.0)

    def test_model_tamper_unapproved_or_symlink_fails_before_inference(self):
        self.model.joinpath("model.bin").write_bytes(b"changed")
        with self.assertRaises(mod.LocalFasterWhisperError):
            mod.validate_local_model(str(self.model),str(self.manifest))
        self.model.joinpath("model.bin").write_bytes(b"TEST_ONLY_NO_NEURAL_WEIGHTS")
        data=json.loads(self.manifest.read_text())
        data["commercial_rights_reviewed"]=False
        self.manifest.write_text(json.dumps(data))
        with self.assertRaises(mod.LocalFasterWhisperError):
            mod.validate_local_model(str(self.model),str(self.manifest))
        data["commercial_rights_reviewed"]=True
        data["model_revision"]="f"*40
        self.manifest.write_text(json.dumps(data))
        with self.assertRaises(mod.LocalFasterWhisperError):
            mod.validate_local_model(str(self.model),str(self.manifest))
        data["model_revision"]=REVISION
        self.manifest.write_text(json.dumps(data))
        p=self.model/"model.bin"
        p.unlink()
        p.symlink_to(self.wav)
        with self.assertRaises(mod.LocalFasterWhisperError):
            mod.validate_local_model(str(self.model),str(self.manifest))

    def test_model_fail_closed_without_real_installed_dependency(self):
        # Env-dependent: invoke module's actual import, not pretending accuracy.
        with patch.dict(sys.modules,{"faster_whisper":None}):
            with self.assertRaises(mod.LocalFasterWhisperError):
                mod.infer_audio(**self.arguments())
        self.assertFalse(self.output.exists())

    def test_speech_empty_or_missing_word_timing_is_never_green(self):
        class Empty:
            def __init__(self,*args,**kwargs): pass
            def transcribe(self,*args,**kwargs):
                return iter([]),types.SimpleNamespace(language="en")
        with patch.dict(sys.modules,{"faster_whisper":types.SimpleNamespace(
            WhisperModel=Empty)}):
            with self.assertRaises(mod.LocalFasterWhisperError):
                mod.infer_audio(**self.arguments())
        self.assertFalse(self.output.exists())

    def test_original_audio_mutated_during_actual_decode_denied(self):
        source=self.wav
        class MutatingModel:
            def __init__(self,*args,**kwargs): pass
            def transcribe(self,*args,**kwargs):
                source.write_bytes(source.read_bytes()+b"tamper")
                return iter([Segment([Word("sale",0.5,0.9)])]),types.SimpleNamespace(language="en")
        with patch.dict(sys.modules,{
            "faster_whisper":types.SimpleNamespace(WhisperModel=MutatingModel)
        }):
            with self.assertRaisesRegex(mod.LocalFasterWhisperError,
                                        "mutated during CPU inference"):
                mod.infer_audio(**self.arguments())
        self.assertFalse(self.output.exists())

    def test_network_gpu_and_wrong_language_denied(self):
        with patch.dict(os.environ,{"CUDA_VISIBLE_DEVICES":"0"}):
            with self.assertRaises(mod.LocalFasterWhisperError):
                mod.infer_audio(**self.arguments())
        with self.assertRaises(mod.LocalFasterWhisperError):
            mod.infer_audio(**self.arguments(language="fa"))
        with self.assertRaises(mod.LocalFasterWhisperError):
            mod.infer_audio(**self.arguments(threads=100))
        with self.assertRaises(mod.LocalFasterWhisperError):
            mod.infer_audio(**self.arguments(audio_duration=1000))


if __name__=="__main__":
    unittest.main()
