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

    def test_oversized_and_forged_scope_never_reaches_authority(self):
        class ForgedUUID(str):
            def __eq__(self, other):
                return True

        rights = Feature3CurrentOutputRights(authoritative_read=self.authority)
        invalid = ("x" * 100000, ForgedUUID(self.shop),
                   self.shop.replace("-", ""), self.shop.upper())
        for field in range(3):
            for value in invalid:
                scope = [self.shop, self.job, self.asset]
                scope[field] = value
                with self.subTest(field=field, kind=type(value).__name__):
                    self.assertIs(rights(*scope), False)
        self.assertEqual(self.calls, 0)

    def test_backend_pinned_digest_rejects_substituted_output(self):
        rights = Feature3CurrentOutputRights(
            authoritative_read=self.authority, expected_output_sha256="a" * 64)
        self.assertIs(rights(self.shop, self.job, self.asset), True)
        self.row["output_sha256"] = "b" * 64
        self.assertIs(rights(self.shop, self.job, self.asset), False)

    def test_invalid_backend_digest_configuration_fails_closed(self):
        for invalid in ("", "A" * 64, "0" * 63, True, 42):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    Feature3CurrentOutputRights(
                        authoritative_read=self.authority,
                        expected_output_sha256=invalid)

    def test_missing_or_extra_authority_fields_never_grant(self):
        for field in list(self.row):
            with self.subTest(field=field):
                copy = dict(self.row)
                del copy[field]
                self.assertIs(self.check(lambda *_: copy), False)
        extra = dict(self.row, browser_approved=True)
        self.assertIs(self.check(lambda *_: extra), False)


    def test_trusted_revision_floor_denies_stale_rights_after_regrant(self):
        rights = Feature3CurrentOutputRights(
            authoritative_read=self.authority,
            expected_output_sha256="a" * 64,
            minimum_rights_revision=3,
        )
        self.assertFalse(rights(self.shop, self.job, self.asset))
        self.row["rights_revision"] = 3
        self.assertTrue(rights(self.shop, self.job, self.asset))
        self.row["rights_revision"] = 2
        self.assertFalse(rights(self.shop, self.job, self.asset))
        self.row["rights_revision"] = 4
        self.row["rights_revoked"] = True
        self.assertFalse(rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 4)

    def test_invalid_trusted_revision_floor_is_rejected(self):
        for invalid in (0, -1, True, False, 1.0, "1", [], {}):
            with self.subTest(invalid=repr(invalid)):
                with self.assertRaises(ValueError):
                    Feature3CurrentOutputRights(
                        authoritative_read=self.authority,
                        minimum_rights_revision=invalid,
                    )
        self.assertEqual(self.calls, 0)

    def test_revision_floor_does_not_skip_authority_rechecks(self):
        rights = Feature3CurrentOutputRights(
            authoritative_read=self.authority, minimum_rights_revision=1)
        self.assertTrue(rights(self.shop, self.job, self.asset))
        self.row["customer_approval_current"] = False
        self.assertFalse(rights(self.shop, self.job, self.asset))
        self.assertEqual(self.calls, 2)

    def test_authority_identity_denies_objects_with_forged_equality(self):
        # A source adapter must not grant access because a custom object
        # pretends to compare equal to any signed shop/job/asset identifier.
        # Only an exact canonical string returned by the authority is valid.
        class AlwaysEqual:
            def __eq__(self, other):
                return True
            def __ne__(self, other):
                return False

        class EqualText(str):
            def __eq__(self, other):
                return True
            def __ne__(self, other):
                return False

        rights = Feature3CurrentOutputRights(authoritative_read=self.authority)
        self.assertTrue(rights(self.shop, self.job, self.asset))
        for field in ("shop_id", "job_id", "asset_id"):
            original = self.row[field]
            for forged in (AlwaysEqual(), EqualText("not-a-canonical-uuid")):
                with self.subTest(field=field, forged=type(forged).__name__):
                    self.row[field] = forged
                    self.assertFalse(rights(self.shop, self.job, self.asset))
            self.row[field] = original
        self.assertTrue(rights(self.shop, self.job, self.asset))

if __name__ == "__main__":
    unittest.main()
