"""Actual decoded FFmpeg quality evidence, never creative approval."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"/"feature7"))
from decoded_quality_gate import DecodedQualityError,evaluate_decoded_video

@unittest.skipUnless(all(shutil.which(x) for x in ("ffmpeg","ffprobe")),
                     "Real FFmpeg/FFprobe required")
class Feature7DecodedQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix="f7_decoded_qa_")
        cls.root=Path(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def make(self,name,video,audio):
        p=self.root/(name+".mp4")
        ff=subprocess.run([
          "ffmpeg","-hide_banner","-v","error","-nostdin","-y",
          "-f","lavfi","-i",video,
          "-f","lavfi","-i",audio,
          "-t","4","-map","0:v:0","-map","1:a:0",
          "-c:v","libx264","-preset","ultrafast",
          "-pix_fmt","yuv420p","-c:a","aac","-b:a","96k",str(p)],
          capture_output=True,text=True,timeout=50)
        self.assertEqual(ff.returncode,0,ff.stderr[-1200:])
        return p,hashlib.sha256(p.read_bytes()).hexdigest()

    def test_genuine_decoded_shot_and_speech_tone_metrics_review_only(self):
        p,sha=self.make("regular","testsrc2=s=160x288:r=12:d=4",
                        "sine=f=480:d=4")
        report=evaluate_decoded_video(video_path=p,expected_sha256=sha,
                                      expected_duration_seconds=4)
        self.assertTrue(report["real_decoding_performed"])
        self.assertTrue(report["source_bytes_unchanged"])
        self.assertTrue(report["objective_checks_passed"],report)
        self.assertLess(report["audio_peak_dbfs"],-.3)
        self.assertEqual(report["frame_dimensions"],[160,288])
        self.assertLessEqual(report["av_start_skew_seconds"],.12)
        self.assertLessEqual(report["av_end_skew_seconds"],.18)
        for field in ["commercial_quality_accepted","approved",
            "customer_publishable","lip_sync_measured",
            "spoken_word_accuracy_verified","product_or_model_identity_verified"]:
            self.assertFalse(report[field])

    def test_real_four_seconds_black_video_is_not_accepted(self):
        p,sha=self.make("black","color=c=black:s=160x288:r=12:d=4",
                        "sine=f=480:d=4")
        report=evaluate_decoded_video(video_path=p,expected_sha256=sha)
        self.assertIn("EXTENDED_BLACK_VIDEO",report["faults"])
        self.assertFalse(report["objective_checks_passed"])
        self.assertFalse(report["approved"])

    def test_real_silent_audio_is_not_accepted(self):
        p,sha=self.make("silence","testsrc2=s=160x288:r=12:d=4",
                        "anullsrc=r=16000:cl=mono")
        report=evaluate_decoded_video(video_path=p,expected_sha256=sha)
        self.assertFalse(report["objective_checks_passed"])
        self.assertIn("AUDIO_TOO_QUIET_FOR_REVIEW",report["faults"])

    def test_tampered_hash_symlink_missing_and_wrong_duration_denied(self):
        p,sha=self.make("private","testsrc2=s=160x288:r=12:d=4",
                        "sine=f=480:d=4")
        with self.assertRaises(DecodedQualityError):
            evaluate_decoded_video(video_path=p,expected_sha256="0"*64)
        with self.assertRaises(DecodedQualityError):
            evaluate_decoded_video(video_path=p,expected_sha256=sha,
                                   expected_duration_seconds=14)
        link=self.root/"alias.mp4"
        link.symlink_to(p)
        with self.assertRaises(DecodedQualityError):
            evaluate_decoded_video(video_path=link,expected_sha256=sha)
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),sha)

if __name__=="__main__":unittest.main()
