"""Real FFmpeg media integration checks (synthetic images, NOT Hunyuan inference).

Generates and probes genuine H.264 MP4 bytes on CI hosts with FFmpeg. These
checks verify the machine-readable handoff profile but NOT fashion/visual QA
or Feature4's separate unmerged rendering implementation.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from feature5_motion.contracts import MotionError
from feature5_motion.worker import validate_clip


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and ffprobe executable binaries are required")
class TestFeature5RealFFmpegMedia(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="feature5-machine-media-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def make_clip(self, name: str, *, fps: int = 24, seconds: int = 5) -> Path:
        target = self.root / name
        cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
               "-f", "lavfi", "-i", f"color=c=navy:s=480x832:r={fps}",
               "-t", str(seconds), "-c:v", "libx264", "-preset", "ultrafast",
               "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart",
               "-y", str(target)]
        proc = subprocess.run(cmd, capture_output=True, timeout=45)
        if proc.returncode != 0:
            self.fail("Expected CI FFmpeg binary with H.264 libx264 encoder")
        self.assertGreater(target.stat().st_size, 1024)
        return target

    def test_genuine_five_second_clip_meets_private_motion_profile(self):
        actual = self.make_clip("genuine-synthetic.mp4")
        result = validate_clip(actual)
        self.assertEqual((result["width"], result["height"]), (480, 832))
        self.assertEqual(result["codec"], "h264")
        self.assertEqual(result["fps"], 24)
        self.assertGreater(result["bytes"], 1024)
        self.assertTrue(4.5 <= result["duration_seconds"] <= 5.5)

    def test_real_wrong_fps_and_duration_fail_closed(self):
        bad_fps = self.make_clip("fps-30.mp4", fps=30)
        with self.assertRaises(MotionError):
            validate_clip(bad_fps)
        bad_length = self.make_clip("short-4-seconds.mp4", seconds=4)
        with self.assertRaises(MotionError):
            validate_clip(bad_length)


if __name__ == "__main__":
    unittest.main()
