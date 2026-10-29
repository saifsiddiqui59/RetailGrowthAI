"""Actual encoded Feature4 SRT burn-in; fixture is original test footage, not speech."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from feature4_subtitles import export_private_subtitle_pair
from feature4_private_preview import inspect_mp4
import feature4_subtitle_burnin as burn


class Feature4SubtitleBurnTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="f4-burn-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.source = self.root / "source.mp4"
        self.output = self.root / "captioned.mp4"
        self.srt = self.root / "approved.srt"
        self.vtt = self.root / "approved.vtt"
        self.cues = [{"start": 2.0, "duration": 3.0,
                      "text": "New arrivals tonight"}]

    def source_fixture(self):
        subprocess.run([
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=black:s=540x960:r=24:d=15",
            "-f", "lavfi", "-i", "sine=frequency=375:sample_rate=48000:duration=15",
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "64k", "-shortest", "-threads", "2",
            str(self.source),
        ], check=True, capture_output=True, timeout=90)
        self.source.chmod(0o600)

    def approved_track(self):
        export_private_subtitle_pair(self.cues, duration_seconds=15,
                                     srt_path=self.srt, vtt_path=self.vtt)

    def frame_bottom(self, seconds):
        proc = subprocess.run([
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-ss", str(seconds), "-i", str(self.output),
            "-frames:v", "1", "-vf",
            "crop=540:300:0:660,scale=90:50,format=gray",
            "-f", "rawvideo", "-",
        ], check=True, capture_output=True, timeout=40)
        self.assertEqual(len(proc.stdout), 90 * 50)
        return proc.stdout

    def test_real_caption_pixels_only_in_reviewed_interval(self):
        self.source_fixture()
        self.approved_track()
        src = self.source.read_bytes()
        proof = burn.burn_reviewed_subtitles(
            self.source, self.srt, self.output, cues=self.cues,
            expected_seconds=15)
        self.assertEqual(self.source.read_bytes(), src)
        self.assertEqual(proof["status"], "PRIVATE_ENCODED_SUBTITLES_NOT_PUBLISHED")
        self.assertTrue(proof["actual_encoded_subtitle_filter_executed"])
        self.assertFalse(proof["spoken_word_alignment_verified"])
        self.assertFalse(proof["commercial_release_eligible"])
        self.assertFalse(proof["signed_download_ready"])
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
        self.assertEqual((inspect_mp4(self.output, max_size=80*1024*1024)["width"],
                          inspect_mp4(self.output, max_size=80*1024*1024)["height"]),
                         (540, 960))
        during = self.frame_bottom(3)
        outside = self.frame_bottom(9)
        # Genuine libass rendered white caption glyphs against black original.
        self.assertGreater(sum(during) / len(during),
                           sum(outside) / len(outside) + 2.0)
        with self.assertRaisesRegex(burn.SubtitleBurnError, "fresh"):
            burn.burn_reviewed_subtitles(
                self.source, self.srt, self.output,
                cues=self.cues, expected_seconds=15)

    def test_unreviewed_caption_bytes_are_rejected(self):
        self.source_fixture()
        self.approved_track()
        self.srt.write_text("1\n00:00:02,000 --> 00:00:05,000\nBUY NOW!!!\n")
        with self.assertRaisesRegex(burn.SubtitleBurnError, "differ"):
            burn.burn_reviewed_subtitles(
                self.source, self.srt, self.output,
                cues=self.cues, expected_seconds=15)
        self.assertFalse(self.output.exists())

    def test_escape_filename_nonprivate_directory_and_invalid_duration_rejected(self):
        self.source_fixture()
        self.approved_track()
        unsafe = self.root / "captions:force_style=FontName=bad.srt"
        unsafe.write_bytes(self.srt.read_bytes())
        unsafe.chmod(0o600)
        with self.assertRaisesRegex(burn.SubtitleBurnError, "Unsafe"):
            burn.burn_reviewed_subtitles(
                self.source, unsafe, self.output,
                cues=self.cues, expected_seconds=15)
        self.root.chmod(0o755)
        with self.assertRaisesRegex(burn.SubtitleBurnError, "nonprivate"):
            burn.burn_reviewed_subtitles(
                self.source, self.srt, self.output,
                cues=self.cues, expected_seconds=15)
        self.root.chmod(0o700)
        with self.assertRaisesRegex(burn.SubtitleBurnError, "15/30/60"):
            burn.burn_reviewed_subtitles(
                self.source, self.srt, self.output,
                cues=self.cues, expected_seconds=12)
        self.assertFalse(self.output.exists())

    def test_mutation_after_encode_fails_closed_and_cleans_temporary_mp4(self):
        self.source_fixture()
        self.approved_track()
        actual = burn._ffmpeg
        def mutate_after_render(args, **kwargs):
            actual(args, **kwargs)
            with self.source.open("ab") as stream:
                stream.write(b"changed-on-disk-after-encode")
        with patch.object(burn, "_ffmpeg", side_effect=mutate_after_render):
            with self.assertRaisesRegex(burn.SubtitleBurnError, "changed"):
                burn.burn_reviewed_subtitles(
                    self.source, self.srt, self.output,
                    cues=self.cues, expected_seconds=15)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".subtitle-burn-*.mp4")), [])


if __name__ == "__main__":
    unittest.main()
