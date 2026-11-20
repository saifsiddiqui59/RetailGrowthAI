"""#249: retired one-shot original Y1 OAuth audit must never auto-run again."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / ".github/workflows/p0249-y1-original-package-head-once.yml"
MANUAL = ROOT / ".github/workflows/p0249-dev-y1-private-versioned-five-get-protected.yml"
SOURCE = ROOT / "ops/p0249_y1_external_private_package.py"
NEGATIVES = ROOT / "tests/infra/test_p0249_y1_original_blob_oauth_preflight.py"


class RetiredOriginalBlobProbeTests(unittest.TestCase):
    def test_completed_one_shot_has_no_push_trigger(self):
        self.assertFalse(BRIDGE.exists(),
                         "Remove temporary push-main OIDC audit after evidence")

    def test_permanent_private_release_remains_manual_and_guarded(self):
        self.assertTrue(MANUAL.is_file())
        self.assertTrue(SOURCE.is_file())
        self.assertTrue(NEGATIVES.is_file())
        workflow = MANUAL.read_text()
        source = SOURCE.read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch'", workflow)
        self.assertIn("environment: dev", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertNotIn("\n  schedule:", workflow)
        self.assertIn("def _oauth_head_original_private_blob(old_uri, container):", source)
        self.assertIn("_oauth_head_original_private_blob(old, container)", source)
        self.assertIn("mark_stage(\"BLOB_OAUTH_READ\")", source)
        self.assertIn('method="HEAD"', source)
        self.assertIn("PASS_NO_WRITES", source)
        for unsafe in ("--account-key", "az storage account keys list",
                       "role assignment create"):
            self.assertNotIn(unsafe, source)


if __name__ == "__main__":
    unittest.main()
