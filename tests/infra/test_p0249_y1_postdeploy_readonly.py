"""Read-only Y1 post-deploy workflow safety checks."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/p0249-dev-y1-post202-readonly-once.yml"


class Y1Post202ReadOnlyTests(unittest.TestCase):
    def test_readonly_workflow_uses_only_existing_y1_site(self):
        w = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("rgai-dev-y1-p0249-d4e5ddbd", w)
        self.assertIn("environment: dev", w)
        self.assertIn("refs/heads/main", w)
        self.assertIn("workflow_dispatch:", w)
        self.assertIn("YES-READONLY-Y1-INDEX", w)
        self.assertIn("az functionapp function list", w)
        self.assertIn("p0249_y1_canary_guard.py verify", w)
        self.assertIn("g.probe()", w)

    def test_never_create_deploy_delete_or_mutate(self):
        w = WORKFLOW.read_text(encoding="utf-8")
        for forbidden in (
            "az deployment group create",
            "az functionapp deployment source",
            "az resource delete",
            "az group delete",
            "az functionapp delete",
            "az functionapp config appsettings set",
            "az functionapp scale config always-ready set",
            "az storage account delete",
        ):
            with self.subTest(command=forbidden):
                self.assertNotIn(forbidden, w)

    def test_fails_closed_before_http_when_identity_not_verified(self):
        w = WORKFLOW.read_text(encoding="utf-8")
        self.assertLess(
            w.index("python3 -u ops/p0249_y1_canary_guard.py verify"),
            w.index("g.probe()"),
        )


if __name__ == "__main__":
    unittest.main()
