"""Feature3 no-URL binary HTTP adapter, synthetic PNG and fake signed rights."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest
from uuid import uuid4
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions"/"campaign-api"))
from feature3_private_binary_http import Feature3PrivateBinaryHTTP
from feature3_private_png_reader import PrivateGeneratedDownloadDenied

def sample_png():
    s=BytesIO()
    Image.new("RGB",(320,400),"#7c654d").save(s,format="PNG")
    return s.getvalue()

class AuthorizedReader:
    def __init__(self,shop,job):
        self.shop,self.job=shop,job
        self.media=str(uuid4())
        self.png=sample_png()
        self.calls=[]
        self.fail=None
        self.extra={}
    def read(self,*,user_token,shop_id,job_id):
        self.calls.append((user_token,shop_id,job_id))
        if self.fail is not None:raise self.fail
        return {"shop_id":self.shop,"job_id":self.job,
                "media_asset_id":self.media,"image_sha256":sha256(self.png).hexdigest(),
                "mime_type":"image/png","image_bytes":self.png,
                "private":True,"signed_url_issued":False,
                "approved_model":False,"publish_approved":False,
                **self.extra}

class BinaryHTTPTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.job=str(uuid4()),str(uuid4())
        self.reader=AuthorizedReader(self.shop,self.job)
        self.api=Feature3PrivateBinaryHTTP(reader=self.reader)
    def call(self,method="GET",auth="Bearer signed-retailer-test"):
        return self.api.handle(method=method,authorization=auth,
                               shop_id=self.shop,job_id=self.job)
    def assert_private_headers(self,headers):
        self.assertEqual(headers["Cache-Control"],"no-store, private, max-age=0")
        self.assertEqual(headers["X-Content-Type-Options"],"nosniff")
        self.assertEqual(headers["Vary"],"Authorization")
        self.assertNotIn("Access-Control-Allow-Origin",headers)
        self.assertNotIn("Location",headers)
        self.assertNotIn("X-Storage-Object-Path",headers)
    def test_exact_png_stream_after_trusted_user_jwt_and_rights_read(self):
        status,blob,headers=self.call()
        self.assertEqual(status,200)
        self.assertEqual(blob,self.reader.png)
        self.assertEqual(headers["Content-Type"],"image/png")
        self.assertEqual(headers["Content-Length"],str(len(blob)))
        self.assertEqual(headers["X-Feature3-Shop-Id"],self.shop)
        self.assertEqual(headers["X-Feature3-Job-Id"],self.job)
        self.assertEqual(headers["X-Feature3-Media-Asset-Id"],self.reader.media)
        self.assertEqual(headers["X-Feature3-Image-Sha256"],sha256(blob).hexdigest())
        self.assertEqual(headers["Content-Disposition"],
                         f'attachment; filename="feature3-{self.job}.png"')
        self.assert_private_headers(headers)
        self.assertEqual(self.reader.calls,
                         [("signed-retailer-test",self.shop,self.job)])
        self.assertNotIn(self.reader.media,str(headers))
        self.assertNotIn("token",str(headers).lower())
    def test_invalid_method_or_token_refuses_without_private_read(self):
        for method in ("POST","PATCH","DELETE","HEAD","OPTIONS"):
            code,body,headers=self.call(method=method)
            self.assertEqual(code,405)
            self.assertEqual(body,b"")
            self.assertEqual(headers["Allow"],"GET")
        for token in ("","foo","Bearer ","Bearer sb_secret_untrusted",
                      "Bearer sb_publishable_test","Bearer bad\r\nInjected",
                      "Bearer x","Bearer "+"x"*9000,None):
            code,body,headers=self.call(auth=token)
            self.assertEqual(code,401)
            self.assertEqual(body,b"")
            self.assert_private_headers(headers)
        self.assertEqual(self.reader.calls,[])
    def test_revoked_foreign_job_or_unverified_reader_never_returns_bytes(self):
        for exc in (PrivateGeneratedDownloadDenied("revoked"),
                    ValueError("foreign output"),KeyError("source missing")):
            self.reader.fail=exc
            status,body,headers=self.call()
            self.assertEqual(status,404)
            self.assertEqual(body,b"")
            self.assert_private_headers(headers)
        self.reader.fail=TimeoutError("private rights unknown")
        status,body,headers=self.call()
        self.assertEqual(status,503)
        self.assertEqual(body,b"")
        self.assert_private_headers(headers)
    def test_corrupted_or_foreign_receipts_fail_closed(self):
        png=sample_png()
        bad=(
            {"shop_id":str(uuid4())},{"job_id":str(uuid4())},
            {"media_asset_id":"not-a-uuid"},{"image_sha256":"a"*64},
            {"image_bytes":png+b"unauthorized edit"},
            {"image_bytes":"not bytes"},
            {"signed_url_issued":True},{"approved_model":True},
            {"publish_approved":True},{"private":False},
            {"mime_type":"image/jpeg"},{"url":"https://evil.test/"}
        )
        for extra in bad:
            self.reader.extra=extra
            with self.subTest(extra=list(extra)):
                status,body,headers=self.call()
                self.assertEqual(status,503)
                self.assertEqual(body,b"")
                self.assert_private_headers(headers)
        self.reader.extra={}
    def test_invalid_job_shop_or_missing_verifier_never_emits_private_body(self):
        status,body,_=self.api.handle(
            method="GET",authorization="Bearer signed-retailer-test",
            shop_id=str(uuid4()).upper(),job_id=self.job)
        self.assertEqual((status,body),(404,b""))
        with self.assertRaises(ValueError):
            Feature3PrivateBinaryHTTP(reader=object())
        self.assertEqual(self.reader.calls,[])
    def test_does_not_expose_signed_storage_url_or_authorize_gpu(self):
        status,body,headers=self.call()
        self.assertEqual(status,200)
        self.assertNotIn("signed",str(headers).lower())
        self.assertNotIn("provider",str(headers).lower())
        self.assertNotIn("publish",str(headers).lower())
        self.assertEqual(body,self.reader.png)

if __name__=="__main__":
    unittest.main()
