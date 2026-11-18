"""F4-12: caption density warnings are NOT actual visual/voice approval."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-engine"))
from feature4_subtitles import (  # noqa: E402
    SubtitleExportError, caption_readability_flags, export_private_subtitle_pair,
)


class CaptionReadabilityTests(unittest.TestCase):
    def test_concise_reviewed_cue_has_no_heuristic_warning(self):
        cues = [{"start": 1.0, "duration": 3.0, "text": "New arrivals"}]
        self.assertEqual(caption_readability_flags(cues, duration_seconds=15), [])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = export_private_subtitle_pair(
                cues, duration_seconds=15,
                srt_path=root / "captions.srt", vtt_path=root / "captions.vtt")
            self.assertFalse(report["caption_layout_review_required"])
            self.assertEqual(report["caption_layout_risks"], [])
            self.assertFalse(report["encoded_text_legibility_verified_here"])
            self.assertFalse(report["human_visual_approval"])

    def test_fast_three_line_cue_requires_real_visual_review_without_rewriting(self):
        text = "A carefully selected collection of seasonal pieces for every special celebration"
        cues = [{"start": 2.0, "duration": 1.0, "text": text}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = export_private_subtitle_pair(
                cues, duration_seconds=15,
                srt_path=root / "review.srt", vtt_path=root / "review.vtt")
            self.assertTrue(report["caption_layout_review_required"])
            codes = report["caption_layout_risks"][0]["codes"]
            self.assertIn("FAST_CAPTION_OVER_20_CHARS_PER_SECOND", codes)
            self.assertIn("OVER_TWO_MOBILE_LINES", codes)
            self.assertIn(text, (root / "review.srt").read_text())
            self.assertFalse(report["human_visual_approval"])

    def test_unbroken_word_warning_does_not_claim_visual_failure(self):
        cue = [{"start": 0, "duration": 3.0, "text": "a" * 40}]
        self.assertEqual(caption_readability_flags(cue, duration_seconds=15), [
            {"cue_index": 1, "codes": ["UNBROKEN_TOKEN_OVER_36"]}])

    def test_unapproved_or_invalid_cues_are_rejected_before_output(self):
        for cue in ([{"start": 0, "duration": 3, "text": "<unapproved>"}],
                    [{"start": 14.8, "duration": 2, "text": "Beyond Reel"}]):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.assertRaises(SubtitleExportError):
                    export_private_subtitle_pair(cue, duration_seconds=15,
                        srt_path=root / "review.srt", vtt_path=root / "review.vtt")
                self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
