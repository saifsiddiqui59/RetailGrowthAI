"""An actual OpenPeople-shaped LOCAL image import, without downloading assets."""
from dataclasses import replace
from hashlib import sha1, sha256
from pathlib import Path
import sys
import tempfile
import unittest
from uuid import uuid4

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
from openpeople_import_v2 import OpenPeopleSelection, import_openpeople_still
from model_library_v2 import ModelLibraryDenied, checked_model_for_use


class OpenPeopleTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.photo = (self.root / "openpeople/data/curated/P001/assets/studio_posture.jpg")
        self.photo.parent.mkdir(parents=True)
        Image.new("RGB", (420, 700), "#CDB6B3").save(self.photo, "JPEG")
        self.shop = str(uuid4())
        self.calls = []
        self.registered_media_id = str(uuid4())
        self.source_revision = "a" * 40
        raw = self.photo.read_bytes()
        self.git_blob_sha = sha1(b"blob " + str(len(raw)).encode("ascii") +
                                 bytes([0]) + raw).hexdigest()
        self.selection = OpenPeopleSelection(
            dataset_root=self.root, source_revision=self.source_revision,
            person_id="P001", image_kind="studio_posture",
            expected_image_git_blob_sha=self.git_blob_sha)
        self.license_hash = "b" * 64

    def import_it(self, **overrides):
        arguments = dict(
            selection=self.selection, owner_shop_id=self.shop,
            scope="shop", license_evidence_sha256=self.license_hash,
            source_rights_reviewed=True,
            authorize_import=lambda candidate: {
                "shop_id":self.shop, "scope":candidate.scope,
                "authorized": True, "curator_approved": False},
            verify_image_license=lambda candidate, digest: {
                "approved": True, "license_id": candidate.license_id,
                "evidence_sha256": candidate.license_evidence_sha256,
                "allow_reuse": True,
                "uses": ["poster","try_on","video_reference"]},
            write_private_png=lambda key, raw, metadata: self.write(key, raw, metadata),
            register_model=lambda doc: self.register(doc),
        )
        arguments.update(overrides)
        return import_openpeople_still(**arguments)

    def write(self, key, raw, metadata):
        self.calls.append(("write", key, raw))
        return {"key":key, "sha256":sha256(raw).hexdigest(),"private":True,
                "owner_shop_id":self.shop,"media_asset_id":self.registered_media_id}

    def register(self, doc):
        self.calls.append(("register", doc))
        return {k:doc[k] for k in ("model_id","owner_shop_id","scope","status","media_asset_id")}

    def test_open_source_avatar_real_still_is_normalized_and_stored_privately(self):
        record = self.import_it()
        self.assertEqual(record["license_id"], "CC-BY-4.0")
        self.assertEqual(record["pose"], "full_body")
        self.assertIn("Prompt Haus", record["attribution"])
        self.assertIn(self.source_revision, record["source_uri"])
        self.assertEqual(record["status"], "PENDING_REVIEW")
        self.assertEqual(record["media_asset_id"],self.registered_media_id)
        self.assertEqual([x[0] for x in self.calls], ["write","register"])
        self.assertTrue(self.calls[0][1].startswith(self.shop+"/model-library/"))
        self.assertTrue(self.calls[0][2].startswith(b"\x89PNG\r\n\x1a\n"))
        reviewed = {**record, "status": "APPROVED"}
        for purpose in ("poster","try_on","video_reference"):
            receipt = checked_model_for_use(
                model=reviewed, requesting_shop_id=self.shop,
                usage=purpose, authorize_use=lambda *_: True)
            self.assertEqual(receipt["model_id"], record["model_id"])

    def test_openpeople_stills_do_not_bypass_independent_rights_review(self):
        with self.assertRaisesRegex(ModelLibraryDenied, "review required"):
            self.import_it(source_rights_reviewed=False)
        with self.assertRaisesRegex(ModelLibraryDenied, "rights"):
            self.import_it(verify_image_license=lambda *_: {
                "approved":False})
        self.assertEqual(self.calls, [])

    def test_missing_or_unlisted_content_and_path_symlink_denied(self):
        with self.assertRaisesRegex(ModelLibraryDenied, "missing"):
            self.import_it(selection=replace(
                self.selection,person_id="P002"))
        with self.assertRaisesRegex(ModelLibraryDenied, "identity"):
            self.import_it(selection=replace(
                self.selection,person_id="../P001"))
        with self.assertRaisesRegex(ModelLibraryDenied, "still type"):
            self.import_it(selection=replace(
                self.selection,image_kind="thumbnails/studio_posture"))
        other = self.photo.parent / "original.jpg"
        self.photo.rename(other)
        try:
            self.photo.symlink_to(other)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        with self.assertRaisesRegex(ModelLibraryDenied, "Linked"):
            self.import_it()

    def test_same_path_changed_bytes_or_forged_blob_digest_fail_closed(self):
        original = self.photo.read_bytes()
        mutated = bytearray(original)
        mutated[-3] ^= 1
        self.photo.write_bytes(mutated)
        with self.assertRaisesRegex(ModelLibraryDenied, "pinned Git blob"):
            self.import_it()
        self.assertFalse(self.calls)
        self.photo.write_bytes(original)
        with self.assertRaisesRegex(ModelLibraryDenied, "pinned Git blob"):
            self.import_it(selection=replace(
                self.selection, expected_image_git_blob_sha="b"*40))
        self.assertFalse(self.calls)

    def test_import_belongs_to_original_shop_and_bears_no_gpu_charge(self):
        record = self.import_it()
        self.assertFalse(record["inference_executed_by_import"])
        self.assertEqual(record["source_kind"], "opensource_render")
        reviewed = {**record, "status":"APPROVED"}
        with self.assertRaisesRegex(ModelLibraryDenied, "Another shop"):
            checked_model_for_use(model=reviewed,
                                  requesting_shop_id=str(uuid4()),
                                  usage="poster", authorize_use=lambda *_:True)


if __name__ == "__main__":
    unittest.main()
