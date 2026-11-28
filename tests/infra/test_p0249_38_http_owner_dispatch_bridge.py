"""Offline contract for the owner-authorized protected 38-HTTP launcher."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / ".github/workflows/p0249-y1-38-http-owner-dispatch-once.yml"
TARGET = ROOT / ".github/workflows/p0249-dev-y1-five-to-38-http-protected.yml"


class Protected38LauncherTests(unittest.TestCase):
    def test_dispatch_requires_actual_stage_and_exact_main(self):
        text = BRIDGE.read_text()
        self.assertIn("branches: [main]", text)
        self.assertIn("ops(#249): owner-delegated Y1 38 HTTP dispatch", text)
        self.assertIn("77e678355c8e4a0ba20a8bbf88084f6d2814edd6", text)
        self.assertIn("P0249_OWNER_PINNED_ACTION_MAIN_CI_4OF4=PASS", text)
        self.assertIn("P0249_PRIOR_PROTECTED_CORE_STAGE=VERIFIED", text)
        self.assertLess(text.index("P0249_PRIOR_PROTECTED_CORE_STAGE=VERIFIED"), text.index("gh api -X POST"))
        self.assertIn("Main advanced; refuse dispatch", text)
        self.assertIn(".total_count == 0", text)
        self.assertIn("YES-P0249-DEV-Y1-FIVE-TO-38-WITH-FIVE-ROLLBACK", text)
        self.assertEqual(text.count("gh api -X POST"), 1)
        for forbidden in ("azure/login", "id-token: write", "secrets.", "schedule:", "pull_request:", "p0249-dev-y1-core-connections-protected.yml/dispatches"):
            self.assertNotIn(forbidden, text)

    def test_target_remains_manual_dev_and_rollback(self):
        text = TARGET.read_text()
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("environment: dev", text)
        self.assertIn("--mode http-only", text)
        self.assertIn("independent-restore:", text)
        self.assertIn("sleep 240", text)
        self.assertNotIn("\n  push:", text)


if __name__ == "__main__":
    unittest.main()
