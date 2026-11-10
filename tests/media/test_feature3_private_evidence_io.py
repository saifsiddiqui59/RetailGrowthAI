"""Mocked HTTP wire tests for Feature3 real private Storage and service RPC adapter.

No live URLs, tenant tokens, real licensed assets, GPU or Supabase mutations.
"""
import json
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from uuid import uuid4
import sys
import unittest

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
from model_evidence_v1 import EvidenceDenied
from feature3_private_evidence_io import (
    Feature3PrivateEvidenceIO, PrivateEvidenceUnavailable,
)

ORIGIN = "https://fictionaltestproject.supabase.co"
PUB_KEY = "sb_publishable_FAKE_FOR_OFFLINE_TESTS"
SERVICE_KEY = "sb_secret_FAKE_FOR_OFFLINE_TESTS"


class FakeResponse:
    def __init__(self, url, data, *, redirect=False):
        self.url = url + "/changed" if redirect else url
        self.data = data
        self.headers = {"Content-Length": str(len(data))}

    def __enter__(self): return self
    def __exit__(self, *args): return False
    def geturl(self): return self.url
    def read(self, limit): return self.data[:limit]


class EvidenceWireTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.model_id, self.media_id, self.actor, self.foreign = [
            str(uuid4()) for _ in range(5)
        ]
        image = Image.new("RGB", (480, 720), "#B4A093")
        fd = BytesIO()
        image.save(fd, format="PNG")
        self.png = fd.getvalue()
        self.image_sha = sha256(self.png).hexdigest()
        self.license_sha = "a" * 64
        self.storage_path = (
            f"{self.shop}/model-library/{self.model_id}/{self.image_sha}.png")
        self.member = {"shop_id": self.shop, "user_id": self.actor,
                       "active": True, "role": "EDITOR"}
        self.model = {
            "owner_shop_id": self.shop, "model_id": self.model_id,
            "media_asset_id": self.media_id, "created_by": self.actor,
            "status": "PENDING_REVIEW", "rights_verified": False,
            "rights_revision": 1, "scope": "shop", "source_kind": "retailer_licensed",
            "image_sha256": self.image_sha,
            "license_evidence_sha256": self.license_sha,
            "license_id": "REVIEWED-COMMERCIAL", "synthetic_adult": True,
            "attribution": "Fictional test photo",
        }
        self.asset = {
            "id": self.media_id, "shop_id": self.shop,
            "storage_bucket": "retailgrowth-media",
            "object_path": self.storage_path,
            "mime_type": "image/png", "source": "UPLOAD",
            "license_name": "owned", "attribution": "Fictional test media only",
        }
        self.rights = {
            "model_id": self.model_id,
            "image_sha256": self.image_sha, "license_id": "REVIEWED-COMMERCIAL",
            "license_evidence_sha256": self.license_sha,
            "pose": "front", "source_uri": "https://example.invalid/licensed-photo",
            "synthetic_adult_verified": True, "component_rights_cleared": True,
            "commercial_reuse_approved": True,
        }
        self.calls = []
        self.ack = None
        self.redirect_blob = False
        self.user_token = "fake-signed-retailer-JWT-used-only-by-unit-test"
        def verify(token):
            if token != self.user_token:
                raise PrivateEvidenceUnavailable("Fake JWT rejected")
            return self.actor
        self.adapter = Feature3PrivateEvidenceIO(
            ORIGIN, PUB_KEY, SERVICE_KEY,
            verify_user_jwt=verify, transport=self.transport)

    def transport(self, req, *, timeout):
        self.calls.append(req)
        url = req.full_url
        if "/rest/v1/shop_memberships?" in url:
            payload = [self.member]
        elif "/rest/v1/feature3_models?" in url:
            payload = [self.model]
        elif "/rest/v1/media_assets?" in url:
            payload = [self.asset]
        elif "/rest/v1/rpc/feature3_commit_verified_evidence" in url:
            self.assertEqual(req.get_method(), "POST")
            self.assertEqual(req.get_header("Apikey"), SERVICE_KEY)
            self.assertIsNone(req.get_header("Authorization"))
            body = json.loads(req.data.decode())
            self.assertEqual(body["p_shop_id"], self.shop)
            self.assertEqual(body["p_model_id"], self.model_id)
            self.assertEqual(body["p_verifier_id"], self.actor)
            self.assertEqual(body["p_expected_image_sha256"], self.image_sha)
            payload = self.ack if self.ack is not None else {
                "owner_shop_id": self.shop, "model_id": self.model_id,
                "media_asset_id": self.media_id,
                "image_sha256": self.image_sha,
                "license_evidence_sha256": self.license_sha,
                "evidence_revision": 1, "persisted": True,
            }
        elif "/storage/v1/object/authenticated/retailgrowth-media/" in url:
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(req.get_header("Apikey"), PUB_KEY)
            self.assertEqual(req.get_header("Authorization"), "Bearer " + self.user_token)
            self.assertIn(self.storage_path, url)
            return FakeResponse(url, self.png, redirect=self.redirect_blob)
        else:
            raise AssertionError("Unknown or unsafe URL: " + url)
        if "/rpc/" not in url:
            self.assertEqual(req.get_header("Authorization"), "Bearer " + self.user_token)
        return FakeResponse(url, json.dumps(payload).encode())

    def call(self):
        return self.adapter.register_evidence(
            user_token=self.user_token, shop_id=self.shop,
            model_id=self.model_id,
            verify_image_license=lambda model, sha: self.rights)

    def rpc_count(self):
        return sum("/rpc/" in x.full_url for x in self.calls)

    def test_real_private_authenticated_endpoint_then_service_only_insert(self):
        result = self.call()
        self.assertTrue(result["evidence_persisted"])
        self.assertFalse(result["model_approved"])
        self.assertFalse(result["gpu_authorized"])
        self.assertEqual(self.rpc_count(), 1)
        self.assertEqual(len(self.calls), 5)  # member, model, asset, storage, RPC
        self.assertFalse(any("object/public/" in x.full_url or "object/sign/" in x.full_url
                             for x in self.calls))

    def test_viewer_foreign_inactive_membership_denied_without_storage_or_rpc(self):
        for changes in ({"role": "VIEWER"}, {"active": False},
                        {"shop_id": self.foreign}, {"user_id": self.foreign}):
            self.member = {"shop_id": self.shop, "user_id": self.actor,
                           "active": True, "role": "EDITOR", **changes}
            self.calls.clear()
            with self.subTest(changes=changes), self.assertRaises(PrivateEvidenceUnavailable):
                self.call()
            self.assertEqual(len(self.calls), 1)
            self.assertEqual(self.rpc_count(), 0)

    def test_changed_blob_hash_wrong_path_or_model_denies_rpc(self):
        for case in ("hash", "key", "shop", "revoked"):
            old_png, old_asset, old_model = self.png, dict(self.asset), dict(self.model)
            if case == "hash":
                image = Image.new("RGB", (480, 720), "#456789")
                f = BytesIO(); image.save(f, format="PNG")
                self.png = f.getvalue()
            elif case == "key":
                self.asset["object_path"] = f"{self.foreign}/model-library/stolen.png"
            elif case == "shop":
                self.model["owner_shop_id"] = self.foreign
            else:
                self.model["status"] = "REVOKED"
            self.calls.clear()
            with self.subTest(case=case), self.assertRaises((EvidenceDenied, PrivateEvidenceUnavailable)):
                self.call()
            self.assertEqual(self.rpc_count(), 0)
            self.png, self.asset, self.model = old_png, old_asset, old_model

    def test_bad_unverified_license_denied_after_read_but_before_rpc(self):
        self.rights["commercial_reuse_approved"] = False
        with self.assertRaises(EvidenceDenied):
            self.call()
        self.assertEqual(self.rpc_count(), 0)

    def test_storage_redirect_refused_no_rpc(self):
        self.redirect_blob = True
        with self.assertRaises(PrivateEvidenceUnavailable):
            self.call()
        self.assertEqual(self.rpc_count(), 0)

    def test_uncertain_or_forged_privileged_ack_no_retry(self):
        self.ack = {"persisted": True}
        with self.assertRaises(EvidenceDenied):
            self.call()
        self.assertEqual(self.rpc_count(), 1)
        self.calls.clear()
        self.ack = False
        with self.assertRaises(PrivateEvidenceUnavailable):
            self.call()
        self.assertEqual(self.rpc_count(), 1)

    def test_invalid_verifier_token_and_project_origin_denied(self):
        with self.assertRaises(PrivateEvidenceUnavailable):
            self.adapter.register_evidence(
                user_token="expired-or-forged", shop_id=self.shop,
                model_id=self.model_id, verify_image_license=lambda *_: self.rights)
        self.assertEqual(self.calls, [])
        for origin in ("http://not-https.supabase.co",
                       "https://example.invalid",
                       "https://project.supabase.co@evil.invalid",
                       "https://project.supabase.co/unsafe"):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                Feature3PrivateEvidenceIO(origin, PUB_KEY, SERVICE_KEY,
                                          verify_user_jwt=lambda _: self.actor)


if __name__ == "__main__":
    unittest.main()
