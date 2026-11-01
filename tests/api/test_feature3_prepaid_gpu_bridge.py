"""No cloud/GPU: adapter for an already-reserved fenced SQL job."""
import sys
from io import BytesIO
from pathlib import Path
from uuid import uuid4
import unittest
from hashlib import sha256

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
from ai_providers_v2 import InferenceJob, OptionalGPUProvider, ProviderConfig, ProviderBlocked
from feature3_gpu_prepaid_bridge import PrepaidGPUJobCallbacks

def fixture_png():
    output=BytesIO()
    Image.new("RGB",(80,80),"#d8ad7f").save(output,"PNG")
    return output.getvalue()

class PrepaidBridgeTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.job_id,self.asset,self.reservation=[
            str(uuid4()) for _ in range(4)]
        self.job=InferenceJob(self.shop,self.job_id,"image_edit",(self.asset,))
        cfg=ProviderConfig("unit-fixture","1",frozenset({"image_edit"}),
            "Apache-2.0","Apache-2.0",
            dependency_licenses_approved=True,cost_approved=True,
            gpu_deployed=True,gpu_rate_usd_per_hour=1,
            estimated_gpu_seconds=60,max_cost_usd_per_job=0.05)
        self.png=fixture_png()
        self.provider=OptionalGPUProvider(cfg,runner=lambda *_:self.png)
        self.events=[]
        self.foreign=False
        self.enabled=True
        self.bill="0.011500"
        self.expected_claim_token=None
        self.output_id=str(uuid4())
        self.denied_reservation=False
        self.claim_attempt=1
        self.reservation_attempt=1
        self.output_mode="ok"
        self.revoke_after_inference=False
    def _callbacks(self):
        def claim(job_id,claim_token):
            self.expected_claim_token=claim_token
            self.events.append("claim")
            return {"shop_id":self.shop if not self.foreign else str(uuid4()),
                "job_id":job_id,"attempt":self.claim_attempt,"claim_token":claim_token}
        def authorize(shop,job_id,claim_token,ids):
            self.events.append("authorize")
            return (self.enabled and shop==self.shop and ids==(self.asset,)
                    and not (self.revoke_after_inference and self.events.count("authorize")>=2))
        def reserve(shop,job_id,attempt,token):
            self.events.append("read reservation")
            if self.denied_reservation: return None
            return {"shop_id":shop,"job_id":job_id,"attempt":self.reservation_attempt,
                "claim_token":token,"reservation_id":self.reservation,
                "reserved_usd":0.05}
        def write(shop,job_id,image,metadata):
            self.events.append("private write")
            if self.output_mode=="timeout":
                raise TimeoutError("output Storage or DB ACK unknown")
            return {"shop_id":shop if self.output_mode!="wrong_tenant" else str(uuid4()),
                    "job_id":job_id,"attempt":1,
                "claim_token":metadata["claim_token"],
                "media_asset_id":self.output_id,
                "image_sha256":sha256(image).hexdigest(),"private":True,
                "review_status":"UNREVIEWED"}
        def meter(job_id,token,seconds,successful):
            self.events.append("trusted cost")
            return self.bill
        def finish(job_id,token,actual,asset):
            self.events.append(("settled",actual,asset))
            return True
        return PrepaidGPUJobCallbacks(
            provider=self.provider,claim_rpc=claim,
            read_authorization=authorize,
            resolve_private_inputs=lambda shop, ids:{self.asset:b"PRIVATE_SOURCE"},
            read_prepaid_reservation=reserve,register_private_output=write,
            trusted_meter_usd=meter,finish_rpc=finish,
        )
    def test_reuses_reservation_does_not_reserve_twice(self):
        receipt=self._callbacks().execute(self.job)
        self.assertEqual(receipt["media_asset_id"],self.output_id)
        self.assertEqual([x for x in self.events if x=="read reservation"],
                         ["read reservation"])
        self.assertEqual([x for x in self.events if x=="private write"],
                         ["private write"])
        self.assertEqual(self.events[-1],("settled","0.011500",self.output_id))
        self.assertEqual(self.events.count("authorize"),2)
    def test_claim_foreign_and_denied_rights_stop_before_charge(self):
        self.foreign=True
        with self.assertRaises(ProviderBlocked):
            self._callbacks().execute(self.job)
        self.assertNotIn("private write",self.events)
        self.assertNotIn("trusted cost",self.events)
        self.events=[]
        self.foreign=False
        self.enabled=False
        with self.assertRaises(ProviderBlocked):
            self._callbacks().execute(self.job)
        self.assertNotIn("private write",self.events)
        self.assertNotIn("trusted cost",self.events)
    def test_nonexistent_reserved_receipt_denies_gpu(self):
        self.denied_reservation=True
        with self.assertRaises(ProviderBlocked):
            self._callbacks().execute(self.job)
        self.assertNotIn("private write",self.events)
    def test_meter_exceeds_amount_refuses_settlement_not_silent_charge(self):
        self.bill="0.050001"
        with self.assertRaisesRegex(ProviderBlocked,"exceeds reserved"):
            self._callbacks().execute(self.job)
        self.assertNotIn("settled",str(self.events))
    def test_invalid_meter_refuses_paid_settlement(self):
        for amount in ("NaN","Infinity",None,-1):
            with self.subTest(amount=amount):
                self.bill=amount
                self.events=[]
                with self.assertRaises(ProviderBlocked):
                    self._callbacks().execute(self.job)
                self.assertNotIn("settled",str(self.events))
    def test_lost_private_output_ack_never_settles_or_retries_paid_job(self):
        self.output_mode="timeout"
        with self.assertRaisesRegex(TimeoutError,"unknown"):
            self._callbacks().execute(self.job)
        self.assertEqual(self.events.count("private write"),1)
        self.assertEqual(self.events.count("read reservation"),1)
        self.assertNotIn("trusted cost",self.events)
        self.assertFalse(any(isinstance(x,tuple) and x[0]=="settled" for x in self.events))
        # Caller must hold RUNNING/reservation for independently measured
        # operator reconciliation, not label a possible SQL CAS as FAILED.

    def test_wrong_private_output_receipt_never_settles(self):
        self.output_mode="wrong_tenant"
        with self.assertRaisesRegex(ProviderBlocked,"cross-tenant"):
            self._callbacks().execute(self.job)
        self.assertEqual(self.events.count("private write"),1)
        self.assertNotIn("trusted cost",self.events)
        self.assertFalse(any(isinstance(x,tuple) and x[0]=="settled" for x in self.events))

    def test_revocation_before_output_attempt_still_finalizes_failure(self):
        self.revoke_after_inference=True
        with self.assertRaisesRegex(ProviderBlocked,"revoked"):
            self._callbacks().execute(self.job)
        self.assertNotIn("private write",self.events)
        self.assertIn("trusted cost",self.events)
        self.assertTrue(any(isinstance(x,tuple) and x[0]=="settled" and x[2] is None
                            for x in self.events))

    def test_forged_one_shot_claim_attempt_denied_before_reservation_or_gpu(self):
        # Python equality would otherwise accept True and 1.0 as 1.
        for bad in (True, 1.0, "1", 0, 2, None, False):
            with self.subTest(claim_attempt=repr(bad)):
                self.setUp()
                self.claim_attempt=bad
                self.provider.runner=lambda *_:self.fail("GPU runner called")
                with self.assertRaisesRegex(ProviderBlocked,"claim token/shop mismatch"):
                    self._callbacks().execute(self.job)
                self.assertEqual(self.events,["claim"])

    def test_forged_prepaid_attempt_denied_before_gpu_or_private_write(self):
        for bad in (True, 1.0, "1", 0, 2, None, False):
            with self.subTest(reservation_attempt=repr(bad)):
                self.setUp()
                self.reservation_attempt=bad
                self.provider.runner=lambda *_:self.fail("GPU runner called")
                with self.assertRaisesRegex(ProviderBlocked,"reservation not authoritative"):
                    self._callbacks().execute(self.job)
                self.assertEqual(self.events,["claim","authorize","read reservation"])

    def test_forged_one_shot_job_attempt_denied_before_provider_or_sql(self):
        # True and 1.0 are equal to 1 but not a signed SQL attempt integer.
        for bad in (True, 1.0, "1", None, False, 0, 2):
            with self.subTest(job_attempt=repr(bad)):
                self.setUp()
                other=InferenceJob(self.shop,self.job_id,"image_edit",
                                   (self.asset,),attempt=bad)
                provider_status_calls=[]
                self.provider.status=lambda: provider_status_calls.append("status")
                with self.assertRaisesRegex(ProviderBlocked,"one GPU attempt"):
                    self._callbacks().execute(other)
                self.assertEqual(provider_status_calls,[])
                self.assertEqual(self.events,[])

    def test_malformed_paid_provider_status_never_claims_or_runs(self):
        # Even an injected adapter's "enabled" field cannot be interpreted
        # using truthiness before the paid SQL claim and model execution.
        for status in (None, [], True, {}, {"enabled":None},
                       {"enabled":1}, {"enabled":"true"},
                       {"enabled":"false"}, {"enabled":False}):
            with self.subTest(status=repr(status)):
                self.setUp()
                self.provider.status=lambda value=status:value
                self.provider.execute=lambda *a,**kw:self.fail(
                    "paid provider execute called on untrusted status")
                with self.assertRaisesRegex(ProviderBlocked,"remains disabled"):
                    self._callbacks().execute(self.job)
                self.assertEqual(self.events,[])

    def test_no_second_attempt_or_disabled_provider(self):
        other=InferenceJob(self.shop,self.job_id,"image_edit",(self.asset,),attempt=2)
        with self.assertRaises(ProviderBlocked):
            self._callbacks().execute(other)
        self.assertEqual(self.events,[])
        self.provider=OptionalGPUProvider(ProviderConfig(
            "fixture","0",frozenset({"image_edit"}),"Apache-2.0","Apache-2.0"),
            runner=lambda *_:self.png)
        with self.assertRaisesRegex(ProviderBlocked,"disabled"):
            self._callbacks().execute(self.job)
        self.assertEqual(self.events,[])

if __name__=="__main__":
    unittest.main()
