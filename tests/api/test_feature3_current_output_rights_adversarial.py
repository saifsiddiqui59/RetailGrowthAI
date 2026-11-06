"""F3-08 adversarial rights-authority regression tests (synthetic, not hosted)."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from feature3_current_output_rights import Feature3CurrentOutputRights


class AdversarialRightsTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job, self.asset = (str(uuid4()) for _ in range(3))
        self.row = dict(
            shop_id=self.shop, job_id=self.job, asset_id=self.asset,
            output_sha256="a" * 64, rights_revision=1,
            output_registered=True, source_rights_current=True,
            customer_approval_current=True, rights_revoked=False,
            job_succeeded=True, private_storage=True,
        )
        self.calls = 0

    def authority(self, shop, job, asset):
        self.calls += 1
        return dict(self.row)

    def check(self, provider=None):
        return Feature3CurrentOutputRights(
            authoritative_read=provider or self.authority
        )(self.shop, self.job, self.asset)

    def test_fresh_read_rejects_revocation_after_prior_success(self):
        rights = Feature3CurrentOutputRights(authoritative_read=self.authority)
        self.assertIs(rights(self.shop, self.job, self.asset), True)
        self.row["rights_revoked"] = True
        self.assertIs(rights(self.shop, self.job, self.asset), False)
        self.assertEqual(self.calls, 2)

    def test_all_boolean_grants_must_be_literal_true(self):
        for field in ("output_registered", "source_rights_current",
                      "customer_approval_current", "job_succeeded",
                      "private_storage"):
            for invalid in (1, "true", [], None, False):
                with self.subTest(field=field, invalid=invalid):
                    self.row[field] = invalid
                    self.assertIs(self.check(), False)
            self.row[field] = True

    def test_revocation_must_be_literal_false(self):
        for invalid in (0, None, "", [], True):
            with self.subTest(invalid=invalid):
                self.row["rights_revoked"] = invalid
                self.assertIs(self.check(), False)
        self.row["rights_revoked"] = False

    def test_malformed_authority_result_never_grants(self):
        for value in (None, True, [], (), "approved", 1, object()):
            with self.subTest(value=repr(value)):
                self.assertIs(self.check(lambda *_: value), False)

    def test_provider_errors_never_grant(self):
        for error in (TimeoutError, ConnectionError, PermissionError, ValueError):
            def fail(*_):
                raise error("synthetic failure")
            with self.subTest(error=error.__name__):
                self.assertIs(self.check(fail), False)

    def test_no_authority_call_for_noncanonical_identity(self):
        rights = Feature3CurrentOutputRights(authoritative_read=self.authority)
        for shop in ("", "not-a-uuid", self.shop.upper(), self.shop + " "):
            with self.subTest(shop=shop):
                self.assertIs(rights(shop, self.job, self.asset), False)
        self.assertEqual(self.calls, 0)

    def test_missing_or_extra_authority_fields_never_grant(self):
        for field in list(self.row):
            with self.subTest(field=field):
                copy = dict(self.row)
                del copy[field]
                self.assertIs(self.check(lambda *_: copy), False)
        extra = dict(self.row, browser_approved=True)
        self.assertIs(self.check(lambda *_: extra), False)


if __name__ == "__main__":
    unittest.main()
