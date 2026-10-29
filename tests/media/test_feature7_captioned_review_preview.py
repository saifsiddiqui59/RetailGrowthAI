"""Actual FFmpeg visible-caption QA; NO SaaS publish or real CPU ASR claim."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine" / "feature7"))
from captioned_review_preview import (
    CaptionPreviewError, render_captioned_review_preview)

def projection():
    return {
        "version": "feature7_autoclip_autobroll_caption_projection_v1",
        "shop_id": "fixture-shop", "asset_id": "verified-clip",
        "approved": False, "renderable": False,
        "human_review_required": True,
        "actual_timeline_duration_ms": 4000,
        "feature4_caption_track": [
            {"start": .5, "duration": .8, "text": "Welcome to our store"},
            {"start": 2, "duration": 1, "text": "Browse our latest collection"}
        ]
    }

@unittest.skipUnless(all(shutil.which(p) for p in
                          ("ffmpeg", "ffprobe")), "Real FFmpeg required")
class CaptionedReviewPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="feature7_caption_qa_")
        cls.home = Path(cls.temp.name)
        cls.source = cls.home / "previously_edited_autoclip.mp4"
        call = subprocess.run([
            "ffmpeg", "-hide_banner", "-v", "error", "-nostdin", "-y",
            "-f", "lavfi", "-i", "testsrc2=s=320x568:r=15:d=4",
            "-f", "lavfi", "-i", "sine=frequency=560:duration=4",
            "-t", "4", "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "64k", "-pix_fmt", "yuv420p",
            str(cls.source)
        ], capture_output=True, text=True, timeout=50)
        if call.returncode:
            cls.temp.cleanup()
            raise RuntimeError(call.stderr[-1000:])
        cls.sha = hashlib.sha256(cls.source.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def render(self, dest, captions=None, digest=None):
        return render_captioned_review_preview(
            source_path=self.source,
            source_sha256=self.sha if digest is None else digest,
            caption_projection=projection() if captions is None else captions,
            output_path=dest)

    def frame(self, video, second):
        return subprocess.run([
            "ffmpeg", "-hide_banner", "-v", "error", "-nostdin",
            "-ss", str(second), "-i", str(video), "-frames:v", "1",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"
        ], capture_output=True, timeout=20, check=True).stdout

    def test_real_caption_burn_in_copies_original_aac_packets_unchanged(self):
        dest = self.home / "with_visible_captions.mp4"
        result = self.render(dest)
        self.assertTrue(dest.exists())
        self.assertTrue(result["output_aac_packets_identical"])
        self.assertTrue(result["visible_captions_in_preview"])
        self.assertTrue(result["review_only"])
        self.assertFalse(result["approved"])
        self.assertFalse(result["professional_quality_accepted"])
        self.assertFalse(result["real_asr_inference_proven"])
        self.assertEqual(result["caption_count"], 2)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),
                         self.sha)
        self.assertGreater(dest.stat().st_size, 10000)
        self.assertNotEqual(self.frame(self.source, .95),
                            self.frame(dest, .95))
        # Not permitted to overwrite an approved/earlier video.
        with self.assertRaises(CaptionPreviewError):
            self.render(dest)

    def test_unsafe_foreign_or_unaligned_caption_denied_without_output(self):
        cases = [
            (lambda p: p.update(shop_id="../foreign"), "tenant"),
            (lambda p: p.update(approved=True), "self approval"),
            (lambda p: p.update(renderable=True), "renderable"),
            (lambda p: p.update(actual_timeline_duration_ms=10000),
             "wrong timeline"),
            (lambda p: p["feature4_caption_track"][0].update(
                text="<font color='red'>attack</font>"), "SRT markup"),
            (lambda p: p["feature4_caption_track"][0].update(
                text="hello\nworld"), "caption injection"),
            (lambda p: p["feature4_caption_track"][1].update(
                start=.7), "overlap"),
            (lambda p: p["feature4_caption_track"][0].update(
                duration=6.0), "out of source"),
            (lambda p: p["feature4_caption_track"].clear(),
             "missing captions")
        ]
        for index, (change, description) in enumerate(cases):
            with self.subTest(description=description):
                data = projection()
                change(data)
                dest = self.home / f"blocked_{index}.mp4"
                with self.assertRaises(CaptionPreviewError):
                    self.render(dest, captions=data)
                self.assertFalse(dest.exists())

    def test_source_tamper_and_symlink_denied(self):
        with self.assertRaises(CaptionPreviewError):
            self.render(self.home / "changed.mp4", digest="f" * 64)
        link = self.home / "symlink.mp4"
        link.symlink_to(self.source)
        with self.assertRaises(CaptionPreviewError):
            render_captioned_review_preview(
                source_path=link, source_sha256=self.sha,
                caption_projection=projection(),
                output_path=self.home / "unsafe.mp4")
        self.assertFalse((self.home / "unsafe.mp4").exists())

if __name__ == "__main__":
    unittest.main()
