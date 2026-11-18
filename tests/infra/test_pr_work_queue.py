"""Deterministic PR claim and refresh regressions (no network/no secrets)."""
import importlib.util
from datetime import datetime, timezone, timedelta
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[2] / "scripts" / "coordination" / "pr_work_queue.py"
spec = importlib.util.spec_from_file_location("pr_work_queue", PATH)
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)
HEAD = "a" * 40
OTHER = "b" * 40
NOW = datetime(2026, 11, 15, 14, tzinfo=timezone.utc)


def sample():
    return {"schema_version": 1, "repository": queue.REPO, "ledger_branch": queue.BRANCH,
            "main_merge_owner": "manual-integration", "summary": {"open_prs": 1},
            "entries": [{"pr": 551, "title": "Feature2 parent", "head_sha": HEAD,
                         "feature": "F2", "base_branch": "main", "work_owner": "schedule-f2",
                         "priority": "P0", "phase": "needs-triage", "claim": None,
                         "checkpoint": None, "url": "https://github.com/example/pr/551"}]}


class QueueTest(unittest.TestCase):
    def test_one_owner_per_open_pr(self):
        old = sample()
        new = queue.claim_entry(old, 551, "schedule-f2", HEAD, NOW)
        self.assertIsNone(old["entries"][0]["claim"])
        with self.assertRaisesRegex(queue.QueueError, "active lease"):
            queue.claim_entry(new, 551, "manual-integration", HEAD, NOW)
        self.assertEqual(queue.find(new, 551)["claim"]["owner"], "schedule-f2")

    def test_distinct_manual_chats_cannot_rebind_one_anothers_lease(self):
        first = queue.claim_entry(sample(), 551, "manual-integration-chat-a", HEAD, NOW)
        with self.assertRaisesRegex(queue.QueueError, "active lease"):
            queue.claim_entry(first, 551, "manual-integration-chat-b", HEAD, NOW)
        resumed = queue.claim_entry(first, 551, "manual-integration-chat-a", HEAD, NOW)
        self.assertEqual(queue.find(resumed, 551)["claim"]["owner"], "manual-integration-chat-a")
        with self.assertRaisesRegex(queue.QueueError, "not assigned"):
            queue.claim_entry(sample(), 551, "manual-integration-chat-!", HEAD, NOW)

    def test_integration_schedule_lease_blocks_manual_collision(self):
        state = queue.claim_entry(sample(), 551, "schedule-integration", HEAD, NOW)
        with self.assertRaisesRegex(queue.QueueError, "active lease"):
            queue.claim_entry(state, 551, "manual-integration", HEAD, NOW)

    def test_expired_lease_can_be_reclaimed(self):
        state = queue.claim_entry(sample(), 551, "schedule-f2", HEAD, NOW, minutes=10)
        changed = queue.claim_entry(state, 551, "manual-integration", HEAD,
                                    NOW + timedelta(minutes=11))
        self.assertEqual(queue.find(changed, 551)["claim"]["owner"], "manual-integration")

    def test_stale_head_and_foreign_scope_denied(self):
        with self.assertRaisesRegex(queue.QueueError, "stale"):
            queue.claim_entry(sample(), 551, "schedule-f2", OTHER, NOW)
        with self.assertRaisesRegex(queue.QueueError, "not assigned"):
            queue.claim_entry(sample(), 551, "schedule-f4", HEAD, NOW)

    def test_release_cannot_mark_done_or_steal(self):
        state = queue.claim_entry(sample(), 551, "schedule-f2", HEAD, NOW)
        with self.assertRaisesRegex(queue.QueueError, "only current"):
            queue.release_entry(state, 551, "manual-integration")
        with self.assertRaisesRegex(queue.QueueError, "no DONE"):
            queue.release_entry(state, 551, "schedule-f2", "DONE")
        self.assertIsNone(queue.release_entry(state, 551, "schedule-f2")["entries"][0]["claim"])

    def test_refresh_preserves_owner_and_flags_changed_head(self):
        state = queue.claim_entry(sample(), 551, "schedule-f2", HEAD, NOW)
        pull = {"number": 551, "title": "feature2 updates",
                "head": {"sha": OTHER, "ref": "feature2"}, "base": {"ref": "main"},
                "html_url": "https://github.com/example/pr/551", "state": "open"}
        updated = queue.sync_entries(state, [pull])
        row = queue.find(updated, 551)
        self.assertEqual(row["phase"], "head-moved-recheck")
        self.assertEqual(row["claim"]["head_sha"], HEAD)
        with self.assertRaisesRegex(queue.QueueError, "active lease"):
            queue.claim_entry(updated, 551, "manual-integration", OTHER, NOW)
        renewed = queue.claim_entry(updated, 551, "schedule-f2", OTHER, NOW)
        self.assertEqual(queue.find(renewed, 551)["claim"]["head_sha"], OTHER)

    def test_expired_moved_head_may_be_safely_reclaimed(self):
        state = queue.claim_entry(sample(), 551, "schedule-f2", HEAD, NOW, minutes=10)
        pull = {"number": 551, "title": "Feature2 parent",
                "head": {"sha": OTHER, "ref": "feature2"}, "base": {"ref": "main"},
                "html_url": "https://github.com/example/pr/551", "state": "open"}
        state = queue.sync_entries(state, [pull])
        newer = queue.claim_entry(state, 551, "manual-integration", OTHER, NOW + timedelta(minutes=11))
        self.assertEqual(queue.find(newer, 551)["claim"]["head_sha"], OTHER)

    def test_global_cap_is_ten_active_pr_claims_even_with_expired_prior_claim(self):
        state = sample()
        seed = state["entries"][0]
        state["entries"] = [{**seed, "pr": n, "claim": None}
                            for n in range(551, 562)]
        for n in range(551, 561):
            state = queue.claim_entry(state, n, "schedule-f2", HEAD, NOW)
        with self.assertRaisesRegex(queue.QueueError, "global maximum"):
            queue.claim_entry(state, 561, "schedule-f2", HEAD, NOW)
        # Same-PR lease renewal must not consume an extra slot.
        state = queue.claim_entry(state, 551, "schedule-f2", HEAD, NOW)
        self.assertEqual(sum(bool(x["claim"]) for x in state["entries"]), 10)
        # Expired lease on the next row cannot be used to bypass ten
        # concurrently unexpired claims for *different* PRs.
        expired = queue.claim_entry(sample(), 551, "schedule-f2", HEAD,
                                    NOW - timedelta(minutes=11), minutes=10)
        stale = expired["entries"][0]
        full = sample()
        full["entries"] = [stale] + [
            {**seed, "pr": n, "claim": {"owner": "schedule-f2",
              "head_sha": HEAD, "claimed_at": queue.iso(NOW),
              "expires_at": queue.iso(NOW + timedelta(minutes=90))}}
            for n in range(552, 562)]
        with self.assertRaisesRegex(queue.QueueError, "global maximum"):
            queue.claim_entry(full, 551, "schedule-f2", HEAD, NOW)
        # When an existing claim expires, those leases cease to count.
        later = queue.claim_entry(state, 561, "schedule-f2", HEAD,
                                  NOW + timedelta(minutes=91))
        self.assertIsNotNone(queue.find(later, 561)["claim"])

    def test_feature5_takes_priority_over_cross_feature3_reference(self):
        self.assertEqual(queue.feature("Feature #5 Wan with Feature3 producer", "feature5-branch"), "F5")

    def test_checkpoint_requires_own_current_lease_and_records_no_done(self):
        state = queue.claim_entry(sample(), 551, "schedule-f2", HEAD, NOW)
        new = queue.checkpoint_entry(state, 551, "schedule-f2", HEAD, NOW,
                                     commits=2, tests="5 targeted tests passed",
                                     ci="pending", next_action="recheck 4/4 CI")
        item = queue.find(new, 551)
        self.assertEqual(item["checkpoint"]["commits_reported"], 2)
        self.assertEqual(item["checkpoint"]["evidence_status"], "worker-reported-unverified")
        with self.assertRaisesRegex(queue.QueueError, "valid own active lease"):
            queue.checkpoint_entry(state, 551, "manual-integration", HEAD, NOW)
        with self.assertRaisesRegex(queue.QueueError, "invalid commit count"):
            queue.checkpoint_entry(state, 551, "schedule-f2", HEAD, NOW, commits=-1)

    def test_closed_pr_is_not_kept_in_live_queue(self):
        state = queue.sync_entries(sample(), [])
        self.assertEqual(state["summary"]["open_prs"], 0)
        self.assertEqual(state["entries"], [])


if __name__ == "__main__":
    unittest.main()
