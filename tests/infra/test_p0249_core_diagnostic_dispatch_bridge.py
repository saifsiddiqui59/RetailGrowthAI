"""Source guards for one protected, read-only core diagnostic dispatch."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class CoreDiagnosticDispatchBridge(unittest.TestCase):
    def test_only_existing_readonly_target(self):
        code = (ROOT / ".github/workflows/p0249-y1-core-diagnostic-owner-dispatch-once.yml").read_text()
        self.assertEqual(code.count("gh api -X POST"), 1)
        self.assertIn("p0249-y1-deploy-diagnostic-readonly-once.yml/dispatches", code)
        self.assertIn("YES-Y1-READONLY-BUILD", code)
        self.assertIn("46123450728", code)
        self.assertIn("P0249_OWNER_PINNED_ACTION_MAIN_CI_4OF4=PASS", code)
        self.assertIn("Main advanced; refuse dispatch", code)
        for token in ("id-token: write", "azure/login", "secrets.", "core-connections-protected.yml/dispatches", "five-to-38-http-protected.yml/dispatches"):
            self.assertNotIn(token, code)

if __name__ == "__main__":
    unittest.main()
