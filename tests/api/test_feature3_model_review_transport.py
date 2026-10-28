"""Signed Feature3 human model-review/revoke API transport, offline HTTP mocks."""
from pathlib import Path
from uuid import uuid4
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from feature3_v2_store import Feature3V2Store
from tenant_store import StorageUnavailable

CHECKS = {
    "adult_synthetic": True, "likeness_and_consent": True,
    "image_license": True, "private_media_integrity": True,
    "visual_quality": True, "approved_uses": True,
}


class ReviewTransportTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.model, self.event = [str(uuid4()) for _ in range(3)]
        self.token = "signed-retailer-jwt-verified-by-existing-auth"
        self.digest = "a" * 64
        self.store = Feature3V2Store("https://project.supabase.co", "public-publishable-key")
        self.requests = []
        self.result = {
            "owner_shop_id": self.shop, "model_id": self.model,
            "review_event_id": self.event, "status": "APPROVED",
            "rights_verified": True, "rights_revision": 2,
            "audit_persisted": True,
        }
        def req(token, path, *, query=None, body=None):
            self.requests.append((token, path, body))
            return self.result
        self.store._request = req

    def review(self, **kw):
        a = dict(decision="APPROVE", expected_revision=1,
                 image_sha256=self.digest, evidence_revision=1,
                 checks=CHECKS, notes="Independently reviewed adult model image")
        a.update(kw)
        return self.store.review_model(self.token, self.shop, self.model, **a)

    def revoke(self, **kw):
        a = dict(expected_revision=1, image_sha256=self.digest,
                 reason="Verified marketing rights were withdrawn")
        a.update(kw)
        return self.store.revoke_model(self.token, self.shop, self.model, **a)

    def test_review_uses_same_user_jwt_and_complete_sql_args(self):
        out = self.review()
        self.assertTrue(out["audit_persisted"])
        self.assertEqual(self.requests[0][0], self.token)
        self.assertEqual(self.requests[0][1], "rpc/feature3_review_model")
        body = self.requests[0][2]
        self.assertEqual(body["p_shop_id"], self.shop)
        self.assertEqual(body["p_model_id"], self.model)
        self.assertEqual(body["p_expected_image_sha256"], self.digest)
        self.assertEqual(body["p_checks"], CHECKS)
        self.assertNotIn("p_actor_id", body)
        self.assertNotIn("service_role", str(body))

    def test_explicit_rejection_is_reviewed_but_not_rights_verified(self):
        self.result = {**self.result, "status": "REJECTED", "rights_verified": False}
        out = self.review(decision="REJECT", checks={**CHECKS, "visual_quality": False})
        self.assertFalse(out["rights_verified"])

    def test_revoke_does_not_require_license_and_changes_to_revoked(self):
        self.result = {**self.result, "status": "REVOKED", "rights_verified": False}
        out = self.revoke()
        self.assertEqual(out["status"], "REVOKED")
        self.assertEqual(self.requests[0][1], "rpc/feature3_revoke_model")
        self.assertNotIn("p_actor_id", self.requests[0][2])

    def test_stale_or_foreign_or_missing_audit_receipt_denied(self):
        for fields in (
            {"owner_shop_id": str(uuid4())}, {"model_id": str(uuid4())},
            {"rights_revision": 1}, {"audit_persisted": False},
            {"rights_verified": False}, {"review_event_id": "forged"},
            {"status": "PENDING_REVIEW"},
        ):
            self.result = {**self.result, **fields}
            with self.subTest(fields=fields), self.assertRaises((StorageUnavailable, ValueError)):
                self.review()
            self.result = {
                "owner_shop_id": self.shop, "model_id": self.model,
                "review_event_id": self.event, "status": "APPROVED",
                "rights_verified": True, "rights_revision": 2,
                "audit_persisted": True,
            }
        self.result = None
        self.assertIsNone(self.review())

    def test_untrusted_body_fails_before_any_rpc(self):
        for changes in (
            {"decision": "AUTO_APPROVE"},
            {"checks": {**CHECKS, "image_license": "true"}},
            {"checks": {"visual_quality": True}},
            {"checks": {**CHECKS, "image_license": False}},
            {"evidence_revision": 0},
            {"evidence_revision": True},
            {"notes": "too short"},
            {"notes": "Unsafe\nreview note"},
            {"expected_revision": 0},
            {"image_sha256": "fake"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.review(**changes)
        self.assertEqual(self.requests, [])

    def test_no_service_key_as_fake_reviewer_token(self):
        with self.assertRaises(ValueError):
            self.store.review_model("sb_secret_nope", self.shop, self.model,
                                    decision="APPROVE", expected_revision=1,
                                    image_sha256=self.digest, evidence_revision=1,
                                    checks=CHECKS, notes="Human review evidence")
        self.assertEqual(self.requests, [])


if __name__ == "__main__":
    unittest.main()
