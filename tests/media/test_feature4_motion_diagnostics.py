"""CPU motion checks are a lower bound, NEVER commercial human approval."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_motion_diagnostics import inspect_staged_motion, MotionProbeError


class MotionDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.path=Path(cls.temp.name)
        for name,src in (("static","color=c=darkblue:s=180x320:r=12:d=3"),
                         ("moving","testsrc2=size=180x320:rate=12:duration=3")):
            subprocess.run(["ffmpeg","-nostdin","-v","error","-y",
                            "-f","lavfi","-i",src,"-c:v","libx264",
                            "-preset","ultrafast","-pix_fmt","yuv420p",
                            str(cls.path/(name+".mp4"))],timeout=45,check=True)
    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_frozen_source_is_not_accepted_as_motion(self):
        s=inspect_staged_motion(self.path/"static.mp4")
        self.assertEqual(s["frame_freeze_check"],"FAILED_FROZEN_OR_LOW_MOTION")
        self.assertFalse(s["visible_temporal_change"])
        self.assertFalse(s["commercial_quality_approved"])
        self.assertFalse(s["photoreal_human_verified"])

    def test_real_temporal_pixel_change_does_not_certify_human_or_garment(self):
        s=inspect_staged_motion(self.path/"moving.mp4")
        self.assertEqual(s["samples"],6)
        self.assertTrue(s["visible_temporal_change"])
        self.assertEqual(s["frame_freeze_check"],"PASS")
        self.assertGreater(s["mean_frame_delta"],1.2)
        self.assertFalse(s["garment_identity_verified"])
        self.assertFalse(s["commercial_quality_approved"])

    def test_rejects_nonlocal_and_invalid_media(self):
        for v in ("https://example.org/test.mp4",self.path/"missing.mp4",self.path/"x.txt"):
            with self.subTest(v=str(v)),self.assertRaises(MotionProbeError):
                inspect_staged_motion(v)

if __name__=="__main__":unittest.main()
