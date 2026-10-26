"""Source-only safety checks; no credentials, network, test account or mutation."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SignedJwtCanarySafety(unittest.TestCase):
    def test_exact_dev_auth_only_preview_and_cleanup(self):
        sql = (ROOT / "tests/e2e/p0249_dev_signed_jwt_read_once.py").read_text()
        self.assertIn('SUPABASE = "https://jeearzffnjbvghwjjjrf.supabase.co"', sql)
        self.assertIn("p0249secure.eastasia.2.azurestaticapps.net", sql)
        self.assertIn('if __name__ == "__main__":', sql)
        self.assertIn('RGAI_DEV_P0249_JWT_CANARY_APPROVAL', sql)
        self.assertIn('OWNER_APPROVED_READ_ONLY_JWT_TEST', sql)
        self.assertIn('owner_only_cleanup(key, marker, uid)', sql)
        self.assertIn("method=\"DELETE\"", sql)
        self.assertIn("CANARY_PREFIX", sql)
        self.assertIn('email = marker + "@example.invalid"', sql)
        self.assertIn('P0249_MODIFIED_SIGNATURE_REJECTED=PASSED', sql)
        self.assertIn("P0249_GENUINE_SIGNED_JWT_JWKS_RLS_READ=PASSED", sql)
        self.assertIn('x-rgai-supabase-jwt', sql)
        self.assertIn('/auth/v1/.well-known/jwks.json', sql)
        self.assertNotIn('sb_secret_', sql.replace('"sb_secret_"', ''))
        self.assertNotIn('AZURE_STORAGE_CONNECTION_STRING', sql)
        self.assertNotIn('Retail_FOUNDRY_API_KEY', sql)
        self.assertNotIn('POST", data={"shop_id"', sql)
        self.assertNotIn('"/api/campaigns", method="POST"', sql)
        self.assertNotIn('"/storage/v1/object"', sql)

    def test_exact_one_shot_protected_existing_environment(self):
        workflow=(ROOT / ".github/workflows/p0249-signed-jwt-read-canary-once.yml").read_text()
        self.assertIn("environment: dev",workflow)
        self.assertIn("startsWith(github.event.head_commit.message",workflow)
        self.assertIn("P0 249 temporary signed JWT Free SWA read canary",workflow)
        self.assertIn("secrets.RETAIL_SUPABASE_SERVICE_ROLE_KEY",workflow)
        self.assertIn("python3 -u tests/e2e/p0249_dev_signed_jwt_read_once.py",workflow)
        self.assertNotIn("workflow_dispatch:",workflow)
        self.assertNotIn("id-token: write",workflow)
        self.assertNotIn("azure/login",workflow)
        self.assertNotIn("static-web-apps-deploy",workflow)
        self.assertNotIn("apply_migration",workflow)


if __name__ == "__main__":
    unittest.main()
