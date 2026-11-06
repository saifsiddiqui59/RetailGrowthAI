"""Actual FFmpeg test for private small preview; no owner-release or hosted claims."""
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from feature4_private_preview import (
    PreviewExportError, export_private_preview, inspect_mp4,
)

class Feature4PreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rgai-preview-unit-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.mp4"
        self.output = self.root / "preview.mp4"

    def make_source(self, *, seconds=15, size="540x960", codec="libx264"):
        # Genuine video/audio encode, synthetic moving frames only, no borrowed clips.
        subprocess.run([
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=12:duration={seconds}",
            "-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=32000:duration={seconds}",
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", codec,
            "-preset", "ultrafast", "-crf", "32", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "48k", "-shortest", "-threads", "2",
            str(self.source),
        ], check=True, capture_output=True, timeout=90)

    def test_actual_video_preview_is_small_private_and_original_immutable(self):
        self.make_source()
        original = self.source.read_bytes()
        report = export_private_preview(self.source, self.output, expected_seconds=15)
        self.assertTrue(self.output.is_file())
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(report["status"], "PRIVATE_PREVIEW_ENCODED_NOT_PUBLISHED")
        self.assertFalse(report["signed_download_ready"])
        self.assertFalse(report["commercial_release_eligible"])
        self.assertFalse(report["retailer_media_authorization_checked_here"])
        self.assertLess(report["preview_bytes"], report["source_bytes"])
        metadata = inspect_mp4(self.output, max_size=8 * 1024 * 1024)
        self.assertEqual((metadata["width"], metadata["height"]), (540, 960))
        self.assertAlmostEqual(metadata["seconds"], 15, delta=.45)
        with self.assertRaisesRegex(PreviewExportError, "fresh"):
            export_private_preview(self.source, self.output, expected_seconds=15)

    def test_concurrent_destination_race_does_not_replace_existing_preview(self):
        self.make_source()
        def raced_link(src,dst):
            Path(dst).write_bytes(b"another-render-owner")
            raise FileExistsError("already exists")
        with mock.patch("feature4_private_preview.os.link",side_effect=raced_link):
            with self.assertRaisesRegex(PreviewExportError,"Unable to encode"):
                export_private_preview(self.source,self.output,expected_seconds=15)
        self.assertEqual(self.output.read_bytes(),b"another-render-owner")
        self.assertEqual(list(self.root.glob(".preview-*.mp4")),[])

    def test_source_mutation_during_encode_cannot_publish_wrong_provenance(self):
        self.make_source()
        original_run = subprocess.run
        changed = False
        def mutate_after_encode(args, **kwargs):
            nonlocal changed
            result = original_run(args, **kwargs)
            if not changed and args[0] == "ffmpeg" and "-movflags" in args:
                with self.source.open("ab") as source:
                    source.write(b"concurrent-authorized-source-revision")
                changed = True
            return result
        with mock.patch("feature4_private_preview.subprocess.run", side_effect=mutate_after_encode):
            with self.assertRaisesRegex(PreviewExportError, "changed"):
                export_private_preview(self.source, self.output, expected_seconds=15)
        self.assertTrue(changed)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".preview-*.mp4")), [])

    def test_wrong_duration_and_bad_preset_denied(self):
        self.make_source()
        with self.assertRaisesRegex(PreviewExportError, "duration"):
            export_private_preview(self.source, self.output, expected_seconds=60)
        with self.assertRaisesRegex(PreviewExportError, "15/30/60"):
            export_private_preview(self.source, self.output, expected_seconds=12)

    def test_symlink_input_and_cross_aspect_denied(self):
        self.make_source()
        link = self.root / "untrusted.mp4"
        link.symlink_to(self.source)
        with self.assertRaisesRegex(PreviewExportError, "unsafe"):
            export_private_preview(link, self.output, expected_seconds=15)
        self.source.unlink()
        self.make_source(size="640x360")
        with self.assertRaisesRegex(PreviewExportError, "aspect"):
            export_private_preview(self.source, self.output, expected_seconds=15)

    def test_partial_or_garbage_media_cannot_be_published(self):
        self.source.write_bytes(b"not a video" * 1000)
        with self.assertRaises(PreviewExportError):
            export_private_preview(self.source, self.output, expected_seconds=15)
        self.assertFalse(self.output.exists())

if __name__ == "__main__":
    unittest.main()
