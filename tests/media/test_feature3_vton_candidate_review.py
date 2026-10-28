"""No-GPU synthetic kurti candidate, testable six-human-check QA intake."""
import sys
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
from uuid import uuid4
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"poster-engine"))
from fashion_reference_v1 import FashionReferenceDenied
from feature3_vton_candidate_review_v1 import intake_vton_candidate
from test_feature3_fashion_reference import FashionKurtiReferenceTests


class VTONCandidateTests(unittest.TestCase):
    def setUp(self):
        self.fixture=FashionKurtiReferenceTests(methodName="test_real_png_bytes_and_garment_exact_source_as_first_frame")
        self.fixture.setUp()
        f=self.fixture
        self.bundle=f.prepare(model_asset_id=f.model_asset,model_id=f.model_id)
        self.output=f.images["tryon"]
        self.response={
            "shop_id":f.shop,"provider_job_id":str(uuid4()),"claim_token":str(uuid4()),
            "provider":"tryon-v1.6","source_fingerprint":self.bundle["reference_fingerprint"],
            "model_asset_id":f.model_asset,"garment_asset_id":f.garment,
            "output_sha256":sha256(self.output).hexdigest(),
            "attempt":1,"output_png":self.output,
        }
        self.calls=[]
        def claim(*args):
            self.calls.append(args);return True
        self.claim=claim

    def intake(self,**kwargs):
        args={"approved_manifest":self.bundle,
              "provider_response":self.response,
              "verify_current_private_worker":self.claim}
        args.update(kwargs)
        return intake_vton_candidate(**args)

    def test_real_synthetic_png_unreviewed_never_approved(self):
        r=self.intake()
        self.assertEqual(r["status"],"CANDIDATE_UNREVIEWED")
        self.assertEqual(r["dimensions"],[720,1080])
        self.assertEqual(r["output_sha256"],sha256(self.output).hexdigest())
        self.assertEqual([x["feature"] for x in r["human_fidelity_checklist"]],
                         ["color","pattern","neckline","sleeves","length","embroidery"])
        self.assertEqual(r["human_fidelity_checklist"][-1]["expected"],
                         "Gold floral chest embroidery")
        for flag in ("generated_output_registered","publish_approved",
                     "licensed_for_marketing","gpu_authorized","visual_fidelity_verified"):
            self.assertIs(r[flag],False)
        self.assertNotIn("output_png",str(r))
        self.assertEqual(len(self.calls),1)

    def test_changed_png_sha_rejected_prior_to_claim(self):
        self.response["output_sha256"]="a"*64
        with self.assertRaises(FashionReferenceDenied):self.intake()
        self.assertEqual(self.calls,[])

    def test_wrong_shop_job_claim_and_attempt_denied(self):
        originals=deepcopy(self.response)
        for key,value in (("shop_id",str(uuid4())),("provider_job_id","bad-id"),
                          ("claim_token","fake"),("attempt",2),("provider","unlicensed-model")):
            self.response={**originals,key:value}
            with self.subTest(key=key),self.assertRaises(FashionReferenceDenied):
                self.intake()
        self.assertEqual(self.calls,[])

    def test_changed_first_frame_and_garment_source_denied(self):
        for key,value in (("source_fingerprint","b"*64),
                          ("garment_asset_id",str(uuid4())),
                          ("model_asset_id",str(uuid4()))):
            changed={**self.response,key:value}
            with self.subTest(key=key),self.assertRaises(FashionReferenceDenied):
                self.intake(provider_response=changed)
        self.assertEqual(self.calls,[])

    def test_lease_or_revoked_rights_denied(self):
        with self.assertRaises(FashionReferenceDenied):
            self.intake(verify_current_private_worker=lambda *args:False)
        self.assertEqual(len(self.calls),0)

    def test_no_model_unreviewed_model_or_approved_tryon_denied(self):
        changed=deepcopy(self.bundle);changed["model"]=None
        with self.assertRaises(FashionReferenceDenied):self.intake(approved_manifest=changed)
        changed=deepcopy(self.bundle);changed["try_on_review"]={"state":"HUMAN_REVIEW_PASSED"}
        with self.assertRaises(FashionReferenceDenied):self.intake(approved_manifest=changed)
        self.assertEqual(self.calls,[])

    def test_browser_additional_fields_and_text_media_denied(self):
        with self.assertRaises(FashionReferenceDenied):
            self.intake(provider_response={**self.response,"approved":True})
        with self.assertRaises(FashionReferenceDenied):
            self.intake(provider_response={**self.response,"output_png":b"not png"})
        self.assertEqual(self.calls,[])

    def test_missing_exact_garment_spec_denied(self):
        changed=deepcopy(self.bundle);changed["garment"]["embroidery"]=""
        with self.assertRaises(FashionReferenceDenied):self.intake(approved_manifest=changed)
        self.assertEqual(self.calls,[])

if __name__=="__main__":
    unittest.main()
