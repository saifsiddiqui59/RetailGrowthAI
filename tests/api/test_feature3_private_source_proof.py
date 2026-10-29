"""Feature3 real-private-pixel GPU OFF proof tests (all network mocked).

Pillow creates genuine image bytes. Trust authority is an explicitly separate
service-only TEST DOUBLE, never a browser approval. No cloud, claim or billing.
"""
import copy
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError
from uuid import uuid4

from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from feature3_private_source_proof import (
    Feature3TrustedPrivateSourceProof,SourceProofDenied,
)


def image_bytes(kind="PNG"):
    out=BytesIO()
    Image.new("RGB",(320,400),"#e08943").save(out,format=kind)
    return out.getvalue()


class FakeResponse:
    def __init__(self,url,payload,*,mime,status,redirect=False,read_hook=None,content_length=None):
        self.url=url+("/evil" if redirect else "")
        self.payload=payload
        self.status=status
        self.read_hook=read_hook
        self.headers={"Content-Type":mime,
                      "Content-Length":str(len(payload)) if content_length is None else content_length}
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def geturl(self):return self.url
    def getcode(self):return self.status
    def read(self,limit):
        if self.read_hook:self.read_hook()
        return self.payload[:limit]


class PrivateSourceProofTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.asset,self.model=(str(uuid4()) for _ in range(3))
        self.png=image_bytes()
        self.sha=sha256(self.png).hexdigest()
        self.row={
            "id":self.asset,"shop_id":self.shop,
            "storage_bucket":"retailgrowth-media",
            "object_path":f"{self.shop}/model-library/{self.model}/{self.sha}.png",
            "mime_type":"image/png","source":"UPLOAD",
            "license_name":"owned","license_url":None,
            "attribution":"Independently licensed synthetic adult source.",
        }
        self.calls=[]
        self.authorized=True
        self.revoke_second=False
        self.review_revision=3
        self.change_revision_second=False
        self.http_payload=self.png
        self.http_mime="image/png"
        self.http_status=200
        self.redirect=False
        self.length=None
        self.read_hook=None
        self.proof=self.build()

    def review(self,shop,asset,digest,row):
        self.calls.append(("review",digest))
        self.assertEqual((shop,asset),(self.shop,self.asset))
        self.assertEqual(row,self.row)
        count=len([x for x in self.calls if x[0]=="review"])
        valid=self.authorized and not (self.revoke_second and count>=2)
        return {
            "shop_id":shop,"asset_id":asset,
            "image_sha256":digest if valid else self.sha,
            "rights_revision":self.review_revision+(1 if count>=2 and
                              self.change_revision_second else 0),
            "independent_license_verified":valid,
            "current_customer_approval":valid,
            "rights_revoked":not valid,
        }

    def transport(self,req,*,timeout):
        self.calls.append(("get",req.full_url))
        self.assertEqual(timeout,15)
        self.assertEqual(req.get_method(),"GET")
        self.assertEqual(req.get_header("Apikey"),
                         "sb_secret_"+"z"*36)
        self.assertEqual(req.get_header("Cache-control"),"no-store")
        self.assertIn("/storage/v1/object/retailgrowth-media/",req.full_url)
        self.assertIn(self.row["object_path"],req.full_url)
        self.assertNotIn("object/sign/",req.full_url)
        self.assertNotIn("object/public/",req.full_url)
        self.assertNotIn("http://",req.full_url)
        return FakeResponse(
            req.full_url,self.http_payload,mime=self.http_mime,
            status=self.http_status,redirect=self.redirect,
            read_hook=self.read_hook,content_length=self.length)

    def build(self):
        return Feature3TrustedPrivateSourceProof(
            origin="https://fictional.supabase.co",
            backend_secret="sb_secret_"+"z"*36,
            review_authority=self.review,transport=self.transport)

    def test_real_png_bytes_recheck_current_rights_and_no_secrets(self):
        receipt=self.proof(self.shop,self.row)
        self.assertEqual(receipt,{
            "shop_id":self.shop,"asset_id":self.asset,"image_sha256":self.sha,
            "rights_revision":3,"private_bytes_verified":True,
            "independent_license_verified":True,
            "current_customer_approval":True,"rights_revoked":False})
        self.assertEqual([x[0] for x in self.calls],["get","review","review"])
        self.assertNotIn("object_path",receipt)
        self.assertNotIn("url",receipt)
        self.assertNotIn("image_bytes",receipt)
        self.assertNotIn("provider_call_permitted",receipt)
        self.assertNotIn("gpu_started",receipt)

    def test_real_jpeg_and_webp_are_allowed_only_with_correct_media(self):
        for kind,mime,ext in (("JPEG","image/jpeg",".jpg"),
                              ("WEBP","image/webp",".webp")):
            self.setUp()
            payload=image_bytes(kind)
            digest=sha256(payload).hexdigest()
            self.http_payload=payload
            self.http_mime=mime
            self.row["mime_type"]=mime
            self.row["object_path"]=(
                f"{self.shop}/model-library/{self.model}/{digest}{ext}")
            self.assertEqual(self.proof(self.shop,self.row)["image_sha256"],digest)

    def test_revoked_rights_after_private_bytes_read_denied(self):
        self.revoke_second=True
        with self.assertRaises(SourceProofDenied):
            self.proof(self.shop,self.row)
        self.assertEqual([x[0] for x in self.calls],["get","review","review"])

    def test_revision_change_after_first_review_denied(self):
        self.change_revision_second=True
        with self.assertRaisesRegex(SourceProofDenied,"changed"):
            self.proof(self.shop,self.row)

    def test_revoked_during_http_get_denied(self):
        self.read_hook=lambda:setattr(self,"authorized",False)
        with self.assertRaises(SourceProofDenied):
            self.proof(self.shop,self.row)
        self.assertEqual([x[0] for x in self.calls],["get","review"])

    def test_missing_authority_refuses_even_real_original_png(self):
        self.authorized=False
        with self.assertRaises(SourceProofDenied):
            self.proof(self.shop,self.row)
        with self.assertRaises(ValueError):
            Feature3TrustedPrivateSourceProof(
                origin="https://fictional.supabase.co",
                backend_secret="sb_secret_"+"z"*36,
                review_authority=None,transport=self.transport)

    def test_foreign_and_unsafe_object_names_denied_before_network(self):
        bad=[
            ("shop_id",str(uuid4())),
            ("id","foreign"),
            ("storage_bucket","public"),
            ("object_path",f"{str(uuid4())}/model-library/{self.model}/{self.sha}.png"),
            ("object_path",f"{self.shop}/../../owned/{self.sha}.png"),
            ("object_path",f"{self.shop}/%2e%2e/{self.sha}.png"),
            ("object_path",f"{self.shop}//{self.sha}.png"),
            ("object_path",f"{self.shop}/model-library/{self.model}/{self.sha}.exe"),
            ("mime_type","text/html"),
            ("license_name","forged_public"),
            ("attribution","bad"),
            ("source","STOCK"),
        ]
        for key,value in bad:
            self.setUp()
            row={**self.row,key:value}
            with self.subTest(key=key,value=str(value)[:22]), self.assertRaises(SourceProofDenied):
                self.proof(self.shop,row)
            self.assertEqual(self.calls,[])

    def test_duplicate_approval_extra_fields_or_untrusted_source_row_denied(self):
        self.row["browser_verified"]=True
        with self.assertRaises(SourceProofDenied):
            self.proof(self.shop,self.row)
        self.assertEqual(self.calls,[])

    def test_changed_image_wrong_mime_redirect_status_and_length_denied(self):
        for flag,value in (
            ("http_payload",image_bytes("JPEG")),
            ("http_payload",b"evil"*100),
            ("http_mime","text/html"),
            ("redirect",True),
            ("http_status",302),
            ("length","not-number"),
            ("length",str(26*1024*1024)),
        ):
            self.setUp()
            setattr(self,flag,value)
            with self.subTest(flag=flag),self.assertRaises(SourceProofDenied):
                self.proof(self.shop,self.row)
            self.assertEqual([x[0] for x in self.calls],["get"])

    def test_non_supabase_or_publishable_backend_key_denied(self):
        for origin in ("http://fictional.supabase.co",
                       "https://fictional.supabase.co.evil.org",
                       "https://bob:pass@fictional.supabase.co",
                       "https://fictional.supabase.co/path"):
            with self.subTest(origin=origin),self.assertRaises(ValueError):
                Feature3TrustedPrivateSourceProof(
                    origin=origin,backend_secret="sb_secret_"+"z"*36,
                    review_authority=self.review,transport=self.transport)
        with self.assertRaises(ValueError):
            Feature3TrustedPrivateSourceProof(
                origin="https://fictional.supabase.co",
                backend_secret="sb_publishable_NO",
                review_authority=self.review,transport=self.transport)

if __name__=="__main__":
    unittest.main()
