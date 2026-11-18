"""Feature3 generated output one-shot service PostgREST transport (no cloud)."""
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from feature3_gpu_service import Feature3GPUServiceStore
from tenant_store import StorageUnavailable


class PrivateOutputCASTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.job, self.token, self.asset, self.source = [
            str(uuid4()) for _ in range(5)]
        self.sha = "c" * 64
        self.key = f"{self.shop}/feature3/gpu/{self.job}/{self.sha}.png"
        self.store = Feature3GPUServiceStore("https://example.supabase.co",
                                              "sb_secret_fixture")
        self.store.db.request = Mock()
        self.args = (self.shop,self.job,1,self.token,
                     self.key,self.sha,345,[self.source])
        self.receipt = {"media_asset_id": self.asset,"shop_id":self.shop,
                        "job_id":self.job,"claim_token":self.token,"attempt":1,
                        "image_sha256":self.sha,"object_path":self.key,
                        "review_status":"UNREVIEWED","source":"GENERATED",
                        "private":True}

    def test_exact_service_one_shot_rpc_receipt(self):
        self.store.db.request.return_value = dict(self.receipt)
        result = self.store.commit_private_output(*self.args)
        self.assertEqual(result["media_asset_id"],self.asset)
        self.assertNotIn("object_path",result)
        self.assertEqual(result["review_status"],"UNREVIEWED")
        self.store.db.request.assert_called_once_with(
            "rpc/feature3_commit_gpu_private_output", method="POST",
            data={"p_shop_id":self.shop,"p_job_id":self.job,"p_attempt":1,
                  "p_claim_token":self.token,"p_object_path":self.key,
                  "p_image_sha256":self.sha,"p_object_bytes":345,
                  "p_source_asset_ids":[self.source]})

    def test_missing_or_ambiguous_ack_single_call_never_replay(self):
        for response in (None,{},[],{**self.receipt,"private":False},
                         {**self.receipt,"shop_id":str(uuid4())},
                         {**self.receipt,"attempt":2},
                         {**self.receipt,"review_status":"APPROVED"},
                         {**self.receipt,"image_sha256":"a"*64}):
            with self.subTest(response=response):
                self.store.db.request.reset_mock(return_value=True,side_effect=True)
                self.store.db.request.return_value=response
                with self.assertRaises(StorageUnavailable):
                    self.store.commit_private_output(*self.args)
                self.assertEqual(self.store.db.request.call_count,1)

    def test_forged_or_malformed_input_denied_before_transport(self):
        invalid = (
            (str(uuid4()),self.job,1,self.token,self.key,self.sha,345,[self.source]),
            (self.shop,self.job,2,self.token,self.key,self.sha,345,[self.source]),
            (self.shop,self.job,1,self.token,self.key,"0"*63,345,[self.source]),
            (self.shop,self.job,1,self.token,self.key,self.sha,True,[self.source]),
            (self.shop,self.job,1,self.token,self.key,self.sha,0,[self.source]),
            (self.shop,self.job,1,self.token,self.key,self.sha,345,[str(uuid4()),str(uuid4())]*7),
            (self.shop,self.job,1,self.token,self.key,self.sha,345,[self.source,self.source]),
        )
        for args in invalid:
            with self.subTest(args=args),self.assertRaises(ValueError):
                self.store.commit_private_output(*args)
        self.store.db.request.assert_not_called()

if __name__=="__main__":
    unittest.main()
