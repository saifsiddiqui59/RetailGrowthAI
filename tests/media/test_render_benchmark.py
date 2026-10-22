"""Offline budget and cost modeling tests; no Azure or hosted credentials."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops/benchmarks"))
from render_benchmark import (BenchmarkError, budget_assessment,
                               estimate_compute_cost, _sample_tree)


class RenderBudgetTests(unittest.TestCase):
    def test_three_budgets_consistent(self):
        result = budget_assessment(45.0, 500 * 1024 * 1024, 2048)
        self.assertEqual(result["host_timeout_seconds"], 1200)
        self.assertEqual(result["claim_lease_seconds"], 1500)
        self.assertEqual(result["ffmpeg_subprocess_cap_seconds"], 780)
        self.assertEqual(result["reserved_non_ffmpeg_seconds"], 420)
        self.assertEqual(result["claim_lease_exceeds_host_by_seconds"], 300)
        self.assertTrue(result["preserves_full_420s_non_ffmpeg_reserve"])
        self.assertTrue(result["sampled_memory_within_specified_limit"])
        self.assertFalse(result["azure_runtime_verified"])

    def test_over_budget_and_over_memory_are_not_approved(self):
        result = budget_assessment(781.0, 3 * 1024 ** 3, 2048)
        self.assertFalse(result["preserves_full_420s_non_ffmpeg_reserve"])
        self.assertFalse(result["sampled_memory_within_specified_limit"])

    def test_cost_requires_explicit_rates_and_labels_exclusions(self):
        estimate = estimate_compute_cost(100, 1000, 2, 2, 0.01, 0.001)
        self.assertAlmostEqual(estimate["batch_estimate_usd"], 2200)
        self.assertEqual(estimate["rate_source"],
                         "caller-supplied, NOT fetched or validated Azure price")
        self.assertIn("retries", estimate["excludes"])

    def test_invalid_runtime_and_rate_denied(self):
        with self.assertRaises(BenchmarkError):
            budget_assessment(float("inf"))
        with self.assertRaises(BenchmarkError):
            estimate_compute_cost(30, 1000, 2, 2, -1, 0.001)

    def test_unavailable_linux_process_does_not_fabricate_metrics(self):
        # A nonexistent PID returns zero (the caller reports only sampled data).
        rss, cpu = _sample_tree(99999999)
        self.assertEqual(rss, 0)
        self.assertEqual(cpu, {})


if __name__ == "__main__":
    unittest.main()
