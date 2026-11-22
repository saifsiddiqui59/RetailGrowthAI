"""Static release contract for original F4 CPU API and isolated worker gates."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "azure-functions" / "campaign-api" / "function_app.py"
WORKER = ROOT / "azure-functions" / "feature4-cpu-worker" / "function_app.py"
RUNBOOK = ROOT / "docs" / "FEATURE4_CPU_DEV_RELEASE_RUNBOOK_20261122.md"


class Feature4ActivationReleaseContract(unittest.TestCase):
    def test_original_api_requires_four_true_flags(self):
        source = API.read_text()
        start = source.index("feature4_api=(Feature4CpuRenderAPI(store)")
        end = source.index("feature4_review_api=(Feature4PlanReviewAPI(store)")
        block = source[start:end]
        for name in ("RETAIL_FEATURE4_PLAN_ISSUE_ENABLED",
                     "RETAIL_FEATURE4_PLAN_REVIEW_ENABLED",
                     "RETAIL_FEATURE4_CPU_WORKER_ENABLED",
                     "RETAIL_FEATURE4_CPU_RENDER_ENABLED"):
            self.assertIn('os.environ.get("' + name + '") == "true"', block)

    def test_isolated_worker_has_private_triggers_not_http_routes(self):
        source = WORKER.read_text()
        for name in ("feature4_cpu_render_message", "feature4_cpu_poison_message",
                     "feature4_cpu_dispatch_timer",
                     "RETAIL_FEATURE4_CPU_WORKER_ENABLED"):
            self.assertIn(name, source)
        self.assertNotIn("@app.route", source)
        self.assertNotIn("retail-reel-render", source)

    def test_runbook_only_activates_api_after_worker_verified(self):
        doc = RUNBOOK.read_text()
        self.assertIn("worker-readiness attestation", doc)
        self.assertIn("old URI rollback pinned", doc)
        self.assertIn("RETAIL_FEATURE4_CPU_RENDER_ENABLED=true", doc)
        self.assertIn("LAST. Enable frontend controls", doc)
        self.assertIn("genuine signed two-shop E2E remains mandatory", doc)


if __name__ == "__main__":
    unittest.main()
