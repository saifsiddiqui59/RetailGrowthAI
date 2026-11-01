"""Feature3 service-only private generated output composition; CPU-only fixtures.

All model output uses Pillow and a fake private HTTPS transport. Fake provider
approvals only drive in-memory contract code; no GPU/cloud/API money is spent.
"""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest
from uuid import uuid4
from urllib.error import HTTPError

from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"poster-engine"))
from ai_providers_v2 import (
    InferenceJob, OptionalGPUProvider, ProviderConfig, ProviderBlocked,
)
from feature3_private_gpu_runtime import Feature3PrivateGPUWorker


def generated_png():
    buffer=BytesIO()
    Image.new("RGB",(320,400),"#2a5976").save(buffer,"PNG")
    return buffer.getvalue()


class Reply(BytesIO):
    def __init__(self,raw,url,status=200):
        super().__init__(raw)
        self._url=url
        self._status=status
    def geturl(self): return self._url
    def getcode(self): return self._status


class FakePrivateStorage:
    def __init__(self):
        self.bytes={}
        self.methods=[]
        self.corrupt=False
    def __call__(self,request,timeout):
        assert timeout==30
        url=request.full_url
        method=request.get_method()
        self.methods.append(method)
        if method=="POST":
            if url in self.bytes:
                raise OSError("duplicate object")
            self.bytes[url]=request.data
            path=url.split("/storage/v1/object/retailgrowth-media/",1)[1]
            return Reply(json.dumps({"Key":path}).encode(),url,201)
        if method=="GET":
            if url not in self.bytes:
                raise HTTPError(url,404,"Not Found",None,None)
            data=self.bytes[url]
            if self.corrupt:
                data=data[:-1]+bytes([data[-1]^1])
            return Reply(data,url)
        if method=="DELETE":
            self.bytes.pop(url,None)
            return Reply(b"{}",url)
        raise AssertionError("unexpected private Storage method")


class FakeSQL:
    def __init__(self,shop,job,source):
        self.shop,self.job,self.source=shop,job,source
        self.reservation=str(uuid4())
        self.media=str(uuid4())
        self.token=None
        self.calls=[]
        self.lease_active=True
        self.foreign_receipt=False
        self.unknown_commit=False
        self.reservation_attempt=1
        self.reservation_id_override=None
        self.reserved_usd="0.05"
        self.commit_attempt=1
    def claim(self,job_id,token):
        self.calls.append("claim")
        if job_id!=self.job or self.token is not None:
            raise AssertionError("second/foreign one-shot GPU claim")
        self.token=token
        return {"shop_id":self.shop,"job_id":job_id,"attempt":1,"claim_token":token}
    def read_prepaid_reservation(self,shop,job,attempt,token):
        self.calls.append("lease")
        if not self.lease_active or (shop,job,attempt,token)!=(
                self.shop,self.job,1,self.token):
            raise ProviderBlocked("expired/foreign one-shot SQL lease")
        return {"reservation_id":self.reservation if self.reservation_id_override is None
                else self.reservation_id_override,
                "shop_id":self.shop if not self.foreign_receipt else str(uuid4()),
                "job_id":job,"attempt":self.reservation_attempt,"claim_token":token,
                "reserved_usd":self.reserved_usd}
    def commit_private_output(self,shop,job,attempt,token,key,digest,size,ids):
        self.calls.append("commit")
        if (shop,job,attempt,token)!=(self.shop,self.job,1,self.token):
            raise AssertionError("invalid CAS identity")
        if ids!=(self.source,) or len(digest)!=64 or size<100 or not key.endswith(digest+".png"):
            raise AssertionError("untrusted immutable output CAS")
        if self.unknown_commit:
            raise TimeoutError("DB write may have committed")
        return {"shop_id":shop if not self.foreign_receipt else str(uuid4()),
                "job_id":job,"claim_token":token,"attempt":self.commit_attempt,
                "media_asset_id":self.media,"image_sha256":digest,
                "private":True,"review_status":"UNREVIEWED"}
    def finish(self,job,token,actual,asset):
        self.calls.append(("finish",actual,asset))
        if job!=self.job or token!=self.token or asset!=self.media:
            raise AssertionError("unconfirmed financial settlement")
        return True


class WorkerCompositionTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.job,self.source=[str(uuid4()) for _ in range(3)]
        self.png=generated_png()
        self.storage=FakePrivateStorage()
        self.service=FakeSQL(self.shop,self.job,self.source)
        self.rights_calls=0
        self.revoke_after=None
        self.provider=self.provider_fixture(True)
        self.runtime=self.make_runtime()

    def provider_fixture(self,enabled):
        # Local CPU-only synchronous mock. Not a real FLUX/GPU authorization.
        return OptionalGPUProvider(ProviderConfig(
            name="local-test",version="unit",capabilities=frozenset({"image_edit"}),
            code_license="Apache-2.0",weights_license="Apache-2.0",
            dependency_licenses_approved=True,cost_approved=enabled,
            gpu_deployed=enabled,gpu_rate_usd_per_hour=1,
            estimated_gpu_seconds=60,max_cost_usd_per_job=0.05,
        ),runner=lambda *_:self.png)

    def rights(self,shop,job,token,sources):
        self.rights_calls+=1
        return (shop==self.shop and job==self.job and token==self.service.token
                and sources==(self.source,)
                and (self.revoke_after is None or self.rights_calls<self.revoke_after))

    def make_runtime(self):
        return Feature3PrivateGPUWorker(
            provider=self.provider,service=self.service,
            supabase_origin="https://fixture.supabase.co",
            backend_secret="sb_secret_"+"z"*36,
            current_rights=self.rights,
            resolve_private_inputs=lambda shop,ids:{self.source:b"PRIVATE_INPUT"},
            trusted_meter_usd=lambda *_:"0.011500",
            storage_transport=self.storage,
        )

    def test_end_to_end_fake_sql_private_png_and_one_real_settle(self):
        result=self.runtime.execute(InferenceJob(
            self.shop,self.job,"image_edit",(self.source,),prompt="test only"))
        self.assertEqual(result["media_asset_id"],self.service.media)
        self.assertEqual(result["image_sha256"],sha256(self.png).hexdigest())
        self.assertTrue(result["private"])
        self.assertEqual(result["review_status"],"UNREVIEWED")
        self.assertEqual(self.storage.methods,["POST","GET"])
        self.assertEqual(self.service.calls.count("claim"),1)
        self.assertEqual(self.service.calls.count("commit"),1)
        self.assertEqual(self.service.calls.count("lease"),2)
        self.assertEqual([x for x in self.service.calls if isinstance(x,tuple)],
                         [("finish","0.011500",self.service.media)])
        self.assertGreaterEqual(self.rights_calls,4)
        self.assertFalse(any("signed" in str(x).lower() for x in result.values()))

    def test_disabled_provider_does_not_claim_store_or_output(self):
        self.provider=self.provider_fixture(False)
        disabled=self.make_runtime()
        with self.assertRaisesRegex(ProviderBlocked,"disabled"):
            disabled.execute(InferenceJob(self.shop,self.job,"image_edit",(self.source,)))
        self.assertEqual(self.storage.methods,[])
        self.assertEqual(self.service.calls,[])

    def test_expired_claim_blocks_private_stage_before_network(self):
        self.service.claim(self.job,str(uuid4()))
        self.service.lease_active=False
        metadata=self.metadata()
        with self.assertRaises(ProviderBlocked):
            self.runtime.registrar(self.shop,self.job,self.png,metadata)
        self.assertNotIn("commit",self.service.calls)
        self.assertEqual(self.storage.methods,[])

    def test_foreign_reservation_denied_before_storage(self):
        self.service.claim(self.job,str(uuid4()))
        self.service.foreign_receipt=True
        with self.assertRaises(ProviderBlocked):
            self.runtime.registrar(self.shop,self.job,self.png,self.metadata())
        self.assertEqual(self.storage.methods,[])
        self.assertNotIn("commit",self.service.calls)

    def test_private_readback_corrupt_blocks_database_registration(self):
        self.service.claim(self.job,str(uuid4()))
        self.storage.corrupt=True
        with self.assertRaises(ProviderBlocked):
            self.runtime.registrar(self.shop,self.job,self.png,self.metadata())
        self.assertEqual(self.storage.methods,["POST","GET"])
        self.assertNotIn("commit",self.service.calls)

    def test_revocation_after_upload_quarantines_before_sql_cas(self):
        self.service.claim(self.job,str(uuid4()))
        # claim-validator rights=1, pre-stage rights=2,
        # post-stage rights=3 => revoked and quarantine only pre-CAS.
        self.revoke_after=3
        with self.assertRaises(ProviderBlocked):
            self.runtime.registrar(self.shop,self.job,self.png,self.metadata())
        self.assertIn("DELETE",self.storage.methods)
        self.assertEqual(self.storage.bytes,{})
        self.assertNotIn("commit",self.service.calls)

    def test_unknown_sql_commit_does_not_remove_immutable_staged_bytes(self):
        self.service.claim(self.job,str(uuid4()))
        self.service.unknown_commit=True
        with self.assertRaisesRegex(TimeoutError,"may have committed"):
            self.runtime.registrar(self.shop,self.job,self.png,self.metadata())
        self.assertEqual(self.service.calls.count("commit"),1)
        self.assertEqual(self.storage.methods,["POST","GET"])
        self.assertEqual(len(self.storage.bytes),1)
        # Not a safe candidate for cleanup or automatic replay.

    def test_noninteger_prepaid_lease_attempt_denied_before_storage_stage(self):
        for invalid in (True, 1.0, "1", False, None, 2):
            with self.subTest(lease_attempt=repr(invalid)):
                self.setUp()
                self.service.claim(self.job,str(uuid4()))
                self.service.reservation_attempt=invalid
                with self.assertRaises(ProviderBlocked):
                    self.runtime.registrar(self.shop,self.job,self.png,self.metadata())
                self.assertEqual(self.storage.methods,[])
                self.assertEqual(self.service.calls.count("commit"),0)
        self.setUp()
        self.service.claim(self.job,str(uuid4()))
        self.assertIsNotNone(self.runtime.registrar(
            self.shop,self.job,self.png,self.metadata())["media_asset_id"])

    def test_late_lease_malformed_or_unfunded_snapshot_never_stages_bytes(self):
        # The initial pre-inference reserve is not enough: current SQL can
        # return malformed/revoked funds before the output Storage POST.
        for invalid in ("0", 0, -0.01, "0.051", "NaN", "Infinity",
                        None, True, "not-money"):
            with self.subTest(late_reserved_usd=repr(invalid)):
                self.setUp()
                self.service.claim(self.job,str(uuid4()))
                self.service.reserved_usd=invalid
                with self.assertRaises(ProviderBlocked):
                    self.runtime.registrar(
                        self.shop,self.job,self.png,self.metadata())
                self.assertEqual(self.storage.methods,[])
                self.assertEqual(self.service.calls.count("commit"),0)
        for invalid_id in ("not-a-uuid", str(uuid4()).upper(), None, True):
            with self.subTest(late_reservation_id=repr(invalid_id)):
                self.setUp()
                self.service.claim(self.job,str(uuid4()))
                self.service.reservation_id_override=invalid_id
                with self.assertRaises(ProviderBlocked):
                    self.runtime.registrar(
                        self.shop,self.job,self.png,self.metadata())
                self.assertEqual(self.storage.methods,[])
                self.assertEqual(self.service.calls.count("commit"),0)

    def test_noninteger_postcommit_sql_receipt_denied_without_delete_or_retry(self):
        for invalid in (True, 1.0, "1", False, None, 2):
            with self.subTest(commit_attempt=repr(invalid)):
                self.setUp()
                self.service.claim(self.job,str(uuid4()))
                self.service.commit_attempt=invalid
                with self.assertRaisesRegex(ProviderBlocked,"SQL CAS unconfirmed"):
                    self.runtime.registrar(self.shop,self.job,self.png,self.metadata())
                self.assertEqual(self.service.calls.count("commit"),1)
                self.assertEqual(self.storage.methods,["POST","GET"])
                self.assertEqual(len(self.storage.bytes),1)
                self.assertNotIn("DELETE",self.storage.methods)
                self.assertFalse(any(isinstance(v,tuple) and v[0]=="finish"
                                     for v in self.service.calls))

    def test_bad_service_or_user_secret_rejected_before_any_io(self):
        with self.assertRaises(ProviderBlocked):
            Feature3PrivateGPUWorker(
                provider=self.provider,service=object(),
                supabase_origin="https://fixture.supabase.co",
                backend_secret="sb_secret_"+"z"*36,
                current_rights=self.rights,
                resolve_private_inputs=lambda *_:{},
                trusted_meter_usd=lambda *_:0)
        with self.assertRaises(ValueError):
            Feature3PrivateGPUWorker(
                provider=self.provider,service=self.service,
                supabase_origin="https://fixture.supabase.co",
                backend_secret="sb_publishable_untrusted",
                current_rights=self.rights,
                resolve_private_inputs=lambda *_:{},
                trusted_meter_usd=lambda *_:0)
        self.assertEqual(self.storage.methods,[])
        self.assertEqual(self.service.calls,[])

    def metadata(self):
        return {"provider":"local-test","provider_version":"unit",
                "weights_license":"Apache-2.0","synthetic":True,
                "attempt":1,"claim_token":self.service.token,
                "source_asset_ids":[self.source],
                "image_sha256":sha256(self.png).hexdigest(),
                "quoted_cost_usd":0.01,"inference_wall_seconds":0.01,
                "requires_human_review":True,
                "garment_fidelity_not_guaranteed":True}


if __name__=="__main__":
    unittest.main()
