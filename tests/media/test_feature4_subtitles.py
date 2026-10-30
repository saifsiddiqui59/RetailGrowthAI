"""SRT/VTT accepted sidecars with exact speech timecodes and no silent editing."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from feature4_subtitles import (
    SubtitleExportError, compose_approved_subtitles, export_private_subtitle_pair,
)

class Feature4SubtitleTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.srt = self.root / "captions.srt"
        self.vtt = self.root / "captions.vtt"
        self.cues = [
            {"start": 0.505, "duration": 1.245, "text": "The autumn edit"},
            {"start": 10.125, "duration": 2.375, "text": "See the garment detail"},
            {"start": 28.500, "duration": 1.500, "text": "Stock example only"},
        ]

    def test_precise_caption_sidecars_preserve_wording_and_timing(self):
        report = export_private_subtitle_pair(
            self.cues, duration_seconds=30, srt_path=self.srt, vtt_path=self.vtt)
        srt, vtt = self.srt.read_text(), self.vtt.read_text()
        self.assertIn("00:00:00,505 --> 00:00:01,750", srt)
        self.assertIn("00:00:10.125 --> 00:00:12.500", vtt)
        self.assertIn("The autumn edit", srt)
        self.assertTrue(vtt.startswith("WEBVTT"))
        self.assertEqual(report["cue_count"], 3)
        self.assertFalse(report["signed_download_ready"])
        self.assertFalse(report["speech_text_alignment_verified_here"])
        self.assertEqual(self.srt.stat().st_mode & 0o777, 0o600)
        with self.assertRaisesRegex(SubtitleExportError, "fresh"):
            export_private_subtitle_pair(
                self.cues, duration_seconds=30, srt_path=self.srt, vtt_path=self.vtt)

    def test_sixty_second_validated_timecodes(self):
        cues = [{"start": 58.750, "duration": 1.250,
                 "text": "Example end card"}]
        srt, vtt = compose_approved_subtitles(cues, duration_seconds=60)
        self.assertIn("00:00:58,750 --> 00:01:00,000", srt)
        self.assertIn("00:00:58.750 --> 00:01:00.000", vtt)

    def test_unicode_scripts_preserved_and_spoofing_controls_rejected(self):
        # Legitimate Arabic/Devanagari scripts need Unicode automatic
        # shaping; ZWJ/ZWNJ used for Indic conjuncts are not stripped.
        good=[
            {"start": 1, "duration": 2, "text": "दीवाली की नई पेशकश"},
            {"start": 4, "duration": 2, "text": "عرض جديد"},
            {"start": 7, "duration": 1, "text": "रक्ष\u200dा"},
        ]
        srt,vtt=compose_approved_subtitles(good,duration_seconds=15)
        for cue in good:
            self.assertIn(cue["text"],srt)
            self.assertIn(cue["text"],vtt)
        for bad in ("SALE\u202eLMTH", "SAVE\u200bNOW", "DEAL\ufeffX",
                    "OFFER\u2066hidden", "SAVE\u00adMORE",
                    "\u0301\u0301", "\u2028hidden"):
            with self.subTest(bad=repr(bad)), self.assertRaises(SubtitleExportError):
                compose_approved_subtitles(
                    [{"start": 0, "duration": 2, "text": bad}],
                    duration_seconds=15)

    def test_invalid_input_or_unreviewed_control_sequences_fail(self):
        for cues in (
            [{"start": 0.505, "duration": 1.245, "text": "Hello --> World"}],
            [{"start": 0.5, "duration": 1, "text": "\ufeffbad"}],
            [{"start": 0.5, "duration": 1.2454, "text": "Sub-ms time"}],
            [{"start": 29.8, "duration": .5, "text": "Out of range"}],
            [self.cues[0], {"start": 1, "duration": 1, "text": "Overlaps"}],
        ):
            with self.assertRaises(SubtitleExportError):
                export_private_subtitle_pair(
                    cues, duration_seconds=30, srt_path=self.srt, vtt_path=self.vtt)
            self.assertFalse(self.srt.exists())
            self.assertFalse(self.vtt.exists())

    def test_exclusive_create_rollback_on_conflicting_second_file(self):
        def second_file_collision(path, flags, mode):
            if str(path) == str(self.vtt):
                raise FileExistsError("racing writer")
            return self.actual_open(path, flags, mode)
        import os
        self.actual_open = os.open
        with patch("feature4_subtitles.os.open", side_effect=second_file_collision):
            with self.assertRaises(SubtitleExportError):
                export_private_subtitle_pair(self.cues, duration_seconds=30,
                                              srt_path=self.srt, vtt_path=self.vtt)
        self.assertFalse(self.srt.exists())
        self.assertFalse(self.vtt.exists())

    def test_symlink_destination_rejected_without_touching_target(self):
        target = self.root / "do_not_change.txt"
        target.write_text("unchanged")
        self.srt.symlink_to(target)
        with self.assertRaises(SubtitleExportError):
            export_private_subtitle_pair(self.cues, duration_seconds=30,
                                          srt_path=self.srt, vtt_path=self.vtt)
        self.assertEqual(target.read_text(), "unchanged")
