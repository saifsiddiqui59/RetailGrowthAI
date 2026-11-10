"""Mock-network actual-image tests for Feature3 private Storage stage/readback."""
from hashlib import sha256
from io import BytesIO
import json
import sys
from urllib.error import HTTPError
from pathlib import Path
from uuid import uuid4
from unittest import TestCase, main
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"poster-engine"))
from feature3_private_output_storage import Feature3PrivateOutputStorage, ProviderBlocked
from feature3_private_output_v1 import PrivateOutputRegistrar


def png():
    im=Image.new("RGB",(280,360),"#1c6e83")
    b=BytesIO();im.save(b,"PNG");return b.getvalue()


class Response(BytesIO):
    def __init__(self,raw,url,status=200):
        super().__init__(raw)
        self.url,self.status=url,status
    def geturl(self): return self.url
    def getcode(self): return self.status


class Transport:
    def __init__(self):
        self.objects={}
        self.calls=[]
        self.corrupt_read=False
        self.bad_ack=False
        self.redirect=False
        self.send_error=False
        self.delete_still_present=False
        self.delete_timeout=False
        self.verify_after_delete_timeout=False
        self.deleted_once=False
    def __call__(self,req,timeout):
        assert timeout==30
        url=req.full_url
        self.calls.append((req.get_method(),url,req.headers))
        realurl="https://other.invalid/" if self.redirect else url
        method=req.get_method()
        if method=="POST":
            if self.send_error: raise TimeoutError("uncertain ACK")
            if url in self.objects: raise OSError("immutable path already exists")
            self.objects[url]=req.data
            key=url.split("/storage/v1/object/retailgrowth-media/",1)[1]
            return Response(json.dumps({"Key":"bad" if self.bad_ack else key}).encode(),realurl,201)
        if method=="GET":
            if self.deleted_once and self.verify_after_delete_timeout:
                raise TimeoutError("unknown verification result")
            if url not in self.objects:
                raise HTTPError(url,404,"Not Found",None,None)
            raw=self.objects[url]
            if self.corrupt_read:
                raw=raw[:-1]+bytes([raw[-1]^1])
            return Response(raw,realurl)
        if method=="DELETE":
            self.deleted_once=True
            if not self.delete_still_present:
                self.objects.pop(url,None)
            if self.delete_timeout:
                raise TimeoutError("delete ACK lost")
            return Response(b"{}",realurl)
        raise AssertionError("Unsupported private Storage request")


