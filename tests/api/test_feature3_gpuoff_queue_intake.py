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


class FakePlan:
    def __init__(self,shop,job,source):
        self.shop,self.job,self.source=shop,job,source
        self.calls=[]
        self.invalid=False
        self.foreign=False
        self.blocked=False
        self.unsafe_flag=None
        self.override=None
        self.raise_backend=False

    def check(self,shop,job):
        self.calls.append((shop,job))
        if (shop,job)!=(self.shop,self.job):
            raise Feature3PlanDenied("foreign queued job absent")
        if self.blocked:
            raise Feature3PlanDenied("source rights revoked")
        if self.raise_backend:
            raise OSError("unavailable private Storage or SQL")
        packet={"shop_id":str(uuid4()) if self.foreign else shop,
                "job_id":job, "source_asset_ids":(self.source,),
                "source_sha256s":("a"*64,),
                "rights_revisions":(2,),
                "preflight_verified":True,
                "provider_call_permitted":False,
                "gpu_started":False,"claim_performed":False,
                "paid_retry_authorized":False}
        if self.unsafe_flag:packet[self.unsafe_flag]=True
        if self.invalid:packet["public_url"]="https://evil.invalid/asset"
        if self.override is not None:packet.update(self.override)
        return packet


class Tests(unittest.TestCase):
    def setUp(self):
        self.shop,self.job,self.asset=[str(uuid4()) for _ in range(3)]
        self.plan=FakePlan(self.shop,self.job,self.asset)
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
                 self.msg+"garbage")
        for raw in invalid:
            self.plan.calls.clear()
            with self.subTest(raw=str(raw)[:70]),self.assertRaises(
                Feature3QueueIntakeBlocked):
                self.queue.inspect(raw)
            self.assertEqual(self.plan.calls,[])
        # Another canonical UUID is valid syntax but NOT authorized SQL job.
        # It must reach the trusted DB resolver and be denied there.
        other_job=str(uuid4())
        with self.assertRaises(Feature3QueueIntakeBlocked):
            self.queue.inspect(encode_dispatch_envelope(self.shop,other_job))
        self.assertEqual(self.plan.calls,[(self.shop,other_job)])

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


    def test_untrusted_plan_receipt_values_never_pass_even_with_off_provider(self):
        invalid=(
            ("source_asset_ids",lambda:("not-a-uuid",)),
            ("source_asset_ids",lambda:(self.asset,self.asset)),
            ("source_sha256s",lambda:None),
            ("source_sha256s",lambda:("Z"*64,)),
            ("source_sha256s",lambda:("a"*64,"b"*64)),
            ("rights_revisions",lambda:None),
            ("rights_revisions",lambda:(True,)),
            ("rights_revisions",lambda:(0,)),
            ("rights_revisions",lambda:(-1,)),
            ("rights_revisions",lambda:(2.5,)),
        )
        for field,generate in invalid:
            self.setUp()
            self.plan.override={field:generate()}
            with self.subTest(field=field,invalid=repr(self.plan.override)),self.assertRaises(
                    Feature3QueueIntakeBlocked):
                self.queue.inspect(self.msg)
            self.assertEqual(self.plan.calls,[(self.shop,self.job)])

    def test_private_rights_outage_and_unavailable_provider_status_fail_closed(self):
        self.plan.raise_backend=True
        with self.assertRaises(Feature3QueueIntakeBlocked):
            self.queue.inspect(self.msg)
        self.assertEqual(self.plan.calls,[(self.shop,self.job)])
        self.plan.calls.clear()
        def unknown_provider_state():
            raise OSError("provider gate unavailable")
        queue=Feature3GPUOffQueueIntake(
            plan_reader=self.plan,provider_status=unknown_provider_state)
        with self.assertRaises(Feature3QueueIntakeBlocked):
            queue.inspect(self.msg)
        self.assertEqual(self.plan.calls,[])

    def test_provider_enabled_during_authoritative_plan_denies_stale_receipt(self):
        original_check = self.plan.check
        states = []
        def provider():
            states.append(self.enabled)
            return {"enabled": self.enabled}
        def enable_during_plan(shop, job):
            result = original_check(shop, job)
            self.enabled = True
            return result
        self.plan.check = enable_during_plan
        queue = Feature3GPUOffQueueIntake(
            plan_reader=self.plan, provider_status=provider)
        with self.assertRaises(Feature3QueueIntakeBlocked):
            queue.inspect(self.msg)
        self.assertEqual(states, [False, True])
        self.assertEqual(self.plan.calls, [(self.shop, self.job)])

    def test_second_provider_snapshot_outage_or_unknown_fails_closed(self):
        for second in (None, {"enabled": True}, OSError("provider status lost")):
            self.setUp()
            calls = []
            def provider():
                calls.append(1)
                if len(calls) == 1:
                    return {"enabled": False}
                if isinstance(second, Exception):
                    raise second
                return second
            queue = Feature3GPUOffQueueIntake(
                plan_reader=self.plan, provider_status=provider)
            with self.subTest(second=repr(second)), self.assertRaises(
                    Feature3QueueIntakeBlocked):
                queue.inspect(self.msg)
            self.assertEqual(len(calls), 2)
            self.assertEqual(self.plan.calls, [(self.shop, self.job)])

    def test_success_requires_two_fresh_gpu_off_snapshots(self):
        calls = []
        def provider():
            calls.append(True)
            return {"enabled": False}
        queue = Feature3GPUOffQueueIntake(
            plan_reader=self.plan, provider_status=provider)
        receipt = queue.inspect(self.msg)
        self.assertEqual(len(calls), 2)
        self.assertIs(receipt["gpu_enabled"], False)
        self.assertIs(receipt["queue_message_delete_permitted"], False)

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
