#!/usr/bin/env python3
"""Read-only Microsoft retail-price lookup for existing South India GPT-4.1-mini.

No Azure inference, authenticated API request, DB mutation or API key. Prints
only public SKU/meter metadata; NEVER configures Functions or authorizes spend.
"""
from __future__ import annotations
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen

ENDPOINT = "https://prices.azure.com/api/retail/prices"
REGION = "southindia"
MODEL = "gpt 4 1 mini"  # normalize() turns model punctuation into spaces
SKIP = ("global", "glbl", "data zone", "datazone", "dzone",
        "batch", "provisioned", "ptu")


def normalize(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def choose_meters(items, *, now=None):
    """Return independently verified regional, uncached input/output meters."""
    now = now or datetime.now(timezone.utc)
    rows = {"input": [], "output": []}
    for row in items:
        if not isinstance(row, dict):
            continue
        sku = normalize(str(row.get("skuName", "")))
        if MODEL not in sku or any(x in sku for x in SKIP):
            continue
        if "cached" in sku or "cache" in sku:
            continue
        region = str(row.get("armRegionName", "")).lower()
        if region != REGION or row.get("currencyCode") != "USD":
            continue
        if not str(row.get("productName","")).lower().startswith("azure openai"):
            continue
        if row.get("isPrimaryMeterRegion") is False:
            continue
        if row.get("type") not in (None, "Consumption"):
            continue
        unit = normalize(str(row.get("unitOfMeasure", "")))
        # Azure OpenAI GPT-4 meters often publish USD/1K tokens while
        # newer models publish USD/1M. Normalize BEFORE budget comparison.
        if unit in ("1k", "1k tokens"):
            factor = Decimal("1000")
        elif unit in ("1m", "1m tokens", "1 million", "1 million tokens"):
            factor = Decimal("1")
        else:
            continue
        direction = ("input" if "input" in sku.split() or "inp" in sku.split()
                     else "output" if "output" in sku.split() or "outp" in sku.split()
                     else None)
        if direction is None:
            continue
        try:
            rate = Decimal(str(row["retailPrice"])) * factor
            when = datetime.fromisoformat(row["effectiveStartDate"].replace("Z", "+00:00"))
        except (KeyError, ValueError, TypeError, InvalidOperation):
            continue
        if not rate.is_finite() or rate <= 0 or when > now:
            continue
        rows[direction].append({
            "skuName": row["skuName"], "meterId": str(row.get("meterId", "")),
            "unitOfMeasure": row["unitOfMeasure"],
            "effectiveStartDate": when.isoformat(),
            "usd_per_million": str(rate), "when": when,
        })
    selected = {}
    for direction, candidates in rows.items():
        if not candidates:
            raise ValueError("Missing verified South India regional GPT-4.1-mini "+direction+" meter")
        latest = max(x["when"] for x in candidates)
        head = [x for x in candidates if x["when"] == latest]
        if len({x["usd_per_million"] for x in head}) != 1:
            raise ValueError("Ambiguous current regional "+direction+" meter prices")
        head.sort(key=lambda x: (x["skuName"], x["meterId"]))
        pick = {k: v for k, v in head[0].items() if k != "when"}
        selected[direction] = pick
    return selected


def fetch_prices(fetch=urlopen):
    query = urlencode({"$filter": "armRegionName eq 'southindia' and contains(productName, 'Azure OpenAI')",
                       "currencyCode": "USD"})
    url = ENDPOINT + "?" + query
    items = []
    seen = set()
    for _ in range(16):
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "prices.azure.com" or parsed.path != "/api/retail/prices" or url in seen:
            raise RuntimeError("Refused unknown or repeated Microsoft prices page")
        seen.add(url)
        with fetch(url, timeout=20) as resp:
            payload = json.load(resp)
        if not isinstance(payload, dict) or not isinstance(payload.get("Items"), list):
            raise RuntimeError("Invalid Microsoft retail price response")
        items.extend(payload["Items"])
        nxt = payload.get("NextPageLink")
        if not nxt:
            return items
        if not isinstance(nxt, str):
            raise RuntimeError("Invalid Microsoft pagination")
        url = nxt
    raise RuntimeError("Microsoft retail pricing exceeded page limit")


def main():
    records = fetch_prices()
    try:
        meters = choose_meters(records)
    except ValueError:
        # Price API response contains public catalog data only; NEVER print
        # tenant credentials, JWTs, Azure configuration or subscription details.
        related = [row for row in records
                   if isinstance(row, dict) and
                   ("mini" in normalize(str(row.get("skuName", ""))) or
                    "4 1" in normalize(str(row.get("skuName", ""))))]
        print("FEATURE2_PUBLIC_PRICE_CATALOG_DIAGNOSTIC="+json.dumps({
            "records_received": len(records),
            "related_sku_count": len(related),
            "public_examples": [
                {k: row.get(k) for k in
                 ("productName", "skuName", "unitOfMeasure",
                  "armRegionName", "type", "retailPrice")}
                for row in related[:20]]
        }, sort_keys=True))
        raise
    print("FEATURE2_OFFICIAL_RETAIL_METER_LOOKUP=PASS")
    print(json.dumps({"region": REGION, "model": "gpt-4.1-mini",
                      "deployment_type": "Regional Standard",
                      "pricing_type": "PUBLIC_RETAIL_NOT_ACCOUNT_CONTRACT",
                      "meters": meters,
                      "azure_inference_attempted": False,
                      "subscription_spend_authorized_by_meter": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("FEATURE2_OFFICIAL_RETAIL_METER_LOOKUP=BLOCKED: "+type(exc).__name__+
              ": "+str(exc)[:250], file=sys.stderr)
        sys.exit(1)
