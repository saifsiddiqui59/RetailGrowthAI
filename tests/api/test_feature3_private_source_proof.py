"""Actual image bytes plus independently injected rights authority, GPU off."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest
from uuid import uuid4

from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
                       "azure-functions"/"campaign-api"))
from feature3_private_source_proof import (
    Feature3PrivateSourceProof,Feature3SourceProofDenied,
)


class FakeResponse:
    def __init__(self,url,data,*,status=200,redirect=False,mime="image/png",
                 length=None,on_read=None):
        self.url=url+"/redirect" if redirect else url
        self.code=status
        self.data=data
        self.headers={"Content-Type":mime,
                      "Content-Length":str(len(data)) if length is None else length}
        self.on_read=on_read
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def geturl(self): return self.url
    def getcode(self): return self.code
    def read(self,limit):
        if self.on_read:self.on_read()
        return self.data[:limit]


class ProofTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.asset,self.model=(str(uuid4()) for _ in range(3))
        buffer=BytesIO()
        Image.new("RGB",(320,400),"#894315").save(buffer,"PNG")
        self.png=buffer.getvalue()
        self.digest=sha256(self.png).hexdigest()
        self.key=f"{self.shop}/model-library/{self.model}/{self.digest}.png"
        self.media={"id":self.asset,"shop_id":self.shop,
                    "storage_bucket":"retailgrowth-media",
                    "object_path":self.key,"mime_type":"image/png",
                    "source":"UPLOAD"}
        self.review={"shop_id":self.shop,"asset_id":self.asset,
                     "image_sha256":self.digest,"rights_revision":2,
                     "license_review_status":"APPROVED",
                     "customer_approved":True,
                     "commercial_use_approved":True,
                     "provenance_verified":True,
                     "rights_revoked":False}
        self.calls=[]
        self.http=[]
        self.response_bytes=self.png
        self.redirect=False
        self.status=200
        self.mime="image/png"
        self.length=None
        self.on_read=None
        self.proof=Feature3PrivateSourceProof(
            "https://tenantfixture.supabase.co",
            "sb_secret_DO_NOT_USE_OUTSIDE_TEST",
            current_rights=self.current_rights,transport=self.transport)

    def current_rights(self,shop,asset):
        self.calls.append((shop,asset))
        if shop!=self.shop or asset!=self.asset:
            raise AssertionError("Authoritative source identity mismatch")
        return dict(self.review)

    def transport(self,req,timeout):
        self.assertEqual(timeout,15)
        self.assertEqual(req.get_method(),"GET")
        self.assertEqual(req.get_header("Apikey"),
                         "sb_secret_DO_NOT_USE_OUTSIDE_TEST")
        self.assertEqual(req.get_header("Cache-control"),"no-store")
        self.assertFalse(req.get_header("Authorization"))
        self.assertIn("/storage/v1/object/retailgrowth-media/",req.full_url)
        self.assertTrue(req.full_url.endswith(self.key))
        self.assertNotIn("sign",req.full_url)
        self.http.append(req)
        return FakeResponse(req.full_url,self.response_bytes,
                            status=self.status,redirect=self.redirect,
                            mime=self.mime,length=self.length,
                            on_read=self.on_read)

    def inspect(self):
        return self.proof(self.shop,self.media)

    def test_private_actual_png_bytes_and_legal_current_rights_twice(self):
        result=self.inspect()
        self.assertEqual(result,{
            "shop_id":self.shop,"asset_id":self.asset,
            "image_sha256":self.digest,"rights_revision":2,
            "private_bytes_verified":True,
            "independent_license_verified":True,
            "current_customer_approval":True,"rights_revoked":False})
        self.assertEqual(self.calls,[(self.shop,self.asset)]*2)
        self.assertEqual(len(self.http),1)
        self.assertNotIn("object_path",result)
        self.assertNotIn("image_bytes",result)
        self.assertNotIn("publish_approved",result)
        self.assertNotIn("provider_call_permitted",result)

    def test_rights_revoked_during_storage_get_denies_data(self):
        self.on_read=lambda:self.review.update({
            "rights_revoked":True,"rights_revision":3})
        with self.assertRaises(Feature3SourceProofDenied):
            self.inspect()
        self.assertEqual(len(self.calls),2)

    def test_rights_revoked_before_storage_get_does_not_fetch(self):
        for field,value in (("license_review_status","PENDING"),
                            ("customer_approved",False),
                            ("commercial_use_approved",False),
                            ("provenance_verified",False),
                            ("rights_revoked",True),
                            ("rights_revision",0),
                            ("image_sha256","not-sha")):
            self.setUp()
            self.review[field]=value
            with self.subTest(field=field),self.assertRaises(Feature3SourceProofDenied):
                self.inspect()
            self.assertEqual(self.http,[])

    def test_invalid_private_registered_media_denies_before_rights_or_http(self):
        for field,value in (("shop_id",str(uuid4())),
                            ("storage_bucket","public"),
                            ("object_path","https://evil.invalid/file.png"),
                            ("object_path",f"{self.shop}/../bad.png"),
                            ("object_path",f"{self.shop}/%2fprivate.png"),
                            ("mime_type","text/html"),
                            ("source","STOCK")):
            self.setUp()
            self.media[field]=value
            with self.subTest(field=field),self.assertRaises(Feature3SourceProofDenied):
                self.inspect()
            self.assertEqual(self.http,[])
            self.assertEqual(self.calls,[])

    def test_tampered_png_real_byte_sha_denied(self):
        buf=BytesIO()
        Image.new("RGB",(320,400),"#123456").save(buf,"PNG")
        self.response_bytes=buf.getvalue()
        with self.assertRaises(Feature3SourceProofDenied):
            self.inspect()
        self.assertEqual(len(self.calls),1)

    def test_corrupt_mime_redirect_wrong_http_content_size_denied(self):
        for field,value in (("response_bytes",b"x"*500),
                            ("redirect",True),
                            ("status",302),
                            ("mime","image/jpeg"),
                            ("length","314159265"),
                            ("length","unknown")):
            self.setUp()
            setattr(self,field,value)
            with self.subTest(field=field),self.assertRaises(Feature3SourceProofDenied):
                self.inspect()
            self.assertEqual(len(self.http),1)
            self.assertEqual(len(self.calls),1)

    def test_strict_origin_credentials_and_independent_review_required(self):
        for origin in ("http://tenantfixture.supabase.co",
                       "https://tenantfixture.supabase.co.evil.invalid",
                       "https://user:pass@tenantfixture.supabase.co",
                       "https://tenantfixture.supabase.co/private"):
            with self.subTest(origin=origin),self.assertRaises(ValueError):
                Feature3PrivateSourceProof(
                    origin,"sb_secret_DO_NOT_USE_OUTSIDE_TEST",
                    current_rights=self.current_rights,transport=self.transport)
        with self.assertRaises(ValueError):
            Feature3PrivateSourceProof(
                "https://tenantfixture.supabase.co","sb_secret_DO_NOT_USE_OUTSIDE_TEST",
                current_rights=None,transport=self.transport)


if __name__=="__main__":
    unittest.main()
