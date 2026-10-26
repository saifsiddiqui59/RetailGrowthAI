"""Fail-closed source-only gates for a Reel intent client with NO deployed SQL RPC."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "experiments/secure-node-http/src"
MIGRATIONS = ROOT / "supabase/migrations"

class RenderIntentSourceIsolation(unittest.TestCase):
    def test_unregistered_reel_route_until_approved_rpc_exists(self):
        index = (SRC / "index.mjs").read_text()
        self.assertNotIn("reel-intent.mjs", index)
        self.assertNotIn('route: "campaigns/{id}/renders"', index)
        self.assertNotIn("createReelIntentGateway", index)

    def test_source_only_real_user_jwt_no_privileged_key_or_direct_queue(self):
        source = (SRC / "reel-intent.mjs").read_text()
        self.assertIn("/rest/v1/rpc/request_reel_render_job", source)
        self.assertIn('Authorization:"Bearer "+token', source)
        self.assertIn("memberWrite(", source)
        self.assertIn("licensedMedia(", source)
        self.assertIn('method:"POST"', source)
        self.assertIn("new UpstreamUnavailable()", source)
        for prohibited in ("service_role", "createQueueClient", "enqueueJob(", "render_jobs/insert"):
            # Documentation mentions the service role only as an explicit refusal.
            if prohibited == "service_role":
                self.assertNotIn("RETAIL_SUPABASE_SERVICE_ROLE_KEY", source)
            else:
                self.assertNotIn(prohibited, source)

    def test_no_mutating_sql_migration_or_broad_user_table_insert_grants_added(self):
        # Source-only PR must not create an unsafe shortcut around DB permissions.
        names = [p.name for p in MIGRATIONS.glob("*.sql")]
        self.assertFalse(any("249_reel_render_rpc" in p for p in names))
        source = (SRC / "reel-intent.mjs").read_text()
        self.assertNotIn("/rest/v1/render_jobs", source)
        self.assertNotIn("grant insert", source.lower())

if __name__ == "__main__":
    unittest.main()
