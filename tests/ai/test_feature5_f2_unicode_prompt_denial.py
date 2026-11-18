"""F5-02: reject malformed Unicode in untrusted offline Feature2 prompt bytes.

Synthetic contract fixtures only. No authentic exporter, GPU, model inference,
customer authorization, commercial media, or provider submission is claimed.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest

from feature5_motion.feature2_storyboard_bridge import qualify_feature2_offline_storyboard
from feature5_motion.verify_feature2_export import qualify_export_bytes
from feature5_motion.wan22_motion_adapter import WanCompatibilityError
from test_feature5_feature2_storyboard_bridge import make_packet


class OriginalDirectorUnicodeDenialTests(unittest.TestCase):
    def test_valid_source_still_non_authorizing(self):
        for duration in (15, 30, 60):
            with self.subTest(duration=duration):
                receipt = qualify_feature2_offline_storyboard(make_packet(duration))
                self.assertIs(receipt["can_submit_provider"], False)
                self.assertIs(receipt["can_publish"], False)

    def test_escaped_lone_surrogates_fail_closed_at_both_boundaries(self):
        for codepoint in (0xD800, 0xDBFF, 0xDC00, 0xDFFF):
            with self.subTest(codepoint=hex(codepoint)):
                packet = make_packet(15)
                packet["feature5"]["clip_requests"][0]["original_direction"][
                    "generation_prompt"
                ] += chr(codepoint)
                with self.assertRaises(WanCompatibilityError):
                    qualify_feature2_offline_storyboard(packet)

                # JSON can legally decode escaped surrogate code units into
                # Python strings that cannot be UTF-8 encoded. The CLI must
                # deny them, not leak an exception or produce a receipt.
                raw = json.dumps(packet, ensure_ascii=True).encode("utf-8")
                with self.assertRaises(WanCompatibilityError):
                    qualify_export_bytes(raw, duration=15)
                result = subprocess.run(
                    [sys.executable, "-m", "feature5_motion.verify_feature2_export",
                     "--duration", "15"],
                    input=raw, capture_output=True, check=False, timeout=30,
                )
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                self.assertNotIn(b"Traceback", result.stderr)
                self.assertIn(b"no GPU/provider call", result.stderr)


if __name__ == "__main__":
    unittest.main()
