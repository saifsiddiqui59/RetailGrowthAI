"""Feature3 new revocable private PNG read contract; no hosted I/O or URLs."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest
from uuid import uuid4

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "azure-functions" / "campaign-api"))
from feature3_private_png_reader import (
    Feature3RevocablePNGReader, PrivateGeneratedDownloadDenied,
)


class FakeTenant:
    origin="https://fictional.supabase.co"
    key="sb_publishable_OFFLINE_UNIT_ONLY"
    def __init__(self,shop,job,user,asset,sha):
        self.shop,self.job,self.user,self.asset,self.sha=shop,job,user,asset,sha
        self.path=f"{shop}/feature3/gpu/{job}/{sha}.png"
        self.active=True
        self.status="SUCCEEDED"
        self.foreign=False
        self.calls=[]
    def member(self,token,actor,shop,write=False):
        self.calls.append("member")
        return self.active and token=="fake-signed-retailer-token" and (
            actor,shop)==(self.user,self.shop)
    def feature3_gpu_job(self,token,shop,job):
        self.calls.append("job")
        return {"id":job,"shop_id":shop,"status":self.status,
                "output_asset_id":self.asset}
    def feature3_generated_asset(self,token,shop,job,asset):
        self.calls.append("asset")
        return {"object_path":self.path if not self.foreign else
                f"{str(uuid4())}/feature3/gpu/{job}/{self.sha}.png",
                "mime_type":"image/png"}


class Response:
    def __init__(self,url,data,*,redirect=False,status=200,
                 mime="image/png",content_length=None,on_read=None):
        self.url=url+"/redirected" if redirect else url
        self.data=data
        self.status=status
        self.headers={"Content-Type":mime,
                      "Content-Length":str(len(data)) if content_length is None
                      else content_length}
        self.on_read=on_read
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def geturl(self):return self.url
    def getcode(self):return self.status
    def read(self,limit):
        if self.on_read:self.on_read()
        return self.data[:limit]


def original_png():
    stream=BytesIO()
    Image.new("RGB",(320,400),"#b47a45").save(stream,"PNG")
    return stream.getvalue()


class RevocableReaderTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.job,self.user,self.asset=[str(uuid4()) for _ in range(4)]
        self.png=original_png()
        self.sha=sha256(self.png).hexdigest()
        self.tenant=FakeTenant(self.shop,self.job,self.user,self.asset,self.sha)
        self.calls=[]
        self.license_active=True
        self.revoke_after_first=False
        self.rights_called=0
        self.binary=None
        self.redirect=False
        self.http_status=200
        self.mime="image/png"
        self.content_length=None
        self.on_read=None
        self.reader=self.build()

    def verify(self,token):
        self.calls.append("verify")
        if token!="fake-signed-retailer-token":
            raise ValueError("invalid token in synthetic test")
        return self.user

    def rights(self,shop,job,asset):
        self.rights_called+=1
        return ((shop,job,asset)==(self.shop,self.job,self.asset) and
                self.license_active and
                not (self.revoke_after_first and self.rights_called>=2))

    def transport(self,req,timeout):
        self.calls.append("get")
        self.assertEqual(timeout,10)
        self.assertEqual(req.get_method(),"GET")
        self.assertEqual(req.get_header("Apikey"),self.tenant.key)
        self.assertEqual(req.get_header("Authorization"),
                         "Bearer fake-signed-retailer-token")
        self.assertEqual(req.get_header("Cache-control"),"no-store")
        self.assertIn("/storage/v1/object/authenticated/retailgrowth-media/",
                      req.full_url)
        self.assertIn(self.tenant.path,req.full_url)
        self.assertNotIn("/object/public/",req.full_url)
        self.assertNotIn("/object/sign/",req.full_url)
        return Response(req.full_url,
                        self.png if self.binary is None else self.binary,
                        redirect=self.redirect,status=self.http_status,
                        mime=self.mime,content_length=self.content_length,
                        on_read=self.on_read)

    def build(self):
        return Feature3RevocablePNGReader(
            tenant_store=self.tenant,verify_user_jwt=self.verify,
            current_output_rights=self.rights,transport=self.transport)

    def read(self):
        return self.reader.read(user_token="fake-signed-retailer-token",
                                shop_id=self.shop,job_id=self.job)

    def test_private_bytes_verified_twice_no_signed_link(self):
        result=self.read()
        self.assertEqual(result["image_bytes"],self.png)
        self.assertEqual(result["image_sha256"],self.sha)
        self.assertEqual(result["media_asset_id"],self.asset)
        self.assertTrue(result["private"])
        self.assertFalse(result["signed_url_issued"])
        self.assertFalse(result["approved_model"])
        self.assertFalse(result["publish_approved"])
        self.assertNotIn("url",result)
        self.assertNotIn("object_path",result)
        self.assertEqual(self.calls,["verify","get"])
        self.assertEqual(self.tenant.calls,
                         ["member","job","asset","member","job","asset"])
        self.assertEqual(self.rights_called,2)

    def test_revocation_during_private_read_blocks_returned_png(self):
        self.on_read=lambda:setattr(self.tenant,"active",False)
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            self.read()
        self.assertEqual(self.calls,["verify","get"])
        self.assertEqual(self.tenant.calls.count("member"),2)
        self.assertEqual(self.rights_called,1)

    def test_rights_revocation_after_bytes_blocks_returned_png(self):
        self.revoke_after_first=True
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            self.read()
        self.assertEqual(self.rights_called,2)
        self.assertEqual(self.calls,["verify","get"])

    def test_foreign_media_missing_job_or_denied_current_rights_no_get(self):
        for case in ("foreign","failed","revoked","not_member"):
            self.setUp()
            if case=="foreign":self.tenant.foreign=True
            elif case=="failed":self.tenant.status="FAILED"
            elif case=="revoked":self.license_active=False
            else:self.tenant.active=False
            with self.subTest(case=case),self.assertRaises(
                PrivateGeneratedDownloadDenied):
                self.read()
            self.assertEqual(self.calls,["verify"])

    def test_changed_png_wrong_hash_or_invalid_bytes_deny(self):
        changed=BytesIO()
        Image.new("RGB",(320,400),"#123456").save(changed,"PNG")
        for image in (changed.getvalue(),b"not actually a png"+b"x"*300):
            self.binary=image
            with self.subTest(imglen=len(image)),self.assertRaises(
                PrivateGeneratedDownloadDenied):
                self.read()
            self.assertEqual(self.rights_called%2,1)
            self.calls.clear()
            self.tenant.calls.clear()
            self.rights_called=0

    def test_http_redirect_wrong_status_wrong_mime_and_length_denied(self):
        for flag,value in (("redirect",True),("http_status",302),
                           ("mime","image/jpeg"),
                           ("content_length",str(26*1024*1024)),
                           ("content_length","not-length")):
            self.setUp()
            setattr(self,flag,value)
            with self.subTest(flag=flag),self.assertRaises(
                PrivateGeneratedDownloadDenied):
                self.read()
            self.assertEqual(self.rights_called,1)
            self.assertEqual(self.calls,["verify","get"])

    def test_invalid_jwt_and_origin_and_source_rights_reader_denied(self):
        for token in ("", "sb_secret_forbidden_key",
                      "sb_publishable_forbidden", "fake\rheader",
                      "no-auth"):
            with self.subTest(token=token),self.assertRaises(
                PrivateGeneratedDownloadDenied):
                self.reader.read(user_token=token,
                                 shop_id=self.shop,job_id=self.job)
        self.assertNotIn("get",self.calls)
        original=self.tenant.origin
        for invalid in ("http://not.secure.supabase.co",
                        "https://fictional.supabase.co.evil.invalid",
                        "https://user:pass@fictional.supabase.co",
                        "https://fictional.supabase.co/path"):
            self.tenant.origin=invalid
            with self.subTest(origin=invalid),self.assertRaises(ValueError):
                self.build()
        self.tenant.origin=original
        saved_key=self.tenant.key
        for secret_key in ("sb_secret_BAD_BACKEND_FOR_TEST",
                           "some-arbitrary-key",
                           "eyJ0eXAiOiJKV1QifQ.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.fake"):
            self.tenant.key=secret_key
            with self.subTest(key=secret_key[:12]),self.assertRaises(ValueError):
                self.build()
        self.tenant.key=saved_key
        with self.assertRaises(ValueError):
            Feature3RevocablePNGReader(
                tenant_store=self.tenant,verify_user_jwt=self.verify,
                current_output_rights=None,transport=self.transport)

    def test_does_not_issue_url_or_authorize_publish_or_gpu(self):
        result=self.read()
        forbidden={"url","signed_url","provider_call_permitted",
                   "gpu_authorized","object_path","source_asset_ids","service_key"}
        self.assertFalse(forbidden.intersection(result))
        self.assertFalse(any("sign" in c for c in self.calls))


if __name__=="__main__":
    unittest.main()
