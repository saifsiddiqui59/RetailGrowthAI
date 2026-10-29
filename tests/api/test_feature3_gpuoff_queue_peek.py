"""Actual SDK-shaped peek_messages contract; no Azure network, queue mutations."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions"/"campaign-api"))
from feature3_gpu_envelope import encode_dispatch_envelope
from feature3_gpuoff_queue_intake import Feature3GPUOffQueueIntake
from feature3_gpuoff_queue_peek import Feature3GPUOffAzureQueuePeek,Feature3QueuePeekDenied


class Plan:
    def __init__(self,shop,job,source):
        self.shop,self.job,self.source=shop,job,source
        self.calls=[]
        self.revoked=False
    def check(self,shop,job):
        self.calls.append((shop,job))
        if self.revoked or (shop,job)!=(self.shop,self.job):
            raise PermissionError("foreign source denied")
        return {"shop_id":shop,"job_id":job,"source_asset_ids":(self.source,),
                "source_sha256s":("a"*64,),"rights_revisions":(2,),
                "preflight_verified":True,"provider_call_permitted":False,
                "gpu_started":False,"claim_performed":False,
                "paid_retry_authorized":False}


class SafeQueuePeekTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.job,self.source=[str(uuid4()) for _ in range(3)]
        self.plan=Plan(self.shop,self.job,self.source)
        self.queue=Mock()
        self.queue.peek_messages.return_value=[
            SimpleNamespace(content=encode_dispatch_envelope(self.shop,self.job))]
        self.enabled=False
        self.intake=Feature3GPUOffQueueIntake(
            plan_reader=self.plan,
            provider_status=lambda:{"enabled":self.enabled})
        self.inspect=Feature3GPUOffAzureQueuePeek(
            queue_client=self.queue,gpu_off_intake=self.intake)

    def assert_no_mutation(self):
        self.queue.peek_messages.assert_called_once_with(
            max_messages=5,timeout=5)
        for forbidden in ("receive_message","receive_messages","delete_message",
                          "update_message","send_message","clear_messages",
                          "delete_queue"):
            getattr(self.queue,forbidden).assert_not_called()

    def test_true_azure_peek_is_read_only_and_bounded(self):
        result=self.inspect.inspect_visible()
        self.assertEqual(result["checked_visible_messages"],1)
        self.assertEqual(result["inspected"],[{
            "shop_id":self.shop,"job_id":self.job,"source_count":1,
            "gpu_started":False,
            "queue_delivery_acknowledged":False,"delete_permitted":False,
            "paid_retry_authorized":False,
        }])
        for field in ("queue_message_deleted","queue_message_received",
                      "gpu_enabled","paid_retry_authorized"):
            self.assertIs(result[field],False)
        self.assertNotIn(self.source,str(result))
        self.assertEqual(self.plan.calls,[(self.shop,self.job)])
        self.assert_no_mutation()

    def test_empty_queue_is_safe_but_never_treated_as_claimed(self):
        self.queue.peek_messages.return_value=[]
        result=self.inspect.inspect_visible()
        self.assertEqual(result["inspected"],[])
        self.assertEqual(result["checked_visible_messages"],0)
        self.assertEqual(self.plan.calls,[])
        self.assert_no_mutation()

    def test_wrong_uuid_corrupt_message_or_foreign_shop_fail_closed(self):
        cases=(SimpleNamespace(content="not-json"),
               SimpleNamespace(content="{}"),
               SimpleNamespace(content=encode_dispatch_envelope(str(uuid4()),self.job)),
               SimpleNamespace(content=encode_dispatch_envelope(self.shop,str(uuid4()))),
               SimpleNamespace(content={"gpu":"on"}),
               SimpleNamespace(content=None))
        for item in cases:
            self.setUp()
            self.queue.peek_messages.return_value=[item]
            with self.subTest(item=str(item)[:60]),self.assertRaises(
                    Feature3QueuePeekDenied):
                self.inspect.inspect_visible()
            self.assert_no_mutation()

    def test_paid_mode_or_revoked_rights_never_acks_queue(self):
        for revoke,enable in ((False,True),(True,False)):
            self.setUp()
            self.plan.revoked=revoke
            self.enabled=enable
            with self.assertRaises(Feature3QueuePeekDenied):
                self.inspect.inspect_visible()
            self.assert_no_mutation()

    def test_unknown_read_error_oversized_or_duplicate_batch_denied(self):
        first=SimpleNamespace(content=encode_dispatch_envelope(self.shop,self.job))
        for response in ([first,first],list(range(6)),None,
                         "not-a-list"):
            self.setUp()
            self.queue.peek_messages.return_value=response
            with self.subTest(case=str(response)[:40]),self.assertRaises(
                Feature3QueuePeekDenied):
                self.inspect.inspect_visible()
            self.assert_no_mutation()

    def test_transport_timeout_denies_instead_of_reporting_empty(self):
        self.queue.peek_messages.side_effect=TimeoutError("network unknown")
        with self.assertRaises(Feature3QueuePeekDenied):
            self.inspect.inspect_visible()
        self.assert_no_mutation()

    def test_empty_queue_does_not_claim_gpu_off_when_provider_enabled_or_unknown(self):
        self.queue.peek_messages.return_value=[]
        self.enabled=True
        with self.assertRaises(Feature3QueuePeekDenied):
            self.inspect.inspect_visible()
        self.queue.peek_messages.assert_not_called()
        self.enabled=False
        self.intake._status=lambda: (_ for _ in ()).throw(TimeoutError("status"))
        with self.assertRaises(Feature3QueuePeekDenied):
            self.inspect.inspect_visible()
        self.queue.peek_messages.assert_not_called()
        for forbidden in ("receive_message","delete_message","send_message"):
            getattr(self.queue,forbidden).assert_not_called()

    def test_gpu_enabling_during_empty_peek_fails_closed(self):
        def flip_provider(**kwargs):
            self.enabled=True
            return []
        self.queue.peek_messages.side_effect=flip_provider
        with self.assertRaises(Feature3QueuePeekDenied):
            self.inspect.inspect_visible()
        self.assert_no_mutation()
        self.assertEqual(self.plan.calls,[])

    def test_gpu_turning_on_after_valid_job_peek_fails_closed(self):
        original=self.queue.peek_messages.return_value
        def flip_provider(**kwargs):
            self.enabled=True
            return original
        self.queue.peek_messages.side_effect=flip_provider
        with self.assertRaises(Feature3QueuePeekDenied):
            self.inspect.inspect_visible()
        self.assert_no_mutation()

    def test_limit_cannot_be_decorative_or_unbounded(self):
        for limit in (0,-1,6,20,None,True,"5"):
            with self.subTest(limit=limit),self.assertRaises(Feature3QueuePeekDenied):
                self.inspect.inspect_visible(limit=limit)
        self.queue.peek_messages.assert_not_called()


if __name__=="__main__":
    unittest.main()
