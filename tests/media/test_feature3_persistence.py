"""Revision immutability and RLS-handoff tests (offline adapter fixtures)."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poster-engine"))

from studio_v2 import compose_poster
from persistence_contract_v2 import (
    DraftAccessDenied, DraftConflict, TrustedEditContext,
    RevisionToken, persist_versioned_draft,
)


class RevisionContractTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.user, self.campaign, self.day = (str(uuid4()) for _ in range(4))
        self.draft = str(uuid4())
        self.media = str(uuid4())
        self.context = TrustedEditContext(
            user_id=self.user, shop_id=self.shop, campaign_id=self.campaign,
            day_id=self.day, role="EDITOR", campaign_status="DRAFT",
            day_status="DRAFT",
        )
        self.document = compose_poster(
            shop_id=self.shop, mode="image", prompt="Festive kurti promotion",
            business_name="Local Fashion Shop", source_asset_id=self.media,
        )
        self.ticket = RevisionToken(self.draft, 0)
        self.rows = {}
        self.calls = []

    def load(self, ctx, design_id):
        self.calls.append("read")
        return self.rows.get(design_id)

    def rights(self, ctx, asset_ids):
        self.calls.append("rights")
        self.assertEqual(asset_ids, (self.media,))
        return True

    def commit(self, ctx, token, design, digest, assets):
        self.calls.append("cas")
        return {"design_id": token.design_id,
                "revision": token.expected_revision + 1,
                "design_sha256": digest}

    def save(self, **changes):
        kwargs = dict(fetch_current=self.load, authorize_assets=self.rights,
                      commit_if_revision=self.commit)
        kwargs.update(changes)
        return persist_versioned_draft(self.context, self.ticket,
                                       self.document, **kwargs)

    def test_new_draft_only_through_fenced_cas(self):
        result = self.save()
        self.assertEqual(result["revision"], 1)
        self.assertEqual(self.calls, ["read", "rights", "cas"])

    def test_stale_revision_and_approved_overwrite_forbidden(self):
        self.rows[self.draft] = {
            "design_id": self.draft, "shop_id": self.shop,
            "campaign_id": self.campaign, "day_id": self.day,
            "revision": 2, "status": "DRAFT",
        }
        with self.assertRaisesRegex(DraftConflict, "changed"):
            self.save()
        self.assertEqual(self.calls, ["read"])
        self.rows[self.draft]["status"] = "APPROVED"
        self.calls.clear()
        with self.assertRaisesRegex(DraftConflict, "Approved"):
            self.save()
        self.assertEqual(self.calls, ["read"])

    def test_new_approved_variation_requires_fresh_id(self):
        self.rows[self.draft] = {
            "design_id": self.draft, "shop_id": self.shop,
            "campaign_id": self.campaign, "day_id": self.day,
            "revision": 3, "status": "APPROVED",
        }
        variation_id = str(uuid4())
        self.ticket = RevisionToken(variation_id, 0, variation_of=self.draft)
        result = self.save()
        self.assertEqual(result["design_id"], variation_id)
        self.assertEqual(result["revision"], 1)
        with self.assertRaisesRegex(DraftConflict, "new design ID"):
            RevisionToken(self.draft, 0, variation_of=self.draft).validate()

    def test_wrong_shop_or_denied_role_does_not_enter_storage(self):
        other = self.document.copy()
        other["shop_id"] = str(uuid4())
        with self.assertRaisesRegex(DraftAccessDenied, "Cross-shop"):
            persist_versioned_draft(
                self.context, self.ticket, other,
                fetch_current=self.load, authorize_assets=self.rights,
                commit_if_revision=self.commit,
            )
        self.assertEqual(self.calls, [])
        self.context = TrustedEditContext(
            self.user, self.shop, self.campaign, self.day,
            "VIEWER", "DRAFT", "DRAFT",
        )
        with self.assertRaisesRegex(DraftAccessDenied, "editable"):
            self.save()
        self.assertEqual(self.calls, [])

    def test_rights_revocation_stops_commit(self):
        with self.assertRaisesRegex(DraftAccessDenied, "revoked"):
            self.save(authorize_assets=lambda *_: False)
        self.assertEqual(self.calls, ["read"])

    def test_ambiguous_failed_cas_does_not_claim_success(self):
        with self.assertRaisesRegex(DraftConflict, "not confirmed"):
            self.save(commit_if_revision=lambda *_: None)
        self.assertEqual(self.calls, ["read", "rights"])

    def test_cross_campaign_lineage_rejected(self):
        self.rows[self.draft] = {
            "design_id": self.draft, "shop_id": self.shop,
            "campaign_id": str(uuid4()), "day_id": self.day,
            "revision": 1, "status": "DRAFT",
        }
        self.ticket = RevisionToken(self.draft, 1)
        with self.assertRaisesRegex(DraftAccessDenied, "lineage"):
            self.save()


if __name__ == "__main__":
    unittest.main()
