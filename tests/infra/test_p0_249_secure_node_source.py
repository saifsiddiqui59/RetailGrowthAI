"""Fail closed: lightweight Node facade is experimental, read-only and not live."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SECURE = ROOT / "experiments/secure-node-http"


class SecureNodeParitySource(unittest.TestCase):
    def test_only_read_routes_source_only(self):
        p = json.loads((SECURE / "package.json").read_text())
        self.assertEqual(p["main"], "src/index.mjs")
        self.assertEqual(list(p["dependencies"]), ["@azure/functions"])
        code = (SECURE / "src/index.mjs").read_text()
        self.assertEqual(code.count("app.http("), 7)
        self.assertEqual(code.count('methods: ["GET"]'), 7)
        self.assertIn("private-reads.mjs", code)
        private = (SECURE / "src/private-reads.mjs").read_text()
        self.assertIn("class PrivateReader", private)
        self.assertIn("expiresIn: 60", private)
        self.assertIn("posterDownload", private)
        self.assertIn('x-rgai-supabase-jwt', code)
        self.assertNotIn('POST', code)
        self.assertNotIn('service_role', code.lower())
        self.assertNotIn('console.log', code)
        self.assertIn('SOURCE ONLY', code)

    def test_asymmetric_public_jwks_and_rls_only(self):
        security = (SECURE / "src/security.mjs").read_text()
        store = (SECURE / "src/tenant-read.mjs").read_text()
        self.assertIn('jwks.json', security)
        self.assertIn('createPublicKey', security)
        self.assertIn('["ES256", "RS256"]', security)
        self.assertIn('role !== "authenticated"', security)
        self.assertIn('"shop_memberships"', store)
        self.assertIn('active: "eq.true"', store)
        self.assertIn('Authorization: "Bearer " + token', store)
        self.assertIn('publishableKey.startsWith("sb_secret_")', store)
        self.assertNotIn('RETAIL_SUPABASE_SERVICE_ROLE_KEY', store)
        self.assertNotIn('method: "POST"', store)

if __name__ == "__main__":
    unittest.main()
