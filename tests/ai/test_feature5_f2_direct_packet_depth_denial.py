"""F5-02: direct Python bridge must deny ambiguous/deep editorial objects.

These are synthetic offline contract fixtures, not actual F2 Node exporter
stdout, approved private garment media, or a Wan model/GPU run.
"""
from __future__ import annotations

import copy
import unittest

from feature5_motion.feature2_storyboard_bridge import qualify_feature2_offline_storyboard
from feature5_motion.wan22_motion_adapter import WanCompatibilityError
from test_feature5_feature2_storyboard_bridge import make_packet


class Feature2DirectPacketDepthDenialTests(unittest.TestCase):
    def test_normal_fixture_is_still_source_only(self):
        for duration in (15, 30, 60):
            with self.subTest(duration=duration):
                receipt = qualify_feature2_offline_storyboard(make_packet(duration))
                self.assertEqual(receipt["duration_seconds"], duration)
                self.assertIs(receipt["can_submit_provider"], False)
                self.assertIs(receipt["can_publish"], False)

    def test_deep_extra_metadata_is_rejected_without_recursion_escape(self):
        # A Python caller can bypass the CLI's bounded JSON parser. The
        # top-level packet is otherwise structurally valid; digesting the
        # untrusted extra field must never leak RecursionError.
        packet = make_packet(15)
        nested = []
        root = nested
        for _ in range(1600):
            child = []
            nested.append(child)
            nested = child
        packet["extra_editorial_metadata"] = root
        with self.assertRaises(WanCompatibilityError):
            qualify_feature2_offline_storyboard(packet)

    def test_cyclic_extra_metadata_is_rejected(self):
        packet = make_packet(15)
        extra = {}
        extra["self"] = extra
        packet["extra_editorial_metadata"] = extra
        with self.assertRaises(WanCompatibilityError):
            qualify_feature2_offline_storyboard(packet)

    def test_nonfinite_extra_metadata_is_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=str(value)):
                packet = make_packet(15)
                packet["extra_editorial_metadata"] = {"unsafe": value}
                with self.assertRaises(WanCompatibilityError):
                    qualify_feature2_offline_storyboard(packet)


if __name__ == "__main__":
    unittest.main()
