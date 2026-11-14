"""F3-08 synthetic receipt boundary tests; no hosted JWT or rights proof."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_png_tenant import VerifiedGeneratedAssetTenant


class SyntheticRLS:
    origin = "https://demo-project.supabase.co"
    key = "sb_publishable_" + "x" * 24

    def __init__(self, receipt):
        self.receipt = receipt
        self.calls = []

    def member(self, *args):
        self.calls.append(("member", args))
        return False

    def feature3_gpu_job(self, *args):
        self.calls.append(("job", args))
        return None

    def feature3_generated_asset(self, *args):
        self.calls.append(("asset", args))
        return self.receipt


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job, self.asset = (str(uuid4()) for _ in range(3))
        self.path = f"{self.shop}/feature3/gpu/{self.job}/" + "a" * 64 + ".png"

    def test_valid_minimal_receipt_preserves_exact_identity_without_rights(self):
        backend = SyntheticRLS({"object_path": self.path, "mime_type": "image/png"})
        adapter = VerifiedGeneratedAssetTenant(backend)
        result = adapter.feature3_generated_asset("synthetic-jwt", self.shop, self.job, self.asset)
        self.assertEqual(result["id"], self.asset)
        self.assertEqual(result["shop_id"], self.shop)
        self.assertEqual(result["source"], "GENERATED")
        self.assertEqual(result["storage_bucket"], "retailgrowth-media")
        self.assertNotIn("rights_approved", result)
        self.assertEqual(backend.calls, [("asset", ("synthetic-jwt", self.shop, self.job, self.asset))])

    def test_foreign_or_forged_receipts_fail_closed(self):
        for receipt in (
            None, {}, [], {"object_path": self.path, "mime_type": "image/jpeg"},
            {"object_path": self.path + ".png", "mime_type": "image/png"},
            {"object_path": f"{uuid4()}/feature3/gpu/{self.job}/" + "a"*64 + ".png",
             "mime_type": "image/png"},
            {"object_path": self.path, "mime_type": "image/png", "id": str(uuid4())},
            {"object_path": self.path, "mime_type": "image/png", "shop_id": str(uuid4())},
            {"object_path": self.path, "mime_type": "image/png", "source": "UPLOAD"},
            {"object_path": self.path, "mime_type": "image/png", "storage_bucket": "public"},
            {"object_path": self.path, "mime_type": "image/png", "id": object()},
        ):
            with self.subTest(receipt=repr(receipt)):
                adapter = VerifiedGeneratedAssetTenant(SyntheticRLS(receipt))
                self.assertIsNone(adapter.feature3_generated_asset(
                    "synthetic-jwt", self.shop, self.job, self.asset))

    def test_invalid_scope_never_reaches_backend(self):
        backend = SyntheticRLS({"object_path": self.path, "mime_type": "image/png"})
        adapter = VerifiedGeneratedAssetTenant(backend)
        with self.assertRaises(ValueError):
            adapter.feature3_generated_asset("synthetic-jwt", "not-uuid", self.job, self.asset)
        self.assertEqual(backend.calls, [])


if __name__ == "__main__":
    unittest.main()
