"""Protect the one-time F4 CPU DEV queue Actions workflow from scope drift."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/retail-dev-feature4-cpu-queues-once.yml"


class Feature4DevQueuesOneShotWorkflowTests(unittest.TestCase):
    def test_exact_main_and_existing_protected_environment_only(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("branches: [main]", source)
        self.assertIn("paths:", source)
        self.assertIn("'.github/workflows/retail-dev-feature4-cpu-queues-once.yml'", source)
        self.assertIn("github.repository == 'saifsiddiqui59/RetailGrowthAI'", source)
        self.assertIn("github.ref == 'refs/heads/main'", source)
        self.assertIn("environment: dev", source)
        self.assertIn("cancel-in-progress: false", source)
        self.assertNotIn("pull_request:", source)
        self.assertNotIn("schedule:", source)
        self.assertIn("persist-credentials: false", source)

    def test_only_exact_pinned_dev_schema_and_queue_script(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        for item in (
            "jeearzffnjbvghwjjjrf",
            "feature4_cpu_six_candidate_atomic_dev_20261123",
            "feature4_creative_plans",
            "feature4_cpu_render_jobs",
            "feature4_cpu_outbox",
            "feature4_cpu_poison_receipts",
            "has_function_privilege('service_role'",
            "NOT has_function_privilege('anon'",
            "NOT has_function_privilege('authenticated'",
            "RETAIL_FEATURE4_CPU_RENDER_ENABLED: 'false'",
            "RETAIL_FEATURE4_CPU_QUEUE_APPLY: 'YES'",
            "python3 scripts/deploy/feature4_cpu_dev_queues.py --apply",
        ):
            self.assertIn(item, source)
        self.assertEqual(source.count("scripts/deploy/feature4_cpu_dev_queues.py --apply"), 1)

    def test_scoped_identity_and_no_customer_activation(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("uses: azure/login@v3", source)
        self.assertIn("id-token: write", source)
        self.assertIn("secrets.AZURE_SUBSCRIPTION_ID", source)
        self.assertIn("secrets.RETAIL_SUPABASE_DB_URL", source)
        self.assertIn("2>/dev/null", source)
        for banned in (
            "az role assignment create", "--auth-mode key", "az storage queue delete",
            "az functionapp config appsettings set", "RETAIL_FEATURE4_CPU_RENDER_ENABLED: 'true'",
            "AZURE_STORAGE_KEY:", "supabase db push",
            "mcp__Supabase__apply_migration",
        ):
            self.assertNotIn(banned, source)


if __name__ == "__main__":
    unittest.main()
