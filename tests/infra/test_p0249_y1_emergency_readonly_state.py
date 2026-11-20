"""Nonsecret failure-state classifier safety tests."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"ops"))
import p0249_y1_emergency_readonly_state as e
import p0249_y1_remote_build_mode as mode


class EmergencyReadOnlyTests(unittest.TestCase):
    def test_saved_package_and_original_index_with_owner(self):
        uri="https://rgaid4e5ddbdf0d21d96.blob.core.windows.net/private/baseline.zip?sig=NEVER_PRINT"
        info=e.classify({"WEBSITE_RUN_FROM_PACKAGE":uri,
                         mode.BACKUP:uri,mode.OWNER:e.FAILED_RUN_ID,
                         "SCM_DO_BUILD_DURING_DEPLOYMENT":"true"},mode.TWO)
        self.assertTrue(info["current_matches_backup"])
        self.assertTrue(info["owner_is_failed_release"])
        self.assertTrue(info["two_function_index"])
        self.assertFalse(info["enable_oryx_present"])
        for secret in ("NEVER_PRINT","baseline.zip","blob.core.windows.net"):
            self.assertNotIn(secret,str(info))

    def test_incomplete_recovery_reports_uncertainty(self):
        uri="https://rgaid4e5ddbdf0d21d96.blob.core.windows.net/private/other.zip?sig=SECRET"
        for current in (None, "1", uri):
            info=e.classify({mode.BACKUP:uri,mode.OWNER:"unexpected",
                             "WEBSITE_RUN_FROM_PACKAGE":current},mode.TWO)
            self.assertFalse(info["owner_is_failed_release"])
            self.assertEqual(info["current_matches_backup"],current==uri)
            self.assertNotIn("SECRET",str(info))

    def test_no_azure_write_or_sensitive_echo_in_diagnostic_and_workflow(self):
        src=(ROOT/"ops/p0249_y1_emergency_readonly_state.py").read_text()
        wf=(ROOT/".github/workflows/p0249-y1-emergency-readonly-once.yml").read_text()
        for forbidden in ("appsettings set", "appsettings delete", "config-zip",
                          "sync-function-triggers", "az rest --method post"):
            self.assertNotIn(forbidden,src)
            self.assertNotIn(forbidden,wf)
        self.assertIn("environment: dev",wf)
        self.assertIn("id-token: write",wf)
        self.assertIn("p0249_y1_emergency_readonly_state.py",wf)
        self.assertIn("github.event_name == 'push'",wf)
        self.assertIn("refs/heads/main",wf)
        self.assertNotIn("secrets.AZURE_CLIENT_SECRET",wf)


if __name__=="__main__":
    unittest.main()
