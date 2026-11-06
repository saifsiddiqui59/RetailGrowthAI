"""F3-08 synthetic binding tests: never evidence of hosted authorization."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_private_rights_binding import build_private_png_reader


class Store:
    origin = "https://example.supabase.co"
    key = "sb_publishable_abcdef123456"
    def member(self, *args): return True
    def feature3_gpu_job(self, *args): return None
    def feature3_generated_asset(self, *args): return None


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job, self.asset = [str(uuid4()) for _ in range(3)]
        self.calls = 0
        self.row = dict(
            shop_id=self.shop, job_id=self.job, asset_id=self.asset,
            output_sha256="a" * 64, rights_revision=2,
            output_registered=True, source_rights_current=True,
            customer_approval_current=True, rights_revoked=False,
            job_succeeded=True, private_storage=True,
        )

    def authority(self, *args):
        self.calls += 1
        return dict(self.row)

    def build(self, **changes):
        values = dict(tenant_store=Store(), verify_user_jwt=lambda token: self.shop,
                      authoritative_read=self.authority,
                      expected_output_sha256="a" * 64,
                      minimum_rights_revision=2)
        values.update(changes)
        return build_private_png_reader(**values)

    def test_binding_rechecks_current_authority_and_revocation(self):
        reader = self.build()
        self.assertTrue(reader.rights(self.shop, self.job, self.asset))
        self.row["rights_revoked"] = True
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 2)

    def test_binding_denies_foreign_shop_and_stale_revision(self):
        reader = self.build()
        self.assertFalse(reader.rights(str(uuid4()), self.job, self.asset))
        self.row["rights_revision"] = 1
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))

    def test_binding_denies_substituted_digest(self):
        reader = self.build()
        self.row["output_sha256"] = "b" * 64
        self.assertFalse(reader.rights(self.shop, self.job, self.asset))

    def test_missing_trusted_pins_fail_before_reader_construction(self):
        for changes in (dict(expected_output_sha256=None),
                        dict(minimum_rights_revision=None),
                        dict(authoritative_read=None),
                        dict(verify_user_jwt=None)):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    self.build(**changes)
        self.assertEqual(self.calls, 0)


if __name__ == "__main__":
    unittest.main()
