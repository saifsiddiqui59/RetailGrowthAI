"""Feature3 actual PNG/JPEG bytes handoff with synthetic tenant authorizers.

Real image decoding runs; JWT/curator/lease are isolated mocks. Never confuse
this suite with a hosted customer upload or actual provider inference.
"""
import json
import sys
import unittest
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"poster-engine"))
from fashion_reference_v1 import FashionReferenceDenied,prepare_fashion_references
from feature3_worker_inputs_v1 import materialize_feature4_inputs,materialize_feature5_input
from test_feature3_fashion_reference import FashionKurtiReferenceTests


class Feature3PrivateHandoffTests(unittest.TestCase):
    def setUp(self):
        self.f=FashionKurtiReferenceTests(methodName=
          "test_real_png_bytes_and_garment_exact_source_as_first_frame")
        self.f.setUp()
        self.leases=[]
    def claim(self,shop,ids,fingerprint):
        self.leases.append((shop,ids,fingerprint))
        return True
    def build(self,purpose,tryon=True):
        return prepare_fashion_references(
            shop_id=self.f.shop,garment_asset_id=self.f.garment,
            purpose=purpose,model_asset_id=self.f.model_asset,
            model_id=self.f.model_id,
            try_on_asset_id=self.f.tryon if tryon else None,
            **self.f.readers(),
        )

    def test_feature4_consumes_real_pillow_private_model_garment_tryon_bytes(self):
        manifest=self.build("editing")
        result=materialize_feature4_inputs(
            expected_manifest=manifest,current_readers=self.f.readers(),
            verify_render_job=self.claim)
        self.assertEqual(result["consumer"],"feature4")
        self.assertEqual(result["sources"]["garment"]["image_bytes"],
                         self.f.blobs[self.f.garment])
        self.assertEqual(result["sources"]["model"]["image_bytes"],
                         self.f.blobs[self.f.model_asset])
        self.assertEqual(result["sources"]["first_frame"]["image_bytes"],
                         self.f.blobs[self.f.tryon])
        self.assertEqual(result["sources"]["model"]["sha256"],
                         sha256(self.f.blobs[self.f.model_asset]).hexdigest())
        self.assertEqual(len(self.leases),1)
        self.assertFalse(result["publish_approved"])
        self.assertFalse(result["gpu_authorized"])
        self.assertNotIn("signed_url",str(result))
        self.assertNotIn("object_path",str(result))

    def test_feature4_unreviewed_input_uses_original_garment_as_first_frame(self):
        manifest=self.build("editing",tryon=False)
        result=materialize_feature4_inputs(
            expected_manifest=manifest,current_readers=self.f.readers(),
            verify_render_job=self.claim)
        self.assertEqual(result["sources"]["first_frame"]["image_bytes"],
                         result["sources"]["garment"]["image_bytes"])
        self.assertFalse(result["output_approved"])

    def test_feature5_actual_private_frame_bytes_without_gpu_permission(self):
        manifest=self.build("image_to_video")
        result=materialize_feature5_input(
            expected_manifest=manifest,current_readers=self.f.readers(),
            verify_motion_job=self.claim)
        self.assertEqual(result["consumer"],"feature5")
        self.assertEqual(result["image_bytes"],self.f.blobs[self.f.tryon])
        self.assertEqual(result["dimensions"],[720,1080])
        self.assertFalse(result["provider_call_permitted"])
        self.assertFalse(result["gpu_authorized"])
        self.assertTrue(len(self.leases)>=2)
        self.assertNotIn("signed_url",str(result))
        self.assertNotIn("object_path",str(result))

    def test_missing_durable_lease_denies_both_consumers(self):
        for purpose,fn,field in (("editing",materialize_feature4_inputs,"verify_render_job"),
                                ("image_to_video",materialize_feature5_input,"verify_motion_job")):
            with self.subTest(purpose=purpose):
                with self.assertRaises(FashionReferenceDenied):
                    fn(expected_manifest=self.build(purpose),
                       current_readers=self.f.readers(),
                       **{field:lambda *_:False})

    def test_stale_source_rights_fail_closed_without_delivering_bytes(self):
        for purpose,fn,field in (("editing",materialize_feature4_inputs,"verify_render_job"),
                                ("image_to_video",materialize_feature5_input,"verify_motion_job")):
            with self.subTest(purpose=purpose):
                expected=self.build(purpose)
                self.f.grants[self.f.model_asset]["rights_revoked"]=True
                with self.assertRaises(FashionReferenceDenied):
                    fn(expected_manifest=expected,current_readers=self.f.readers(),
                       **{field:self.claim})
                self.f.grants[self.f.model_asset]["rights_revoked"]=False

    def test_changed_original_bytes_denied_before_worker_reads(self):
        manifest=self.build("editing")
        self.f.blobs[self.f.garment]=self.f.blobs[self.f.model_asset]
        with self.assertRaises(FashionReferenceDenied):
            materialize_feature4_inputs(expected_manifest=manifest,
                current_readers=self.f.readers(),verify_render_job=self.claim)

    def test_foreign_shop_and_tampered_model_reference_rejected(self):
        manifest=self.build("editing")
        manifest["shop_id"]=self.f.other
        with self.assertRaises(FashionReferenceDenied):
            materialize_feature4_inputs(expected_manifest=manifest,
                current_readers=self.f.readers(),verify_render_job=self.claim)
        model=self.build("image_to_video")
        model["sources"]["model"]["sha256"]="0"*64
        with self.assertRaises(FashionReferenceDenied):
            materialize_feature5_input(expected_manifest=model,
                current_readers=self.f.readers(),verify_motion_job=self.claim)

    def test_missing_private_reader_and_forged_published_status_rejected(self):
        manifest=self.build("editing")
        incomplete=self.f.readers()
        incomplete["read_private_bytes"]=None
        with self.assertRaises(FashionReferenceDenied):
            materialize_feature4_inputs(expected_manifest=manifest,
                current_readers=incomplete,verify_render_job=self.claim)
        manifest=self.build("editing")
        manifest["output_approved"]=True
        with self.assertRaises(FashionReferenceDenied):
            materialize_feature4_inputs(expected_manifest=manifest,
                current_readers=self.f.readers(),verify_render_job=self.claim)


if __name__=="__main__":
    unittest.main()
