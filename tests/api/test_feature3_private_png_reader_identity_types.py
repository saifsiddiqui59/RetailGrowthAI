"""F3-08 isolated negative RLS receipt tests; no hosted credentials."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_reader import Feature3RevocablePNGReader, PrivateGeneratedDownloadDenied


class EqualEverything:
    def __eq__(self, other):
        return True


class EqualString(str):
    def __eq__(self, other):
        return True


class SyntheticTenant:
    origin = "https://demo-project.supabase.co"
    key = "sb_publishable_" + "x" * 24

    def __init__(self, shop, job, asset):
        self.shop, self.job, self.asset = shop, job, asset
        self.job_row = {"id": job, "shop_id": shop, "status": "SUCCEEDED",
                        "output_asset_id": asset}
        self.asset_row = {"id": asset, "shop_id": shop,
                          "storage_bucket": "retailgrowth-media",
                          "source": "GENERATED", "mime_type": "image/png",
                          "object_path": f"{shop}/feature3/gpu/{job}/" + "a" * 64 + ".png"}
        self.asset_calls = 0

    def member(self, token, actor, shop):
        return True

    def feature3_gpu_job(self, token, shop, job):
        return self.job_row

    def feature3_generated_asset(self, token, shop, job, asset):
        self.asset_calls += 1
        return self.asset_row


class IdentityReceiptTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job, self.asset, self.actor = [str(uuid4()) for _ in range(4)]
        self.tenant = SyntheticTenant(self.shop, self.job, self.asset)
        self.rights_calls = 0

        def rights(*args):
            self.rights_calls += 1
            return True

        self.reader = Feature3RevocablePNGReader(
            tenant_store=self.tenant, verify_user_jwt=lambda _: self.actor,
            current_output_rights=rights)

    def current(self):
        return self.reader._current("synthetic-only-token", self.actor,
                                    self.shop, self.job)

    def test_valid_exact_string_receipt_reaches_rights(self):
        asset, key, digest = self.current()
        self.assertEqual(asset, self.asset)
        self.assertEqual(digest, "a" * 64)
        self.assertEqual(self.rights_calls, 1)

    def test_job_identity_spoof_denied_before_asset_and_rights(self):
        for field in ("id", "shop_id"):
            for spoof in (EqualEverything(), EqualString(str(uuid4()))):
                with self.subTest(field=field, spoof=type(spoof).__name__):
                    self.tenant.job_row[field] = spoof
                    with self.assertRaises(PrivateGeneratedDownloadDenied):
                        self.current()
                    self.assertEqual(self.tenant.asset_calls, 0)
                    self.assertEqual(self.rights_calls, 0)
                    self.tenant.job_row[field] = self.job if field == "id" else self.shop

    def test_asset_identity_spoof_denied_before_rights(self):
        for field in ("id", "shop_id"):
            for spoof in (EqualEverything(), EqualString(str(uuid4()))):
                with self.subTest(field=field, spoof=type(spoof).__name__):
                    self.tenant.asset_row[field] = spoof
                    with self.assertRaises(PrivateGeneratedDownloadDenied):
                        self.current()
                    self.assertEqual(self.rights_calls, 0)
                    self.tenant.asset_row[field] = self.asset if field == "id" else self.shop

    def test_asset_metadata_equality_spoof_denied(self):
        for field in ("storage_bucket", "source", "mime_type"):
            original = self.tenant.asset_row[field]
            for spoof in (EqualEverything(), EqualString("foreign")):
                with self.subTest(field=field, spoof=type(spoof).__name__):
                    self.tenant.asset_row[field] = spoof
                    with self.assertRaises(PrivateGeneratedDownloadDenied):
                        self.current()
                    self.assertEqual(self.rights_calls, 0)
            self.tenant.asset_row[field] = original


if __name__ == "__main__":
    unittest.main()
