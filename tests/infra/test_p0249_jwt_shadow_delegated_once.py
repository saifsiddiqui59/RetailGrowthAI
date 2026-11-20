"""Keep temporary Issue #249 privileged GitHub dispatch bridge retired."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / ".github/workflows/p0249-jwt-y1-shadow-delegated-once.yml"
PROTECTED = ROOT / ".github/workflows/p0249-dev-y1-public-shadow-bounded-once.yml"


class JwtShadowDelegatedOnceTests(unittest.TestCase):
    def test_completed_actions_write_dispatch_bridge_removed(self):
        self.assertFalse(BRIDGE.exists(), "One-time JWT dispatch bridge must be retired")

    def test_permanent_dev_workflow_preserves_scoped_secret_and_cleanup(self):
        self.assertTrue(PROTECTED.is_file())
        workflow = PROTECTED.read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch'", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("environment: dev", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("independent-restore:", workflow)
        self.assertIn("RGAI_DEV_SERVICE_KEY: ${{ secrets.RETAIL_SUPABASE_SERVICE_ROLE_KEY }}", workflow)
        self.assertIn("p0249_y1_signed_auth_shadow_once.py cleanup-only", workflow)
        self.assertIn("p0249_y1_public_shadow_trial_guard.py rollback", workflow)
        self.assertIn("YES-Y1-DEV-PUBLIC-SHADOW-BOUNDED", workflow)
        self.assertNotIn("RGAI_DEV_SERVICE_KEY=", workflow)
        for trigger in ("push", "schedule", "pull_request", "workflow_run"):
            self.assertNotIn("  " + trigger + ":", workflow)


if __name__ == "__main__":
    unittest.main()
