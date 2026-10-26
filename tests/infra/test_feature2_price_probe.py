"""Network-free Azure price probe regressions for pytest and unittest discovery."""
from datetime import datetime, timezone
from pathlib import Path
import runpy
import unittest

P = runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts/ci/feature2_price_probe.py"))
choose = P["choose_meters"]
NOW = datetime(2026, 10, 26, tzinfo=timezone.utc)


def rec(name, price, *, region="southindia", date="2025-11-01T00:00:00Z",
        unit="1M Tokens", product="Azure OpenAI"):
    return dict(armRegionName=region, currencyCode="USD", productName=product,
                skuName=name, meterId="SYNTHETIC_TEST_METER", type="Consumption",
                retailPrice=price, unitOfMeasure=unit, effectiveStartDate=date,
                isPrimaryMeterRegion=True)


class TestFeature2PriceProbe(unittest.TestCase):
    def test_only_regional_standard_uncached_and_effective_current_rates_accepted(self):
        items = [
          rec("gpt 4.1 mini Inp", "0.44"), rec("gpt 4.1 mini Outp", "1.76"),
          rec("gpt 4.1 mini Inp Global", "0.40"),
          rec("gpt 4.1 mini Outp Data Zone", "1.60"),
          rec("gpt 4.1 mini cached Inp", "0.11"),
          rec("gpt 4.1 mini Inp", "0.99", date="2027-01-01T00:00:00Z"),
          rec("gpt 4.1 mini Inp", "0.20", region="eastus"),
          rec("gpt 4.1 mini Outp", "0.50", unit="1 Token"),
        ]
        meters = choose(items, now=NOW)
        self.assertEqual(meters["input"]["usd_per_million"], "0.44")
        self.assertEqual(meters["output"]["usd_per_million"], "1.76")
        self.assertEqual(meters["input"]["unitOfMeasure"], "1M Tokens")

    def test_exact_azure_public_one_thousand_token_meter_conversion(self):
        rows=[rec("gpt 4.1 mini Inp", "0.00044",unit="1K"),
              rec("gpt 4.1 mini Outp", "0.00176",unit="1K")]
        meters=choose(rows, now=NOW)
        self.assertEqual(meters["input"]["usd_per_million"],"0.44000")
        self.assertEqual(meters["output"]["usd_per_million"],"1.76000")

    def test_known_azure_openai_product_family_preserved(self):
        rows=[rec("gpt 4.1 mini Inp", "0.44",product="Azure OpenAI GPT4"),
              rec("gpt 4.1 mini Outp", "1.76",product="Azure OpenAI GPT4")]
        self.assertEqual(choose(rows,now=NOW)["output"]["usd_per_million"],"1.76")

    def test_missing_direction_ambiguous_or_wrong_region_fails_closed(self):
        a=rec("gpt 4.1 mini Inp", "0.44")
        b=rec("gpt 4.1 mini Outp", "1.76")
        with self.assertRaisesRegex(ValueError, "Missing"):
            choose([a], now=NOW)
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            choose([a,b,rec("gpt 4.1 mini Outp Regional", "1.90")], now=NOW)
        with self.assertRaisesRegex(ValueError, "Missing"):
            choose([rec("gpt 4.1 mini Inp", "0.44",region="eastus"), b],now=NOW)

    def test_no_secret_or_credentials_required_for_price_reader(self):
        self.assertNotIn("api-key", Path(P["__file__"]).read_text().lower())
        self.assertEqual(P["ENDPOINT"], "https://prices.azure.com/api/retail/prices")


if __name__ == "__main__":
    unittest.main()
