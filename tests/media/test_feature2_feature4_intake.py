"""F2→F4 atomic submission boundary and exact user-preview integrity tests.

The in-memory transaction is deliberately fake; no claims about Supabase
hosting, real approval persistence or billing commit are made by these tests.
"""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from creative_contract import CreativeContractError  # noqa: E402
from feature2_feature4_bridge import compile_feature2_direction  # noqa: E402
from feature2_feature4_intake import Feature4ApprovedPlanIntake, Feature4IntakeUnavailable  # noqa: E402
from test_feature2_feature4_bridge import original, REVIEW, SHOP, CAMPAIGN, OTHER
JOB = "33333333-3333-4333-8333-333333333333"  # noqa: E402

USER = "77777777-7777-4777-8777-777777777777"


def make():
    direction, snapshot = original()
    compiled = compile_feature2_direction(direction, snapshot, reviewed_hash=REVIEW)
    draft = compiled["approved_draft"]
    item = {"shop_id": SHOP, "campaign_id": CAMPAIGN, "requested_by": USER,
            "approval_id": direction["approval_id"], "draft": draft,
            "preset": "feature4_reel_v1"}
    item["idempotency_key"] = hashlib.sha256(json.dumps(
        [SHOP, USER, CAMPAIGN, item["approval_id"], draft],
        sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    return direction, snapshot, item


class FakeAtomicStore:
    """Test stand-in: compilation happens BEFORE any fake ledger mutation."""
    def __init__(self, direction, snapshot):
        self.direction, self.snapshot = direction, snapshot
        self.active_editor = True
        self.revision_hash = REVIEW
        self.rights_revoked = False
        self.records = {}
        self.writes = 0
        self.compiled = None

    def atomic_create_feature4_intent(self, item, prepare):
        locked = copy.deepcopy(self.snapshot)
        locked["idempotency_key"] = item["idempotency_key"]
        if self.rights_revoked:
            locked["assets"]["photokurti"]["approved"] = False
        output = prepare({
            "direction": copy.deepcopy(self.direction), "snapshot": locked,
            "reviewed_hash": self.revision_hash, "active_editor": self.active_editor,
        })
        # In production this bundle, usage reservation and outbox must commit
        # together (all absent if prepare failed).
        self.compiled = output
        key = item["idempotency_key"]
        if key not in self.records:
            self.records[key] = {"id": JOB, "shop_id": SHOP, "status": "QUEUED"}
            self.writes += 1
        return self.records[key]


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.direction, self.snapshot, self.item = make()
        self.backend = FakeAtomicStore(self.direction, self.snapshot)
        self.api = Feature4ApprovedPlanIntake(self.backend)

    def test_complete_f2_plan_to_f4_request_bundle_one_logical_job(self):
        response = self.api.create_feature4_intent(self.item)
        self.assertEqual(response, {"id": JOB, "shop_id": SHOP, "status": "QUEUED"})
        self.assertEqual(self.backend.writes, 1)
        self.assertEqual(self.api.create_feature4_intent(self.item), response)
        self.assertEqual(self.backend.writes, 1)
        compiled = self.backend.compiled
        self.assertEqual(compiled["request"]["version"], "creative_reel_v1")
        self.assertEqual(compiled["approved_draft"], self.item["draft"])
        self.assertEqual(compiled["request"]["script"], self.snapshot["script"])
        self.assertEqual(compiled["lineage"]["media_asset_ids"],
                         sorted(compiled["manifest"]["assets"]))

    def test_revised_browser_copy_cannot_reuse_approved_director_plan(self):
        tampered = copy.deepcopy(self.item)
        tampered["draft"]["scenes"][0]["headline"] = "FREE EVERYTHING"
        tampered["idempotency_key"] = hashlib.sha256(json.dumps(
            [SHOP, USER, CAMPAIGN, tampered["approval_id"], tampered["draft"]],
            sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
        with self.assertRaisesRegex(CreativeContractError, "differs"):
            self.api.create_feature4_intent(tampered)
        self.assertEqual(self.backend.writes, 0)

    def test_wrong_digest_revoked_rights_and_changed_immutable_plan_are_denied(self):
        bad = copy.deepcopy(self.item)
        bad["idempotency_key"] = "0" * 64
        with self.assertRaises(CreativeContractError):
            self.api.create_feature4_intent(bad)
        self.backend.rights_revoked = True
        with self.assertRaises(CreativeContractError):
            self.api.create_feature4_intent(self.item)
        self.backend.rights_revoked = False
        self.backend.direction["scenes"][0]["transition"] = "slide"
        with self.assertRaises(CreativeContractError):
            self.api.create_feature4_intent(self.item)
        self.assertEqual(self.backend.writes, 0)

    def test_foreign_locked_tenant_or_missing_editor_is_denied(self):
        self.backend.active_editor = False
        with self.assertRaises(CreativeContractError):
            self.api.create_feature4_intent(self.item)
        self.backend.active_editor = True
        self.backend.snapshot["shop_id"] = OTHER
        with self.assertRaises(CreativeContractError):
            self.api.create_feature4_intent(self.item)
        self.assertEqual(self.backend.writes, 0)

    def test_unauthorized_replay_after_commit_does_not_skip_approval(self):
        self.api.create_feature4_intent(self.item)
        self.backend.active_editor = False
        with self.assertRaises(CreativeContractError):
            self.api.create_feature4_intent(self.item)
        self.assertEqual(self.backend.writes, 1)

    def test_no_unknown_db_or_injected_fields_fail_without_writes(self):
        with self.assertRaises(Feature4IntakeUnavailable):
            Feature4ApprovedPlanIntake(object())
        bad = copy.deepcopy(self.item)
        bad["media_url"] = "https://other-shop.example/movie.mp4"
        with self.assertRaises(CreativeContractError):
            self.api.create_feature4_intent(bad)
        self.assertEqual(self.backend.writes, 0)


if __name__ == "__main__":
    unittest.main()
