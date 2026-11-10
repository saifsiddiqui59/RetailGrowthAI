"""Feature7 offline preflight tests. Mocked dependency list is TEST-ONLY.

No imported model weights or a synth-only mock can turn this into a real
speech-decoding acceptance. Missing runtime/weights must fail closed.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine" / "feature7"))
from faster_whisper_preflight import (
    preflight_real_cpu_model, assert_offline_cpu_worker)
from faster_whisper_cpu import LocalFasterWhisperError

REV="536b0662742c02347bc0e980a01041f333bce120"


class Feature7OfflineAsrPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="f7-offline-operator-preflight-")
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.model=self.base/"model"
        self.model.mkdir()
        files={}
        for name,contents in (
           ("config.json",b"{}"),
           ("model.bin",b"TEST-ONLY-FAKE-NOT-REAL-WEIGHTS"),
           ("tokenizer.json",b"{}")
        ):
            (self.model/name).write_bytes(contents)
            files[name]=hashlib.sha256(contents).hexdigest()
        self.manifest=self.base/"manifest.json"
        self.manifest.write_text(json.dumps({
            "version":"feature7_faster_whisper_model_manifest_v1",
            "model_project":"Systran/faster-whisper-small",
            "model_revision":REV,"commercial_rights_reviewed":True,
            "files":files
        }))
        env=patch.dict(os.environ,{
          "HF_HUB_OFFLINE":"1","TRANSFORMERS_OFFLINE":"1",
          "CUDA_VISIBLE_DEVICES":"",
          "FEATURE7_GPU_ENABLED":"0",
          "FEATURE7_ALLOW_PAID_INFERENCE":"0",
          "FEATURE7_NETWORK_MODELS":"0"
        })
        env.start()
        self.addCleanup(env.stop)

    def invoke(self,*,pkg="1.2.1",ct="4.6.0",supported=("float32","int8")):
        def version(label):
            if label=="faster-whisper":return pkg
            if label=="ctranslate2":return ct
            raise AssertionError("Unexpected installed distribution")
        with patch("faster_whisper_preflight.metadata.version",
                   side_effect=version),patch.dict(sys.modules,{
                       "ctranslate2":types.SimpleNamespace(
                           get_supported_compute_types=lambda dev:supported)
                   }):
            return preflight_real_cpu_model(
                str(self.model),str(self.manifest))

    def test_operator_source_and_dependency_checks_do_not_claim_asr_accuracy(self):
        # Files/installed versions simulated. A passing contract test cannot
        # prove actual weights, commercial legality, recognition or WER.
        result=self.invoke()
        self.assertTrue(result["offline_cpu_int8_supported"])
        self.assertTrue(result["local_manifest_sha256_verified"])
        self.assertEqual(result["model_revision"],REV)
        self.assertFalse(result["model_weights_actual_inference_executed"])
        self.assertFalse(result["commercial_rights_independently_verified"])
        self.assertFalse(result["word_timing_quality_verified"])
        self.assertFalse(result["customer_publishable"])

    def test_wrong_dependency_and_unapproved_int8_fail_closed(self):
        for data in ({"pkg":"0.0.1"},{"supported":("float32",)}):
            with self.subTest(data=data):
                with self.assertRaises(LocalFasterWhisperError):
                    self.invoke(**data)

    def test_missing_wheels_must_fail_not_mark_cpu_ready(self):
        from importlib.metadata import PackageNotFoundError
        with patch("faster_whisper_preflight.metadata.version",
                   side_effect=PackageNotFoundError("faster-whisper")):
            with self.assertRaises(LocalFasterWhisperError):
                preflight_real_cpu_model(str(self.model),str(self.manifest))

    def test_unapproved_file_revision_and_gpu_network_policy_reject(self):
        self.model.joinpath("model.bin").write_bytes(b"tampered")
        with self.assertRaises(LocalFasterWhisperError):
            self.invoke()
        for k,v in (("CUDA_VISIBLE_DEVICES","0"),
                    ("HF_HUB_OFFLINE","0"),
                    ("FEATURE7_ALLOW_PAID_INFERENCE","1"),
                    ("FEATURE7_NETWORK_MODELS","1")):
            with self.subTest(setting=k),patch.dict(os.environ,{k:v}):
                with self.assertRaises(LocalFasterWhisperError):
                    assert_offline_cpu_worker()


if __name__=="__main__":
    unittest.main()
