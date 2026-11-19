"""Offline privacy and parser checks for read-only Y1 diagnostics."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops"))
import p0249_y1_deploy_diagnostic_readonly as diagnostic


class Y1DiagnosticSafetyTests(unittest.TestCase):
    def test_app_settings_never_emit_values_or_unknown_keys(self):
        settings = [
            {"name": "ENABLE_ORYX_BUILD", "value": "true"},
            {"name": "WEBSITE_RUN_FROM_PACKAGE", "value": "https://signed.example/?sig=SECRET"},
            {"name": "AzureWebJobsStorage", "value": "AccountKey=VERYSECRET"},
        ]
        summary = diagnostic.setting_flags(settings)
        output = str(summary)
        self.assertIn("ENABLE_ORYX_BUILD", output)
        self.assertTrue(summary["ENABLE_ORYX_BUILD"]["is_true"])
        self.assertNotIn("SECRET", output)
        self.assertNotIn("AzureWebJobsStorage", output)

    def test_deployment_codes_sanitized(self):
        statuses = diagnostic.deployment_summary([
            {"status": 4, "message": "private secret"},
            {"status": 3, "message": "private secret"},
            {"status": 2, "message": "private secret"},
        ])
        self.assertEqual(statuses["status_counts"]["success"], 1)
        self.assertEqual(statuses["status_counts"]["failed"], 1)
        self.assertNotIn("secret", str(statuses))

    def test_log_categories_are_boolean_only(self):
        categories = diagnostic.log_categories({
            "message": "Oryx failed for https://private.example/?sig=TOP_SECRET"
        })
        self.assertTrue(categories["categories"]["oryx"])
        self.assertTrue(categories["categories"]["failed"])
        self.assertNotIn("TOP_SECRET", str(categories))

    def test_audit_verifies_scope_before_readonly_azure_calls(self):
        with patch.object(diagnostic, "verify", side_effect=RuntimeError("bad scope")), \
             patch.object(diagnostic, "az_read", side_effect=AssertionError("no Azure reads")), \
             self.assertRaises(RuntimeError):
            diagnostic.main()

    def test_y1_exact_index_shapes_never_emit_unexpected_names(self):
        self.assertEqual(diagnostic.index_shape(["p0249_health", "campaign_read"]), "EXACT_TWO")
        self.assertEqual(diagnostic.index_shape([
            diagnostic.SITE + "/p0249_health", diagnostic.SITE + "/campaign_read",
            diagnostic.SITE + "/render_job_read", diagnostic.SITE + "/poster_job_read",
            diagnostic.SITE + "/poster_draft_read"
        ]), "EXACT_FIVE")
        self.assertEqual(diagnostic.index_shape(["p0249_health", "secret_route"]), "OTHER_UNVERIFIED")
        self.assertEqual(diagnostic.index_shape(["p0249_health", "p0249_health"]), "OTHER_UNVERIFIED")
        self.assertEqual(diagnostic.index_shape([None]), "INVALID")

    def test_index_never_trusts_a_suffix_from_a_different_site(self):
        two = ["p0249_health", "campaign_read"]
        five = two + ["render_job_read", "poster_job_read", "poster_draft_read"]
        for approved in (two, five):
            expected = "EXACT_TWO" if len(approved) == 2 else "EXACT_FIVE"
            self.assertEqual(diagnostic.index_shape(approved), expected)
            self.assertEqual(diagnostic.index_shape([
                diagnostic.SITE + "/" + name for name in approved
            ]), expected)
            for wrong in (
                ["untrusted-site/" + name for name in approved],
                [diagnostic.SITE + "/functions/" + name for name in approved],
                [diagnostic.SITE + "/" + approved[0], *approved[1:]],
            ):
                with self.subTest(approved=expected, wrong=wrong[0]):
                    self.assertEqual(diagnostic.index_shape(wrong),
                                     "OTHER_UNVERIFIED")
        for invalid in ([""], ["p0249_health\\n"], ["p0249_health\\\\bad"],
                        [" p0249_health"], ["/p0249_health"]):
            with self.subTest(invalid=invalid):
                self.assertNotIn(diagnostic.index_shape(invalid),
                                 ("EXACT_TWO", "EXACT_FIVE"))

    def test_ambiguous_expected_settings_fail_without_exposing_values(self):
        with self.assertRaisesRegex(RuntimeError, "Duplicate"):
            diagnostic.setting_flags([
                {"name": "ENABLE_ORYX_BUILD", "value": "true"},
                {"name": "enable_oryx_build", "value": "sensitive-data"},
            ])
        with self.assertRaisesRegex(RuntimeError, "Malformed"):
            diagnostic.setting_flags([{"value": "sensitive-data"}])

    def test_protected_readonly_diagnostic_is_manual_only(self):
        work = (ROOT / ".github/workflows/p0249-y1-deploy-diagnostic-readonly-once.yml").read_text()
        self.assertIn("  workflow_dispatch:", work)
        self.assertNotIn("  push:", work)
        self.assertNotIn("  pull_request:", work)
        self.assertNotIn("head_commit.message", work)
        self.assertIn("github.event_name == 'workflow_dispatch'", work)
        self.assertIn("environment: dev", work)
        self.assertIn("id-token: write", work)
        self.assertNotIn("az functionapp config appsettings set", work)

    def test_diagnostics_do_not_issue_mutating_commands(self):
        p=(ROOT/"ops"/"p0249_y1_deploy_diagnostic_readonly.py").read_text()
        for forbidden in (
            '"create"', '"delete"', '"set"', "deployment source config-zip",
            "az functionapp config appsettings set", "az deployment group create",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, p)


if __name__ == "__main__":
    unittest.main()
