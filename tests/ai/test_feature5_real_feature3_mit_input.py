"""Actual-bytes Feature3 MIT model+garment -> Feature5 native input tests.

These are SOURCE-verified images carried into the repository from Feature3's
pinned OpenVTO upstream; they are NOT the same garment worn by the model.
No network, no VTON, no ComfyUI HTTP, no cloud, no GPU or provider charges.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest

from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"poster-engine"))
from feature3_demo_inputs_v1 import validated_manifest, verify_demo_image
from feature5_motion.feature3_mit_demo_input import stage_feature3_mit_fashion_test_input
from feature5_motion.wan22_motion_adapter import WanCompatibilityError
from feature5_motion.infra.feature35_comfy_api_graphs import offline_graph_validate

MEDIA=ROOT/"tests/fixtures/feature5/f3_real_openvto"
MANIFEST=ROOT/"tests/fixtures/feature3/openvto_demo_sources_v1.json"


class ActualF3GarmentModelInputTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads(MANIFEST.read_text("utf8"))
        self.assertTrue(MEDIA.is_dir())

    def receive(self, root, manifest=None, validator=validated_manifest, verifier=verify_demo_image):
        return stage_feature3_mit_fashion_test_input(
            fixture_dir=root,scratch_parent=self.temp,
            source_manifest=self.manifest if manifest is None else manifest,
            validate_f3_manifest=validator,verify_f3_image=verifier)

    def test_real_feature3_original_images_to_native_wan_input_graph_gpu_off(self):
        with TemporaryDirectory() as td:
            self.temp=Path(td)
            with self.receive(MEDIA) as (frame,graph,proof):
                self.assertTrue(frame.is_file())
                self.assertEqual(frame.stat().st_mode & 0o777,0o600)
                self.assertEqual(frame.parent.stat().st_mode & 0o777,0o700)
                self.assertEqual(proof["source_feature"],"feature3")
                self.assertEqual(proof["source_commit"],self.manifest["source_commit"])
                self.assertEqual(proof["staged_first_frame_sha256"],sha256(frame.read_bytes()).hexdigest())
                self.assertNotEqual(proof["model_image_sha256"],proof["garment_image_sha256"])
                self.assertTrue(proof["source_garment_is_separate_from_model"])
                with Image.open(frame) as image:
                    self.assertEqual(image.size,(704,1280))
                    self.assertEqual(image.format,"PNG")
                    self.assertIsNotNone(image.getbbox())
                self.assertTrue(offline_graph_validate(graph))
                latent=[n for n in graph["prompt"].values()
                        if n["class_type"]=="Wan22ImageToVideoLatent"]
                self.assertEqual(len(latent),1)
                self.assertEqual((latent[0]["inputs"]["width"],
                                  latent[0]["inputs"]["height"],
                                  latent[0]["inputs"]["length"]),(704,1280,121))
                for key in ("model_wears_retailer_garment_verified",
                            "actual_vton_inference_performed",
                            "actual_wan_inference_performed",
                            "provider_call_permitted","cost_reservation_authorized",
                            "publish_approved","gpu_started"):
                    self.assertIs(proof[key],False,key)
            self.assertFalse(frame.exists())

    def test_source_pixels_license_and_permissions_reject_mutation(self):
        with TemporaryDirectory() as td:
            self.temp=Path(td)
            folder=Path(td)/"sources"
            shutil.copytree(MEDIA,folder)
            for filename in ("model_posture.jpg","garment_front.jpg","LICENSE-OpenVTO.txt"):
                original=(folder/filename).read_bytes()
                changed=bytearray(original)
                changed[-1]^=1
                (folder/filename).write_bytes(changed)
                with self.subTest(filename=filename),self.assertRaises(WanCompatibilityError):
                    with self.receive(folder):
                        pass
                (folder/filename).write_bytes(original)
            (folder/"model_posture.jpg").unlink()
            (folder/"model_posture.jpg").symlink_to(MEDIA/"model_posture.jpg")
            with self.assertRaises(WanCompatibilityError):
                with self.receive(folder):
                    pass

    def test_forged_commercial_rights_and_provider_flags_not_accepted(self):
        for change in (
            ("rights_approved_for_customer_publishing",True),
            ("virtual_tryon_generated_by_retailgrowth",True),
            ("tenant_private",True),
        ):
            modified=deepcopy(self.manifest)
            modified[change[0]]=change[1]
            with TemporaryDirectory() as td:
                self.temp=Path(td)
                with self.subTest(change=change),self.assertRaises(WanCompatibilityError):
                    with self.receive(MEDIA,modified):
                        pass
        for field,value in (("provider_call_authorized",True),
                            ("cost_reservation_authorized",True),
                            ("first_frame","garment_front.jpg")):
            modified=deepcopy(self.manifest)
            modified["feature5"][field]=value
            with TemporaryDirectory() as td:
                self.temp=Path(td)
                with self.subTest(field=field),self.assertRaises(WanCompatibilityError):
                    with self.receive(MEDIA,modified):
                        pass

    def test_must_use_feature3_real_verification_not_fake_receipt(self):
        with TemporaryDirectory() as td:
            self.temp=Path(td)
            with self.assertRaises(WanCompatibilityError):
                with self.receive(MEDIA,verifier=lambda row,raw: {
                    "file":row["file"],"sha256":"0"*64,
                    "git_blob_sha1":row["git_blob_sha1"]}):
                    pass
            with self.assertRaises(WanCompatibilityError):
                with self.receive(MEDIA,validator=lambda m:{"fake":True}):
                    pass


if __name__=="__main__":
    unittest.main()
