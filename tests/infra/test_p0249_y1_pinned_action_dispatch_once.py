"""One-shot owner-delegated protected Y1 five-GET dispatch: source-only gates."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / ".github/workflows/p0249-y1-pinned-action-owner-dispatch-once.yml"
TARGET = ROOT / ".github/workflows/p0249-dev-y1-five-get-remote-build-protected.yml"


class P0249PinnedActionDispatchTests(unittest.TestCase):
    def setUp(self):
        self.source = BRIDGE.read_text()
        self.target = TARGET.read_text()

    def test_dispatch_is_one_shot_push_main_only_not_direct_azure(self):
        w = self.source
        for marker in (
            "on:\n  push:\n    branches: [main]",
            "paths:\n      - \".github/workflows/p0249-y1-pinned-action-owner-dispatch-once.yml\"",
            "startsWith(github.event.head_commit.message, 'ops(#249): owner-delegated pinned action Y1 release')",
            "github.ref == 'refs/heads/main'",
            "github.event_name == 'push'",
            "permissions:\n  contents: read\n  actions: write",
            "persist-credentials: false",
            'test "$(git rev-parse HEAD)" = "$GITHUB_SHA"',
        ):
            self.assertIn(marker, w)
        for forbidden in ("az functionapp", "az storage", "azure/login@", "workflow_dispatch:\n"):
            self.assertNotIn(forbidden, w)

    def test_all_source_pins_and_official_action(self):
        w = self.source
        for sha in (
            "ea7a6411ce011fc8e7b9cffc8ca097d1c950869a",
            "fc67d27105dedd2f06f39162f901fb39831246c5",
            "b6cc730a0bce59093e831965ca4ee1f817121203",
            "109098490b767dae3d4f01f1c3b2284560b23eb1",
            "d5091e4cf14071473813b77226c2a5ad61b84635",
            "139069d79029d6a84112ec389ece0d0f111e341a",
            "e10548a4dbc27795028d1141c548a6209aa90135",
            "c5060b3b8bb1ebbcb531abd00c822ecbaa8ea656",
        ):
            self.assertIn(sha, w)
        self.assertIn("Azure/functions-action@c5060b3b8bb1ebbcb531abd00c822ecbaa8ea656", self.target)
        self.assertIn("scm-do-build-during-deployment: 'true'", self.target)
        self.assertIn("enable-oryx-build: 'true'", self.target)

    def test_requires_real_exact_main_four_job_ci_and_only_pinned_protected_dispatch(self):
        w = self.source
        for s in (
            'run_id="$(jq',
            'test "$outcome" = "success"',
            '"Python / uv + campaign contract tests"',
            '"Supabase isolation + authentication client tests"',
            '"Frontend build + contract tests"',
            '"FFmpeg codecs + renderer tests"',
            'length == 4 and all(.[]; . == "success")',
            'test "$current" = "$GITHUB_SHA"',
            'test "$duplicate" = "0"',
            'YES-P0249-DEV-Y1-REMOTE-BUILD-ROLLBACK',
            "p0249-dev-y1-five-get-remote-build-protected.yml/dispatches",
            'reviewed_main_sha:$sha',
        ):
            self.assertIn(s, w)
        for s in ("environment: dev", "id-token: write", "cancel-in-progress: false", "independent-restore:"):
            self.assertIn(s, self.target)

if __name__ == "__main__":
    unittest.main()
