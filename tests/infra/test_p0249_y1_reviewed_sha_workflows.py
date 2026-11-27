"""Fail-closed source guard for protected Y1 operator input in shell steps.

The SHA is untrusted workflow_dispatch text. Never interpolate its expression
into an executable Bash run block before validating its exact hex format.
This is offline only: no GitHub dispatch, Azure writes, secrets or network.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = (
    ROOT / ".github/workflows/p0249-dev-y1-core-connections-protected.yml",
    ROOT / ".github/workflows/p0249-dev-y1-five-to-38-http-protected.yml",
)


class ReviewedMainShaInputSafety(unittest.TestCase):
    def test_reviewed_sha_is_data_not_shell_source(self):
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow.name):
                text = workflow.read_text(encoding="utf-8")
                self.assertIn("workflow_dispatch:", text)
                self.assertIn("environment: dev", text)
                self.assertIn("REVIEWED_MAIN_SHA: ${{ inputs.reviewed_main_sha }}", text)
                # The expression may appear in the YAML env value, never
                # inside a run script where an injected $(...) would execute.
                for body in text.split("run: |")[1:]:
                    self.assertNotIn("${{ inputs.reviewed_main_sha }}", body)
                self.assertIn('[[ "$REVIEWED_MAIN_SHA" =~ ^[0-9a-f]{40}$ ]]', text)
                self.assertIn('test "$REVIEWED_MAIN_SHA" = "$GITHUB_SHA"', text)
                self.assertIn("id-token: write", text)

    def test_connection_stage_requires_live_health_before_success(self):
        text = WORKFLOWS[0].read_text(encoding="utf-8")
        before, after = text.split("      - name: Require live Y1 HTTP health after settings and CORS readback", 1)
        self.assertIn("python3 ops/p0249-y1-cutover/stage_core_connections.py --apply", before)
        self.assertNotIn("P0249_Y1_POST_STAGE_HTTP=PASS", before)
        self.assertIn("set -euo pipefail", after)
        self.assertIn("python3 ops/p0249_y1_canary_guard.py probe", after)
        self.assertLess(after.index("python3 ops/p0249_y1_canary_guard.py probe"),
                        after.index("P0249_Y1_POST_STAGE_HTTP=PASS"))
        self.assertNotIn("continue-on-error", after)
        self.assertNotIn("|| true", after)

    def test_staging_still_explicit_and_never_push_deployed(self):
        text = WORKFLOWS[0].read_text(encoding="utf-8")
        self.assertIn("inputs.confirm == 'YES-P0249-RETAILGROWTHAI-DEV-Y1-MISSING-ONLY'", text)
        self.assertIn('github.ref == \'refs/heads/main\'', text)
        self.assertNotIn("\n  push:", text)
        self.assertNotIn("\n  pull_request:", text)
        self.assertIn("python3 ops/p0249-y1-cutover/stage_core_connections.py --apply", text)


if __name__ == "__main__":
    unittest.main()
