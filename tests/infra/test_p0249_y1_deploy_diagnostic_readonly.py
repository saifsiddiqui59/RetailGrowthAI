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
