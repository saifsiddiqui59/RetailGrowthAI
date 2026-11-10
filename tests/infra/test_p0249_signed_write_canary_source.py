"""P0 #249 source-only guarantee: real signed write canary is Auth-only."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

class LiveDevWriteCanaryGuards(unittest.TestCase):
    def test_only_isolated_free_preview_and_temporary_auth(self):
        s=(ROOT/"tests/e2e/p0249_dev_signed_write_negative_once.py").read_text()
        self.assertIn("p0249writes.eastasia.2.azurestaticapps.net",s)
        self.assertIn("OWNER_APPROVED_AUTH_ONLY_WRITE_NEGATIVE",s)
        self.assertIn("p0249_dev_signed_jwt_read_once",s)
        self.assertIn("common.owner_only_cleanup(key,marker,uid)",s)
        self.assertIn("P0249_REAL_JWT_DEV_ALL_SIX_UNOWNED_WRITES_DENIED=PASSED",s)
        self.assertIn("P0249_NO_SHOP_MEDIA_JOB_OR_QUOTA_WRITTEN_BY_CANARY=true",s)
        self.assertIn("P0249_CROSS_SITE_SIGNED_JWT_MUTATION_BLOCKED=true",s)
        self.assertIn("P0249_FORGED_SIGNED_WRITE_JWT_DENIED=true",s)
        self.assertNotIn("service-role",s.lower())
        self.assertNotIn("sb_secret_t",s)
        self.assertNotIn("azurewebsites.net",s)
        self.assertNotIn("supabase.com/storage/v1/object",s)
        self.assertNotIn("/rest/v1/shops",s)
        self.assertNotIn("/rest/v1/render_jobs",s)
        self.assertNotIn("/rest/v1/poster_jobs",s)
        self.assertNotIn("/rest/v1/rpc/retail_platform_review_onboarding",s)
        self.assertEqual(s.count("common.request(DEV_WRITE_PREVIEW+path,method=method"),1)

    def test_one_shot_only_protected_main_dev_and_no_provision(self):
        s=(ROOT/".github/workflows/p0249-dev-signed-write-negative-once.yml").read_text()
        self.assertIn("environment: dev",s)
        self.assertIn("startsWith(github.event.head_commit.message",s)
        self.assertIn("secrets.RETAIL_SUPABASE_SERVICE_ROLE_KEY",s)
        self.assertIn("python3 -u tests/e2e/p0249_dev_signed_write_negative_once.py",s)
        for forbidden in ("workflow_dispatch:","azure/login","static-web-apps-deploy",
                          "id-token: write","az group create","apply_migration"):
            self.assertNotIn(forbidden,s)

if __name__=="__main__":
    unittest.main()
