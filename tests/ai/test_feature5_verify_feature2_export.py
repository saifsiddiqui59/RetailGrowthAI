"""Real byte-level GPU-off integration boundary for Feature2 Node stdout.

Uses the existing contract-shaped fixture until F2 #551 merges; separate
authentic Node export execution remains an explicit coordinator integration gate.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest

from feature5_motion.verify_feature2_export import (
    MAX_INPUT_BYTES, qualify_export_bytes,
)
from feature5_motion.wan22_motion_adapter import WanCompatibilityError
from test_feature5_feature2_storyboard_bridge import make_packet


class Feature2OriginalExportBytesTests(unittest.TestCase):
    def test_all_duration_bytes_validate_with_no_release_authority(self):
        for duration in (15, 30, 60):
            with self.subTest(duration=duration):
                original = make_packet(duration)
                raw = json.dumps(original, ensure_ascii=False).encode("utf-8")
                receipt = qualify_export_bytes(raw, duration=duration)
                self.assertEqual(receipt["segment_count"], duration // 5)
                self.assertFalse(receipt["can_submit_provider"])
                self.assertFalse(receipt["can_publish"])
                self.assertFalse(receipt["approved_for_feature4"])
                self.assertEqual(receipt, qualify_export_bytes(raw, duration=duration))

    def test_trust_never_added_by_serialization(self):
        for change in (
            lambda p: p["feature5"].update(can_run_paid_motion=True),
            lambda p: p["review"].update(can_publish=True),
            lambda p: p["feature5"]["clip_requests"][0]["original_direction"].update(
                next_shot_id="invented"),
            lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                product_sku="different"),
        ):
            packet = make_packet(15)
            change(packet)
            with self.subTest(change=str(change)), self.assertRaises(WanCompatibilityError):
                qualify_export_bytes(json.dumps(packet).encode(), duration=15)

    def test_missing_duplicate_oversized_non_utf8_and_duration_mismatch_denied(self):
        originals = (
            b"",
            b"{\"schema\":\"a\",\"schema\":\"b\"}",
            b"\xff\xfe",
            b"null",
            b"NaN",
            b" " * (MAX_INPUT_BYTES + 1),
        )
        for raw in originals:
            with self.subTest(case=raw[:25]), self.assertRaises(WanCompatibilityError):
                qualify_export_bytes(raw, duration=15)
        with self.assertRaises(WanCompatibilityError):
            qualify_export_bytes(json.dumps(make_packet(15)).encode(), duration=30)

    def test_deeply_nested_untrusted_json_is_denied_without_a_traceback(self):
        # Below the byte limit but beyond Python's JSON decoder nesting limit.
        # A public-facing exporter boundary must return a denial, never crash.
        raw = b"[" * 20000 + b"0" + b"]" * 20000
        self.assertLess(len(raw), MAX_INPUT_BYTES)
        with self.assertRaises(WanCompatibilityError):
            qualify_export_bytes(raw, duration=15)
        cmd = [sys.executable, "-m", "feature5_motion.verify_feature2_export",
               "--duration", "15"]
        denied = subprocess.run(cmd, input=raw, capture_output=True,
                                check=False, timeout=30)
        self.assertEqual(denied.returncode, 2)
        self.assertFalse(denied.stdout)
        self.assertIn(b"no GPU", denied.stderr)
        self.assertNotIn(b"Traceback", denied.stderr)

    def test_actual_cli_stdout_is_only_source_denial_receipt(self):
        packet = make_packet(15)
        cmd = [sys.executable, "-m", "feature5_motion.verify_feature2_export",
               "--duration", "15"]
        completed = subprocess.run(cmd, input=json.dumps(packet).encode(), capture_output=True,
                                   check=False, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode(errors="replace"))
        receipt = json.loads(completed.stdout)
        self.assertEqual(receipt["segment_count"], 3)
        self.assertFalse(receipt["can_submit_provider"])
        self.assertNotIn("generation_prompt", completed.stdout.decode())
        self.assertNotIn("retailer", completed.stdout.decode())
        packet["review"]["signed_customer_approval"] = True
        denied = subprocess.run(cmd, input=json.dumps(packet).encode(), capture_output=True,
                                check=False, timeout=30)
        self.assertEqual(denied.returncode, 2)
        self.assertFalse(denied.stdout)
        self.assertIn(b"no GPU", denied.stderr)


if __name__ == "__main__":
    unittest.main()
