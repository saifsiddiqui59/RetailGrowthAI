"""Fail-closed workflow source checks for corrected Linux Y1 remote build."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
NEW = ROOT / ".github/workflows/p0249-dev-y1-five-get-remote-build-protected.yml"
ORIGINAL = ROOT / ".github/workflows/p0249-dev-y1-five-get-release-manual.yml"


class Y1RemoteBuildWorkflowSourceTests(unittest.TestCase):
    def setUp(self):
        self.new = NEW.read_text(encoding="utf-8")
        self.old = ORIGINAL.read_text(encoding="utf-8")

    def test_new_release_manual_only_exact_main_and_approved_confirmation(self):
        w = self.new
        for token in (
            "\non:\n  workflow_dispatch:", "reviewed_main_sha",
            "YES-P0249-DEV-Y1-REMOTE-BUILD-ROLLBACK",
            "github.event_name == 'workflow_dispatch'",
            "github.ref == 'refs/heads/main'",
            'test "$GITHUB_SHA" = "$REVIEWED_MAIN_SHA"',
            "environment: dev", "id-token: write",
            "rgai-p0249-y1-five-get-release", "cancel-in-progress: false",
            "persist-credentials: false",
        ):
            self.assertIn(token, w)
        self.assertNotIn("\n  push:", w)
        self.assertNotIn("\n  pull_request:", w)

    def test_original_manual_workflow_remains_unchanged_and_readonly_source(self):
        self.assertIn("YES-P0249-DEV-Y1-FIVE-GET-ROLLBACK", self.old)
        self.assertIn("--build-remote false", self.old)
        self.assertNotIn("ops/p0249_y1_remote_build_mode.py", self.old)
        self.assertNotIn("config appsettings set", self.new)
        self.assertNotIn("config appsettings delete", self.new)
        self.assertNotIn("az functionapp create", self.new)
        self.assertNotIn("az functionapp delete", self.new)
        self.assertNotIn("rgai-dev-functions-d4e5ddbd", self.new)

    def test_original_source_closure_is_validated_before_mutation_and_clean_zip(self):
        w = self.new
        checkpoints = (
            "build_five_get_release.py",
            "verify_staged_y1_auth_transport.py",
            'cp -a "$RUNNER_TEMP/y1-five" "$RUNNER_TEMP/y1-five-source"',
            'zip -qr "$RUNNER_TEMP/y1-five-source.zip"',
            "P0249_Y1_FIVE_AND_ROLLBACK_PACKAGES_BUILT=PASS",
            "p0249_y1_canary_guard.py verify",
            "P0249_Y1_DEPLOY_PREFLIGHT=EXACT_TWO",
            'echo "attempted=true" >> "$GITHUB_OUTPUT"',
            "p0249_y1_remote_build_mode.py prepare",
            "Azure/functions-action@c5060b3b8bb1ebbcb531abd00c822ecbaa8ea656",
            "scm-do-build-during-deployment: 'true'",
            "enable-oryx-build: 'true'",
            "p0249_y1_remote_build_mode.py verify-build-mode",
            "P0249_Y1_REMOTE_BUILD_FIVE_ROUTE_HOSTED_NEGATIVE_AUTH_ACCEPTED_BACKUP_RETAINED",
        )
        positions = []
        for token in checkpoints:
            self.assertIn(token, w)
            positions.append(w.index(token))
        self.assertEqual(sorted(positions), positions)

    def test_same_run_and_independent_rollback_do_not_repeat_bad_zip(self):
        w = self.new
        self.assertIn("trap on_exit EXIT", w)
        self.assertIn("p0249_y1_remote_build_mode.py rollback", w)
        self.assertIn("independent-restore:", w)
        self.assertIn("needs.deploy.outputs.attempted == 'true'", w)
        self.assertIn("needs.deploy.result != 'success'", w)
        self.assertIn("P0249_Y1_INDEPENDENT_ORIGINAL_EXTERNAL_ROLLBACK=PASS", w)
        self.assertIn("Same-run rollback after failed publication", w)
        self.assertIn("steps.mutation_marker.outputs.attempted == 'true'", w)
        self.assertNotIn("az functionapp deployment source config-zip", w)
        self.assertNotIn('          --src "$RUNNER_TEMP/y1-two.zip"', w)
        self.assertNotIn("--build-remote false", w)

    def test_lease_and_five_get_negative_401_still_enforced(self):
        w = self.new
        for token in (
            "P0249_Y1_START_IDLE_SECONDS=240",
            "g.probe()", "len(names)==5 and set(names)==expected",
            'status==401', "marker and seconds<18",
            "p0249_y1_remote_build_mode.py verify-five",
            "opener=urllib.request.build_opener(NoRedirects())",
            "err.close()", '["methods"]==["get"]'
        ):
            self.assertIn(token, w)
        self.assertNotIn("SIGNED_RLS=PASS", w)

    def test_no_obsolete_external_package_rejection_or_literal_secret_escape(self):
        self.assertNotIn("--fail-if-pinned-package", self.new)
        self.assertNotIn("\\${{", self.new)
        self.assertIn("env:\n      RGAI_DEV_EXPECTED_SUBSCRIPTION: ${{ secrets.AZURE_SUBSCRIPTION_ID }}",
                      self.new)
        bridge_path = ROOT / ".github/workflows/p0249-y1-owner-delegated-remote-build-once.yml"
        # The temporary dispatcher MUST be deleted after its single use;
        # permanent manual protected release tests above still always run.
        if not bridge_path.exists():
            return
        bridge = bridge_path.read_text()
        self.assertNotIn("\\${{", bridge)
        self.assertIn("GH_TOKEN: ${{ github.token }}", bridge)
        self.assertIn("c009961ab876f9336fac7941957658810eb56c8c", bridge)
        self.assertIn("on:\n  push:\n", bridge)
        self.assertIn("actions: write", bridge)
        self.assertIn("event=push", bridge)
        self.assertIn("P0249_OWNER_REMOTE_BUILD_EXACT_MAIN_CI_4OF4=PASS", bridge)
        self.assertIn("p0249-dev-y1-five-get-remote-build-protected.yml/dispatches", bridge)
        self.assertNotIn("az functionapp", bridge)

    def test_successful_one_shot_owner_dispatch_was_retired(self):
        # Hosted Y1 5/5 was accepted under #45021333842. Prevent a second
        # push-main dispatch from a consumed one-shot workflow or its test.
        self.assertFalse((ROOT / ".github/workflows/p0249-y1-pinned-action-owner-dispatch-once.yml").exists())
        self.assertFalse((ROOT / "tests/infra/test_p0249_y1_pinned_action_dispatch_once.py").exists())
        # Keep the protected manual release/rollback workflow separately.
        self.assertTrue(NEW.is_file())

    def test_original_pkg_backup_is_owned_and_sanitized_not_published(self):
        script = (ROOT / "ops/p0249_y1_remote_build_mode.py").read_text()
        for token in (
            "RGAI_P0249_Y1_BASELINE_PACKAGE_REF",
            "RGAI_P0249_Y1_REMOTE_BUILD_RUN_ID",
            '"GITHUB_RUN_ID"', 'guard.verify()',
            '_delete("WEBSITE_RUN_FROM_PACKAGE")',
            '_set(ENABLE_ORYX_BUILD="true")',
            "_set(WEBSITE_RUN_FROM_PACKAGE=old)",
            "guard.probe()",
            "P0249_Y1_REMOTE_BUILD_POSTPUBLISH_SETTINGS=PASS",
        ):
            self.assertIn(token, script)
        self.assertNotIn("print(original)", script)
        self.assertNotIn("print(old)", script)


if __name__ == "__main__":
    unittest.main()
