"""Feature3 private model-byte proof, independent license gate (synthetic only)."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from uuid import uuid4
import sys
import unittest

from PIL import Image, PngImagePlugin

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
from model_evidence_v1 import EvidenceDenied, prepare_verified_model_evidence


def fake_png(extra=False):
    im = Image.new("RGB", (360, 512), "#CC9988")
    io = BytesIO()
    info = None
    if extra:
        info = PngImagePlugin.PngInfo()
        info.add_text("XML:com.adobe.xmp", "private-camera-metadata")
    im.save(io, "PNG", pnginfo=info)
    return io.getvalue()


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.other, self.model_id, self.media, self.verifier = [
            str(uuid4()) for _ in range(5)
        ]
        self.raw = fake_png()
        self.digest = sha256(self.raw).hexdigest()
        self.license_sha = "a" * 64
        self.model = {
            "owner_shop_id": self.shop, "model_id": self.model_id,
            "media_asset_id": self.media, "status": "PENDING_REVIEW",
            "rights_verified": False, "rights_revision": 1,
            "scope": "shop", "source_kind": "retailer_licensed",
            "license_id": "REVIEWED-COMMERCIAL",
            "license_evidence_sha256": self.license_sha,
            "image_sha256": self.digest, "synthetic_adult": True,
        }
        self.path = f"{self.shop}/model-library/{self.model_id}/{self.digest}.png"
        self.asset = {"id": self.media, "shop_id": self.shop,
                      "storage_bucket": "retailgrowth-media",
                      "object_path": self.path, "mime_type": "image/png",
                      "source": "UPLOAD"}
        self.rights = {
            "model_id": self.model_id, "image_sha256": self.digest,
            "license_id": "REVIEWED-COMMERCIAL",
            "license_evidence_sha256": self.license_sha,
            "pose": "front",
            "source_uri": "https://example.invalid/licensed-original",
            "synthetic_adult_verified": True,
            "component_rights_cleared": True,
            "commercial_reuse_approved": True,
        }
        self.grant = {
            "authorized": True, "service_verified": True,
            "shop_id": self.shop, "verifier_id": self.verifier,
        }
        self.writes = []
        self.reads = []
        self.persisted = True

    def args(self, **changes):
        def binary(bucket, path):
            self.reads.append((bucket, path))
            return self.raw

        def insert(row):
            self.writes.append(row)
            return {
                "owner_shop_id": self.shop, "model_id": self.model_id,
                "media_asset_id": self.media,
                "image_sha256": self.digest,
                "license_evidence_sha256": self.license_sha,
                "evidence_revision": 1, "persisted": self.persisted,
            }

        p = dict(shop_id=self.shop, model_id=self.model_id,
                 verifier_id=self.verifier,
                 read_model=lambda *_: self.model,
                 authorize_verifier=lambda *_: self.grant,
                 read_media=lambda *_: self.asset,
                 read_private_bytes=binary,
                 verify_image_license=lambda *_: self.rights,
                 write_evidence_once=insert)
        p.update(changes)
        return p

    def test_true_private_binary_and_license_commit_not_approval(self):
        receipt = prepare_verified_model_evidence(**self.args())
        self.assertTrue(receipt["evidence_persisted"])
        self.assertEqual(receipt["image_dimensions"], [360, 512])
        self.assertEqual(receipt["image_sha256"], self.digest)
        self.assertFalse(receipt["model_approved"])
        self.assertFalse(receipt["gpu_authorized"])
        self.assertEqual(self.reads, [("retailgrowth-media", self.path)])
        self.assertEqual(self.writes[0]["verified_by"], self.verifier)
        self.assertNotIn("object_path", self.writes[0])
        self.assertNotIn("image_bytes", self.writes[0])

    def test_viewer_or_untrusted_verifier_cannot_make_evidence(self):
        for change in ({"authorized": False}, {"service_verified": False},
                       {"shop_id": self.other}, {"verifier_id": self.other}):
            self.grant = {**self.grant, **change}
            with self.subTest(change=change), self.assertRaises(EvidenceDenied):
                prepare_verified_model_evidence(**self.args())
            self.grant = {**self.grant, **{k: v for k, v in
                          {"authorized": True, "service_verified": True,
                           "shop_id": self.shop, "verifier_id": self.verifier}.items()}}
        self.assertEqual(self.reads, [])
        self.assertEqual(self.writes, [])

    def test_foreign_replaced_private_registration_denied(self):
        for key, value in [("shop_id", self.other), ("storage_bucket", "public"),
                           ("object_path", f"{self.other}/model-library/stolen.png"),
                           ("mime_type", "image/jpeg"), ("id", self.other)]:
            original = self.asset[key]
            self.asset[key] = value
            with self.subTest(key=key), self.assertRaises(EvidenceDenied):
                prepare_verified_model_evidence(**self.args())
            self.asset[key] = original
        self.assertEqual(self.reads, [])

    def test_replaced_pixels_and_metadata_and_nonbinary_fail_closed(self):
        for raw in (fake_png(extra=True), fake_png() + b"modified", b"garbage", None):
            self.raw = raw
            with self.subTest(raw_type=type(raw)), self.assertRaises(EvidenceDenied):
                prepare_verified_model_evidence(**self.args())
        self.assertEqual(self.writes, [])

    def test_unreviewed_or_revoked_or_rights_revision_changed_deny(self):
        for field, value in [("status", "APPROVED"), ("status", "REVOKED"),
                             ("rights_verified", True), ("rights_revision", 2),
                             ("owner_shop_id", self.other),
                             ("source_kind", "unlicensed")]:
            old = self.model[field]
            self.model[field] = value
            with self.subTest(field=field), self.assertRaises(EvidenceDenied):
                prepare_verified_model_evidence(**self.args())
            self.model[field] = old
        self.assertEqual(self.writes, [])

    def test_independent_commercial_license_is_not_declared_by_browser(self):
        for field, value in [
            ("commercial_reuse_approved", False),
            ("component_rights_cleared", False),
            ("synthetic_adult_verified", False),
            ("pose", "not-a-pose"),
            ("license_evidence_sha256", "0" * 64),
            ("source_uri", "http://untrusted.invalid"),
            ("source_uri", "https://example.invalid:broken/path"),
            ("model_id", self.other),
        ]:
            original = self.rights[field]
            self.rights[field] = value
            with self.subTest(field=field), self.assertRaises(EvidenceDenied):
                prepare_verified_model_evidence(**self.args())
            self.rights[field] = original
        self.assertEqual(self.writes, [])

    def test_uncertain_storage_commit_never_reports_success(self):
        self.persisted = False
        with self.assertRaises(EvidenceDenied):
            prepare_verified_model_evidence(**self.args())
        self.assertEqual(len(self.writes), 1)
        # No automatic retry after lost ACK.
        self.assertEqual(len(self.reads), 1)

    def test_platform_reference_keeps_owner_first_private_storage(self):
        self.model["scope"] = "platform"
        self.asset["object_path"] = (
            f"{self.shop}/model-library/platform/{self.model_id}/{self.digest}.png")
        out = prepare_verified_model_evidence(**self.args())
        self.assertTrue(out["evidence_persisted"])
        self.assertTrue(self.reads[0][1].startswith(self.shop + "/"))


if __name__ == "__main__":
    unittest.main()
