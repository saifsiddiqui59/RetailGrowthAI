"""Azure official price snapshot parser unit tests; no API calls in CI."""
import sys
import unittest
from pathlib import Path
from decimal import Decimal
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from feature5_motion.contracts import MotionError
from feature5_motion.azure_pricing import extract_rates, estimate_execution_usd


def row(region, meter, price, unit):
    return {"serviceName": "Azure Container Apps", "armRegionName": region,
            "meterName": meter, "retailPrice": price, "unitOfMeasure": unit,
            "currencyCode": "USD", "type": "Consumption",
            "effectiveStartDate": "2026-04-01T00:00:00Z",
            "isPrimaryMeterRegion": True}


class TestAzureRetailPriceVerification(unittest.TestCase):
    def setUp(self):
        self.items = [
            row("eastus", "Standard NC A100 v4 GPU Usage", 0.000529, "1 Second"),
            row("eastus", "Standard vCPU Active Usage", 0.000024, "1 Second"),
            row("eastus", "Standard Memory Active Usage", 0.000003, "1 GiB Second"),
        ]

    def test_official_eastus_a100_meter(self):
        rates = extract_rates({"BillingCurrency": "USD", "Items": self.items},
                              region="eastus", gpu="A100")
        self.assertEqual(rates.gpu_per_second_usd, Decimal("0.000529"))
        self.assertEqual(estimate_execution_usd(rates, billable_seconds=600,
                         vcpus=4, gib_memory=16), Decimal("0.403800"))

    def test_unavailable_gpu_must_not_be_inferred_from_other_region(self):
        with self.assertRaises(MotionError):
            extract_rates({"BillingCurrency": "USD", "Items": self.items},
                          region="centralindia", gpu="A100")

    def test_zero_nan_duplicate_and_nonprimary_prices_fail(self):
        for price in (0, "-1", float("nan"), float("inf"), True):
            damaged = [dict(item) for item in self.items]
            damaged[0]["retailPrice"] = price
            with self.subTest(price=price), self.assertRaises(MotionError):
                extract_rates({"BillingCurrency": "USD", "Items": damaged},
                              region="eastus", gpu="A100")
        with self.assertRaises(MotionError):
            extract_rates({"BillingCurrency": "USD", "Items": self.items + [self.items[0]]},
                          region="eastus", gpu="A100")
        bad = [dict(item) for item in self.items]
        bad[0]["isPrimaryMeterRegion"] = False
        with self.assertRaises(MotionError):
            extract_rates({"BillingCurrency": "USD", "Items": bad},
                          region="eastus", gpu="A100")

    def test_bad_capacity_and_currency_rejected(self):
        for sec in (0, 3601, True):
            rates = extract_rates({"BillingCurrency": "USD", "Items": self.items},
                                  region="eastus", gpu="A100")
            with self.assertRaises(MotionError):
                estimate_execution_usd(rates, billable_seconds=sec,
                                       vcpus=4, gib_memory=16)
        with self.assertRaises(MotionError):
            extract_rates({"BillingCurrency": "INR", "Items": self.items},
                          region="eastus", gpu="A100")


if __name__ == "__main__":
    unittest.main()
