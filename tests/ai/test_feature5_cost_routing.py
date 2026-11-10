"""Feature5 cheapest honest media path: CPU first, GPU never implicitly."""
from decimal import Decimal
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from feature5_motion.azure_pricing import MotionSpendGuard, VerifiedAzureRates
from feature5_motion.cost_routing import plan_lowest_cost_delivery
from feature5_motion.contracts import MotionError


def quote():
    rates = VerifiedAzureRates(
        "eastus", "A100", Decimal("0.000529"), Decimal("0.000024"),
        Decimal("0.000003"), "2026-10-26T00:00:00Z",
    )
    return MotionSpendGuard(
        rates, max_billable_seconds=600, vcpus=4, gib_memory=16,
        ancillary_allowance_usd=Decimal("0.05"),
    )


class TestCostAwareDelivery(unittest.TestCase):
    def test_existing_free_media_preferred_even_when_gpu_budget_exists(self):
        selected = plan_lowest_cost_delivery(
            requires_realistic_ai_motion=False, existing_media_approved=True,
            allow_paid_gpu=True, max_premium_usd="100", guard=quote())
        self.assertEqual(selected.route, "EXISTING_FFMPEG")
        self.assertIsNone(selected.reserved_quote_usd)

    def test_realistic_walking_model_not_faked_with_ffmpeg_stills(self):
        selected = plan_lowest_cost_delivery(
            requires_realistic_ai_motion=True, existing_media_approved=True)
        self.assertEqual(selected.route, "DEFER")
        self.assertEqual(selected.max_premium_usd, Decimal(0))

    def test_zero_default_and_unapproved_spend_never_route_to_gpu(self):
        for kwargs in (
            {},
            {"max_premium_usd": "999", "allow_paid_gpu": False},
            {"max_premium_usd": "999", "allow_paid_gpu": True},
        ):
            with self.subTest(kwargs=kwargs):
                selected = plan_lowest_cost_delivery(
                    requires_realistic_ai_motion=True,
                    existing_media_approved=True, **kwargs)
                self.assertEqual(selected.route, "DEFER")

    def test_quote_above_cap_deferred_without_gpu_call(self):
        expected = quote().minimum_reservation_usd()
        self.assertGreater(expected, Decimal("0.4"))
        selected = plan_lowest_cost_delivery(
            requires_realistic_ai_motion=True, existing_media_approved=True,
            allow_paid_gpu=True, max_premium_usd="0.20", guard=quote())
        self.assertEqual(selected.route, "DEFER")
        self.assertEqual(selected.reserved_quote_usd, expected)

    def test_explicit_gpu_permission_and_budget_only_unlock_preflight(self):
        expected = quote().minimum_reservation_usd()
        selected = plan_lowest_cost_delivery(
            requires_realistic_ai_motion=True, existing_media_approved=False,
            allow_paid_gpu=True, max_premium_usd=str(expected), guard=quote())
        self.assertEqual(selected.route, "GPU_BUDGET_ELIGIBLE")
        self.assertEqual(selected.reserved_quote_usd, expected)
        self.assertIn("licence", selected.reason)
        # GPU_BUDGET_ELIGIBLE is not a paid launch: the DB/rights/license gate still blocks by default.

    def test_fails_closed_on_negative_nan_bool_and_invalid_intent(self):
        for bad in (-1, "NaN", "Infinity", True, None, "unknown"):
            with self.subTest(bad=bad):
                with self.assertRaises(MotionError):
                    plan_lowest_cost_delivery(
                        requires_realistic_ai_motion=True,
                        existing_media_approved=True, max_premium_usd=bad)
        with self.assertRaises(MotionError):
            plan_lowest_cost_delivery(requires_realistic_ai_motion=1, existing_media_approved=True)
        with self.assertRaises(MotionError):
            plan_lowest_cost_delivery(
                requires_realistic_ai_motion=True, existing_media_approved=True, allow_paid_gpu="yes")

    def test_unlicensed_stills_cannot_use_free_existing_ffmpeg(self):
        result = plan_lowest_cost_delivery(
            requires_realistic_ai_motion=False, existing_media_approved=False)
        self.assertEqual(result.route, "DEFER")


if __name__ == "__main__":
    unittest.main()
