"""Regression: single-use #249 original Blob OAuth HEAD diagnostic stays read-only."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/p0249-y1-original-package-head-once.yml"


class OriginalPackageReadOnlyOnceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text()

    def test_single_owner_main_push_and_protected_dev_only(self):
        wf = self.source
        self.assertIn("on:\n  push:\n    branches: [main]", wf)
        self.assertIn('".github/workflows/p0249-y1-original-package-head-once.yml"', wf)
        self.assertIn("github.ref == 'refs/heads/main'", wf)
        self.assertIn("github.event_name == 'push'", wf)
        self.assertIn("startsWith(github.event.head_commit.message, 'ops(#249): inspect original Y1 package OAuth HEAD')", wf)
        self.assertIn("environment: dev", wf)
        self.assertIn("id-token: write", wf)
        for forbidden in ("\n  workflow_dispatch:", "\n  schedule:", "\n  pull_request:"):
            self.assertNotIn(forbidden, wf)

    def test_exact_pinned_source_and_four_current_main_ci_before_azure(self):
        wf = self.source
        self.assertIn("75137cb2da5b682611533ef8c484eaa71ffa6f51", wf)
        self.assertIn("0001d47e1987207a7cee86df1232b74e6990ac08", wf)
        self.assertIn("test_p0249_y1_original_blob_oauth_preflight.py", wf)
        self.assertIn("P0249_Y1_ORIGINAL_BLOB_CURRENT_MAIN_CI=PASS_4OF4", wf)
        self.assertIn("gh api", wf)
        self.assertIn("test \"$current\" = \"$GITHUB_SHA\"", wf)
        self.assertLess(wf.index("Require four successful exact current-main CI jobs"),
                        wf.index("azure/login@v3"))
        for job in ("Python / uv + campaign contract tests",
                    "Frontend build + contract tests",
                    "FFmpeg codecs + renderer tests",
                    "Supabase isolation + authentication client tests"):
            self.assertIn(job, wf)

    def test_only_original_blob_read_and_public_gets_no_config_mutation(self):
        wf = self.source
        self.assertIn("package.scoped_baseline(settings, index)", wf)
        self.assertIn("package._oauth_head_original_private_blob(original, container)", wf)
        self.assertIn("guard.probe()", wf)
        self.assertIn("P0249_Y1_ORIGINAL_BLOB_OAUTH_HEAD=DENIED_OR_INCONCLUSIVE_NO_WRITES", wf)
        self.assertIn("actions: read", wf)
        for unsafe in ("az storage blob upload", "az role assignment create",
                       "az storage account keys list", "az functionapp config",
                       "az webapp deploy", "gh workflow run", "actions: write",
                       "azure/functions-action", "service_role", "--account-key"):
            self.assertNotIn(unsafe, wf)


if __name__ == "__main__":
    unittest.main()
