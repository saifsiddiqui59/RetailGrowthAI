"""Source-only invariant checks for the protected five->38 Y1 release workflow."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (ROOT / "ops/p0249-y1-cutover/five_to_38_release.py").read_text()
FLOW = (ROOT / ".github/workflows/p0249-dev-y1-five-to-38-http-protected.yml").read_text()
TESTS = (ROOT / "tests/infra/test_p0249_y1_five_to_38_release.py").read_text()


class ProtectedReleaseSourceTests(unittest.TestCase):
    def test_manual_exact_main_dev_guard_and_oidc_only(self):
        self.assertIn("  workflow_dispatch:", FLOW)
        self.assertNotRegex(FLOW, r"(?m)^  (push|pull_request|schedule):")
        self.assertIn("github.ref == 'refs/heads/main'", FLOW)
        self.assertIn('test "$REVIEWED_MAIN_SHA" = "$GITHUB_SHA"', FLOW)
        self.assertIn("environment: dev", FLOW)
        self.assertIn("id-token: write", FLOW)
        self.assertNotIn("roles/assignments", FLOW)
        self.assertNotIn("az role assignment create", FLOW)

    def test_package_is_38_http_and_never_starts_workers(self):
        self.assertIn('assert len(methods) == 38', FLOW)
        self.assertIn('assert not (set(methods) & mod.WORKERS)', FLOW)
        self.assertIn("--mode http-only", FLOW)
        self.assertNotIn("--mode http-with-short-workers", FLOW)
        self.assertNotIn("az functionapp stop", FLOW)
        self.assertNotIn("az functionapp restart", FLOW)
        self.assertNotIn("az functionapp config appsettings set", FLOW)
        self.assertNotIn("AzureWebJobs.render_campaign_reel.Disabled=true", FLOW)
        self.assertIn("rgai-dev-y1-p0249-d4e5ddbd", FLOW)
        # The source ZIP has requirements.txt but no vendored .python_packages;
        # disabling both build flags would make Azure unable to import Python deps.
        self.assertIn("scm-do-build-during-deployment: 'true'", FLOW)
        self.assertIn("enable-oryx-build: 'true'", FLOW)
        self.assertNotIn("scm-do-build-during-deployment: 'false'", FLOW)
        self.assertNotIn("enable-oryx-build: 'false'", FLOW)
        self.assertNotIn("app-name: rgai-dev-functions-d4e5ddbd", FLOW)

    def test_prewrite_guard_and_two_real_windows(self):
        self.assertLess(
            FLOW.index("Fail closed on missing shared DEV connections BEFORE any Azure write"),
            FLOW.index("Backup exact five-route active private Blob URL"))
        self.assertIn('"y1_same_core_connection_values"', FLOW)
        self.assertIn('"y1_frontend_cors_allowed"', FLOW)
        self.assertIn('"y1_any_background_triggers"', FLOW)
        self.assertIn("sleep 240", FLOW)
        self.assertGreaterEqual(FLOW.count("guard.probe()"), 3)
        self.assertGreaterEqual(FLOW.count("P0249_Y1_HTTP_MISSING_JWT=3_OF_3_MARKED_401"), 2)
        self.assertIn("P0249_Y1_FIVE_TO_38_PREFLIGHT=FIVE_PINNED_NO_WRITE", SCRIPT)

    def test_restore_is_real_five_not_historical_two(self):
        self.assertIn("FIVE = legacy.FIVE", SCRIPT)
        self.assertIn("THIRTY_EIGHT = HTTP |", SCRIPT)
        self.assertIn("legacy._run_id()", SCRIPT)
        self.assertIn('"syncfunctiontriggers"', SCRIPT)
        self.assertIn("if not _wait_for_five()", SCRIPT)
        self.assertIn("guard.probe()", SCRIPT)
        self.assertIn("legacy._delete(BACKUP, OWNER, ORYX_BASELINE)", SCRIPT)
        self.assertIn('legacy._delete("WEBSITE_RUN_FROM_PACKAGE")', SCRIPT)
        self.assertIn('legacy._set(ENABLE_ORYX_BUILD="true")', SCRIPT)
        self.assertIn("ORYX_BASELINE", SCRIPT)
        self.assertIn('steps.release_marker.outputs.attempted', FLOW)
        self.assertIn("independent-restore:", FLOW)
        self.assertIn("five_to_38_release.py rollback", FLOW)
        self.assertIn("test_foreign_and_duplicate_index_deny_before_rollout", TESTS)
        self.assertIn("test_unknown_worker_denies_rollback_before_appsettings_write", TESTS)


if __name__ == "__main__":
    unittest.main()
