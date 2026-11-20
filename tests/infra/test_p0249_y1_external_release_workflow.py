"""Offline guardrails for one-time DEV Y1 external package protected release."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/p0249-dev-y1-private-versioned-five-get-protected.yml"
HELPER=ROOT/"ops/p0249_y1_external_private_package.py"


class Y1ExternalProtectedReleaseTests(unittest.TestCase):
    def setUp(self):
        self.wf=WF.read_text()
        self.helper=HELPER.read_text()

    def test_only_explicit_protected_dev_manual_release_with_exact_reviewed_main(self):
        for token in (
            "on:\n  workflow_dispatch:", "reviewed_main_sha",
            "YES-P0249-Y1-PRIVATE-BLOB-FIVE-GET-RESTORE",
            "environment: dev", "id-token: write",
            "cancel-in-progress: false", "github.event_name == 'workflow_dispatch'",
            "github.ref == 'refs/heads/main'", 'test "$GITHUB_SHA" = "$REVIEWED_MAIN_SHA"',
            "persist-credentials: false",
        ):
            self.assertIn(token,self.wf)
        for forbidden in ("\n  push:","\n  pull_request:","az functionapp create",
                          "az functionapp delete","rgai-dev-functions-d4e5ddbd",
                          "az functionapp config appsettings set"):
            self.assertNotIn(forbidden,self.wf)

    def test_build_is_vendored_and_all_get_only_before_readonly_preflight(self):
        tokens=[
            "build_five_get_release.py",
            "verify_staged_y1_auth_transport.py",
            "pip install --disable-pip-version-check",
            "P0249_Y1_EXTERNAL_FIVE_GET_PREVENDORED_INDEX=PASS",
            "p0249_y1_external_private_package.py preflight",
            'echo "attempted=true" >> "$GITHUB_OUTPUT"',
            "p0249_y1_external_private_package.py publish",
            "p0249_y1_external_private_package.py verify",
        ]
        positions=[]
        for token in tokens:
            self.assertIn(token,self.wf)
            positions.append(self.wf.index(token))
        self.assertEqual(positions,sorted(positions))
        self.assertIn('m["bindings"][0]["methods"]==["get"]',self.wf)
        self.assertNotIn("--build-remote true",self.wf)
        self.assertNotIn("deployment source config-zip",self.wf)

    def test_real_negative_auth_soak_and_exact_original_rollback(self):
        for token in (
            "P0249_Y1_START_IDLE_SECONDS=240", "status==401",
            "marker and seconds<18", "g.probe()", "NoRedirects",
            "on_exit()", "trap on_exit EXIT", "p0249_y1_external_private_package.py rollback",
            "independent-restore:", "needs.deploy.outputs.attempted == 'true'",
            "needs.deploy.result != 'success'", "P0249_Y1_VERSIONED_PRIVATE_FIVE_GET_HOSTED_NEGATIVE_AUTH=PASS"
        ):
            self.assertIn(token,self.wf)
        self.assertNotIn("SIGNED_RLS=PASS",self.wf)

    def test_private_storage_and_original_uri_rollback_are_bounded(self):
        for token in (
            'ACCOUNT = guard.STORAGE', "EXPECTED_FAILED_OWNER",
            "mode._package_url(old)", "settings.get(OLD_OWNER)",
            'az', 'generate-sas', '"--as-user"', '"--auth-mode", "login"',
            '"--overwrite", "false"', '"--permissions", "r"',
            "mode._set(**{PACKAGE_KEY:uri})", "mode._set(**{PACKAGE_KEY:old})",
            "mode.TWO", "mode.FIVE",
        ):
            self.assertIn(token,self.helper)
        for banned in ("--account-key", 'print(uri)', 'print(sas)',
                       'print(old)', "storage account keys list",
                       "functionapp create", "az group delete",
                       "az functionapp scale"):
            self.assertNotIn(banned,self.helper)
        self.assertIn("FAILED_REDACTED",self.helper)


if __name__=="__main__":
    unittest.main()
