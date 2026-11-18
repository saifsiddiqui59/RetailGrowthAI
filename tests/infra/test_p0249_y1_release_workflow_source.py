"""Offline hard safety gates for manual-only Issue #249 five-GET release."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / ".github/workflows/p0249-dev-y1-five-get-release-manual.yml"
PACKAGE = ROOT / "ops/p0249-y1-readonly-extra-get/build_five_get_release.py"


class Y1FiveGetManualReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.y = WF.read_text(encoding="utf-8")

    def test_workflow_is_manual_only_main_and_reviewed_sha(self):
        self.assertIn("\non:\n  workflow_dispatch:\n", self.y)
        self.assertNotIn("\n  push:", self.y)
        self.assertNotIn("\n  pull_request:", self.y)
        for word in (
            "refs/heads/main", "reviewed_main_sha",
            'test "$GITHUB_SHA" = "$REVIEWED_MAIN_SHA"',
            "YES-P0249-DEV-Y1-FIVE-GET-ROLLBACK",
            "environment: dev", "id-token: write",
            "concurrency:", "cancel-in-progress: false",
            "persist-credentials: false",
        ):
            with self.subTest(word=word):
                self.assertIn(word, self.y)

    def test_no_mutating_dev_settings_or_new_app_or_original_flex(self):
        for forbidden in (
            "az functionapp create", "az functionapp delete",
            "az group delete", "az resource delete",
            "az functionapp config appsettings set",
            "az functionapp config appsettings delete",
            "az deployment group create",
            "az functionapp scale",
            "rgai-dev-functions-d4e5ddbd",  # only exact isolated Y1 is targeted
            "retail-dev-part1-live-release",
            "service_role", "sb_secret_",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.y)

    def test_only_exact_isolated_y1_is_deployment_target(self):
        self.assertIn("-n rgai-dev-y1-p0249-d4e5ddbd", self.y)
        self.assertIn("p0249_y1_canary_guard.py verify", self.y)
        self.assertIn('set -euo pipefail', self.y)
        self.assertIn("az functionapp deployment source config-zip", self.y)
        self.assertIn("--build-remote false", self.y)
        self.assertIn("P0249_Y1_FIVE_GET_INDEXED=", self.y)
        self.assertIn("P0249_Y1_DEPLOY_PREFLIGHT=EXACT_TWO", self.y)
        self.assertIn('len(names)==5 and set(names)==expected', self.y)

    def test_two_route_rollback_both_same_run_and_independent(self):
        self.assertIn("mode rollback-two", self.y)
        self.assertIn("upload-artifact@v4", self.y)
        self.assertIn("download-artifact@v4", self.y)
        self.assertIn("independent-restore:", self.y)
        self.assertIn("needs.deploy.outputs.attempted == 'true'", self.y)
        self.assertIn("needs.deploy.result != 'success'", self.y)
        self.assertIn("trap on_exit EXIT", self.y)
        self.assertIn('trap - EXIT', self.y)
        self.assertIn('P0249_Y1_INDEPENDENT_TWO_GET_ROLLBACK=PASS', self.y)
        self.assertIn("set(names)<=allowed", self.y)
        self.assertIn("RG", (ROOT / "ops/p0249_y1_canary_guard.py").read_text())

    def test_same_run_rollback_revalidates_identity_index_and_settings(self):
        self.assertIn("P0249_Y1_SELF_ROLLBACK_PREFLIGHT=EXACT_KNOWN_ROUTES_NO_SHADOW_SETTINGS", self.y)
        self.assertIn("Y1 identity drifted; refuse same-run rollback", self.y)
        self.assertIn("Unknown Y1 index; refuse same-run overwrite", self.y)
        self.assertIn("Y1 settings changed; deny same-run rollback", self.y)
        self.assertIn("y1-pre-revert-index.json", self.y)
        self.assertIn("set(names)<=allowed", self.y)

    def test_read_only_get_after_idle_no_positive_claim(self):
        for proof in (
            "P0249_Y1_START_IDLE_SECONDS=240",
            "g.probe()", "marker and seconds<18",
            'status==401', "httpTrigger",
            '"methods"',  # manifest verified via separate source tests
            'SIGNED_RLS',  # never claim positive hosted RLS
        ):
            if proof == '"methods"':
                self.assertIn('["methods"]==["get"]', self.y)
            elif proof == "SIGNED_RLS":
                self.assertNotIn("SIGNED_RLS=PASS", self.y)
            else:
                self.assertIn(proof, self.y)

    def test_real_y1_get_probe_is_redirect_denied_and_closes_http_errors(self):
        self.assertIn("class NoRedirects(urllib.request.HTTPRedirectHandler)", self.y)
        self.assertIn("def redirect_request(self, req, fp, code, msg, headers, newurl):", self.y)
        self.assertIn("return None", self.y)
        self.assertIn("opener=urllib.request.build_opener(NoRedirects())", self.y)
        self.assertIn("err.close()", self.y)
        self.assertIn("status,marker,seconds=guarded_get(path)", self.y)

    def test_builder_never_calls_azure_or_queues(self):
        code = PACKAGE.read_text()
        for token in ("subprocess.run(", "az functionapp",
                      "function_app.py", "queue_trigger", "timer_trigger"):
            if token == "function_app.py":
                self.assertIn('if (target / "function_app.py").exists():', code)
            else:
                self.assertNotIn(token, code)


if __name__ == "__main__":
    unittest.main()
