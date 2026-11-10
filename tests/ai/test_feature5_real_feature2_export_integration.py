"""Exercise Feature2's ACTUAL pinned MIT Director exporter when integrated.

This test must NOT copy the Feature2 implementation or treat manually shaped
JSON as actual producer evidence. PR #551 is currently draft/unmerged: until
coordinator integrates its real source on this branch, the test is explicitly
skipped, not reported as an executed end-to-end producer.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import unittest

from feature5_motion.verify_feature2_export import qualify_export_bytes
from feature5_motion.wan22_motion_adapter import WanCompatibilityError

ROOT = Path(__file__).resolve().parents[2]
EXPORTER = ROOT / "ai-agents/creative-director/export-feature4-feature5-fixture.js"


@unittest.skipUnless(EXPORTER.is_file(), "Feature2 #551 actual exporter not integrated")
class RealFeature2OriginalExportIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("node") is None:
            raise unittest.SkipTest("Node not installed on this Python test worker")

    @staticmethod
    def actual_export(duration):
        process = subprocess.run(
            ["node", str(EXPORTER), str(duration)], cwd=ROOT,
            capture_output=True, check=False, timeout=45,
        )
        if process.returncode:
            raise AssertionError("Actual Feature2 exporter rejected offline input: " +
                                 process.stderr.decode(errors="replace")[-500:])
        return process.stdout

    def test_real_compiled_15_30_60_export_consumed_by_feature5(self):
        for duration in (15, 30, 60):
            with self.subTest(duration=duration):
                original_bytes = self.actual_export(duration)
                packet = json.loads(original_bytes)
                evidence = qualify_export_bytes(original_bytes, duration=duration)
                self.assertEqual(evidence["segment_count"], duration // 5)
                self.assertEqual(evidence["duration_seconds"], duration)
                self.assertFalse(evidence["can_submit_provider"])
                self.assertFalse(evidence["can_publish"])
                self.assertFalse(evidence["approved_for_feature4"])
                self.assertEqual(len(packet["feature4"]["timeline"]), duration // 5)
                self.assertEqual(len(packet["feature5"]["clip_requests"]), duration // 5)
                self.assertTrue(all(shot["provider_call_permitted"] is False
                                    for shot in packet["feature5"]["clip_requests"]))

    def test_real_compiled_export_rejects_changed_identity_and_approvals(self):
        source = json.loads(self.actual_export(30))
        mutations = (
            lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                next_shot_id="invented-shot"),
            lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                reference_facts_sha256="f" * 64),
            lambda p: p["feature5"]["clip_requests"][1]["original_direction"].update(
                product_sku="different-retailer-sku"),
            lambda p: p["feature4"]["timeline"][1].update(
                immutable_motion_prompt_sha256="e" * 64),
            lambda p: p["review"].update(signed_customer_approval=True),
            lambda p: p["feature5"].update(can_run_paid_motion=True),
            lambda p: p["source_media"].update(approved_feature3_frame_present=True),
        )
        for mutate in mutations:
            packet = deepcopy(source)
            mutate(packet)
            with self.subTest(mutate=str(mutate)), self.assertRaises(WanCompatibilityError):
                qualify_export_bytes(json.dumps(packet).encode(), duration=30)


if __name__ == "__main__":
    unittest.main()
