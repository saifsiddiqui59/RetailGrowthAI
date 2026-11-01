"""GPU-OFF mock output registration; no cloud, CUDA, secrets or paid calls."""
import sys
from pathlib import Path
from io import BytesIO
from uuid import uuid4
from hashlib import sha256
from unittest import TestCase, main
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
from feature3_private_output_v1 import PrivateOutputRegistrar, ProviderBlocked


def synthetic_png():
    image = Image.new("RGB", (256, 320), "#28718C")
    data = BytesIO(); image.save(data, "PNG")
    return data.getvalue()


class OutputContractTests(TestCase):
    def setUp(self):
        self.shop, self.job, self.token, self.asset, self.source = [str(uuid4()) for _ in range(5)]
        self.image = synthetic_png(); self.sha = sha256(self.image).hexdigest()
        self.meta = {"provider": "flux2-klein-4b", "provider_version": "2026-01", "weights_license": "Apache-2.0",
                     "synthetic": True, "attempt": 1, "claim_token": self.token,
                     "source_asset_ids": [self.source], "image_sha256": self.sha,
                     "quoted_cost_usd": 0.25, "inference_wall_seconds": 13.3,
                     "requires_human_review": True, "garment_fidelity_not_guaranteed": False}
        self.calls = []
        self.rights = True; self.claim = True; self.stage_good = True; self.commit_good = True
        self.commit_attempt = 1
        self.rights_sequence = None; self.quarantined = False
        def check_claim(*a):
            self.calls.append("claim");return self.claim
        def check_rights(*a):
            self.calls.append("rights")
            if self.rights_sequence is not None:return self.rights_sequence.pop(0)
            return self.rights
        def stage(shop,key,data,token):
            self.calls.append("stage");return {"object_key":key if self.stage_good else "bad/path",
                                             "sha256":self.sha,"bytes":len(data),"private":True}
        def commit(shop,job,attempt,token,key,digest,size,source_ids):
            self.calls.append("commit");return {
                "media_asset_id":self.asset,"shop_id":shop if self.commit_good else str(uuid4()),"job_id":job,
                "claim_token":token,"attempt":self.commit_attempt,"image_sha256":digest,"object_path":key,
                "review_status":"UNREVIEWED","source":"GENERATED","private":True}
        def quarantine(shop,key,token):
            self.calls.append("quarantine");self.quarantined=True;return True
        self.register = PrivateOutputRegistrar(validate_claim=check_claim,reauthorize=check_rights,
                                               stage=stage,commit=commit,quarantine=quarantine)

    def test_success_receipt_is_private_unreviewed_and_no_urls(self):
        result=self.register(self.shop,self.job,self.image,self.meta)
        self.assertEqual(result["media_asset_id"], self.asset)
        self.assertEqual(result["image_sha256"],self.sha)
        self.assertEqual(result["review_status"],"UNREVIEWED")
        self.assertEqual(self.calls,["claim","rights","stage","rights","commit"])
        self.assertNotIn("object_path",str(result))
        self.assertNotIn("image_bytes",str(result))
    def test_no_lease_denied_before_upload(self):
        self.claim=False
        with self.assertRaises(ProviderBlocked):self.register(self.shop,self.job,self.image,self.meta)
        self.assertNotIn("stage",self.calls)
    def test_no_rights_denied_before_upload(self):
        self.rights=False
        with self.assertRaises(ProviderBlocked):self.register(self.shop,self.job,self.image,self.meta)
        self.assertNotIn("stage",self.calls)
    def test_revoked_after_stage_quarantines_before_commit(self):
        self.rights_sequence=[True,False]
        with self.assertRaises(ProviderBlocked):self.register(self.shop,self.job,self.image,self.meta)
        self.assertTrue(self.quarantined)
        self.assertNotIn("commit",self.calls)
    def test_changed_output_hash_denied_before_upload(self):
        self.meta["image_sha256"]="a"*64
        with self.assertRaises(ProviderBlocked):self.register(self.shop,self.job,self.image,self.meta)
        self.assertFalse(self.calls)
    def test_foreign_or_malformed_job_denied(self):
        with self.assertRaises(ProviderBlocked):self.register("not-uuid",self.job,self.image,self.meta)
        with self.assertRaises(ProviderBlocked):self.register(self.shop,"not-uuid",self.image,self.meta)
        self.assertFalse(self.calls)
    def test_invalid_or_oversized_image_denied(self):
        with self.assertRaises(ProviderBlocked):self.register(self.shop,self.job,b"not png",self.meta)
        with self.assertRaises(ProviderBlocked):self.register(self.shop,self.job,b"0"*(25*1024*1024+1),self.meta)
        self.assertFalse(self.calls)
    def test_malformed_provenance_and_shas_denied(self):
        for k,v in [("provider","../../unknown"),("source_asset_ids",["not-uuid"]),("synthetic",False),
                    ("requires_human_review",False),("attempt",2),("inference_wall_seconds",901),
                    ("quoted_cost_usd",2.6)]:
            original=self.meta[k];self.meta[k]=v
            with self.subTest(k=k),self.assertRaises(ProviderBlocked):self.register(self.shop,self.job,self.image,self.meta)
            self.meta[k]=original
        self.assertFalse(self.calls)
    def test_bad_stage_ack_is_ambiguous_no_commit_or_delete(self):
        self.stage_good=False
        with self.assertRaises(ProviderBlocked):self.register(self.shop,self.job,self.image,self.meta)
        self.assertNotIn("commit",self.calls)
        self.assertFalse(self.quarantined)
    def test_bad_atomic_db_ack_not_retired_or_deleted(self):
        self.commit_good=False
        with self.assertRaises(ProviderBlocked):self.register(self.shop,self.job,self.image,self.meta)
        self.assertIn("commit",self.calls)
        self.assertFalse(self.quarantined)
    def test_private_db_commit_attempt_requires_true_integer_one_only(self):
        # A lost/forged DB acknowledgement must never be treated as verified
        # merely because Python equates True and 1 or 1.0 and 1.
        for invalid in (True, 1.0, "1", 0, 2, None, False):
            with self.subTest(receipt_attempt=repr(invalid)):
                self.setUp()
                self.commit_attempt=invalid
                with self.assertRaisesRegex(ProviderBlocked,"Media commit unconfirmed"):
                    self.register(self.shop,self.job,self.image,self.meta)
                self.assertEqual(self.calls,["claim","rights","stage","rights","commit"])
                self.assertFalse(self.quarantined)
        self.setUp()
        self.assertEqual(self.register(self.shop,self.job,self.image,self.meta)["attempt"],1)

    def test_private_metadata_attempt_bool_float_and_string_deny_before_any_stage(self):
        for invalid in (True, 1.0, "1", False, None):
            with self.subTest(metadata_attempt=repr(invalid)):
                self.setUp()
                self.meta["attempt"]=invalid
                with self.assertRaises(ProviderBlocked):
                    self.register(self.shop,self.job,self.image,self.meta)
                self.assertEqual(self.calls,[])

    def test_reject_untrusted_extra_keys(self):
        self.meta["object_path"]="foreign/key"
        with self.assertRaises(ProviderBlocked):self.register(self.shop,self.job,self.image,self.meta)
        self.assertFalse(self.calls)


if __name__=="__main__":main()
