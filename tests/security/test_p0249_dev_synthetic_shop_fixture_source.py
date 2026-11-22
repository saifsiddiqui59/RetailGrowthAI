"""Source-contract guards for the explicit, disabled-by-default DEV synthetic canary.

These tests make no hosted writes. Acceptance requires a separate reviewed
DEV-only schema deployment and successful protected real-browser run.
"""
from pathlib import Path
import ast
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "supabase/migrations/20261122221500_p0249_dev_synthetic_canary_approval.sql"
CANARY = ROOT / "tests/e2e/retail_dev_canary_once.py"
WORKFLOW = ROOT / ".github/workflows/retail-dev-test-accounts-canary-once.yml"


class DevSyntheticRetailerFixtureSourceTests(unittest.TestCase):
    def test_sql_disabled_in_every_database_until_dev_only_enablement(self):
        sql = MIGRATION.read_text()
        self.assertIn("enabled boolean not null default false", sql)
        self.assertIn("values (true, false)", sql)
        self.assertIn("if not coalesce((select enabled", sql)
        self.assertIn("raise exception 'DEV_FIXTURE_DISABLED'", sql)
        self.assertNotIn("update retail_private.onboarding_gate", sql)
        self.assertNotIn("alter table public.shops disable row level security", sql)
        self.assertNotIn("alter role authenticated", sql)

    def test_only_short_lived_app_metadata_minted_disposable_users_can_pass(self):
        sql = MIGRATION.read_text()
        self.assertIn("^rgai-canary-[0-9a-f]{12}-[ab]@example[.]invalid$", sql)
        self.assertIn("raw_app_meta_data", sql)
        self.assertNotIn("raw_user_meta_data", sql)
        self.assertIn("interval '15 minutes'", sql)
        self.assertIn("status = 'PENDING'", sql)
        self.assertIn("requested_at >=", sql)
        self.assertIn("rgai_dev_run_id", sql)
        self.assertIn("rgai_dev_run_attempt", sql)
        self.assertIn("browser-upload-synthetic", sql)
        self.assertIn("'service_role'", sql)
        self.assertIn("AUTOMATED DEV synthetic fixture by service role; NOT ROOT approval", sql)

    def test_invoker_public_wrapper_and_private_only_definer_permissions(self):
        sql = MIGRATION.read_text().lower()
        self.assertIn("security definer set search_path = ''", sql)
        self.assertIn("security invoker set search_path = ''", sql)
        for func in ("public.p0249_dev_authorize_synthetic_retailer(uuid,text,text)",
                     "retail_private.p0249_authorize_disposable_shop_fixture(uuid,text,text)"):
            self.assertIn("revoke all on function " + func, sql)
            self.assertIn("grant execute on function " + func, sql)
        self.assertNotIn("grant execute on function public.p0249_dev_authorize_synthetic_retailer(uuid,text,text)\n  to authenticated", sql)
        self.assertNotIn("grant execute on function public.p0249_dev_authorize_synthetic_retailer(uuid,text,text)\n  to anon", sql)

    def test_real_campaign_canary_uses_normal_user_jwt_after_fixture_approval(self):
        py = CANARY.read_text()
        ast.parse(py)
        for expected in ("GITHUB_ACTIONS", "GITHUB_REPOSITORY", "GITHUB_REF",
                         "refs/heads/main", "RGAI_DEV_PLAYWRIGHT_UPLOAD",
                         "RGAI_DEV_SYNTHETIC_SHOP_FIXTURE",
                         "rgai_dev_fixture_mode", "app_metadata",
                         'p0249_dev_authorize_synthetic_retailer',
                         "CANARY_TEST_ONLY_FIXTURE_APPROVED=true",
                         'headers=bearer', 'headers=a', "if fixture_mode:"):
            self.assertIn(expected, py)
        self.assertNotIn('attributes["user_metadata"]', py)
        self.assertIn("finally:", py)

    def test_manual_protected_workflow_has_explicit_synthetic_mode(self):
        yaml = WORKFLOW.read_text()
        for expected in ("workflow_dispatch:", "environment: dev",
                         "- browser-upload-synthetic", "RGAI_DEV_SYNTHETIC_SHOP_FIXTURE:",
                         "RGAI_DEV_SERVICE_KEY: ${{ secrets.RETAIL_SUPABASE_SERVICE_ROLE_KEY }}",
                         "inputs.approval_code == 'AUTHORIZED_RETAILGROWTHAI_DEV_ONLY'",
                         "github.ref == 'refs/heads/main'"):
            self.assertIn(expected, yaml)
        self.assertNotIn("\n  push:", yaml)
        before = yaml.split("      - name: Run protected DEV acceptance path")[0]
        self.assertNotIn("RGAI_DEV_SERVICE_KEY:", before)


if __name__ == "__main__":
    unittest.main()
