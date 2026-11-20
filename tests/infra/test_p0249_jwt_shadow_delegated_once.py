"""Strict offline proof of #249 one-shot GitHub-only Y1 signed JWT dispatch."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / ".github/workflows/p0249-jwt-y1-shadow-delegated-once.yml"
PROTECTED = ROOT / ".github/workflows/p0249-dev-y1-public-shadow-bounded-once.yml"


class JwtShadowDelegatedOnceTests(unittest.TestCase):
    def test_one_shot_exact_main_push_trigger_and_immutable_sources(self):
        b = BRIDGE.read_text()
        self.assertIn("on:", b)
        self.assertIn("branches: [main]", b)
        self.assertIn('".github/workflows/p0249-jwt-y1-shadow-delegated-once.yml"', b)
        self.assertIn("startsWith(github.event.head_commit.message, 'ops(#249): launch bounded Y1 signed JWT shadow trial')", b)
        for sha in ("282d3449a188926eb729f570e1d7df1245c40518",
                    "3b30c85411d9a81e93ea76256f5860f28acdef44",
                    "d697b173b2c407293da67c7438a999a2fbe085f1",
                    "331d4d814b4073345668c415bf2459c89e333d0c"):
            self.assertIn(sha, b)
        for trigger in ("workflow_dispatch", "schedule", "pull_request",
                        "workflow_run", "repository_dispatch"):
            self.assertNotIn("  " + trigger + ":", b)

    def test_bridge_is_github_only_and_waits_all_four_main_checks(self):
        b = BRIDGE.read_text()
        self.assertIn("actions: write", b)
        self.assertIn("persist-credentials: false", b)
        self.assertIn("P0249_Y1_SIGNED_JWT_DISPATCH_MAIN_CI=PASS_4OF4", b)
        self.assertIn('test "$current" = "$GITHUB_SHA"', b)
        for name in ("Python / uv + campaign contract tests",
                     "Frontend build + contract tests",
                     "FFmpeg codecs + renderer tests",
                     "Supabase isolation + authentication client tests"):
            self.assertIn(name, b)
        self.assertIn('gh workflow run p0249-dev-y1-public-shadow-bounded-once.yml --ref main', b)
        self.assertIn("-f confirm=YES-Y1-DEV-PUBLIC-SHADOW-BOUNDED", b)
        for denied in ("azure/login", "id-token: write", "az functionapp",
                       "az storage", "az role", "RGAI_DEV_SERVICE_KEY",
                       "RETAIL_SUPABASE_SERVICE_ROLE_KEY", "gh secret",
                       "gh workflow disable"):
            self.assertNotIn(denied, b)

    def test_permanent_dev_workflow_retains_independent_rollback_and_scoped_secret(self):
        workflow = PROTECTED.read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("environment: dev", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("independent-restore:", workflow)
        self.assertIn("RGAI_DEV_SERVICE_KEY: ${{ secrets.RETAIL_SUPABASE_SERVICE_ROLE_KEY }}", workflow)
        self.assertIn("p0249_y1_signed_auth_shadow_once.py cleanup-only", workflow)
        self.assertIn("p0249_y1_public_shadow_trial_guard.py rollback", workflow)
        self.assertIn("YES-Y1-DEV-PUBLIC-SHADOW-BOUNDED", workflow)
        self.assertNotIn("RGAI_DEV_SERVICE_KEY=", workflow)


if __name__ == "__main__":
    unittest.main()
