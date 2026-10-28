"""Feature3 independent human approval and durable CAS boundary: offline only.

Uses real Pillow source PNG bytes, but fictional model, shop, license and
human-review grants. These never authorize production media or paid inference.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from uuid import uuid4, uuid5, NAMESPACE_DNS
import sys
import unittest

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
from model_review_gate_v1 import (
    ModelReviewDenied, decide_model_review, revoke_approved_model,
)

CHECKS = {
    "adult_synthetic": True, "likeness_and_consent": True,
    "image_license": True, "private_media_integrity": True,
    "visual_quality": True, "approved_uses": True,
}


def illustrative_model_png():
    im = Image.new("RGB", (720, 1080), "#E4E0D2")
    d = ImageDraw.Draw(im)
    d.ellipse((265, 95, 460, 300), fill="#B98D74")
    d.polygon([(235, 310), (490, 310), (555, 950), (170, 950)], fill="#346474")
    out = BytesIO()
    im.save(out, "PNG")
    return out.getvalue()


class ModelHumanReviewTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.other, self.creator = [str(uuid4()) for _ in range(3)]
        self.reviewer, self.asset = [str(uuid4()) for _ in range(2)]
        self.model = str(uuid5(NAMESPACE_DNS, "reviewed-pinned-imported-model"))
        self.image = illustrative_model_png()
        self.sha = sha256(self.image).hexdigest()
        self.license_sha = "b" * 64
        self.event_id = str(uuid4())
        self.approval_requests = []
        self.revocation_requests = []
        self.scope = "shop"
        self.authorized = True
        self.role = "OWNER"
        self.active = True
        self.curator = False
        self.evidence_valid = True
        self.row = {
            "model_id": self.model, "owner_shop_id": self.shop,
            "created_by": self.creator, "media_asset_id": self.asset,
            "scope": "shop", "status": "PENDING_REVIEW",
            "source_kind": "retailer_licensed",
            "synthetic_adult": True, "image_sha256": self.sha,
            "license_id": "REVIEWED-COMMERCIAL",
            "license_evidence_sha256": self.license_sha,
            "approved_uses": ["poster", "try_on", "video_reference"],
            "label": "Authorized fictional adult studio pose",
            "rights_revision": 1, "rights_verified": False,
            "attribution": "Verified private studio photographer",
        }
        self.asset_row = {
            "id": self.asset, "shop_id": self.shop,
            "storage_bucket": "retailgrowth-media",
            "object_path": f"{self.shop}/model-library/{self.model}/{self.sha}.png",
            "mime_type": "image/png", "source": "UPLOAD",
        }
        self.evidence = {
            "shop_id": self.shop, "model_id": self.model,
            "media_asset_id": self.asset, "image_sha256": self.sha,
            "license_id": "REVIEWED-COMMERCIAL",
            "license_evidence_sha256": self.license_sha,
            "source_kind": "retailer_licensed", "pose": "front",
            "source_uri": "https://retailer.example.invalid/original-portrait",
            "synthetic_adult_verified": True, "component_rights_cleared": True,
            "commercial_reuse_approved": True, "evidence_revision": 1,
        }

    def callbacks(self):
        return dict(
            read_model=lambda shop, mid: self.row,
            authorize_reviewer=lambda shop, rid, mid: {
                "authorized": self.authorized, "shop_id": self.shop,
                "user_id": self.reviewer, "role": self.role,
                "active": self.active, "platform_curator": self.curator,
            },
            read_license_evidence=lambda shop, mid: self.evidence,
            load_private_media=lambda shop, aid: (self.asset_row, self.image),
            persist_review_atomic=self.persist_review,
        )

    def persist_review(self, proposal):
        self.approval_requests.append(proposal)
        # Simulates the necessary durable SQL compare-and-swap in a disposable
        # unit test; it is not a live service-role DB transaction or approval.
        if proposal["expected_rights_revision"] != self.row["rights_revision"] or \
           proposal["expected_status"] != self.row["status"] or \
           proposal["expected_image_sha256"] != self.row["image_sha256"]:
            return None
        self.row.update(
            status=proposal["decision"], rights_verified=proposal["decision"] == "APPROVED",
            rights_revision=self.row["rights_revision"] + 1)
        return {
            "model_id": self.model, "owner_shop_id": self.shop,
            "status": self.row["status"],
            "rights_verified": self.row["rights_verified"],
            "rights_revision": self.row["rights_revision"],
            "audit_persisted": True, "review_event_id": self.event_id,
        }

    def persist_revocation(self, proposal):
        self.revocation_requests.append(proposal)
        if proposal["expected_rights_revision"] != self.row["rights_revision"] or \
           self.row["status"] != "APPROVED":
            return None
        self.row.update(status="REVOKED", rights_verified=False,
                        rights_revision=self.row["rights_revision"] + 1)
        return {
            "model_id": self.model, "owner_shop_id": self.shop,
            "status": "REVOKED", "rights_verified": False,
            "rights_revision": self.row["rights_revision"],
            "audit_persisted": True, "review_event_id": self.event_id,
        }

    def decide(self, **overrides):
        args = {
            "shop_id": self.shop, "model_id": self.model,
            "reviewer_id": self.reviewer, "decision": "APPROVE",
            "checks": CHECKS, "notes": "Human checked face, rights and image fidelity",
            **self.callbacks(),
        }
        args.update(overrides)
        return decide_model_review(**args)

    def test_approved_model_requires_true_human_and_byte_verified_license(self):
        out = self.decide()
        self.assertEqual(out["status"], "APPROVED")
        self.assertEqual(out["rights_revision"], 2)
        self.assertTrue(out["audit_persisted"])
        self.assertFalse(out["gpu_authorized"])
        p = self.approval_requests[0]
        self.assertEqual(p["media_asset_id"], self.asset)
        self.assertEqual(p["expected_image_sha256"], self.sha)
        self.assertEqual(p["dimensions"], [720, 1080])
        self.assertEqual(p["pose"], "front")
        self.assertNotIn("image_bytes", p)
        self.assertNotIn("object_path", p)
        self.assertFalse(out["generation_executed"])

    def test_rejected_model_cannot_be_used_as_approved_model(self):
        failed = {**CHECKS, "visual_quality": False}
        out = self.decide(decision="REJECT", checks=failed,
                          notes="Visual artifacts in fictional model portrait")
        self.assertEqual(out["status"], "REJECTED")
        self.assertFalse(out["rights_verified"])
        with self.assertRaises(ModelReviewDenied):
            self.decide()
        self.assertEqual(len(self.approval_requests), 1)

    def test_no_automatic_approval_when_checks_missing_or_failed(self):
        for checks in ({"visual_quality": True},
                       {**CHECKS, "image_license": False},
                       {**CHECKS, "adult_synthetic": 1},
                       {**CHECKS, "approved_uses": "yes"}):
            with self.subTest(checks=checks), self.assertRaises(ModelReviewDenied):
                self.decide(checks=checks)
        self.assertFalse(self.approval_requests)

    def test_current_reviewer_membership_and_curator_required(self):
        for role,active,allowed in [
            ("VIEWER", True, True), ("EDITOR", False, True),
            ("OWNER", True, False)]:
            self.role, self.active, self.authorized = role, active, allowed
            with self.assertRaises(ModelReviewDenied):
                self.decide()
        self.assertFalse(self.approval_requests)
        self.authorized, self.active, self.role = True, True, "OWNER"
        self.row["scope"] = "platform"
        self.asset_row["object_path"] = (
            f"{self.shop}/model-library/platform/{self.model}/{self.sha}.png")
        with self.assertRaises(ModelReviewDenied):
            self.decide()
        self.curator = True
        self.decide()
        self.assertEqual(self.row["status"], "APPROVED")

    def test_self_promotion_of_shared_platform_model_denied(self):
        self.row["scope"] = "platform"
        self.asset_row["object_path"] = (
            f"{self.shop}/model-library/platform/{self.model}/{self.sha}.png")
        self.curator = True
        self.row["created_by"] = self.reviewer
        with self.assertRaises(ModelReviewDenied):
            self.decide()
        self.assertEqual(self.row["status"], "PENDING_REVIEW")

    def test_cross_tenant_and_fake_review_privileges_denied(self):
        with self.assertRaises(ModelReviewDenied):
            self.decide(shop_id=self.other)
        with self.assertRaises(ModelReviewDenied):
            self.decide(reviewer_id=str(uuid4()))
        self.asset_row["shop_id"] = self.other
        with self.assertRaises(ModelReviewDenied):
            self.decide()
        self.assertEqual(self.approval_requests, [])

    def test_wrong_private_path_or_binary_replacement_denied(self):
        orig = self.asset_row["object_path"]
        for key in (
            f"{self.shop}/uploads/{self.model}.png",
            f"{self.other}/model-library/{self.model}/{self.sha}.png",
            f"{self.shop}/model-library/{self.model}/fake.png",
        ):
            self.asset_row["object_path"] = key
            with self.subTest(key=key), self.assertRaises(ModelReviewDenied):
                self.decide()
        self.asset_row["object_path"] = orig
        self.image = illustrative_model_png() + b"forged-trailing-payload"
        with self.assertRaises(ModelReviewDenied):
            self.decide()
        self.assertEqual(self.approval_requests, [])

    def test_claimed_license_needs_server_verified_provenance(self):
        for changes in (
            {"commercial_reuse_approved": False},
            {"component_rights_cleared": False},
            {"synthetic_adult_verified": False},
            {"pose": "not-a-pose"},
            {"source_uri": "http://unreviewed.example.invalid"},
            {"source_uri": "https://owner:token@example.invalid/a"},
            {"source_uri": "https://example.invalid:broken/a"},
            {"image_sha256": "a" * 64},
            {"license_evidence_sha256": "f" * 64},
        ):
            old = dict(self.evidence)
            self.evidence.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ModelReviewDenied):
                self.decide()
            self.evidence = old
        self.assertEqual(self.approval_requests, [])

    def test_atomic_cas_failure_and_ambiguous_write_are_not_success(self):
        def no_ack(_):
            return None
        with self.assertRaises(ModelReviewDenied):
            self.decide(persist_review_atomic=no_ack)
        self.assertEqual(self.row["status"], "PENDING_REVIEW")
        def bad_ack(_):
            return {"model_id": self.model, "owner_shop_id": self.shop,
                    "status": "APPROVED", "rights_verified": True,
                    "rights_revision": 2, "audit_persisted": False,
                    "review_event_id": self.event_id}
        with self.assertRaises(ModelReviewDenied):
            self.decide(persist_review_atomic=bad_ack)
        self.assertEqual(self.row["status"], "PENDING_REVIEW")

    def test_current_rights_revocation_is_versioned_and_logged(self):
        self.decide()
        old_revision = self.row["rights_revision"]
        out = revoke_approved_model(
            shop_id=self.shop, model_id=self.model,
            reviewer_id=self.reviewer, reason="Photographer withdrew usage rights",
            read_model=self.callbacks()["read_model"],
            authorize_reviewer=self.callbacks()["authorize_reviewer"],
            persist_revocation_atomic=self.persist_revocation,
        )
        self.assertEqual(out["status"], "REVOKED")
        self.assertEqual(out["rights_revision"], old_revision + 1)
        self.assertFalse(out["rights_verified"])
        self.assertTrue(self.revocation_requests[0]["must_invalidate_media_cache"])
        with self.assertRaises(ModelReviewDenied):
            revoke_approved_model(
                shop_id=self.shop, model_id=self.model,
                reviewer_id=self.reviewer, reason="Previously revoked photo source",
                read_model=self.callbacks()["read_model"],
                authorize_reviewer=self.callbacks()["authorize_reviewer"],
                persist_revocation_atomic=self.persist_revocation,
            )
        self.assertEqual(len(self.revocation_requests), 1)

    def test_can_revoke_approved_model_when_original_license_was_withdrawn(self):
        self.decide()
        self.row["license_id"] = "WITHDRAWN"
        self.row["attribution"] = ""
        out = revoke_approved_model(
            shop_id=self.shop, model_id=self.model,
            reviewer_id=self.reviewer,
            reason="Original image commercial rights are no longer valid",
            read_model=self.callbacks()["read_model"],
            authorize_reviewer=self.callbacks()["authorize_reviewer"],
            persist_revocation_atomic=self.persist_revocation,
        )
        self.assertEqual(out["status"], "REVOKED")
        self.assertFalse(out["rights_verified"])
        self.assertEqual(out["rights_revision"], 3)

    def test_review_revocation_reason_and_replay_are_denied(self):
        self.decide()
        for reason in ("", "no", "unsafe\ntext"):
            with self.subTest(reason=reason), self.assertRaises(ModelReviewDenied):
                revoke_approved_model(
                    shop_id=self.shop, model_id=self.model,
                    reviewer_id=self.reviewer, reason=reason,
                    read_model=self.callbacks()["read_model"],
                    authorize_reviewer=self.callbacks()["authorize_reviewer"],
                    persist_revocation_atomic=self.persist_revocation,
                )
        self.assertFalse(self.revocation_requests)


if __name__ == "__main__":
    unittest.main()
