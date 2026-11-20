"""Ensure the completed Issue #249 read-only dispatch bridge stays retired."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / ".github/workflows/p0249-flex-incident-delegated-once.yml"
MANUAL = ROOT / ".github/workflows/p0-249-incident-platform-readonly-manual.yml"
COLLECTOR = ROOT / "ops/p0_249_recent_http_platform_readonly.py"


class OriginalFlexDelegatedOnceTests(unittest.TestCase):
    def test_temporary_actions_write_bridge_removed(self):
        self.assertFalse(BRIDGE.exists(), "One-shot privileged Actions bridge must be retired")

    def test_permanent_diagnostic_stays_explicitly_manual_and_read_only(self):
        self.assertTrue(MANUAL.is_file())
        self.assertTrue(COLLECTOR.is_file())
        workflow = MANUAL.read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch'", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("environment: dev", workflow)
        self.assertIn("YES-P0249-FLEX-INCIDENT-READONLY", workflow)
        for trigger in ("push", "schedule", "workflow_run", "repository_dispatch"):
            self.assertNotIn("  " + trigger + ":", workflow)
        for denied in ("az storage blob upload", "az functionapp config set",
                       "az role assignment create", "az deployment group create"):
            self.assertNotIn(denied, workflow)


if __name__ == "__main__":
    unittest.main()