class PrivateStorageStageTests(TestCase):
    def setUp(self):
        self.transport=Transport()
        self.shop,self.job,self.token=[str(uuid4()) for _ in range(3)]
        self.data=png()
        self.sha=sha256(self.data).hexdigest()
        self.path=f"{self.shop}/feature3/gpu/{self.job}/{self.sha}.png"
        self.stage=Feature3PrivateOutputStorage(
            "https://dev-example.supabase.co","sb_secret_"+("a"*30),
            transport=self.transport)

    def test_stored_png_roundtrip_exact_sha_and_private_immutable_receipt(self):
        receipt=self.stage.stage(self.shop,self.path,self.data,self.token)
        self.assertEqual(receipt,{"object_key":self.path,
            "sha256":self.sha,"bytes":len(self.data),"private":True})
        self.assertEqual([x[0] for x in self.transport.calls],["POST","GET"])
        self.assertEqual(self.transport.calls[0][2]["X-upsert"],"false")
        self.assertNotIn("Authorization",self.transport.calls[0][2])
        self.assertTrue(self.stage.quarantine(self.shop,self.path,self.token))
        self.assertEqual(self.transport.objects,{})
        self.assertFalse(self.stage.quarantine(self.shop,self.path,self.token))
        self.assertEqual([x[0] for x in self.transport.calls],["POST","GET","DELETE","GET"])

    def test_wrong_path_hash_tenant_or_claim_never_writes(self):
        for path in (self.path.replace(self.shop,str(uuid4())),
                     self.path.replace(self.job,str(uuid4())+"/../"),
                     self.path.replace(self.sha,"b"*64),
                     self.path.replace("/feature3/gpu/","/uploads/")):
            with self.assertRaises(ProviderBlocked):
                self.stage.stage(self.shop,path,self.data,self.token)
        with self.assertRaises(ProviderBlocked):
            self.stage.stage(self.shop,self.path,self.data,"missing")
        self.assertEqual(self.transport.calls,[])

    def test_ambiguous_ack_never_returns_stage_or_deletes(self):
        self.transport.bad_ack=True
        with self.assertRaises(ProviderBlocked):
            self.stage.stage(self.shop,self.path,self.data,self.token)
        self.assertEqual([c[0] for c in self.transport.calls],["POST"])
        self.assertFalse(self.stage.quarantine(self.shop,self.path,self.token))
        self.assertEqual(len(self.transport.objects),1)
        # A second call in this same worker must not retry an uncertain POST.
        with self.assertRaisesRegex(ProviderBlocked,"already attempted"):
            self.stage.stage(self.shop,self.path,self.data,self.token)
        self.assertEqual([c[0] for c in self.transport.calls],["POST"])

    def test_readback_difference_blocks_sql_commit_and_quarantine(self):
        self.transport.corrupt_read=True
        with self.assertRaises(ProviderBlocked):
            self.stage.stage(self.shop,self.path,self.data,self.token)
        self.assertEqual([c[0] for c in self.transport.calls],["POST","GET"])
        self.assertFalse(self.stage.quarantine(self.shop,self.path,self.token))
        with self.assertRaisesRegex(ProviderBlocked,"already attempted"):
            self.stage.stage(self.shop,self.path,self.data,self.token)
        self.assertEqual([c[0] for c in self.transport.calls],["POST","GET"])

    def test_timeout_and_redirect_are_unknown_without_replay(self):
        self.transport.send_error=True
        with self.assertRaisesRegex(ProviderBlocked,"unknown"):
            self.stage.stage(self.shop,self.path,self.data,self.token)
        self.assertEqual(len(self.transport.calls),1)
        with self.assertRaisesRegex(ProviderBlocked,"already attempted"):
            self.stage.stage(self.shop,self.path,self.data,self.token)
        self.assertEqual(len(self.transport.calls),1)
        self.transport=Transport()
        self.transport.redirect=True
        other=Feature3PrivateOutputStorage(
            "https://dev-example.supabase.co","sb_secret_"+("a"*30),
            transport=self.transport)
        with self.assertRaises(ProviderBlocked):
            other.stage(self.shop,self.path,self.data,self.token)
        self.assertEqual(len(self.transport.calls),1)

    def test_delete_ack_without_removal_is_not_success(self):
        self.stage.stage(self.shop,self.path,self.data,self.token)
        self.transport.delete_still_present=True
        with self.assertRaises(ProviderBlocked):
            self.stage.quarantine(self.shop,self.path,self.token)
        self.assertFalse(self.stage.quarantine(self.shop,self.path,self.token))
        self.assertEqual([c[0] for c in self.transport.calls],
                         ["POST","GET","DELETE","GET"])
        self.assertEqual(len(self.transport.objects),1)

    def test_delete_timeout_is_unknown_without_retry(self):
        self.stage.stage(self.shop,self.path,self.data,self.token)
        self.transport.delete_timeout=True
        with self.assertRaisesRegex(ProviderBlocked,"unknown"):
            self.stage.quarantine(self.shop,self.path,self.token)
        self.assertFalse(self.stage.quarantine(self.shop,self.path,self.token))
        self.assertEqual([c[0] for c in self.transport.calls],
                         ["POST","GET","DELETE"])

    def test_post_delete_read_timeout_remains_unknown(self):
        self.stage.stage(self.shop,self.path,self.data,self.token)
        self.transport.verify_after_delete_timeout=True
        with self.assertRaisesRegex(ProviderBlocked,"unknown"):
            self.stage.quarantine(self.shop,self.path,self.token)
        self.assertFalse(self.stage.quarantine(self.shop,self.path,self.token))
        self.assertEqual([c[0] for c in self.transport.calls],
                         ["POST","GET","DELETE","GET"])

    def test_integrate_real_registrar_rights_revoke_and_no_commit(self):
        calls=[]
        rights=[True,False]
        from uuid import uuid4
        source=str(uuid4());asset=str(uuid4())
        meta={"provider":"flux2-klein-4b","provider_version":"2026-01",
              "weights_license":"Apache-2.0","synthetic":True,"attempt":1,
              "claim_token":self.token,"source_asset_ids":[source],
              "image_sha256":self.sha,"quoted_cost_usd":0.0,
              "inference_wall_seconds":0.0,
              "requires_human_review":True,"garment_fidelity_not_guaranteed":True}
        def rights_check(*args):
            calls.append("rights");return rights.pop(0)
        def commit(*args):
            calls.append("commit");raise AssertionError("revoked input must not commit")
        registrar=PrivateOutputRegistrar(validate_claim=lambda *args: True,
            reauthorize=rights_check,stage=self.stage.stage,
            commit=commit,quarantine=self.stage.quarantine)
        with self.assertRaises(ProviderBlocked):
            registrar(self.shop,self.job,self.data,meta)
        self.assertEqual(calls,["rights","rights"])
        self.assertEqual(self.transport.objects,{})

    def test_no_service_key_or_non_supabase_origin(self):
        for origin in ("http://localhost","https://example.com",
                       "https://fake.supabase.co.evil.invalid",
                       "https://user:pass@dev.supabase.co",
                       "https://dev.supabase.co/foreign"):
            with self.assertRaises(ValueError):
                Feature3PrivateOutputStorage(origin,"sb_secret_"+("x"*30))
        for secret in ("sb_publishable_demo", "password", ""):
            with self.assertRaises(ValueError):
                Feature3PrivateOutputStorage("https://dev.supabase.co",secret)


if __name__=="__main__":
    main()
