"""Feature #4 F4-02: no positive 60s visibility receipt for gapped/overlapping time."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from feature4_minute_quality_receipt import (
    MinuteProofError, validate_visibility_evidence,
)

FRACTIONS = [.15, .30, .50, .70, .85]
SOURCE_SHA = "a" * 64


def fixture():
    windows = [{"start": 5 * i, "duration": 5} for i in range(12)]
    scenes = []
    for window in windows:
        scenes.append({
            "scene_start": window["start"],
            "duration": window["duration"],
            "sustained_near_black": False,
            "samples": [
                {"time_seconds": round(window["start"] + fraction * window["duration"], 3),
                 "mean_luma": 75.0, "near_black_fraction": 0.0}
                for fraction in FRACTIONS
            ],
        })
    provenance = {"scene_windows": windows}
    proof = {
        "schema": "feature4_scene_visibility_v2",
        "status": "SAMPLED_SCENES_NOT_BLANK_NOT_CONTENT_APPROVAL",
        "source_sha256": SOURCE_SHA,
        "seconds": 60,
        "checked_scene_count": 12,
        "sample_fractions": FRACTIONS,
        "short_blank_frames_excluded_by_sampling": False,
        "sustained_near_black_count": 0,
        "commercial_release_eligible": False,
        "garment_identity_verified": False,
        "unexpected_overlay_absence_verified": False,
        "checked_scenes": scenes,
    }
    return provenance, proof


class VisibilityWindowIntegrityTests(unittest.TestCase):
    def check(self, provenance, proof):
        with patch("feature4_minute_quality_receipt._record", side_effect=[provenance, proof]), \
             patch("feature4_minute_quality_receipt._sha", return_value=SOURCE_SHA):
            return validate_visibility_evidence(
                original=Path("private-stock-fixture.mp4"),
                provenance=Path("private-provenance.json"),
                visibility_proof=Path("private-visibility.json"),
            )

    def test_valid_contiguous_minute_is_technical_only(self):
        provenance, proof = fixture()
        result = self.check(provenance, proof)
        self.assertEqual(result["checked_scene_count"], 12)
        self.assertIs(result["commercial_release_eligible"], False)

    def test_both_matching_json_timelines_cannot_skip_or_repeat_time(self):
        for altered_start in (24.5, 25.5):
            with self.subTest(altered_start=altered_start):
                provenance, proof = fixture()
                provenance["scene_windows"][5]["start"] = altered_start
                proof["checked_scenes"][5]["scene_start"] = altered_start
                proof["checked_scenes"][5]["samples"] = [
                    {"time_seconds": round(altered_start + fraction * 5, 3),
                     "mean_luma": 75.0, "near_black_fraction": 0.0}
                    for fraction in FRACTIONS
                ]
                with self.assertRaisesRegex(MinuteProofError, "not contiguous"):
                    self.check(provenance, proof)

    def test_full_minute_and_finite_positive_windows_required(self):
        for bad_duration in (0, -5, float("nan"), float("inf"), 4):
            with self.subTest(bad_duration=bad_duration):
                provenance, proof = fixture()
                provenance["scene_windows"][-1]["duration"] = bad_duration
                proof["checked_scenes"][-1]["duration"] = bad_duration
                with self.assertRaisesRegex(
                    MinuteProofError, "not contiguous|full minute"
                ):
                    self.check(provenance, proof)

    def test_window_shape_must_be_exact(self):
        provenance, proof = fixture()
        provenance["scene_windows"][0]["approval"] = True
        with self.assertRaisesRegex(MinuteProofError, "not contiguous"):
            self.check(provenance, proof)


if __name__ == "__main__":
    unittest.main()
