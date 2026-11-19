"""Assert Part 1 CI keeps real browser/media checks without Ubuntu apt mirrors.

Only CI setup changes here; no Azure deployments, tenant/auth changes, model
billing, or feature completion evidence. All four mandatory jobs must remain.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/frontend-bootstrap.yml"
E2E_PACKAGE = ROOT / "frontend/e2e/package.json"


class AptIndependentCISourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.browser = cls.workflow.split("  frontend:\n", 1)[1].split("  python:\n", 1)[0]
        cls.media = cls.workflow.split("  video:\n", 1)[1].split("  security:\n", 1)[0]

    def test_all_four_mandatory_jobs_remain(self):
        for name in ("  frontend:", "  python:", "  video:", "  security:"):
            with self.subTest(name=name):
                self.assertIn(name, self.workflow)
        self.assertIn("permissions:\n  contents: read", self.workflow)

    def test_playwright_real_browser_and_preinstalled_deps_exact_version(self):
        self.assertIn("container: mcr.microsoft.com/playwright:v1.56.1-noble", self.browser)
        self.assertIn("PLAYWRIGHT_BROWSERS_PATH: /ms-playwright", self.browser)
        self.assertIn('"@playwright/test": "1.56.1"', E2E_PACKAGE.read_text())
        self.assertIn('chromium.executablePath()', self.browser)
        self.assertIn('existsSync(path)', self.browser)
        self.assertIn('npm --prefix e2e test', self.browser)
        self.assertIn('npm run build', self.browser)
        self.assertIn('npm test', self.browser)
        self.assertNotIn("apt-get", self.browser)
        self.assertNotIn("playwright install --with-deps", self.browser)

    def test_real_renderer_and_pinned_codecs_remain_mandatory(self):
        for exact in (
            "ffmpeg-static@5.3.0",
            "@derhuerst/ffprobe-static@5.3.0",
            "ffmpeg -hide_banner -encoders",
            "libx264", "aac",
            "ffmpeg -nostdin -hide_banner -loglevel error -y",
            "ffprobe", "ci-artifacts/ffmpeg-smoke.mp4",
            "bash video-engine/ci.sh",
            "retention-days: 3",
        ):
            with self.subTest(exact=exact):
                self.assertIn(exact, self.media)
        self.assertNotIn("apt-get", self.media)
        self.assertNotIn("|| true", self.media)
        self.assertNotIn("continue-on-error:", self.media)

    def test_no_feature_or_cloud_side_effects(self):
        for token in (
            "az login", "az functionapp", "supabase link",
            "npm audit fix", "pull_request_target:", "service_role",
            "skip-tests", "SKIP_BROWSER", "SKIP_FFMPEG",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, self.workflow)


if __name__ == "__main__":
    unittest.main()
