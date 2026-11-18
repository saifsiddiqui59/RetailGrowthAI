"""Run four REAL Feature5 native CPU media acceptance tests in existing video CI.

The existing video-engine/ci.sh discovers tests/media/test_*.py with ffmpeg,
ffprobe and Pillow installed. This small, cross-workstream CI bridge only
delegates to Feature5's strict fail-on-skip runner; it does not modify
video-engine code, workflow files or other media tests.

Temporary synthetic test signals only. No Wan model, GPU, external network,
customer media, storage uploads, signed approval or paid inference.
"""
from __future__ import annotations

from io import StringIO
import unittest

from feature5_motion.ci_native_media import run_cpu_media_suite


class Feature5NativePrivateIntakeCIGate(unittest.TestCase):
    def test_four_real_cpu_ffmpeg_private_intake_cases_not_skipped(self):
        log = StringIO()
        try:
            passed = run_cpu_media_suite(stream=log)
        finally:
            # Emit actual four test names/results even if an unexpected
            # failure interrupts the nested suite; no user media in logs.
            print(log.getvalue())
        self.assertEqual(passed, 4)
        print(
            "Feature5 native media CI gate PASS: 4/4 real ffmpeg/ffprobe "
            "private-intake tests, 0 skipped. No Wan inference or approval."
        )


if __name__ == "__main__":
    unittest.main()
