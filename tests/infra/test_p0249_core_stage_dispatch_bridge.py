"""Offline guard for the bounded GitHub-only owner-dispatch bridge."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / ".github/workflows/p0249-y1-core-stage-owner-dispatch-once.yml"
TARGET = ROOT / ".github/workflows/p0249-dev-y1-core-connections-protected.yml"


class CoreStageDispatchBridgeTests(unittest.TestCase):
    def test_one_shot_scoped_dispatch(self):
        if not BRIDGE.exists():
            self.skipTest("Consumed bridge retired")
        text = BRIDGE.read_text()
        for required in (
            "branches: [main]", "github.event_name == 'push'",
            "github.ref == 'refs/heads/main'", "ops(#249): owner-delegated Y1 core stage dispatch",
            ".github/workflows/p0249-y1-core-stage-owner-dispatch-once.yml", "actions: write",
            "P0249_OWNER_PINNED_ACTION_MAIN_CI_4OF4=PASS",
            "Main advanced; refuse dispatch", "refuse duplicate",
            "p0249-dev-y1-core-connections-protected.yml/dispatches",
            "YES-P0249-RETAILGROWTHAI-DEV-Y1-MISSING-ONLY",
        ):
            self.assertIn(required, text)
        self.assertEqual(text.count("gh api -X POST"), 1)
        for forbidden in ("azure/login", "id-token: write", "secrets.", "schedule:", "pull_request:", "five-to-38-http-protected.yml/dispatches"):
            self.assertNotIn(forbidden, text)

    def test_target_remains_manual_protected(self):
        target = TARGET.read_text()
        self.assertIn("workflow_dispatch:", target)
        self.assertIn("environment: dev", target)
        self.assertIn("id-token: write", target)
        self.assertIn("stage_core_connections.py --apply", target)
        self.assertIn("P0249_Y1_POST_STAGE_HTTP=PASS", target)
        self.assertNotIn("\n  push:", target)


if __name__ == "__main__":
    unittest.main()
