"""Fail-closed CPU-only tests; NO GPU, Azure, third-party payment or network."""
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path
import copy
import json
import tempfile
import unittest

from feature5_motion.external_gpu_budget import (
    ExternalQuoteError, assess_external_gpu_quote, read_approved_external_quote,
)


NOW = datetime(2026, 10, 26, 13, 0, tzinfo=timezone.utc)


def quote():
    return {
        "provider": "runpod", "sku": "RTX_4090_24GB", "gpu_count": 1,
        "system_ram_gib": 48, "region": "us-east-1", "country": "US",
        "billing_mode": "on_demand", "currency": "USD",
        "compute_usd_per_hour": "0.89", "storage_usd_per_hour": "0.02",
        "minimum_billable_seconds": 60,
        "quoted_at": "2026-10-26T12:00:00Z",
        "expires_at": "2026-10-26T23:00:00Z",
    }


def assess(q=None, **kwargs):
    args = dict(max_seconds=600, ancillary_allowance_usd="0.05",
                approved_ceiling_usd="0.25", now=NOW)
    args.update(kwargs)
    return assess_external_gpu_quote(quote() if q is None else q, **args)


class TestExternalGpuBudget(unittest.TestCase):
    def test_valid_quote_is_not_authorization(self):
        result = assess()
        self.assertEqual(str(result.cost_ceiling_usd), "0.2017")
        self.assertEqual(result.status, "QUOTE_ONLY_NOT_EXECUTION_AUTHORIZATION")
        self.assertEqual(result.max_seconds, 600)

    def test_minimum_billing_is_included(self):
        q = quote()
        q["minimum_billable_seconds"] = 900
        self.assertEqual(str(assess(q, approved_ceiling_usd="0.30").cost_ceiling_usd), "0.2775")

    def test_expired_and_future_quotes_denied(self):
        q = quote()
        q["expires_at"] = "2026-10-26T12:30:00Z"
        with self.assertRaises(ExternalQuoteError):
            assess(q)
        q = quote()
        q["quoted_at"] = "2026-10-27T02:00:00Z"
        with self.assertRaises(ExternalQuoteError):
            assess(q)

    def test_no_spot_or_unapproved_provider(self):
        for key, value in (("billing_mode", "spot"), ("provider", "unknown"),
                           ("provider", []), ("sku", ["RTX_4090_24GB"])):
            with self.subTest(key=key, value=value):
                q = quote()
                q[key] = value
                with self.assertRaises(ExternalQuoteError):
                    assess(q)

    def test_hardware_unknown_and_under_ram_denied(self):
        for key, value in (("sku", "T4_16GB"), ("gpu_count", 2),
                           ("system_ram_gib", 25), ("system_ram_gib", True)):
            with self.subTest(key=key, value=value):
                q = quote()
                q[key] = value
                with self.assertRaises(ExternalQuoteError):
                    assess(q)

    def test_cost_uncertainty_fails_closed(self):
        for rate in ("NaN", "-1", "Infinity", "1001", None):
            q = quote()
            q["compute_usd_per_hour"] = rate
            with self.subTest(rate=rate):
                with self.assertRaises(ExternalQuoteError):
                    assess(q)
        with self.assertRaises(ExternalQuoteError):
            assess(approved_ceiling_usd="0.15")
        with self.assertRaises(ExternalQuoteError):
            assess(max_seconds=1801)

    def test_price_region_currency_and_schema(self):
        for key, value in (("region", ""), ("country", "USA"),
                           ("currency", "EUR"), ("minimum_billable_seconds", -1),
                           ("quoted_at", "not-a-date"), ("quoted_at", "2026-10-26T12:00:00+04:00")):
            q = quote()
            q[key] = value
            with self.subTest(key=key):
                with self.assertRaises(ExternalQuoteError):
                    assess(q)
        q = quote()
        q["unexpected"] = 1
        with self.assertRaises(ExternalQuoteError):
            assess(q)

    def test_quote_sha256_required_and_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            f = Path(folder) / "account-quote.json"
            data = json.dumps(quote(), sort_keys=True).encode("utf-8")
            f.write_bytes(data)
            digest = sha256(data).hexdigest()
            self.assertEqual(read_approved_external_quote(f, approved_sha256=digest), quote())
            with self.assertRaises(ExternalQuoteError):
                read_approved_external_quote(f, approved_sha256="0" * 64)
            with self.assertRaises(ExternalQuoteError):
                read_approved_external_quote(f, approved_sha256="not-a-hash")
            f.write_bytes(data + b" ")
            with self.assertRaises(ExternalQuoteError):
                read_approved_external_quote(f, approved_sha256=digest)

    def test_duplicate_keys_rejected_even_with_correct_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            f = Path(folder) / "bad.json"
            f.write_text('{"provider":"runpod","provider":"vast"}')
            with self.assertRaises(ExternalQuoteError):
                read_approved_external_quote(
                    f, approved_sha256=sha256(f.read_bytes()).hexdigest())

    def test_symlink_quote_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            original = Path(folder) / "quote.json"
            original.write_text(json.dumps(quote()))
            link = Path(folder) / "link.json"
            try:
                link.symlink_to(original)
            except (OSError, NotImplementedError):
                self.skipTest("Local OS disallows symlinks")
            with self.assertRaises(ExternalQuoteError):
                read_approved_external_quote(link, approved_sha256=sha256(original.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
