"""Zero-charge Feature3 queue v1 producer/consumer offline integration."""
import copy
import json
from pathlib import Path
import sys
import unittest
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from feature3_gpu_envelope import encode_dispatch_envelope
from feature3_gpu_job_plan import Feature3PlanDenied
from feature3_gpuoff_queue_intake import Feature3GPUOffQueueIntake, Feature3QueueIntakeBlocked


class TestPlan:
    def __init__(self,shop,job,source):
        self.shop,self.job,self.source=shop,job,source
        self.calls=[]
        self.invalid=False
        self.foreign=False
        self.blocked=False
        self.unsafe_flag=None

    def check(self,shop,job):
        self.calls.append((shop,job))
        if self.blocked:
            raise Feature3PlanDenied("source rights revoked")
        packet={"shop_id":self.shop if self.foreign else shop,
                "job_id":job, "source_asset_ids":(self.source,),
                "source_sha256s":("a"*64,),
                "rights_revisions":(2,),
                "preflight_verified":True,
                "provider_call_permitted":False,
                "gpu_started":False,"claim_performed":False,
                "paid_retry_authorized":False}
        if self.unsafe_flag:packet[self.unsafe_flag]=True
        if self.invalid:packet["public_url"]="https://evil.invalid/asset"
        return packet


class Tests(unittest.TestCase):
    def setUp(self):
        self.shop,self.job,self.asset=[str(uuid4()) for _ in range(3)]
        self.plan=TestPlan(self.shop,self.job,self.asset)
        self.enabled=False
        self.queue=Feature3GPUOffQueueIntake(
            plan_reader=self.plan,provider_status=lambda:{"enabled":self.enabled})
        self.msg=encode_dispatch_envelope(self.shop,self.job)

    def test_real_codec_to_plan_with_no_inference_or_ack(self):
        result=self.queue.inspect(self.msg.encode())
        self.assertEqual(self.plan.calls,[(self.shop,self.job)])
        self.assertEqual(result["source_count"],1)
        self.assertTrue(result["preflight_checked"])
        for key in ("provider_call_permitted","gpu_enabled","claim_performed",
                    "queue_message_delete_permitted","queue_delivery_acknowledged",
                    "paid_retry_authorized"):
            self.assertFalse(result[key])
        self.assertEqual(result["charged_usd"],"0.00")
        self.assertNotIn(self.asset,str(result))
        self.assertNotIn("image_bytes",result)

    def test_unknown_or_forbidden_queue_payload_does_not_query_sql(self):
        invalid=(None, "", b"\xff", "{}",
                 json.dumps({**json.loads(self.msg),"source_ids":[self.asset]}),
                 self.msg.replace("dispatch.v1","dispatch.v2"),
                 self.msg.replace(self.job,self.asset),
                 self.msg+"garbage")
        for raw in invalid:
            self.setUp()
            # A *different* valid job UUID is still a legitimate envelope.
            # Its current real shop/job is independently checked by SQL.
            if isinstance(raw,str) and raw==self.msg.replace(self.job,self.asset):
                continue
            with self.subTest(raw=str(raw)[:70]),self.assertRaises(
                Feature3QueueIntakeBlocked):
                self.queue.inspect(raw)
            self.assertEqual(self.plan.calls,[])

    def test_paid_provider_enabled_or_untrusted_status_never_reads(self):
        self.enabled=True
        with self.assertRaises(Feature3QueueIntakeBlocked):
            self.queue.inspect(self.msg)
        self.assertEqual(self.plan.calls,[])
        for status in ({"enabled":1},{"enabled":None},None,{"enabled":True}):
            queue=Feature3GPUOffQueueIntake(
                plan_reader=self.plan,provider_status=lambda val=status:val)
            with self.assertRaises(Feature3QueueIntakeBlocked):
                queue.inspect(self.msg)
        self.assertEqual(self.plan.calls,[])

    def test_foreign_revoke_or_approval_injection_denied(self):
        for attr,value in (("foreign",True),("blocked",True),
                           ("invalid",True),("unsafe_flag","provider_call_permitted"),
                           ("unsafe_flag","claim_performed"),
                           ("unsafe_flag","paid_retry_authorized")):
            self.setUp()
            setattr(self.plan,attr,value)
            with self.subTest(attr=attr),self.assertRaises(Feature3QueueIntakeBlocked):
                self.queue.inspect(self.msg)
            self.assertEqual(len(self.plan.calls),1)

    def test_missing_reader_or_status_denied_before_any_queue(self):
        with self.assertRaises(ValueError):
            Feature3GPUOffQueueIntake(plan_reader=object(),
                                      provider_status=lambda:{"enabled":False})
        with self.assertRaises(ValueError):
            Feature3GPUOffQueueIntake(plan_reader=self.plan,
                                      provider_status=None)
        self.assertEqual(self.plan.calls,[])


if __name__=="__main__":
    unittest.main()
