"""Actual private PNG bytes using the existing Feature3 fixture + offline RLS fakes.

These tests are NOT real DEV JWT sign-in, commercial license or paid generation.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
from fashion_reference_v1 import FashionReferenceDenied
from fashion_reference_v1 import prepare_fashion_references
from feature3_worker_input_handoff import (
    resolve_private_worker_inputs, temporary_private_worker_inputs,
)
from test_feature3_fashion_reference import FashionKurtiReferenceTests


class PrivateHandoffTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FashionKurtiReferenceTests(
            "test_real_png_bytes_and_garment_exact_source_as_first_frame")
        self.fixture.setUp()
        self.readers = self.fixture.readers()
        self.editor = prepare_fashion_references(
            shop_id=self.fixture.shop, garment_asset_id=self.fixture.garment,
            model_asset_id=self.fixture.model_asset, model_id=self.fixture.model_id,
            purpose="editing", **self.readers)
        self.motion = prepare_fashion_references(
            shop_id=self.fixture.shop, garment_asset_id=self.fixture.garment,
            model_asset_id=self.fixture.model_asset, model_id=self.fixture.model_id,
            purpose="image_to_video", **self.readers)
        self.claims = []

    def lease(self, shop, sources, fingerprint):
        self.claims.append((shop, sources, fingerprint))
        return shop == self.fixture.shop and fingerprint in (
            self.editor["reference_fingerprint"], self.motion["reference_fingerprint"])

    def call(self, manifest, **overrides):
        kw = dict(expected_manifest=manifest, current_readers=self.readers,
                  verify_worker_job=self.lease)
        kw.update(overrides)
        return resolve_private_worker_inputs(**kw)

    def test_real_pillow_garment_and_model_bytes_to_editor_not_browser(self):
        packet = self.call(self.editor)
        self.assertEqual(packet["purpose"], "editing")
        self.assertEqual(packet["images"]["garment"]["image_bytes"],
                         self.fixture.images["garment"])
        self.assertEqual(packet["images"]["model"]["image_bytes"],
                         self.fixture.images["model"])
        self.assertEqual(packet["images"]["first_frame"]["image_bytes"],
                         self.fixture.images["garment"])
        self.assertTrue(packet["rights_checked"])
        self.assertFalse(packet["output_approved"])
        self.assertFalse(packet["gpu_authorized"])
        self.assertFalse(packet["provider_call_permitted"])
        self.assertEqual(self.claims[0][0], self.fixture.shop)
        self.assertEqual(len(self.claims[0][1]), 2)

    def test_motion_worker_gets_same_authorized_first_frame_only_with_claim(self):
        packet = self.call(self.motion)
        self.assertEqual(packet["images"]["first_frame"]["image_bytes"],
                         self.fixture.blobs[self.fixture.garment])
        self.assertEqual(packet["purpose"], "image_to_video")
        self.assertGreaterEqual(len(self.claims), 2)  # Existing Feature5 gate reclaims

    def test_tenant_and_worker_lease_denials(self):
        with self.assertRaises(FashionReferenceDenied):
            self.call(self.editor, verify_worker_job=lambda *a: 1)
        with self.assertRaises(FashionReferenceDenied):
            self.call(self.editor, verify_worker_job=None)
        with self.assertRaises(FashionReferenceDenied):
            self.call(self.editor, verify_worker_job=lambda *a: False)
        self.fixture.rows[self.fixture.garment]["shop_id"] = self.fixture.other
        with self.assertRaises(FashionReferenceDenied):
            self.call(self.editor)

    def test_revoke_model_and_product_revision_invalidate_cached_manifest(self):
        self.fixture.grants[self.fixture.model_asset]["rights_revoked"] = True
        with self.assertRaises(FashionReferenceDenied):
            self.call(self.editor)
        self.fixture.grants[self.fixture.model_asset]["rights_revoked"] = False
        self.fixture.product_revision += 1
        with self.assertRaises(FashionReferenceDenied):
            self.call(self.editor)

    def test_worker_final_private_read_rejects_bool_or_float_rights_revision(self):
        # A transient untyped authorizer must not pass because Python treats
        # True and 1.0 as numerically equal to the immutable revision 1.
        # A final later clean grant never excuses an unsafe intermediate read.
        for forged in (True, 1.0):
            with self.subTest(revision=repr(forged)):
                self.setUp()
                for grant in self.fixture.grants.values():
                    grant["rights_revision"] = 1
                self.fixture.model_data["rights_revision"] = 1
                expected = prepare_fashion_references(
                    shop_id=self.fixture.shop,
                    garment_asset_id=self.fixture.garment,
                    model_asset_id=self.fixture.model_asset,
                    model_id=self.fixture.model_id,
                    purpose="editing", **self.readers)
                readers = self.fixture.readers()
                original_grant = readers["authorize_asset"]
                observed = [0]
                def transient_grant(shop, asset, purpose):
                    value = original_grant(shop, asset, purpose)
                    if asset == self.fixture.garment:
                        observed[0] += 1
                        if observed[0] == 2:
                            return {**value, "rights_revision": forged}
                    return value
                readers["authorize_asset"] = transient_grant
                with self.assertRaises(FashionReferenceDenied):
                    resolve_private_worker_inputs(
                        expected_manifest=expected,
                        current_readers=readers,
                        verify_worker_job=lambda *_: True)
                self.assertEqual(observed[0], 2)
                # No worker image packet is returned and ephemeral files
                # must not be allocated by a rejected current source grant.

    def test_transient_private_object_path_substitution_denied_before_worker_read(self):
        # The first manifest pass sees the legitimate shop-owned source.
        # A transient, still-SHA-identical row on the final byte read must
        # not trigger even one read of a foreign or unexpected Storage path.
        for mutation in (
            {"object_path":f"{self.fixture.other}/uploads/{self.fixture.upload_object}.png"},
            {"object_path":f"{self.fixture.shop}/uploads/../secret.png"},
            {"object_path":"https://foreign.example/private.png"},
            {"object_path":f"{self.fixture.shop}/model-library/foreign/portrait.png"},
            {"source":"GENERATED"},
            {"storage_bucket":"public-media"},
        ):
            with self.subTest(mutation=mutation):
                self.setUp()
                row_reader=self.readers["read_asset"]
                byte_reader=self.readers["read_private_bytes"]
                seen=[0]
                paths=[]
                def substituted_row(shop,asset):
                    row=row_reader(shop,asset)
                    if asset==self.fixture.garment:
                        seen[0]+=1
                        if seen[0]==2:
                            return {**row,**mutation}
                    return row
                def observed_bytes(shop,asset,path):
                    paths.append(path)
                    return byte_reader(shop,asset,path)
                readers={**self.readers,"read_asset":substituted_row,
                         "read_private_bytes":observed_bytes}
                with self.assertRaises(FashionReferenceDenied):
                    resolve_private_worker_inputs(
                        expected_manifest=self.editor,
                        current_readers=readers,
                        verify_worker_job=lambda *_: True)
                self.assertEqual(seen[0],2)
                # Initial manifest read: garment and model. No final read
                # against the substituted path is permitted.
                self.assertEqual(len(paths),2)
                self.assertNotIn(mutation.get("object_path","never"),paths)

    def test_final_byte_integrity_fails_after_lease(self):
        def changed(shop, ids, digest):
            self.fixture.blobs[self.fixture.garment] = self.fixture.blobs[self.fixture.model_asset]
            return True
        with self.assertRaises(FashionReferenceDenied):
            self.call(self.editor, verify_worker_job=changed)

    def test_revoke_after_final_private_read_denied(self):
        original = self.readers["read_private_bytes"]
        seen = [0]
        def read(shop, asset, path):
            raw = original(shop, asset, path)
            seen[0] += 1
            if seen[0] >= 4:
                self.fixture.grants[self.fixture.garment]["rights_revoked"] = True
            return raw
        readers = {**self.readers, "read_private_bytes": read}
        with self.assertRaises(FashionReferenceDenied):
            self.call(self.editor, current_readers=readers)

    def test_expired_worker_lease_after_private_reads_denies_bytes(self):
        calls = []
        def expires(*args):
            calls.append(args)
            return len(calls) == 1
        with self.assertRaises(FashionReferenceDenied):
            self.call(self.editor, verify_worker_job=expires)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], calls[1])

    def test_worker_lease_revoked_during_ephemeral_file_write_never_yields(self):
        calls = []
        def expires_after_resolution(*args):
            calls.append(args)
            return len(calls) < 3
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(FashionReferenceDenied):
                with temporary_private_worker_inputs(
                        expected_manifest=self.editor,
                        current_readers=self.readers,
                        verify_worker_job=expires_after_resolution,
                        trusted_temp_root=root):
                    self.fail("Revoked private worker lease exposed staged paths")
            self.assertEqual(len(calls), 3)
            self.assertEqual(list(Path(root).iterdir()), [])


    def test_rights_revoked_in_final_lease_callback_denies_memory_bytes(self):
        calls = []
        def lease_and_revoke(shop, ids, fingerprint):
            calls.append((shop, ids, fingerprint))
            if len(calls) == 2:
                self.fixture.grants[self.fixture.garment]["rights_revoked"] = True
            return True
        with self.assertRaises(FashionReferenceDenied):
            self.call(self.editor, verify_worker_job=lease_and_revoke)
        self.assertEqual(len(calls), 2)

    def test_rights_revoked_after_file_staging_denies_ephemeral_paths(self):
        calls = []
        def lease_and_revoke(shop, ids, fingerprint):
            calls.append((shop, ids, fingerprint))
            if len(calls) == 3:
                self.fixture.grants[self.fixture.model_asset]["rights_revoked"] = True
            return True
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(FashionReferenceDenied):
                with temporary_private_worker_inputs(
                        expected_manifest=self.editor,
                        current_readers=self.readers,
                        verify_worker_job=lease_and_revoke,
                        trusted_temp_root=root):
                    self.fail("Revoked rights exposed staged private paths")
            self.assertEqual(len(calls), 3)
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_garment_revision_changing_during_final_file_lease_denies(self):
        calls = []
        def lease_and_change_product(shop, ids, fingerprint):
            calls.append((shop, ids, fingerprint))
            if len(calls) == 3:
                self.fixture.product_revision += 1
            return True
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(FashionReferenceDenied):
                with temporary_private_worker_inputs(
                        expected_manifest=self.editor,
                        current_readers=self.readers,
                        verify_worker_job=lease_and_change_product,
                        trusted_temp_root=root):
                    self.fail("Changed garment revision exposed private files")
            self.assertEqual(len(calls), 3)
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_reject_arbitrary_browser_claim_reader_or_unapproved_tryon(self):
        with self.assertRaises(FashionReferenceDenied):
            self.call({"purpose": "editing"})
        with self.assertRaises(FashionReferenceDenied):
            self.call(self.editor, current_readers={"read_asset":lambda *_: None})
        bad = dict(self.editor)
        bad["purpose"] = "publish"
        with self.assertRaises(FashionReferenceDenied):
            self.call(bad)

    def test_ephemeral_files_have_no_credentials_and_are_cleaned(self):
        with tempfile.TemporaryDirectory() as root:
            with temporary_private_worker_inputs(
                    expected_manifest=self.editor,
                    current_readers=self.readers, verify_worker_job=self.lease,
                    trusted_temp_root=root) as bundle:
                folder = Path(bundle["temporary_directory"])
                self.assertTrue(folder.is_dir())
                self.assertEqual(folder.stat().st_mode & 0o777, 0o700)
                self.assertEqual(bundle["manifest"]["purpose"], "editing")
                self.assertFalse(bundle["manifest"]["publish_approved"])
                self.assertNotIn("image_bytes", str(bundle["manifest"]))
                self.assertNotIn("storage_key", str(bundle["manifest"]))
                for role in ("garment", "model", "first_frame"):
                    file = folder / bundle["manifest"]["images"][role]["relative_path"]
                    self.assertEqual(file.stat().st_mode & 0o777, 0o600)
                    self.assertGreater(len(file.read_bytes()), 100)
            self.assertFalse(folder.exists())

    def test_cleanup_when_editor_raises(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(RuntimeError):
                with temporary_private_worker_inputs(
                    expected_manifest=self.editor,
                    current_readers=self.readers, verify_worker_job=self.lease,
                    trusted_temp_root=root) as bundle:
                    folder = Path(bundle["temporary_directory"])
                    raise RuntimeError("FFmpeg crashed")
            self.assertFalse(folder.exists())


if __name__ == "__main__":
    unittest.main()
