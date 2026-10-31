"""Cheap, no-render checks for F4-08/12 sample measurement integrity."""
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine" / "hyperframes"))

from benchmark_render import parse_proc_stat, sample_process_group, benchmark


class HyperFramesBenchTests(unittest.TestCase):
    def test_stat_parser_handles_nested_process_names(self):
        fields = ["S"] + ["0"] * 21
        fields[1], fields[2], fields[11], fields[12], fields[21] = "10", "15", "42", "7", "9"
        data = "123 (chromium (worker)) " + " ".join(fields)
        self.assertEqual(parse_proc_stat(data), (123, 10, 15, 49, 9))
        self.assertIsNone(parse_proc_stat("garbage"))
        self.assertIsNone(parse_proc_stat("123 (broken)"))

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux proc filesystem")
    def test_sampling_current_process_group_has_nonzero_rss(self):
        rss, ticks, count = sample_process_group(os.getpgrp())
        self.assertGreater(rss, 0)
        self.assertGreaterEqual(ticks, 0)
        self.assertGreaterEqual(count, 1)

    def test_rejects_unbounded_timeout_before_loading_project(self):
        for value in (0, 781, True, 20.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                benchmark("/nonexistent", "/invalid.mp4", "/invalid.json",
                          timeout_seconds=value)


if __name__ == "__main__":
    unittest.main()
