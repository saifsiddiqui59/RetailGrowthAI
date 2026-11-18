"""Source-level safeguards for exact existing Y1 shadow deployment workflow."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/p0249-dev-y1-campaign-readonly-shadow-once.yml"


class Y1ReadOnlyWorkflowTests(unittest.TestCase):
    def test_requires_exact_scope_and_reviewable_main_trigger(self):
        s=WORKFLOW.read_text(encoding="utf-8")
        for needle in (
            "refs/heads/main", "environment: dev", "id-token: write",
            "YES-Y1-GET-SHADOW",
            "startsWith(github.event.head_commit.message",
            "p0249_y1_canary_guard.py verify",
            "p0249_y1_canary_guard.py probe",
            "--build-remote false", "P0249_Y1_SIGNED_API_NEGATIVE_ACCEPTED=",
            "RGAI_P0249_READONLY_SHADOW",
            "P0249_Y1_READONLY_PACKAGE=2_GET_ROUTES_ORIGINAL_JWT_RLS",
            "P0249_Y1_LAZY_IMPORT_PACKAGE_INDEX=PASS",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle,s)

    def test_never_create_cloud_resource_edit_settings_or_consume_queue(self):
        s=WORKFLOW.read_text()
        for unsafe in (
            "az deployment group create", "az group create",
            "az functionapp create", "az containerapp create",
            "az resource delete", "az functionapp delete",
            "az functionapp config appsettings set",
            "az functionapp config appsettings delete",
            "az functionapp scale config always-ready set",
            "-n rgai-dev-functions-d4e5ddbd",
            "RETAIL_SUPABASE_SERVICE_ROLE_KEY",
            "az storage queue", "az storage message",
        ):
            with self.subTest(unsafe=unsafe):
                self.assertNotIn(unsafe,s)

    def test_pinned_original_source_copied_instead_of_forking_auth(self):
        s=WORKFLOW.read_text()
        for source in ("http_api.py", "security.py", "tenant_store.py",
                       "draft_api.py", "request_diagnostics.py",
                       "ai-agents/src/ai_agents/schemas.py"):
            with self.subTest(source=source):
                self.assertIn(source,s)
        self.assertIn("set(found)=={\"campaign_read\",\"p0249_health\"}",s)
        self.assertIn("set(names)=={\"p0249_health\",\"campaign_read\"}",s)

    def test_denial_before_signed_credentials_and_no_frontend_switch(self):
        s=WORKFLOW.read_text()
        self.assertIn("test -z \"$active\"",s)
        self.assertIn("code==401 and marker and elapsed <18",s)
        self.assertNotIn("VITE_API_URL",s)
        self.assertNotIn("AZURE_STATIC_WEB_APPS_API_TOKEN",s)


if __name__ == "__main__":
    unittest.main()
