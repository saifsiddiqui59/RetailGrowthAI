"""Feature3 model human review: exact JWT route, active roles, SQL receipt.

Synthetic users only. Source-only OFF-by-default route; not hosted live.
"""
from pathlib import Path
import sys
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from http_api import HTTPAPI
from feature3_v2_api import Feature3V2API
from security import AuthenticationError

CHECKS = {"adult_synthetic": True, "approved_uses": True, "image_license": True,
          "likeness_and_consent": True, "private_media_integrity": True,
          "visual_quality": True}


class Tenant:
    def __init__(self, shop):
        self.shop = shop
        self.role = "OWNER"
        self.active = True

    def member(self, token, uid, sid, *, write=False):
        if token != "fixture-signed-owner" or sid != self.shop or not self.active:
            return False
        return self.role in (("OWNER", "EDITOR") if write
                             else ("OWNER", "EDITOR", "VIEWER"))


class SignedStore:
    def __init__(self, shop, model):
        self.shop = shop
        self.model = model
        self.accept = True
        self.calls = []

    def _result(self, action):
        if not self.accept:
            return None
        return {"status": action, "rights_revision": 2,
                "review_event_id": str(uuid4()), "audit_persisted": True}

    def review_model(self, token, sid, mid, **kwargs):
        self.calls.append(("review", token, sid, mid, kwargs))
        return self._result("APPROVED" if kwargs["decision"] == "APPROVE" else "REJECTED")

    def revoke_model(self, token, sid, mid, **kwargs):
        self.calls.append(("revoke", token, sid, mid, kwargs))
        return self._result("REVOKED")


class ReviewHTTPTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.model, self.user = [str(uuid4()) for _ in range(3)]
        self.tenant = Tenant(self.shop)
        self.store = SignedStore(self.shop, self.model)
        self.human = Feature3V2API(self.tenant, self.store, model_review_enabled=True)
        self.off = Feature3V2API(self.tenant, self.store)
        def verify(token):
            if token != "fixture-signed-owner":
                raise AuthenticationError("Invalid synthetic JWT")
            return self.user
        self.verifier = verify
        self.review = f"/shops/{self.shop}/feature3-models/{self.model}/review"
        self.revoke = f"/shops/{self.shop}/feature3-models/{self.model}/revoke"
        self.review_body = {"decision": "APPROVE", "expected_revision": 1,
                            "image_sha256": "a" * 64, "evidence_revision": 1,
                            "checks": CHECKS,
                            "notes": "Human-reviewed synthetic garment source"}
        self.revoke_body = {"expected_revision": 2,
                            "image_sha256": "a" * 64,
                            "reason": "Commercial image usage rights withdrawn"}

    def handle(self, method, path, body=None, *, human=None, auth="Bearer fixture-signed-owner"):
        return HTTPAPI(self.verifier, self.tenant,
                       feature3_api=self.human if human is None else human
                       ).handle(method, path, auth, body)

    def test_model_review_requires_independent_flag_and_signed_jwt(self):
        self.assertEqual(self.handle("POST", self.review, self.review_body,
                                     human=self.off),
                         (503, {"error": "FEATURE3_MODEL_REVIEW_DISABLED"}))
        self.assertEqual(self.handle("POST", self.revoke, self.revoke_body,
                                     human=self.off)[0], 503)
        for auth in ("", "Bearer invalid", "Basic fake", "Bearer expired"):
            self.assertEqual(self.handle("POST", self.review, self.review_body,
                                         auth=auth)[0], 401)
        self.assertEqual(self.store.calls, [])

    def test_owner_review_editor_reject_and_owner_revoke(self):
        code, receipt = self.handle("POST", self.review, self.review_body)
        self.assertEqual(code, 200)
        self.assertEqual(receipt["status"], "APPROVED")
        self.assertTrue(receipt["audit_persisted"])
        self.assertFalse(receipt["gpu_enabled"])
        self.assertFalse(receipt["generation_executed"])
        self.assertEqual(self.store.calls[0][:4],
                         ("review", "fixture-signed-owner", self.shop, self.model))
        self.tenant.role = "EDITOR"
        code, receipt = self.handle(
            "POST", self.review, {**self.review_body,
                                 "decision": "REJECT",
                                 "checks": {**CHECKS, "visual_quality": False}})
        self.assertEqual((code, receipt["status"]), (200, "REJECTED"))
        code, receipt = self.handle("POST", self.revoke, self.revoke_body)
        self.assertEqual((code, receipt["status"]), (200, "REVOKED"))
        self.assertEqual(self.store.calls[-1][0], "revoke")

    def test_viewer_inactive_and_other_shop_never_reach_review_or_revoke(self):
        for state in ("VIEWER", "SUSPENDED", "INACTIVE"):
            self.tenant.role = state
            if state == "INACTIVE": self.tenant.active = False
            for route, body in ((self.review, self.review_body),
                                (self.revoke, self.revoke_body)):
                with self.subTest(state=state, route=route):
                    self.assertEqual(self.handle("POST", route, body)[0], 404)
            self.tenant.active = True
        self.tenant.role = "OWNER"
        wrong = self.review.replace(self.shop, str(uuid4()))
        self.assertEqual(self.handle("POST", wrong, self.review_body)[0], 404)
        self.assertEqual(self.store.calls, [])

    def test_extra_fields_malformed_method_and_unsupported_route_denied(self):
        for body in (None, [], {}, {**self.review_body, "reviewer_id": self.user}):
            with self.subTest(body=body):
                self.assertEqual(self.handle("POST", self.review, body)[0], 400)
        for method in ("GET", "PATCH", "DELETE"):
            self.assertEqual(self.handle(method, self.review, self.review_body)[0], 404)
        self.assertEqual(self.handle("POST", self.review + "/extra", self.review_body)[0], 404)
        self.assertEqual(self.handle("POST", self.review.replace("/review", "/approve"),
                                     self.review_body)[0], 404)
        self.assertEqual(self.handle("POST", self.revoke,
                                     {**self.revoke_body, "gpu": True})[0], 400)
        self.assertEqual(self.store.calls, [])

    def test_ambiguous_status_returns_conflict_no_retry(self):
        self.store.accept = False
        self.assertEqual(self.handle("POST", self.review, self.review_body),
                         (409, {"error": "MODEL_REVIEW_STALE_OR_DENIED"}))
        self.assertEqual(self.handle("POST", self.revoke, self.revoke_body),
                         (409, {"error": "MODEL_REVIEW_STALE_OR_DENIED"}))
        self.assertEqual(len(self.store.calls), 2)  # no automatic replay


if __name__ == "__main__":
    unittest.main()
