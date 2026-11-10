"""Tencent Community License *policy* negative tests; NOT legal clearance."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from feature5_motion.contracts import MotionError
from feature5_motion.license_gate import EXCLUDED_COUNTRIES, HunyuanLicensePolicy


def reviewed(**kwargs):
    values = dict(
        deployment_country="US", retailer_country="IN",
        intended_publication_countries=("IN", "US"),
        actual_provider_legal_name="RetailGrowthAI DEV Licensing Test",
        tencent_no_endorsement_notice=True,
        full_license_terms_available_to_users=True,
        acceptable_use_and_local_law_checked=True,
        commercial_media_rights_checked=True,
        operator_terms_reviewed=True,
        monthly_active_users_at_model_release=1000,
        separate_tencent_license_if_required=False,
    )
    values.update(kwargs)
    return HunyuanLicensePolicy(**values)


class TestHunyuanLicenseGate(unittest.TestCase):
    def test_mock_reviewed_india_and_us(self):
        self.assertIsNone(reviewed().assert_allowed())

    def test_all_eu_uk_korea_are_blocked_in_processing_retailer_and_publication(self):
        for country in EXCLUDED_COUNTRIES:
            for changed in (
                {"deployment_country": country},
                {"retailer_country": country},
                {"intended_publication_countries": ("IN", country)},
            ):
                with self.subTest(country=country, field=list(changed)[0]):
                    with self.assertRaises(MotionError):
                        reviewed(**changed).assert_allowed()

    def test_missing_compliance_disclosure_denied(self):
        for key in (
            "tencent_no_endorsement_notice", "full_license_terms_available_to_users",
            "acceptable_use_and_local_law_checked",
            "commercial_media_rights_checked", "operator_terms_reviewed",
        ):
            with self.subTest(field=key), self.assertRaises(MotionError):
                reviewed(**{key: False}).assert_allowed()
        with self.assertRaises(MotionError):
            reviewed(actual_provider_legal_name="").assert_allowed()
        with self.assertRaises(MotionError):
            reviewed(intended_publication_countries=()).assert_allowed()

    def test_large_licensee_requires_separate_license(self):
        with self.assertRaises(MotionError):
            reviewed(monthly_active_users_at_model_release=100_000_001).assert_allowed()
        self.assertIsNone(reviewed(
            monthly_active_users_at_model_release=100_000_001,
            separate_tencent_license_if_required=True).assert_allowed())

    def test_unknown_or_forged_country_and_mau(self):
        for country in ("", "india", "U1", None, "gb"):
            with self.subTest(country=country), self.assertRaises(MotionError):
                reviewed(retailer_country=country).assert_allowed()
        for mau in (-1, float("nan"), True, None):
            with self.subTest(mau=mau), self.assertRaises(MotionError):
                reviewed(monthly_active_users_at_model_release=mau).assert_allowed()


if __name__ == "__main__":
    unittest.main()
