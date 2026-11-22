"""Static fail-closed boundary for the opt-in real hosted Feature4 test suite.

This is source-contract verification only: it does not constitute a hosted E2E PASS.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "frontend/e2e/feature4-cpu.hosted.mjs"


class Feature4HostedAcceptanceContract(unittest.TestCase):
    def test_real_two_shop_suite_is_opt_in(self):
        source = SPEC.read_text(encoding="utf-8")
        self.assertIn("hostedConfig(process.env)", source)
        self.assertIn("RG_F4_E2E_TEST_RENDER_CONSENT", source)
        self.assertIn("RG_F4_E2E_WORKER_VERIFIED", source)
        self.assertIn("RG_F4_E2E_CAMPAIGN_ID", source)
        self.assertIn("RG_F4_E2E_DAY_ID", source)
        self.assertIn("test.describe.serial", source)
        self.assertNotIn(".route(", source)
        self.assertNotIn("route.fulfill", source)
        self.assertNotIn("service_role", source.lower().replace("never emulate root approval or use service_role", ""))

    def test_approval_and_private_media_verification_are_retained(self):
        source = SPEC.read_text(encoding="utf-8")
        for snippet in (
            "'/feature4-creative-plans/'",
            "'/feature4-render-jobs/'",
            "'/feature4-plans'",
            "'/feature4-renders'",
            "expected_source_sha256",
            "expected_review_hash",
            "signedDownloadUrl(",
            "'ffprobe'",
            "'h264'",
            "'aac'",
            "shop_id === cfg.shopB",
            "cfg.expiredJwt",
            "'REVOKED'",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)


if __name__ == "__main__":
    unittest.main()
