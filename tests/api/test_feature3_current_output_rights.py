"""F3-08 synthetic-only current-rights denial tests; not hosted auth proof."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_current_output_rights import Feature3CurrentOutputRights

class CurrentRightsTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job, self.asset = [str(uuid4()) for _ in range(3)]
        self.calls = []
        self.row = {
            "shop_id": self.shop, "job_id": self.job, "asset_id": self.asset,
            "output_sha256": "a" * 64, "rights_revision": 1,
            "output_registered": True, "source_rights_current": True,
            "customer_approval_current": True, "rights_revoked": False,
            "job_succeeded": True, "private_storage": True,
        }
        def read(shop, job, asset):
            self.calls.append((shop, job, asset))
            return dict(self.row)
        self.rights = Feature3CurrentOutputRights(authoritative_read=read)

    def check(self):
        return self.rights(self.shop, self.job, self.asset)

    def test_valid_fixture_reads_current_authority_twice(self):
        self.assertTrue(self.check())
        self.assertTrue(self.check())
        self.assertEqual(len(self.calls), 2)

    def test_foreign_shop_and_job_denied(self):
        self.assertFalse(self.rights(str(uuid4()), self.job, self.asset))
        self.assertFalse(self.rights(self.shop, str(uuid4()), self.asset))
        self.assertFalse(self.rights(self.shop, self.job, str(uuid4())))

    def test_revocations_and_missing_approvals_fail_closed(self):
        for key in ("output_registered", "source_rights_current",
                    "customer_approval_current", "job_succeeded", "private_storage"):
            with self.subTest(key=key):
                self.row[key] = False
                self.assertFalse(self.check())
                self.row[key] = True
        self.row["rights_revoked"] = True
        self.assertFalse(self.check())

    def test_malformed_authority_data_denied(self):
        cases = [
            ("rights_revision", 0), ("rights_revision", True),
            ("output_sha256", "bad"), ("output_sha256", "A" * 64),
            ("job_id", str(uuid4())), ("shop_id", str(uuid4())),
            ("asset_id", str(uuid4())), ("private_storage", 1),
            ("rights_revoked", 0),
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                old = self.row[key]
                self.row[key] = value
                self.assertFalse(self.check())
                self.row[key] = old

    def test_extra_or_missing_field_denied(self):
        self.row["browser_approved"] = True
        self.assertFalse(self.check())
        del self.row["browser_approved"]
        del self.row["source_rights_current"]
        self.assertFalse(self.check())

    def test_revocation_between_reads_denied(self):
        self.assertTrue(self.check())
        self.row["rights_revoked"] = True
        self.assertFalse(self.check())

    def test_malformed_ids_do_not_reach_authority(self):
        self.assertFalse(self.rights("not-uuid", self.job, self.asset))
        self.assertFalse(self.rights(self.shop.upper(), self.job, self.asset))
        self.assertEqual(self.calls, [])

    def test_provider_outage_denied(self):
        def broken(*args):
            raise TimeoutError("synthetic provider outage")
        self.assertFalse(Feature3CurrentOutputRights(
            authoritative_read=broken)(self.shop, self.job, self.asset))
        with self.assertRaises(ValueError):
            Feature3CurrentOutputRights(authoritative_read=None)

if __name__ == "__main__":
    unittest.main()
