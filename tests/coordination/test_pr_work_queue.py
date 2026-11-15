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
        with self.assertRaisesRegex(queue.QueueError, "claimed head changed"):
            queue.claim_entry(updated, 551, "schedule-f2", OTHER, NOW)

    def test_closed_pr_is_not_kept_in_live_queue(self):
        state = queue.sync_entries(sample(), [])
        self.assertEqual(state["summary"]["open_prs"], 0)
        self.assertEqual(state["entries"], [])


if __name__ == "__main__":
    unittest.main()
