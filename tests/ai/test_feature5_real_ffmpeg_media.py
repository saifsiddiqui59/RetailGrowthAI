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
from feature5_motion.visual_review_artifacts import prepare_visual_review, TIMESTAMPS
from feature5_motion.acceptance import export_pending_review


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

    def test_real_mp4_produces_six_review_frames_and_immutable_hash(self):
        from hashlib import sha256
        from PIL import Image
        clip = self.make_clip("review-clip.mp4")
        destination = self.root / "review"
        result = prepare_visual_review(clip, destination)
        self.assertEqual(result["status"], "PENDING_HUMAN_REVIEW")
        self.assertEqual(len(result["frames"]), len(TIMESTAMPS))
        self.assertEqual(result["clip_sha256"], sha256(clip.read_bytes()).hexdigest())
        self.assertEqual(len(result["clip_sha256"]), 64)
        self.assertTrue((destination / "review-manifest.json").is_file())
        for frame in result["frames"]:
            self.assertTrue((destination / frame["file"]).is_file())
            self.assertEqual(len(frame["sha256"]), 64)
        with Image.open(destination / "contact-sheet.png") as sheet:
            self.assertEqual(sheet.size, (750, 954))
        with self.assertRaises(MotionError):
            prepare_visual_review(clip, destination)

    def test_reviewer_materials_fail_closed_for_bad_duration(self):
        clip = self.make_clip("not-reviewable.mp4", seconds=4)
        output = self.root / "reject-review"
        with self.assertRaises(MotionError):
            prepare_visual_review(clip, output)
        self.assertFalse(output.exists())

    def test_real_synthetic_clip_preserved_as_pending_private_human_review(self):
        import hashlib
        clip = self.make_clip("export-test.mp4")
        root = self.root / "private-review-evidence"
        record = export_pending_review(
            clip, root, mode="text", approved_model_manifest_sha256="b" * 64,
        )
        self.assertEqual(record["status"], "PENDING_HUMAN_REVIEW")
        self.assertIsNone(record["reference_sha256"])
        self.assertEqual(record["clip_sha256"], hashlib.sha256(clip.read_bytes()).hexdigest())
        self.assertTrue((root / "clip.mp4").is_file())
        self.assertTrue((root / "review" / "contact-sheet.png").is_file())
        self.assertTrue((root / "acceptance-pending.json").is_file())
        with self.assertRaises(MotionError):
            export_pending_review(clip, root, mode="text",
                                  approved_model_manifest_sha256="b" * 64)

    def test_real_image_reference_export_is_private_and_reviewable(self):
        import hashlib
        from PIL import Image
        clip = self.make_clip("i2v-synthetic.mp4")
        reference = self.root / "fashion-source.png"
        Image.new("RGB", (480, 832), color="red").save(reference)
        evidence = self.root / "i2v-evidence"
        record = export_pending_review(
            clip, evidence, mode="image", source_image=reference,
            approved_model_manifest_sha256="b" * 64)
        self.assertEqual(record["reference_sha256"],
                         hashlib.sha256(reference.read_bytes()).hexdigest())
        self.assertTrue((evidence / "reference.png").is_file())
        self.assertEqual(validate_clip(evidence / "clip.mp4")["fps"], 24)
        self.assertEqual(record["status"], "PENDING_HUMAN_REVIEW")

    def test_real_wrong_fps_and_duration_fail_closed(self):
        bad_fps = self.make_clip("fps-30.mp4", fps=30)
        with self.assertRaises(MotionError):
            validate_clip(bad_fps)
        bad_length = self.make_clip("short-4-seconds.mp4", seconds=4)
        with self.assertRaises(MotionError):
            validate_clip(bad_length)


if __name__ == "__main__":
    unittest.main()
