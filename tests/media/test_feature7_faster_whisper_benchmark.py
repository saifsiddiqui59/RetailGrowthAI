"""Accuracy benchmark correctness and fail-closed reference provenance, no model fake."""
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"/"feature7"))
from faster_whisper_benchmark import word_error_rate,tokens,benchmark
from faster_whisper_cpu import LocalFasterWhisperError


class Feature7HumanReferenceWERTests(unittest.TestCase):
    def test_exact_words_and_normalized_punctuation(self):
        good=word_error_rate("Our Diwali clothes are here!",
                            "Our Diwali clothes are here.")
        self.assertEqual(good["word_error_rate"],0)
        self.assertEqual(good["reference_word_count"],5)

    def test_insertion_deletion_substitution_penalized(self):
        a=word_error_rate("Our red Diwali clothes have arrived",
                          "Our blue Diwali clothes arrived today")
        self.assertEqual(a["reference_word_count"],6)
        self.assertEqual(a["word_edit_distance"],3)
        self.assertEqual(a["word_error_rate"],.5)

    def test_hindi_unicode_reference_not_silently_dropped(self):
        sample=tokens("दीवाली पर नई साड़ी आई है")
        self.assertGreater(len(sample),0)
        self.assertEqual(word_error_rate("नमस्ते भारत", "नमस्ते भारत")[
            "word_error_rate"],0)

    def test_missing_reference_and_wrong_file_hash_denied(self):
        with self.assertRaises(LocalFasterWhisperError):
            word_error_rate("","a guessed sentence")
        with tempfile.TemporaryDirectory(prefix="f7-asr-reference-") as base:
            p=Path(base)
            wav=p/"private.wav";wav.write_bytes(b"RIFF"*30)
            ref=p/"independent.txt"
            ref.write_text("Our new clothing collection arrived",
                           encoding="utf-8")
            with self.assertRaises(LocalFasterWhisperError):
                benchmark(wav_path=str(wav),expected_sha256="0"*64,
                  model_dir=str(p),manifest_path=str(p/"manifest.json"),
                  reference_path=str(ref),
                  reference_sha256=hashlib.sha256(ref.read_bytes()).hexdigest(),
                  audio_duration=1.0)

    def test_reference_hash_tampering_denied_before_inference(self):
        with tempfile.TemporaryDirectory(prefix="f7-asr-reference-") as base:
            p=Path(base)
            wav=p/"private.wav";wav.write_bytes(b"RIFF"*30)
            ref=p/"independent.txt";ref.write_text("Reference")
            with self.assertRaises(LocalFasterWhisperError):
                benchmark(wav_path=str(wav),
                  expected_sha256=hashlib.sha256(wav.read_bytes()).hexdigest(),
                  model_dir=str(p),manifest_path=str(p/"manifest.json"),
                  reference_path=str(ref),reference_sha256="f"*64,
                  audio_duration=2.0)


if __name__=="__main__":
    unittest.main()
