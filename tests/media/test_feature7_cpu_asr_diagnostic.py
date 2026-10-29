"""CPU-only native PocketSphinx diagnostic: release gate, not production ASR."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"/"feature7"))
from offline_pocketsphinx_diagnostic import (
    CpuAsrBenchmarkError, benchmark_local_pocketsphinx, word_error_rate)

class NativeCpuAsrDiagnosticTests(unittest.TestCase):
    def test_human_reference_word_error_is_measured_not_assumed(self):
        same=word_error_rate("Fashion shirts are here",
                             "Fashion shirts are here")
        self.assertEqual(same["word_error_rate"],0)
        self.assertEqual(same["reference_words"],4)
        wrong=word_error_rate("Fashion shirts are here",
                              "Fashion coats available now")
        self.assertEqual(wrong["word_error_rate"],.75)
        self.assertEqual(wrong["word_edits"],3)

    def test_invalid_reference_or_unverified_media_fails_before_native_decoder(self):
        with self.assertRaises(CpuAsrBenchmarkError):
            word_error_rate("", "hallucinated words")
        with self.assertRaises(CpuAsrBenchmarkError):
            word_error_rate("source", "")
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"private.mp4"
            source.write_bytes(b"0"*6000)
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            with self.assertRaises(CpuAsrBenchmarkError):
                benchmark_local_pocketsphinx(video_path=source,
                    expected_sha256="a"*64,
                    human_reference_text="A human reference")
            with self.assertRaises(CpuAsrBenchmarkError):
                benchmark_local_pocketsphinx(video_path=source,
                    expected_sha256=sha,human_reference_text="")

if __name__=="__main__":
    unittest.main()
