"""Feature 3 model library unit tests: no GPU, no outside image downloads."""
from dataclasses import replace
from io import BytesIO
from pathlib import Path
import sys
import unittest
from uuid import uuid4

from PIL import Image, PngImagePlugin

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
from model_library_v2 import (
    ModelCandidate, ModelLibraryDenied, import_model_image, checked_model_for_use,
)


def picture(extra_metadata=False):
    image = Image.new("RGB", (420, 640), "#C8D6C5")
    buffer = BytesIO()
    extra = None
    if extra_metadata:
        extra = PngImagePlugin.PngInfo()
        extra.add_text("personal-location", "should never leave source upload")
    image.save(buffer, "PNG", pnginfo=extra)
    return buffer.getvalue()


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.shop = str(uuid4())
        self.other = str(uuid4())
        self.evidence = "a" * 64
        self.registered_media_id = str(uuid4())
        self.candidate = ModelCandidate(
            owner_shop_id=self.shop,
            scope="shop",
            source_kind="opensource_render",
            source_uri="https://www.makehumancommunity.org/about/license.html",
            license_id="CC0-1.0",
            license_evidence_sha256=self.evidence,
            synthetic_adult=True,
            third_party_assets_cleared=True,
            label="Sample adult model 01",
            pose="front",
        )
        self.saved = []
        self.assets = {}
        self.approved = True
        self.actor = True
        self.curator = False
        self.valid_uses = ["poster", "try_on", "video_reference"]

    def callbacks(self):
        def authorize(candidate):
            return {
                "shop_id": self.shop, "scope": candidate.scope,
                "authorized": self.actor,
                "curator_approved": self.curator,
            }
        def verify(candidate, _):
            return {
                "approved": self.approved,
                "license_id": candidate.license_id,
                "evidence_sha256": candidate.license_evidence_sha256,
                "allow_reuse": True,
                "uses": self.valid_uses,
            }
        def write(key, data, metadata):
            if key in self.assets and self.assets[key] != data:
                raise AssertionError("Content-addressed object cannot be overwritten")
            self.assets[key] = data
            return {"key": key, "sha256": metadata["image_sha256"],
                    "private": True, "owner_shop_id":self.shop,
                    "media_asset_id":self.registered_media_id}
        def register(row):
            self.saved.append(row)
            return {key: row[key] for key in
                    ("model_id", "owner_shop_id", "scope", "status", "media_asset_id")}
        return {
            "authorize_import": authorize,
            "verify_image_license": verify,
            "write_private_png": write,
            "register_model": register,
        }

    def store(self, image_bytes=None, candidate=None):
        return import_model_image(
            candidate=candidate or self.candidate,
            image_bytes=image_bytes or picture(),
            **self.callbacks())

    def test_single_import_seeds_shop_private_library_reused_by_all_three(self):
        saved = self.store(image_bytes=picture(extra_metadata=True))
        self.assertEqual(saved["status"], "PENDING_REVIEW")
        self.assertEqual(saved["media_asset_id"], self.registered_media_id)
        self.assertTrue(saved["storage_key"].startswith(self.shop + "/model-library/"))
        self.assertFalse(saved["inference_executed_by_import"])
        self.assertEqual(len(self.assets), 1)
        self.assertNotIn(b"personal-location", next(iter(self.assets.values())))
        again = self.store(image_bytes=picture(extra_metadata=True))
        self.assertEqual(saved["model_id"], again["model_id"])
        self.assertEqual(saved["storage_key"], again["storage_key"])
        # Import is not visual approval. A privileged reviewer/DB must
        # change the state outside this module.
        with self.assertRaisesRegex(ModelLibraryDenied, "unreviewed"):
            checked_model_for_use(
                model=saved, requesting_shop_id=self.shop,
                usage="poster", authorize_use=lambda *_: True)
        reviewed = {**saved, "status": "APPROVED"}
        for use in ("poster", "try_on", "video_reference"):
            checked = checked_model_for_use(
                model=reviewed, requesting_shop_id=self.shop,
                usage=use, authorize_use=lambda *_: True)
            self.assertEqual(checked["model_id"], saved["model_id"])
            self.assertTrue(checked["requires_private_signed_media"])
        with self.assertRaisesRegex(ModelLibraryDenied, "Another shop"):
            checked_model_for_use(
                model=reviewed, requesting_shop_id=self.other,
                usage="poster", authorize_use=lambda *_: True)

    def test_model_import_requires_real_registered_same_shop_media_id(self):
        callbacks=self.callbacks()
        good_write=callbacks["write_private_png"]
        for fake in (
            lambda key,data,metadata: {**good_write(key,data,metadata),
                                      "media_asset_id":str(uuid4()),
                                      "owner_shop_id":self.other},
            lambda key,data,metadata: {k:v for k,v in good_write(key,data,metadata).items()
                                      if k!="media_asset_id"},
            lambda key,data,metadata: {**good_write(key,data,metadata),
                                      "media_asset_id":"not-a-uuid"},
        ):
            with self.subTest(fake=fake):
                with self.assertRaises(ModelLibraryDenied):
                    import_model_image(candidate=self.candidate,
                        image_bytes=picture(),
                        **{**callbacks,"write_private_png":fake})
        self.assertEqual(self.saved, [])

    def test_platform_import_requires_curator_and_then_both_shops_can_reference(self):
        platform_candidate = replace(self.candidate, scope="platform")
        with self.assertRaisesRegex(ModelLibraryDenied, "curator"):
            self.store(candidate=platform_candidate)
        self.curator = True
        saved = self.store(candidate=platform_candidate)
        self.assertTrue(saved["storage_key"].startswith(self.shop + "/model-library/platform/"))
        approved = {**saved, "status": "APPROVED"}
        for shop in [self.shop, self.other]:
            result = checked_model_for_use(
                model=approved, requesting_shop_id=shop,
                usage="try_on", authorize_use=lambda *_: True)
            self.assertEqual(result["model_id"], saved["model_id"])

    def test_revoke_license_or_media_before_import_and_every_reuse(self):
        self.approved = False
        with self.assertRaisesRegex(ModelLibraryDenied, "commercial rights"):
            self.store()
        self.assertFalse(self.assets)
        self.assertFalse(self.saved)
        self.approved = True
        saved = self.store()
        with self.assertRaisesRegex(ModelLibraryDenied, "rights"):
            checked_model_for_use(
                model={**saved, "status": "APPROVED"},
                requesting_shop_id=self.shop, usage="video_reference",
                authorize_use=lambda *_: False)

    def test_unreviewed_license_and_missing_platform_sharing_privilege_deny(self):
        for c in (
            replace(self.candidate, license_id="MODEL_CODE_APACHE_2.0"),
            replace(self.candidate, license_evidence_sha256="unverified"),
            replace(self.candidate, synthetic_adult=False),
            replace(self.candidate, third_party_assets_cleared=False),
            replace(self.candidate, source_uri="http://github.com/sample"),
            replace(self.candidate, source_uri="https://person:secret@example.com/image"),
            replace(self.candidate, source_uri="https://example.com/image#token"),
        ):
            with self.subTest(candidate=c):
                with self.assertRaises(ModelLibraryDenied):
                    self.store(candidate=c)
        self.assertEqual(len(self.assets), 0)

    def test_attribution_required_for_cc_by_and_retained_in_consumer_receipt(self):
        ccby = replace(self.candidate, license_id="CC-BY-4.0")
        with self.assertRaisesRegex(ModelLibraryDenied, "attribution"):
            self.store(candidate=ccby)
        ccby = replace(ccby, attribution="Example artist · CC BY 4.0")
        saved = self.store(candidate=ccby)
        approved = {**saved, "status": "APPROVED"}
        receipt = checked_model_for_use(
            model=approved, requesting_shop_id=self.shop,
            usage="poster", authorize_use=lambda *_: True)
        self.assertIn("Example artist", receipt["attribution"])

    def test_false_approval_and_storage_receipt_cannot_create_a_model(self):
        callbacks = self.callbacks()
        callbacks["authorize_import"] = lambda *_: {
            "shop_id": self.other, "scope": "shop", "authorized": True}
        with self.assertRaisesRegex(ModelLibraryDenied, "permission"):
            import_model_image(candidate=self.candidate,
                               image_bytes=picture(), **callbacks)
        self.assertFalse(self.assets)
        callbacks = self.callbacks()
        callbacks["write_private_png"] = lambda key, data, doc: {
            "key": key, "sha256": doc["image_sha256"], "private": False}
        with self.assertRaisesRegex(ModelLibraryDenied, "storage"):
            import_model_image(candidate=self.candidate,
                               image_bytes=picture(), **callbacks)
        self.assertFalse(self.saved)

    def test_invalid_or_animated_source_blocks_before_persistence(self):
        with self.assertRaisesRegex(ModelLibraryDenied, "decoded"):
            self.store(image_bytes=b"fake AI model image")
        large = Image.new("RGB", (200, 300))
        output = BytesIO()
        large.save(output, "PNG")
        with self.assertRaisesRegex(ModelLibraryDenied, "Unsupported"):
            self.store(image_bytes=output.getvalue())
        gif = BytesIO()
        Image.new("RGB", (300, 300), "red").save(gif, format="GIF")
        with self.assertRaisesRegex(ModelLibraryDenied, "Unsupported"):
            self.store(image_bytes=gif.getvalue())
        self.assertEqual(len(self.assets), 0)

    def test_bogus_model_key_or_malformed_permission_list_cannot_be_reused(self):
        saved = self.store()
        reviewed = {**saved, "status": "APPROVED"}
        with self.assertRaisesRegex(ModelLibraryDenied, "storage lineage"):
            checked_model_for_use(
                model={**reviewed, "storage_key":
                       self.shop + "/model-library/other/" +
                       saved["image_sha256"] + ".png"},
                requesting_shop_id=self.shop, usage="poster",
                authorize_use=lambda *_: True)
        with self.assertRaisesRegex(ModelLibraryDenied, "unreviewed"):
            checked_model_for_use(
                model={**reviewed, "approved_uses": None},
                requesting_shop_id=self.shop, usage="poster",
                authorize_use=lambda *_: True)

    def test_independent_rights_uses_must_be_exact_safe_distinct_scopes(self):
        """No malformed or expanded grant can reach private storage/registry."""
        invalid = (
            [["poster"], "try_on", "video_reference"],
            ["poster", "try_on", "try_on"],
            ["poster", "try_on", "video_reference", "admin"],
            ["poster", "try_on"],
            ["poster", False, "video_reference"],
            {"poster": True, "try_on": True, "video_reference": True},
            "poster,try_on,video_reference",
            None,
        )
        for uses in invalid:
            with self.subTest(uses=repr(uses)):
                self.valid_uses = uses
                with self.assertRaisesRegex(ModelLibraryDenied, "commercial rights"):
                    self.store()
                self.assertFalse(self.assets)
                self.assertFalse(self.saved)

    def test_independent_rights_accept_exact_list_tuple_and_set(self):
        for uses in (
            ["poster", "try_on", "video_reference"],
            ("poster", "try_on", "video_reference"),
            {"poster", "try_on", "video_reference"},
            frozenset({"poster", "try_on", "video_reference"}),
        ):
            with self.subTest(type=type(uses).__name__):
                self.valid_uses = uses
                self.assertEqual(self.store()["status"], "PENDING_REVIEW")


    def test_reusable_model_rejects_invalid_use_grants_before_rights_callback(self):
        saved=self.store()
        reviewed={**saved,"status":"APPROVED"}
        invalid=(
            ["poster","unreviewed_paid_inference"],
            ["poster","poster"],
            ["poster",None],
            ["poster",["try_on"]],
            ["poster","try_on","video_reference","admin"],
            {"poster":True},
            [],
            None,
            "poster",
            ["video_reference"],
        )
        for uses in invalid:
            checked=[]
            with self.subTest(uses=repr(uses)),self.assertRaises(ModelLibraryDenied):
                checked_model_for_use(
                    model={**reviewed,"approved_uses":uses},
                    requesting_shop_id=self.shop,usage="poster",
                    authorize_use=lambda *args: checked.append(args) or True)
            self.assertEqual(checked,[])
        for uses in (["poster"],["poster","try_on"],{"poster","video_reference"}):
            with self.subTest(valid=repr(uses)):
                grant=checked_model_for_use(
                    model={**reviewed,"approved_uses":uses},
                    requesting_shop_id=self.shop,usage="poster",
                    authorize_use=lambda *_:True)
                self.assertEqual(grant["model_id"],saved["model_id"])

    def test_reusable_model_rejects_unlicensed_or_malformed_metadata_before_rights(self):
        saved=self.store()
        reviewed={**saved,"status":"APPROVED"}
        malformed=(
            {"license_id":None},
            {"license_id":[]},
            {"license_id":"MODEL_CODE_APACHE_2.0"},
            {"scope":[]},
            {"scope":"unreviewed"},
            {"license_id":"CC-BY-4.0","attribution":42},
            {"license_id":"CC-BY-4.0","attribution":"   "},
            {"license_id":"CC-BY-4.0","attribution":None},
            {"attribution":"x"*201},
        )
        for mutation in malformed:
            calls=[]
            with self.subTest(mutation=repr(mutation)),self.assertRaises(ModelLibraryDenied):
                checked_model_for_use(
                    model={**reviewed,**mutation},
                    requesting_shop_id=self.shop,usage="poster",
                    authorize_use=lambda *args:calls.append(args) or True)
            self.assertEqual(calls,[])
        with self.assertRaises(ModelLibraryDenied):
            checked_model_for_use(
                model=reviewed,requesting_shop_id=self.shop,
                usage=["poster"],authorize_use=lambda *_:True)

    def test_newly_created_ai_model_uses_same_library_contract_no_second_schema(self):
        generated = replace(
            self.candidate, source_kind="created_ai",
            source_uri="https://github.com/black-forest-labs/flux2",
            label="Generated model A"
        )
        saved = self.store(candidate=generated)
        self.assertEqual(saved["source_kind"], "created_ai")
        self.assertEqual(saved["schema"], "retailgrowth.model-library.v1")
        self.assertEqual(saved["status"], "PENDING_REVIEW")


if __name__ == "__main__":
    unittest.main()
