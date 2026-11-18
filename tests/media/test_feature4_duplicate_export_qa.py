"""Real decoded duplicate operation evidence, bounded synthetic negatives only."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
import feature4_duplicate_export_qa as qa
from feature4_duplicate_export_qa import (
    DuplicateExportProofError, verify_mock_duplicate_output,
)

PATTERN = [bytes([10])*6912, bytes([55])*6912, bytes([72])*6912,
           bytes([55])*6912, bytes([72])*6912, bytes([121])*6912]
PROFILE = {"width": 540, "height": 960, "seconds": 30.0}


class DuplicateEditorQaTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="f4-dupe-qa-")
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "duplicate.mp4"
        self.path.write_bytes(b"synthetic-h264-aac" * 300)

    def verify(self, samples=None):
        with patch.object(qa, "inspect_mp4", return_value=PROFILE), \
             patch.object(qa, "_center_frame", side_effect=list(
                 PATTERN if samples is None else samples)):
            return verify_mock_duplicate_output(
                self.path, expected_sha256=hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_restarted_source_motion_and_repeated_clip_pass_only_mock_gate(self):
        report = self.verify()
        self.assertEqual(report["video_scene_starts_seconds"], [10, 15])
        self.assertEqual(report["source_video_inpoints_seconds"], [0, 0])
        self.assertEqual(report["sample_times_seconds"], [2., 11.5, 13.5, 16.5, 18.5, 24.])
        self.assertEqual(report["first_duplicate_luma_delta"], 0)
        self.assertGreater(report["minimum_video_temporal_luma_delta"], .5)
        self.assertFalse(report["exact_source_frame_verified"])
        self.assertFalse(report["commercial_release_eligible"])

    def test_wrong_source_inpoint_or_missing_duplicate_rejected(self):
        for frames in (
            [*PATTERN[:3], bytes([66])*6912, bytes([88])*6912, PATTERN[-1]],
            [*PATTERN[:3], PATTERN[0], PATTERN[0], PATTERN[-1]],
            [PATTERN[0], PATTERN[1], PATTERN[1], PATTERN[3], PATTERN[4], PATTERN[-1]],
            [PATTERN[0], PATTERN[1], PATTERN[2], PATTERN[3], PATTERN[4], PATTERN[0]],
        ):
            with self.subTest(failed=frames[3][:1]), self.assertRaises(
                DuplicateExportProofError
            ):
                self.verify(frames)

    def test_forged_digest_rejected_before_ffprobe(self):
        expected = hashlib.sha256(self.path.read_bytes()).hexdigest()
        for digest in (None, True, "", "g"*64, "0"*64, expected.upper()):
            with self.subTest(digest=digest), \
                 patch.object(qa, "inspect_mp4") as probe:
                with self.assertRaisesRegex(
                    DuplicateExportProofError, "SHA"
                ):
                    verify_mock_duplicate_output(self.path, expected_sha256=digest)
                probe.assert_not_called()

    def test_changed_encoded_source_during_decode_rejected(self):
        original = list(PATTERN)

        def mutate(_file, sec):
            if sec == 16.5:
                with self.path.open("ab") as video:
                    video.write(b"replaced-source")
            return original.pop(0)

        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with patch.object(qa, "inspect_mp4", return_value=PROFILE), \
             patch.object(qa, "_center_frame", side_effect=mutate):
            with self.assertRaisesRegex(DuplicateExportProofError, "changed"):
                verify_mock_duplicate_output(self.path, expected_sha256=digest)

    def test_wrong_duration_and_symlink_denied(self):
        wrong = {**PROFILE, "seconds": 24}
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with patch.object(qa, "inspect_mp4", return_value=wrong):
            with self.assertRaisesRegex(DuplicateExportProofError, "30s"):
                verify_mock_duplicate_output(self.path, expected_sha256=digest)
        real = self.path.with_name("real.mp4")
        self.path.rename(real)
        self.path.symlink_to(real)
        with self.assertRaises(DuplicateExportProofError):
            verify_mock_duplicate_output(self.path, expected_sha256=digest)


if __name__ == "__main__":
    unittest.main()
