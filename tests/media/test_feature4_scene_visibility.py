"""Real decoded FFmpeg blank-scene detection, negative fixtures and time fences."""
import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_scene_visibility import verify_scene_visibility,VisibilityProofError

SCENES=[{"start":0.0,"duration":5.0},
        {"start":5.0,"duration":5.0},
        {"start":10.0,"duration":5.0}]


class Feature4SceneVisibilityTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="f4-visibility-")
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.path=self.root/"encoded.mp4"

    def source(self, first="red"):
        subprocess.run([
            "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
            "-f","lavfi","-i",f"color=c={first}:s=540x960:r=12:d=5",
            "-f","lavfi","-i","color=c=blue:s=540x960:r=12:d=5",
            "-f","lavfi","-i","color=c=green:s=540x960:r=12:d=5",
            "-f","lavfi","-i","sine=frequency=430:duration=15",
            "-filter_complex","[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]",
            "-map","[v]","-map","3:a:0","-c:v","libx264",
            "-preset","ultrafast","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","48k","-threads","2","-shortest",
            str(self.path),
        ],check=True,capture_output=True,timeout=120)

    def test_three_actual_nonblank_encoded_scenes_pass_not_commercial_approval(self):
        self.source()
        report=verify_scene_visibility(self.path,seconds=15,scenes=SCENES)
        self.assertEqual(report["checked_scene_count"],3)
        self.assertEqual(report["sustained_near_black_count"],0)
        self.assertEqual(report["status"],"SAMPLED_SCENES_NOT_BLANK_NOT_CONTENT_APPROVAL")
        self.assertFalse(report["commercial_release_eligible"])
        self.assertFalse(report["unexpected_overlay_absence_verified"])
        self.assertEqual(len(report["checked_scenes"][0]["samples"]),2)
        self.assertGreater(report["checked_scenes"][0]["samples"][0]["mean_luma"],14)

    def test_actual_encoded_fully_black_scene_is_rejected(self):
        self.source(first="black")
        with self.assertRaisesRegex(VisibilityProofError,"nearly entirely blank"):
            verify_scene_visibility(self.path,seconds=15,scenes=SCENES)

    def test_malicious_scene_ranges_and_wrong_run_duration_rejected(self):
        self.source()
        for windows in (
            SCENES[:2],
            [{**SCENES[0],"duration":6.0},*SCENES[1:]],
            [{**SCENES[0],"start":-0.1},*SCENES[1:]],
            [SCENES[0],{**SCENES[1],"duration":float("nan")},SCENES[2]],
            [{"start":0.0,"duration":15.0,"asset_id":"untrusted"},SCENES[1]],
        ):
            with self.subTest(windows=windows),self.assertRaises(VisibilityProofError):
                verify_scene_visibility(self.path,seconds=15,scenes=windows)
        with self.assertRaisesRegex(VisibilityProofError,"duration"):
            verify_scene_visibility(self.path,seconds=60,scenes=SCENES)

    def test_no_fake_decodable_video_from_garbage_or_symlink(self):
        self.path.write_bytes(b"bad mp4"*2000)
        with self.assertRaises(VisibilityProofError):
            verify_scene_visibility(self.path,seconds=15,scenes=SCENES)
        self.path.unlink()
        safe=self.root/"safe.mp4"
        safe.write_bytes(b"fake"*2000)
        self.path.symlink_to(safe)
        with self.assertRaises(VisibilityProofError):
            verify_scene_visibility(self.path,seconds=15,scenes=SCENES)


if __name__=="__main__":
    unittest.main()
