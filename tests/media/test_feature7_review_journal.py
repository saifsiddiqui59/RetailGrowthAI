"""Feature7 offline SQLite review journal tests (NOT hosted JWT/RLS verification)."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-engine" / "feature7"))
from review_journal import (CurrentReviewContext, LocalReviewJournal,
                            ReviewStateError, TTL_MS)

DRAFT = "a" * 64
CANDIDATE = "b" * 64
MEDIA = "c" * 64
NOW = 1700000000000


def trusted(**changes):
    ctx = CurrentReviewContext(shop_id="shop-local-a",
                               campaign_id="campaign-a", reviewer_id="owner-a",
                               role="OWNER", active_membership=True,
                               video_rights_current=True,
                               media_snapshot_sha256=MEDIA)
    return replace(ctx, **changes)


class LocalFeature7ReviewJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="f7-review-journal-")
        self.db_path = Path(self.temp.name) / "isolated.sqlite3"
        self.store = LocalReviewJournal(self.db_path)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def stage(self):
        return self.store.stage(context=trusted(), draft_sha256=DRAFT,
                                candidate_sha256=CANDIDATE, now_ms=NOW)

    def approve(self, stage):
        return self.store.approve(review_id=stage["review_id"],
                                  context=trusted(), candidate_sha256=CANDIDATE,
                                  expected_revision=0,
                                  confirmed_by_human=True, now_ms=NOW+100)

    def claim(self, stage, approval, *, store=None, **changes):
        return (store or self.store).claim_for_feature4(
            review_id=stage["review_id"], approval_id=approval["approval_id"],
            context=trusted(), draft_sha256=DRAFT, candidate_sha256=CANDIDATE,
            expected_revision=1, now_ms=NOW+200, **changes)

    def test_stage_requires_explicit_human_and_preserves_source_scope(self):
        stage = self.stage()
        self.assertFalse(stage["approved"])
        self.assertEqual(stage["revision"], 0)
        with self.assertRaises(ReviewStateError):
            self.store.approve(review_id=stage["review_id"],
                context=trusted(), candidate_sha256=CANDIDATE,
                expected_revision=0, confirmed_by_human=False, now_ms=NOW+100)
        approved = self.approve(stage)
        self.assertEqual(approved["status"], "APPROVED")
        consumed = self.claim(stage, approved)
        self.assertEqual(consumed["status"], "CLAIMED_ONCE")
        self.assertEqual(consumed["draft_sha256"], DRAFT)
        self.assertEqual(consumed["revision"], 2)
        with self.assertRaises(ReviewStateError):
            self.claim(stage, approved)

    def test_persists_across_process_equivalent_connections(self):
        stage = self.stage()
        self.store.close()
        reopened = LocalReviewJournal(self.db_path)
        try:
            approved = reopened.approve(
                review_id=stage["review_id"], context=trusted(),
                candidate_sha256=CANDIDATE, confirmed_by_human=True,
                expected_revision=0, now_ms=NOW+100)
            self.assertEqual(self.claim(stage, approved, store=reopened)["revision"], 2)
        finally:
            reopened.close()
        self.store = LocalReviewJournal(self.db_path)

    def test_changed_or_foreign_rights_and_reviewer_denied(self):
        stage = self.stage()
        for context in (trusted(shop_id="another-shop"),
                        trusted(campaign_id="another-campaign"),
                        trusted(media_snapshot_sha256="e"*64),
                        trusted(active_membership=False),
                        trusted(video_rights_current=False),
                        trusted(role="VIEWER")):
            with self.subTest(context=context):
                with self.assertRaises(ReviewStateError):
                    self.store.approve(
                        review_id=stage["review_id"], context=context,
                        candidate_sha256=CANDIDATE, expected_revision=0,
                        confirmed_by_human=True, now_ms=NOW+100)
        approved = self.approve(stage)
        for context in (trusted(shop_id="another-shop"),
                        trusted(media_snapshot_sha256="d"*64),
                        trusted(active_membership=False),
                        trusted(reviewer_id="someone-else")):
            with self.subTest(context=context):
                with self.assertRaises(ReviewStateError):
                    self.store.claim_for_feature4(
                        review_id=stage["review_id"],
                        approval_id=approved["approval_id"], context=context,
                        draft_sha256=DRAFT, candidate_sha256=CANDIDATE,
                        expected_revision=1, now_ms=NOW+200)

    def test_expiry_stale_draft_and_tampering_are_rejected(self):
        stage = self.stage()
        approved = self.approve(stage)
        kwargs = dict(review_id=stage["review_id"],
                      approval_id=approved["approval_id"],
                      context=trusted(), draft_sha256=DRAFT,
                      candidate_sha256=CANDIDATE,
                      expected_revision=1, now_ms=NOW+200)
        for changes in ({"now_ms": NOW+100+TTL_MS+1},
                        {"draft_sha256": "d"*64},
                        {"candidate_sha256": "d"*64},
                        {"approval_id": "f7a_forged"},
                        {"expected_revision": 0}):
            with self.subTest(changes=changes):
                with self.assertRaises(ReviewStateError):
                    self.store.claim_for_feature4(**(kwargs | changes))
        self.assertEqual(self.store.claim_for_feature4(**kwargs)["revision"], 2)

    def test_trusted_clock_cannot_backdate_approval_or_claim(self):
        stage = self.stage()
        with self.assertRaises(ReviewStateError):
            self.store.approve(
                review_id=stage["review_id"], context=trusted(),
                candidate_sha256=CANDIDATE, expected_revision=0,
                confirmed_by_human=True, now_ms=NOW-1)
        approved = self.approve(stage)
        # A clock rollback after approval must not consume a future decision.
        with self.assertRaises(ReviewStateError):
            self.store.claim_for_feature4(
                review_id=stage["review_id"], approval_id=approved["approval_id"],
                context=trusted(), draft_sha256=DRAFT,
                candidate_sha256=CANDIDATE, expected_revision=1,
                now_ms=NOW+50)
        self.assertEqual(
            self.store.claim_for_feature4(
                review_id=stage["review_id"], approval_id=approved["approval_id"],
                context=trusted(), draft_sha256=DRAFT,
                candidate_sha256=CANDIDATE, expected_revision=1,
                now_ms=NOW+100)["status"],
            "CLAIMED_ONCE")

    def test_trusted_clock_rejects_sqlite_overflow_before_write(self):
        with self.assertRaises(ReviewStateError):
            self.store.stage(context=trusted(), draft_sha256=DRAFT,
                             candidate_sha256=CANDIDATE, now_ms=2**63-1)
        stage = self.stage()
        with self.assertRaises(ReviewStateError):
            self.store.approve(
                review_id=stage["review_id"], context=trusted(),
                candidate_sha256=CANDIDATE, expected_revision=0,
                confirmed_by_human=True, now_ms=2**63-1)
        self.assertEqual(self.approve(stage)["status"], "APPROVED")

    def test_revoke_before_and_after_approval_denies_claim(self):
        pending = self.stage()
        self.store.revoke(review_id=pending["review_id"],
                          expected_revision=0, context=trusted())
        with self.assertRaises(ReviewStateError):
            self.approve(pending)
        stage = self.stage()
        approved = self.approve(stage)
        self.store.revoke(review_id=stage["review_id"],
                          expected_revision=1, context=trusted())
        with self.assertRaises(ReviewStateError):
            self.claim(stage, approved)

    def test_two_independent_connections_only_one_claims(self):
        stage = self.stage()
        approved = self.approve(stage)
        def race(_):
            journal = LocalReviewJournal(self.db_path)
            try:
                return self.claim(stage, approved, store=journal)
            except ReviewStateError:
                return None
            finally:
                journal.close()
        # Client connections remain independent; BEGIN IMMEDIATE serializes
        # writers, with one SUCCESS and no possibility of replay.
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(race, (1,2)))
        self.assertEqual(sum(r is not None for r in results), 1)


if __name__ == "__main__":
    unittest.main()
