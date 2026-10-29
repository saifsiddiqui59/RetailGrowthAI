"""Cheap, no-render checks for F4-08/12 sample measurement integrity."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine" / "hyperframes"))

from benchmark_render import parse_proc_stat, sample_process_group, benchmark, verified_output_sha256


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

    def test_benchmark_receipt_hashes_real_stable_original_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic-render.mp4"
            data = b"test-only-render" * 200
            path.write_bytes(data)
            size, digest = verified_output_sha256(path)
            self.assertEqual(size, len(data))
            self.assertEqual(digest, hashlib.sha256(data).hexdigest())
            self.assertEqual(len(digest), 64)

    def test_rejects_symlink_truncated_and_missing_benchmark_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            real = root / "original.mp4"
            real.write_bytes(b"dummy" * 500)
            alias = root / "foreign.mp4"
            alias.symlink_to(real)
            for candidate in (alias, root / "missing.mp4"):
                with self.subTest(path=candidate), self.assertRaises(ValueError):
                    verified_output_sha256(candidate)
            real.write_bytes(b"short")
            with self.assertRaisesRegex(ValueError, "nonempty"):
                verified_output_sha256(real)

    def test_existing_output_or_receipt_rejected_before_any_render(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            project = root / "project"
            project.mkdir()
            (project / "render-config.json").write_text(json.dumps({
                "contract_version": "rg_video_v2",
                "renderer": "hyperframes", "duration_seconds": 30,
                "width": 540, "height": 960, "fps": 24,
            }), encoding="utf-8")
            output = root / "render.mp4"
            report = root / "report.json"
            for occupied in (output, report):
                occupied.write_bytes(b"already here")
                with self.subTest(occupied=occupied), self.assertRaisesRegex(
                        ValueError, "destinations must be new"):
                    benchmark(project, output, report)
                occupied.unlink()

    def test_rejects_unbounded_timeout_before_loading_project(self):
        for value in (0, 781, True, 20.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                benchmark("/nonexistent", "/invalid.mp4", "/invalid.json",
                          timeout_seconds=value)


if __name__ == "__main__":
    unittest.main()
