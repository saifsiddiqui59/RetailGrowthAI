"""One-shot original Flex read-only dispatcher: offline immutable safety gates."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
BRIDGE=ROOT/".github/workflows/p0249-flex-incident-delegated-once.yml"
MANUAL=ROOT/".github/workflows/p0-249-incident-platform-readonly-manual.yml"
COLLECTOR=ROOT/"ops/p0_249_recent_http_platform_readonly.py"


class OriginalFlexDelegatedOnceTests(unittest.TestCase):
    def test_one_time_main_push_only_and_source_blobs_pinned(self):
        wf=BRIDGE.read_text()
        self.assertIn('on:\n  push:\n    branches: [main]',wf)
        self.assertIn('".github/workflows/p0249-flex-incident-delegated-once.yml"',wf)
        self.assertIn('github.ref == \'refs/heads/main\'',wf)
        self.assertIn('github.event_name == \'push\'',wf)
        self.assertIn("startsWith(github.event.head_commit.message, 'ops(#249): launch original Flex historical read-only query')",wf)
        self.assertIn('2eceff11359b22e74859282bef684267bab003e3',wf)
        self.assertIn('6aefe12004852926cd16f32c500c03c14876a7e9',wf)
        self.assertTrue(MANUAL.is_file())
        self.assertTrue(COLLECTOR.is_file())
        for denied in ('\n  workflow_dispatch:', '\n  schedule:', '\n  pull_request:'):
            self.assertNotIn(denied,wf)

    def test_actions_write_only_dispatches_exact_protected_manual_job_after_main_ci(self):
        wf=BRIDGE.read_text()
        manual=MANUAL.read_text()
        self.assertIn('actions: write',wf)
        self.assertIn('persist-credentials: false',wf)
        self.assertIn('P0249_ORIGINAL_FLEX_DISPATCH_MAIN_CI=PASS_4OF4',wf)
        self.assertIn('P0249_ORIGINAL_FLEX_FIXED_SOURCE=PASS_NO_AZURE_WRITES',wf)
        self.assertIn('P0249_ORIGINAL_FLEX_PROTECTED_READONLY_DISPATCH=REQUESTED',wf)
        self.assertIn('status == "completed"',wf)
        self.assertIn('conclusion == "success"',wf)
        for job in ("Python / uv + campaign contract tests",
                    "Frontend build + contract tests",
                    "FFmpeg codecs + renderer tests",
                    "Supabase isolation + authentication client tests"):
            self.assertIn(job,wf)
        self.assertIn('gh workflow run p0-249-incident-platform-readonly-manual.yml --ref main',wf)
        self.assertIn('-f confirm=YES-P0249-FLEX-INCIDENT-READONLY',wf)
        self.assertIn('github.event_name == \'workflow_dispatch\'',manual)
        self.assertIn('environment: dev',manual)
        self.assertIn('id-token: write',manual)

    def test_dispatch_bridge_cannot_access_azure_or_mutate_resources(self):
        wf=BRIDGE.read_text()
        for forbidden in (
            "azure/login", "az login", "az functionapp", "az resource",
            "az storage", "az monitor", "az role", "az deployment",
            "curl --request POST", "curl -X POST", "id-token: write",
            "actions:checkout@v0", "gh workflow disable"):
            self.assertNotIn(forbidden,wf)
        self.assertIn('test "$current" = "$GITHUB_SHA"',wf)
        self.assertIn('cancel-in-progress: false',wf)


if __name__=="__main__":
    unittest.main()
