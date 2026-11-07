"""GPU OFF: strict Azure Queue envelope contract, no provider/API calls."""
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from feature3_gpu_envelope import (
    GPUEnvelopeDenied, decode_dispatch_envelope, encode_dispatch_envelope,
)
from feature3_gpu_queue_publisher import Feature3GPUOutboxPublisher


class GPUEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.job,self.token=(str(uuid4()) for _ in range(3))
        self.encoded=encode_dispatch_envelope(self.shop,self.job)

    def test_roundtrip_only_job_and_shop_not_auth_or_paid_permission(self):
        self.assertEqual(decode_dispatch_envelope(self.encoded),
                         {"shop_id":self.shop,"job_id":self.job})
        self.assertEqual(decode_dispatch_envelope(self.encoded.encode()),
                         {"shop_id":self.shop,"job_id":self.job})
        self.assertEqual(set(json.loads(self.encoded)),
                         {"schema","shop_id","job_id"})
        self.assertNotIn("claim_token",self.encoded)
        self.assertNotIn("provider",self.encoded)
        self.assertNotIn("model",self.encoded)
        self.assertNotIn("budget",self.encoded)
        self.assertNotIn(self.token,self.encoded)
        self.assertLess(len(self.encoded),512)

    def test_forbidden_extra_bytes_or_instructions_denied(self):
        row=json.loads(self.encoded)
        for key,value in (("token","secret"),("url","https://evil.test/"),
                          ("object_path","/other/shop/file.png"),
                          ("prompt","force GPU inference"),
                          ("source_asset_ids",[str(uuid4())]),
                          ("gpu_authorized",True),
                          ("cost_usd",0),("attempt",1)):
            bad=dict(row,**{key:value})
            with self.subTest(key=key),self.assertRaises(GPUEnvelopeDenied):
                decode_dispatch_envelope(json.dumps(bad))

    def test_no_legacy_or_malformed_ids_accepted(self):
        for value in ("",None,5,{},[],str(uuid4()).upper(),
                      str(uuid4()).replace("-",""),str(uuid4())+"x",
                      "0"*36, str(__import__("uuid").uuid1())):
            with self.subTest(value=value),self.assertRaises(GPUEnvelopeDenied):
                encode_dispatch_envelope(value,self.job)
            malformed=json.dumps({"schema":"retailgrowth.feature3.gpu.dispatch.v1",
                                  "shop_id":value,"job_id":self.job})
            with self.assertRaises(GPUEnvelopeDenied):
                decode_dispatch_envelope(malformed)

    def test_no_duplicate_keys_invalid_encoding_or_oversized_message(self):
        duplicate=self.encoded[:-1]+',"job_id":"'+self.job+'"}'
        for data in (duplicate, "", b"\xff\xfe", "[1,2]",
                     "not JSON", "{}",
                     " " * 513 + self.encoded,
                     self.encoded.replace("dispatch.v1","dispatch.v9"),
                     self.encoded.replace("dispatch.v1","dispatch.v1\\u0000"),
                     self.encoded.replace("dispatch.v1","dispatch.v1\\n"),
                     self.encoded.replace("dispatch.v1","dispatch.v1\\u200b"),
                     self.encoded.replace("dispatch.v1","dispatch.v1") + "null",
                     b'{"job_id":"'+self.job.encode()+b'","shop_id":"'+self.shop.encode()+
                     b'","schema":"retailgrowth.feature3.gpu.dispatch.v1","budget":NaN}',
                     None, True, {"shop_id":self.shop}):
            with self.subTest(data=str(data)[:80]), self.assertRaises(GPUEnvelopeDenied):
                decode_dispatch_envelope(data)

    def test_unpaired_unicode_surrogates_fail_closed_as_poison_envelopes(self):
        # Python can receive malformed in-memory text before the Azure Queue
        # adapter decodes it. A typed denial is required, not an uncaught
        # UnicodeEncodeError that could escape poison-message handling.
        for payload in (self.encoded + chr(0xD800),
                        self.encoded + chr(0xDFFF),
                        self.encoded.replace(self.shop, chr(0xD800) + self.shop[1:]),
                        b"\xed\xa0\x80"):
            with self.subTest(payload_type=type(payload).__name__), self.assertRaises(GPUEnvelopeDenied):
                decode_dispatch_envelope(payload)

    def test_existing_publisher_generates_exact_decoder_compatible_message(self):
        outbox=Mock()
        outbox.claim_dispatch.return_value=[{
            "shop_id":self.shop,"job_id":self.job,
            "dispatch_token":self.token,"expires_in_seconds":120,
            "gpu_started":False,
        }]
        queue=Mock()
        queue.send_message.return_value=SimpleNamespace(id=str(uuid4()))
        # A mocked SQL ACK must explicitly commit, not just return Mock().
        outbox.confirm_dispatch.return_value=True
        publication=Feature3GPUOutboxPublisher(outbox,queue).dispatch_once(1)
        self.assertEqual(publication["gpu_started"],False)
        sent=queue.send_message.call_args.args[0]
        self.assertEqual(sent,self.encoded)
        self.assertEqual(decode_dispatch_envelope(sent),
                         {"shop_id":self.shop,"job_id":self.job})
        self.assertNotIn(self.token,sent)
        outbox.confirm_dispatch.assert_called_once_with(self.job,self.token,True)

    def test_publisher_rejects_untrusted_identifier_before_any_send(self):
        outbox=Mock()
        outbox.claim_dispatch.return_value=[{
            "shop_id":self.shop,"job_id":"not-a-uuid",
            "dispatch_token":self.token,"expires_in_seconds":120,
            "gpu_started":False,
        }]
        queue=Mock()
        with self.assertRaises(GPUEnvelopeDenied):
            Feature3GPUOutboxPublisher(outbox,queue).dispatch_once(1)
        queue.send_message.assert_not_called()
        outbox.confirm_dispatch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
