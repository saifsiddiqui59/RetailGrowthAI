"""Offline schema/release guard for the UNAPPLIED Feature3 review SQL proposal.

This checks source-shape drift against the existing versioned schema. It does
NOT execute SQL, establish a legal licence or count as hosted DEV verification.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
PROPOSAL = ROOT / "supabase/proposals/feature3_current_model_review_20261029.sql"
AUDIT = ROOT / "supabase/migrations/20261028190000_feature3_model_review_audit.sql"
CATALOG = ROOT / "supabase/migrations/20261028092346_feature3_model_catalog_drafts.sql"


class ModelReviewProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = PROPOSAL.read_text(encoding="utf-8")
        cls.audit = AUDIT.read_text(encoding="utf-8")
        cls.catalog = CATALOG.read_text(encoding="utf-8")

    def test_table_and_evidence_fields_exist_in_current_schema(self):
        for table in ("feature3_models", "feature3_model_evidence",
                      "feature3_model_review_events", "media_assets"):
            with self.subTest(table=table):
                self.assertIn(table, self.sql)
        for column in ("license_evidence_sha256", "evidence_revision",
                       "rights_revision", "image_sha256", "approved_uses",
                       "synthetic_adult", "commercial_reuse_approved"):
            with self.subTest(column=column):
                self.assertIn(column, self.audit + self.catalog)
                self.assertIn(column, self.sql)

    def test_service_only_and_latest_event_fence_are_explicit(self):
        sql = self.sql.lower()
        self.assertIn("auth.role()",sql)
        self.assertIn("is distinct from 'service_role'",sql)
        self.assertIn("order by rights_revision desc limit 1",sql)
        self.assertIn("ev.rights_revision <> m.rights_revision",sql)
        self.assertIn("ev.action <> 'approve'",sql)
        self.assertIn("ev.to_status <> 'approved'",sql)
        self.assertIn("m.status",sql)
        self.assertIn("object_path=expected_key",sql)
        self.assertIn("name=expected_key",sql)
        self.assertIn("p_image_sha256",sql)
        self.assertIn("grant execute on function public.feature3_read_current_model_review",sql)
        self.assertIn("to service_role;",sql)
        self.assertIn("from public,anon,authenticated;",sql)

    def test_proposal_is_read_only_and_not_registered_as_migration(self):
        sql = re.sub(r"--[^\\n]*", "", self.sql.lower())
        body = sql.split("as $$", 1)[1].split("end $$;", 1)[0]
        for pattern in (r"\\binsert\\s+into\\b", r"\\bupdate\\s+\\w",
                        r"\\bdelete\\s+from\\b", r"\\btruncate\\b",
                        r"\\bexecute\\s+\\w"):
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, body))
        self.assertFalse(
            list((ROOT/"supabase/migrations").glob("*feature3_current_model_review*")))
        self.assertEqual(self.sql.strip().splitlines()[-1],"commit;")


if __name__ == "__main__":
    unittest.main()
