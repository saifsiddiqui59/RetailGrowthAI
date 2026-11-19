"""Optional genuinely decoded Faster-Whisper CPU acceptance, NEVER a mock.

Set all five FEATURE7_ASR_* env vars only on an authorized private runner
with approved model checkpoint and independently recorded reference speech.
Ordinary public CI skips this test and MUST NOT claim model accuracy.
"""
import hashlib
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"/"feature7"))
from faster_whisper_benchmark import benchmark

REQUIRED=(
  "FEATURE7_ASR_MODEL_DIR",
  "FEATURE7_ASR_MODEL_MANIFEST",
  "FEATURE7_ASR_REAL_WAV",
  "FEATURE7_ASR_HUMAN_REFERENCE",
  "FEATURE7_ASR_WAV_DURATION"
)


@unittest.skipUnless(all(os.environ.get(key) for key in REQUIRED),
                     "Real approved CPU model and human speech not provisioned")
class Feature7FasterWhisperLiveAcceptance(unittest.TestCase):
    def test_actual_upstream_model_decodes_private_recording_and_reports_wer(self):
        wav=Path(os.environ["FEATURE7_ASR_REAL_WAV"])
        ref=Path(os.environ["FEATURE7_ASR_HUMAN_REFERENCE"])
        self.assertTrue(wav.is_file() and ref.is_file())
        with self.subTest("actual_CPU_inference"):
            data=benchmark(
              wav_path=str(wav),
              expected_sha256=hashlib.sha256(wav.read_bytes()).hexdigest(),
              model_dir=os.environ["FEATURE7_ASR_MODEL_DIR"],
              manifest_path=os.environ["FEATURE7_ASR_MODEL_MANIFEST"],
              reference_path=str(ref),
              reference_sha256=hashlib.sha256(ref.read_bytes()).hexdigest(),
              audio_duration=float(os.environ["FEATURE7_ASR_WAV_DURATION"]),
              language=os.environ.get("FEATURE7_ASR_LANGUAGE","en"))
            self.assertTrue(data["actual_cpu_model_inference_executed"])
            self.assertFalse(data["customer_quality_accepted"])
            self.assertFalse(data["word_timing_accuracy_independently_measured"])
            self.assertFalse(data["approved"])
            self.assertGreater(data["reference_word_count"],9)
            # This is ONE sample benchmark. Multi-accent release qualification
            # MUST remain separate, even with a passing single-sample WER.
            self.assertTrue(
                data["engineering_target_wer_at_most_0_20_met"],
                "Real model WER failed 20% acceptance target")


if __name__=="__main__":
    unittest.main()
