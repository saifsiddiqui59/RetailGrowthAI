"""F4-14 proof-only matrix checks; every media probe is mocked (not a real encode)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from feature4_cpu_matrix import aggregate_cpu_matrix, CpuMatrixError


HEAD = "b" * 40


class CpuMatrixTests(unittest.TestCase):
    def setUp(self):
        ctx = tempfile.TemporaryDirectory(prefix="f4-cpu-envelope-")
        self.addCleanup(ctx.cleanup)
        self.root = Path(ctx.name)
        self.manifest = {
            "schema": "feature4_cpu_matrix_inputs_v1",
            "source_commit": HEAD, "renders": []
        }
        for duration in (15, 30, 60):
            media = bytes([duration]) * 5000
            sha = hashlib.sha256(media).hexdigest()
            (self.root / f"clip-{duration}.mp4").write_bytes(media)
            row = {"seconds": duration, "path": f"clip-{duration}.mp4",
                   "sha256": sha, "benchmark": f"clip-{duration}.json"}
            self.manifest["renders"].append(row)
            data = {
                "kind": "OFFLINE_SYNTHETIC_HYPERFRAMES_CPU_BENCHMARK_NOT_AZURE",
                "source_commit_claim": HEAD,
                "output_sha256": sha,
                "output_bytes": len(media),
                "output_hash_type": "SHA256_STABLE_LOCAL_REGULAR_FILE_ONLY",
                "duration_seconds": duration, "width": 1080, "height": 1920,
                "fps": 24, "cloud_or_gpu_inference": False,
                "measured_on_azure_functions": False,
                "commercial_visual_quality_accepted": False,
                "azure_runtime_memory_verified": False, "azure_cost_inr": None,
                "wall_seconds": duration * 2.0,
                "max_sampled_process_tree_rss_bytes": duration * 1000000,
                "max_sampled_cpu_seconds_lower_bound": duration * .8,
                "sampling_interval_seconds": .2,
                "samples": 40, "max_observed_process_count": 2,
            }
            (self.root / row["benchmark"]).write_text(json.dumps(data), encoding="utf-8")

    def _check(self):
        def probe(path, *, duration, width, height, fps):
            self.assertEqual((width, height, fps), (1080, 1920, 24))
            self.assertEqual(path.name, f"clip-{duration}.mp4")
            return {"bytes": path.stat().st_size, "duration_seconds": duration}
        with patch("feature4_export_matrix.verify_mp4", side_effect=probe):
            return aggregate_cpu_matrix(self.manifest, self.root, expected_head=HEAD)

    def _edit_receipt(self, seconds, key, value):
        p = self.root / f"clip-{seconds}.json"
        record = json.loads(p.read_text())
        record[key] = value
        p.write_text(json.dumps(record))

    def test_three_lengths_sha_tied_without_false_cloud_acceptance(self):
        result = self._check()
        self.assertEqual([r["seconds"] for r in result["renders"]], [15, 30, 60])
        self.assertEqual(result["max_measured_wall_seconds"], 120)
        self.assertEqual(result["max_sampled_rss_bytes_lower_bound"], 60000000)
        self.assertFalse(result["cloud_budget_accepted"])
        self.assertFalse(result["code_commit_attested_by_ci"])
        self.assertFalse(result["commercial_release_eligible"])

    def test_missing_duplicate_head_and_path_escape_fail_closed(self):
        self.manifest["source_commit"] = "a" * 40
        with self.assertRaises(CpuMatrixError):
            self._check()
        self.manifest["source_commit"] = HEAD
        self.manifest["renders"][2]["seconds"] = 30
        with self.assertRaises(CpuMatrixError):
            self._check()
        self.manifest["renders"][2]["seconds"] = 60
        self.manifest["renders"][0]["benchmark"] = "../another-tenant.json"
        with self.assertRaises(CpuMatrixError):
            self._check()

    def test_encoded_source_mutation_cannot_pass_even_with_receipt(self):
        target = self.root / "clip-15.mp4"
        target.write_bytes(target.read_bytes() + b"unapproved")
        with self.assertRaisesRegex(CpuMatrixError, "encoded MP4"):
            self._check()

    def test_forged_sha_budget_or_bool_as_int_rejected(self):
        for key, value in (
            ("source_commit_claim", "0" * 40),
            ("output_sha256", "f" * 64),
            ("output_bytes", 4),
            ("cloud_or_gpu_inference", True),
            ("measured_on_azure_functions", True),
            ("commercial_visual_quality_accepted", True),
            ("azure_runtime_memory_verified", True),
            ("azure_cost_inr", 100),
            ("wall_seconds", float("nan")),
            ("max_sampled_process_tree_rss_bytes", -3),
            ("max_sampled_cpu_seconds_lower_bound", 0),
            ("samples", True),
            ("max_observed_process_count", 0),
            ("output_hash_type", "not-original"),
        ):
            with self.subTest(key=key):
                path = self.root / "clip-30.json"
                original = path.read_text()
                self._edit_receipt(30, key, value)
                with self.assertRaises(CpuMatrixError):
                    self._check()
                path.write_text(original)

    def test_missing_symlinked_or_oversized_json_not_read(self):
        receipt = self.root / "clip-30.json"
        receipt.unlink()
        receipt.symlink_to(self.root / "clip-15.json")
        with self.assertRaises(CpuMatrixError):
            self._check()
        receipt.unlink()
        receipt.write_bytes(b"x" * 65536)
        with self.assertRaises(CpuMatrixError):
            self._check()


if __name__ == "__main__":
    unittest.main()
