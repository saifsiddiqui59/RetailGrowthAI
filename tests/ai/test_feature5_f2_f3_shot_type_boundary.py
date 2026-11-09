"""GPU-OFF negative tests for strict Feature2 shot types in the Feature3 handoff.

All media and identity values come from synthetic contract fixtures. These
checks do not verify live tenant grants, GPU inference or production rights.
"""
from __future__ import annotations

import copy
import unittest

from feature5_motion.cross_feature_packet_gate import qualify_feature3_packet
from feature5_motion.wan22_motion_adapter import WanCompatibilityError
from test_feature5_cross_feature_packet_gate import actual_f3_packet_shape


class Feature2ShotTypeBoundaryTests(unittest.TestCase):
    def test_noncanonical_start_seconds_denied_even_when_equal_to_zero(self):
        # Python treats False == 0 and 0.0 == 0 as true. Neither is an
        # integer scene offset in the versioned Feature2/Feature3 contract.
        for malformed in (False, 0.0, "0", None, []):
            with self.subTest(value=repr(malformed)):
                packet = actual_f3_packet_shape()
                packet["feature2"]["shots"][0]["start_second"] = malformed
                packet["feature4"]["timeline"][0]["start_second"] = malformed
                def fresh(shop, brief):
                    return copy.deepcopy(packet)
                with self.assertRaises(WanCompatibilityError):
                    qualify_feature3_packet(
                        expected_packet=packet, read_current_packet=fresh)

    def test_unhashable_camera_denied_as_contract_error(self):
        # A malformed caller must not crash the worker with TypeError while
        # checking SHOT_CAMERAS; it must produce a typed denial.
        for malformed in ([], {"camera": "slow_push_in"}, None, 0):
            with self.subTest(value=repr(malformed)):
                packet = actual_f3_packet_shape()
                packet["feature2"]["shots"][0]["camera"] = malformed
                packet["feature4"]["timeline"][0]["camera"] = malformed
                def fresh(shop, brief):
                    return copy.deepcopy(packet)
                with self.assertRaises(WanCompatibilityError):
                    qualify_feature3_packet(
                        expected_packet=packet, read_current_packet=fresh)

    def test_original_synthetic_contract_still_accepted_without_provider_grant(self):
        packet = actual_f3_packet_shape()
        result = qualify_feature3_packet(
            expected_packet=packet,
            read_current_packet=lambda shop, brief: copy.deepcopy(packet))
        self.assertEqual(result.approved_shots, 3)
        self.assertFalse(result.can_submit_provider)
        self.assertFalse(result.can_publish)


if __name__ == "__main__":
    unittest.main()
