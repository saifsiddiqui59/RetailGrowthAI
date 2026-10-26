"""No-network Feature2 South India published retail-price parser regressions."""
from datetime import datetime, timezone
from pathlib import Path
import runpy
import pytest

P = runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts/ci/feature2_price_probe.py"))
choose = P["choose_meters"]
NOW = datetime(2026, 10, 26, tzinfo=timezone.utc)

def rec(name, price, *, region="southindia", date="2025-11-01T00:00:00Z",
        unit="1M Tokens", product="Azure OpenAI"):
    return dict(armRegionName=region, currencyCode="USD", productName=product,
                skuName=name, meterId="SYNTHETIC_TEST_METER", type="Consumption",
                retailPrice=price, unitOfMeasure=unit, effectiveStartDate=date,
                isPrimaryMeterRegion=True)

def test_only_regional_standard_uncached_and_effective_current_rates_accepted():
    items = [
      rec("gpt 4.1 mini Inp", "0.44"), rec("gpt 4.1 mini Outp", "1.76"),
      rec("gpt 4.1 mini Inp Global", "0.40"),
      rec("gpt 4.1 mini Outp Data Zone", "1.60"),
      rec("gpt 4.1 mini cached Inp", "0.11"),
      rec("gpt 4.1 mini Inp", "0.99", date="2027-01-01T00:00:00Z"),
      rec("gpt 4.1 mini Inp", "0.20", region="eastus"),
      rec("gpt 4.1 mini Outp", "0.50", unit="1K Tokens"),
    ]
    meters = choose(items, now=NOW)
    assert meters["input"]["usd_per_million"] == "0.44"
    assert meters["output"]["usd_per_million"] == "1.76"
    assert meters["input"]["unitOfMeasure"] == "1M Tokens"

def test_missing_direction_ambiguous_or_wrong_region_fails_closed():
    a=rec("gpt 4.1 mini Inp", "0.44")
    b=rec("gpt 4.1 mini Outp", "1.76")
    with pytest.raises(ValueError, match="Missing"):
        choose([a], now=NOW)
    with pytest.raises(ValueError, match="Ambiguous"):
        choose([a,b,rec("gpt 4.1 mini Outp Regional", "1.90")], now=NOW)
    with pytest.raises(ValueError, match="Missing"):
        choose([rec("gpt 4.1 mini Inp", "0.44",region="eastus"), b],now=NOW)

def test_no_secret_or_credentials_required_for_price_reader():
    assert "api-key" not in Path(P["__file__"]).read_text().lower()
    assert P["ENDPOINT"] == "https://prices.azure.com/api/retail/prices"
