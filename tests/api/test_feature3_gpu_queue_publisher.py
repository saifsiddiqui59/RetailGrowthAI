"""Offline P1 durable outbox queue handoff; never sends paid inference."""
import json
import sys
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from feature3_gpu_queue_publisher import Feature3GPUOutboxPublisher
from feature3_gpu_envelope import GPUEnvelopeDenied
from tenant_store import StorageUnavailable


class Feature3QueuePublishingTests(unittest.TestCase):
    def setUp(self):
        self.job,self.shop,self.token=(str(uuid4()) for _ in range(3))
        self.record={"job_id":self.job,"shop_id":self.shop,
                     "dispatch_token":self.token,"expires_in_seconds":120,
                     "gpu_started":False}
        self.outbox=Mock()
        self.outbox.claim_dispatch.return_value=[self.record]
        self.outbox.confirm_dispatch.return_value=True
        self.queue=Mock()
        self.queue.send_message.return_value=SimpleNamespace(id=str(uuid4()))
        self.publisher=Feature3GPUOutboxPublisher(self.outbox,self.queue)

    def test_bounded_once_with_no_images_keys_or_gpu(self):
        receipt=self.publisher.dispatch_once(1)
        self.assertEqual(receipt,{"acknowledged":1,"gpu_started":False,
                                  "inference_executed":False,"charged_usd":"0.00"})
        self.outbox.claim_dispatch.assert_called_once_with(1)
        self.queue.send_message.assert_called_once()
        msg=self.queue.send_message.call_args.args[0]
        self.assertEqual(json.loads(msg),{
            "schema":"retailgrowth.feature3.gpu.dispatch.v1",
            "shop_id":self.shop,"job_id":self.job})
        self.assertNotIn(self.token,msg)
        self.assertNotIn("image",msg)
        self.outbox.confirm_dispatch.assert_called_once_with(self.job,self.token,True)

    def test_empty_claim_does_not_send(self):
        self.outbox.claim_dispatch.return_value=[]
        self.assertEqual(self.publisher.dispatch_once()["acknowledged"],0)
        self.queue.send_message.assert_not_called()
        self.outbox.confirm_dispatch.assert_not_called()

    def test_missing_transport_ack_never_confirms_queue_delivery(self):
        for result in (None, False, True, {}, {"message_id":"queue-ack"},
                       {"id":""}, {"id":"not-a-guid"}, SimpleNamespace(id=None),
                       SimpleNamespace(id=object())):
            self.queue.send_message.reset_mock()
            self.outbox.confirm_dispatch.reset_mock()
            self.queue.send_message.return_value=result
            with self.assertRaises(StorageUnavailable):
                self.publisher.dispatch_once()
            self.outbox.confirm_dispatch.assert_not_called()
            self.assertEqual(self.queue.send_message.call_count,1)

    def test_valid_queue_assigned_id_is_necessary_before_database_ack(self):
        self.queue.send_message.return_value={"id":str(uuid4())}
        self.assertEqual(self.publisher.dispatch_once()["acknowledged"],1)
        self.outbox.confirm_dispatch.assert_called_once_with(
            self.job,self.token,True)

    def test_bogus_receipt_never_reaches_second_claimed_job(self):
        row={**self.record,"job_id":str(uuid4()),
             "dispatch_token":str(uuid4())}
        self.outbox.claim_dispatch.return_value=[self.record,row]
        self.queue.send_message.return_value={"message_id":"not-a-server-id"}
        with self.assertRaisesRegex(StorageUnavailable,"uncertain"):
            self.publisher.dispatch_once()
        self.queue.send_message.assert_called_once()
        self.outbox.confirm_dispatch.assert_not_called()

    def test_unknown_send_error_does_not_confirm_or_paid_retry(self):
        self.queue.send_message.side_effect=TimeoutError("ACK lost")
        with self.assertRaisesRegex(StorageUnavailable,"uncertain"):
            self.publisher.dispatch_once()
        self.outbox.confirm_dispatch.assert_not_called()
        self.assertEqual(self.queue.send_message.call_count,1)

    def test_sql_ack_uncertain_stops_batch_after_one_send(self):
        self.outbox.claim_dispatch.return_value=[self.record,{
          **self.record,"job_id":str(uuid4()),"dispatch_token":str(uuid4())}]
        self.outbox.confirm_dispatch.side_effect=StorageUnavailable("unconfirmed")
        with self.assertRaises(StorageUnavailable):
            self.publisher.dispatch_once()
        self.assertEqual(self.queue.send_message.call_count,1)

    def test_false_or_missing_sql_ack_stops_batch_after_first_send(self):
        second={**self.record,"job_id":str(uuid4()),
                "dispatch_token":str(uuid4())}
        for returned in (None,False,0,1,"true",{"sent":True},[]):
            self.setUp()
            self.outbox.claim_dispatch.return_value=[self.record,second]
            self.outbox.confirm_dispatch.return_value=returned
            with self.subTest(ack=str(returned)),self.assertRaisesRegex(
                    StorageUnavailable,"ACK uncertain"):
                self.publisher.dispatch_once(2)
            self.assertEqual(self.queue.send_message.call_count,1)
            self.outbox.confirm_dispatch.assert_called_once_with(
                self.job,self.token,True)

    def test_ack_exception_is_opaque_and_stops_before_second_queue_send(self):
        self.outbox.claim_dispatch.return_value=[
            self.record,{**self.record,"job_id":str(uuid4()),
                         "dispatch_token":str(uuid4())}]
        self.outbox.confirm_dispatch.side_effect=RuntimeError(
            "PRIVATE-SQL-SERVICE-KEY-DIAGNOSTIC")
        with self.assertRaises(StorageUnavailable) as caught:
            self.publisher.dispatch_once(2)
        self.assertIn("ACK uncertain",str(caught.exception))
        self.assertNotIn("PRIVATE-SQL",str(caught.exception))
        self.assertIsNone(caught.exception.__cause__)
        self.queue.send_message.assert_called_once()

    def test_invalid_or_duplicate_sql_claim_batch_never_reaches_queue(self):
        wrong=[
            None, False, {}, (self.record,),
            [dict(self.record, gpu_started=True)],
            [dict(self.record, expires_in_seconds=119)],
            [dict(self.record, expires_in_seconds=True)],
            [dict(self.record, provider_call_permitted=True)],
            [dict(self.record, job_id=str(uuid4()).upper())],
            [dict(self.record, shop_id="../foreign")],
            [dict(self.record, dispatch_token=str(uuid4()).upper())],
            [self.record,self.record],
            [self.record,{**self.record, "job_id":str(uuid4())}],
        ]
        for rows in wrong:
            self.setUp()
            self.outbox.claim_dispatch.return_value=rows
            with self.subTest(rows=str(rows)[:100]),self.assertRaises((StorageUnavailable,GPUEnvelopeDenied)):
                self.publisher.dispatch_once()
            self.queue.send_message.assert_not_called()
            self.outbox.confirm_dispatch.assert_not_called()

    def test_batch_limit_and_multiple_unique_jobs_validate_before_first_send(self):
        for limit in (0,11,None,True,False,"5",-1):
            self.setUp()
            with self.subTest(limit=limit),self.assertRaises(ValueError):
                self.publisher.dispatch_once(limit)
            self.outbox.claim_dispatch.assert_not_called()
            self.queue.send_message.assert_not_called()
        self.setUp()
        self.outbox.claim_dispatch.return_value=[
            self.record,{**self.record,"job_id":str(uuid4()),
                          "dispatch_token":str(uuid4())}]
        result=self.publisher.dispatch_once(2)
        self.assertEqual(result["acknowledged"],2)
        self.assertEqual(self.queue.send_message.call_count,2)
        self.assertEqual(self.outbox.confirm_dispatch.call_count,2)
        self.assertEqual(result["charged_usd"],"0.00")

    def test_no_default_paid_queue_or_resource_provisioning(self):
        with self.assertRaises(ValueError):
            Feature3GPUOutboxPublisher(self.outbox,None)
        with self.assertRaises(ValueError):
            Feature3GPUOutboxPublisher(None,self.queue)


if __name__=="__main__":
    unittest.main()
