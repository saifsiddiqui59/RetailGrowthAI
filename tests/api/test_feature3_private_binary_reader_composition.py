"""Real Feature3 binary HTTP -> current JWT/RLS -> private Storage -> PNG proof.

Offline test: signed user, tenant, source-rights reviewer and HTTPS transport
are deliberately fake. A PASS does not mean real commercial license approval,
a mounted Azure endpoint, or actual hosted user/storage authorization.
"""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest
from uuid import uuid4

from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from feature3_private_binary_http import Feature3PrivateBinaryHTTP
from feature3_private_png_reader import Feature3RevocablePNGReader


def png_bytes():
    stream=BytesIO()
    Image.new("RGB",(320,400),"#34677e").save(stream,format="PNG")
    return stream.getvalue()


class FakeTenant:
    origin="https://example.supabase.co"
    key="sb_publishable_FAKE_OFFLINE_TEST_ONLY"
    def __init__(self,shop,job,actor,media,digest):
        self.shop,self.job,self.actor,self.media=shop,job,actor,media
        self.path=f"{shop}/feature3/gpu/{job}/{digest}.png"
        self.active=True
        self.status="SUCCEEDED"
        self.foreign_path=False
        self.asset_overrides={}
        self.calls=[]
        self.outage=False

    def member(self,token,actor,shop,write=False):
        self.calls.append("member")
        if self.outage:raise OSError("offline SQL failure")
        return self.active and token=="fixture-signed-retailer-token" and (
            actor,shop)==(self.actor,self.shop)

    def feature3_gpu_job(self,token,shop,job):
        self.calls.append("job")
        return {"id":self.job,"shop_id":self.shop,"status":self.status,
                "output_asset_id":self.media}

    def feature3_generated_asset(self,token,shop,job,asset):
        self.calls.append("asset")
        path=self.path if not self.foreign_path else (
            f"{uuid4()}/feature3/gpu/{self.job}/untrusted.png")
        return {
            "id":self.media, "shop_id":self.shop,
            "storage_bucket":"retailgrowth-media", "source":"GENERATED",
            "object_path":path, "mime_type":"image/png",
            **self.asset_overrides,
        }


class PrivateResponse:
    def __init__(self,url,data,headers):
        self.url,self.payload,self.headers=url,data,headers
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def geturl(self):return self.url
    def getcode(self):return 200
    def read(self,n):return self.payload[:n]


class ComposedBinaryContractTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.job,self.actor,self.media=[str(uuid4()) for _ in range(4)]
        self.png=png_bytes()
        self.digest=sha256(self.png).hexdigest()
        self.tenant=FakeTenant(self.shop,self.job,self.actor,self.media,self.digest)
        self.calls=[]
        self.license_active=True
        self.revoke_at_second_check=False
        self.expire_jwt_after_last_rights=False
        self.jwt_active=True
        self.change_during_get=False
        self.spoof_length=None
        self.content_encoding=None
        self.private_payload=self.png
        self.rights_calls=0

        def verify(token):
            self.calls.append("jwt")
            if token!="fixture-signed-retailer-token" or not self.jwt_active:
                raise ValueError("Synthetic JWT invalid")
            return self.actor

        def current_rights(shop,job,asset):
            self.rights_calls+=1
            allowed=((shop,job,asset)==(self.shop,self.job,self.media)
                    and self.license_active
                    and not (self.revoke_at_second_check and self.rights_calls>=2))
            if self.expire_jwt_after_last_rights and self.rights_calls==2:
                self.jwt_active=False
            return allowed

        def transport(request,timeout):
            self.calls.append("private_get")
            self.assertEqual(timeout,10)
            self.assertEqual(request.get_method(),"GET")
            self.assertEqual(request.get_header("Apikey"),self.tenant.key)
            self.assertEqual(request.get_header("Authorization"),
                             "Bearer fixture-signed-retailer-token")
            self.assertIn("/storage/v1/object/authenticated/retailgrowth-media/",
                          request.full_url)
            self.assertIn(self.tenant.path,request.full_url)
            self.assertNotIn("/object/sign/",request.full_url)
            if self.change_during_get:self.tenant.active=False
            headers={"Content-Type":"image/png",
                     "Content-Length":self.spoof_length if self.spoof_length is not None
                                      else str(len(self.private_payload))}
            if self.content_encoding is not None:
                headers["Content-Encoding"]=self.content_encoding
            return PrivateResponse(request.full_url,self.private_payload,headers)

        self.reader=Feature3RevocablePNGReader(
            tenant_store=self.tenant,verify_user_jwt=verify,
            current_output_rights=current_rights,transport=transport)
        self.http=Feature3PrivateBinaryHTTP(reader=self.reader)

    def request(self,shop=None,job=None,authorization="Bearer fixture-signed-retailer-token",
                method="GET"):
        return self.http.handle(method=method,authorization=authorization,
                                shop_id=self.shop if shop is None else shop,
                                job_id=self.job if job is None else job)

    def assert_denied_without_png(self,result,status):
        code,body,headers=result
        self.assertEqual(code,status)
        self.assertEqual(body,b"")
        self.assertEqual(headers["Cache-Control"],"no-store, private, max-age=0")
        self.assertEqual(headers["X-Content-Type-Options"],"nosniff")
        self.assertNotIn("Location",headers)
        self.assertNotIn("X-Feature3-Image-Sha256",headers)

    def test_exact_real_png_http_headers_and_twice_current_private_rights(self):
        status,body,headers=self.request()
        self.assertEqual(status,200)
        self.assertEqual(body,self.png)
        self.assertEqual(headers["Content-Type"],"image/png")
        self.assertEqual(headers["Content-Length"],str(len(self.png)))
        self.assertEqual(headers["X-Feature3-Shop-Id"],self.shop)
        self.assertEqual(headers["X-Feature3-Job-Id"],self.job)
        self.assertEqual(headers["X-Feature3-Media-Asset-Id"],self.media)
        self.assertEqual(headers["X-Feature3-Image-Sha256"],self.digest)
        self.assertEqual(self.calls,["jwt","private_get","jwt"])
        self.assertEqual(self.tenant.calls,
                         ["member","job","asset","member","job","asset"])
        self.assertEqual(self.rights_calls,2)
        self.assertNotIn("Location",headers)
        self.assertNotIn("object_path",str(headers).lower())
        self.assertNotIn("jwt",str(headers).lower())
        self.assertNotIn("signed_url",str(headers).lower())
        self.assertNotIn("provider",str(headers).lower())

    def test_jwt_expired_during_final_rights_yields_opaque_http_404_not_png(self):
        # The composed route must not return an image even when current
        # membership, media object and legal rights still appear unchanged.
        self.expire_jwt_after_last_rights=True
        response=self.request()
        self.assert_denied_without_png(response,404)
        self.assertEqual(self.calls,["jwt","private_get","jwt"])
        self.assertEqual(self.tenant.calls.count("member"),2)
        self.assertEqual(self.rights_calls,2)

    def test_revoke_membership_or_source_during_real_https_read_denies_body(self):
        for cause in ("membership","license"):
            self.setUp()
            if cause=="membership":self.change_during_get=True
            else:self.revoke_at_second_check=True
            with self.subTest(cause=cause):
                self.assert_denied_without_png(self.request(),404)
            self.assertEqual(self.calls,["jwt","private_get"])
            self.assertEqual(self.tenant.calls.count("member"),2)

    def test_denies_wrong_shop_mime_claim_and_invalid_method_without_private_get(self):
        for case in ("wrong_shop","foreign_path","failed_job","license_revoked",
                     "bad_token","bad_method"):
            self.setUp()
            if case=="wrong_shop":result=self.request(shop=str(uuid4()))
            elif case=="foreign_path":
                self.tenant.foreign_path=True
                result=self.request()
            elif case=="failed_job":
                self.tenant.status="FAILED"
                result=self.request()
            elif case=="license_revoked":
                self.license_active=False
                result=self.request()
            elif case=="bad_token":
                result=self.request(authorization="Bearer sb_secret_fake")
            else:
                result=self.request(method="POST")
            with self.subTest(case=case):
                self.assert_denied_without_png(
                    result,405 if case=="bad_method" else
                    401 if case=="bad_token" else 404)
            self.assertNotIn("private_get",self.calls)

    def test_composed_binary_http_denies_forged_media_row_without_private_read(self):
        # Protect private JSON/PNG even if a future tenant adapter accidentally
        # returns a valid SHA path for the wrong media row or a public bucket.
        for field,bad in (
            ("id",str(uuid4())),
            ("shop_id",str(uuid4())),
            ("storage_bucket","public-bucket"),
            ("source","UPLOAD"),
            ("id",None),
        ):
            self.setUp()
            self.tenant.asset_overrides[field]=bad
            with self.subTest(field=field):
                self.assert_denied_without_png(self.request(),404)
            self.assertEqual(self.calls,["jwt"])
            self.assertEqual(self.rights_calls,0)
            self.assertEqual(self.tenant.calls,["member","job","asset"])

    def test_composed_binary_http_denies_media_row_changed_during_storage_read(self):
        # Real rights may be withdrawn or a media record replaced during
        # the private HTTP GET; the second authoritative check is mandatory.
        for field,bad in (
            ("id",str(uuid4())),
            ("shop_id",str(uuid4())),
            ("storage_bucket","public-bucket"),
            ("source","UPLOAD"),
        ):
            self.setUp()
            original_reader=self.reader.transport
            def read_and_change(request,timeout):
                response=original_reader(request,timeout)
                self.tenant.asset_overrides[field]=bad
                return response
            self.reader.transport=read_and_change
            with self.subTest(field=field):
                self.assert_denied_without_png(self.request(),404)
            self.assertEqual(self.calls,["jwt","private_get"])
            self.assertEqual(self.tenant.calls.count("asset"),2)
            self.assertEqual(self.rights_calls,1)

    def test_transport_length_recode_and_png_mutation_fail_closed_at_http_boundary(self):
        for case in ("short","long","recoded","wrong_png"):
            self.setUp()
            if case=="short":self.spoof_length=str(len(self.png)-1)
            if case=="long":self.spoof_length=str(len(self.png)+1)
            if case=="recoded":self.content_encoding="gzip"
            if case=="wrong_png":
                s=BytesIO()
                Image.new("RGB",(320,400),"#b37d43").save(s,format="PNG")
                self.private_payload=s.getvalue()
            with self.subTest(case=case):
                self.assert_denied_without_png(self.request(),404)
            self.assertEqual(self.calls,["jwt","private_get"])

    def test_backend_uncertainty_returns_opaque_503_no_bytes_and_no_retry(self):
        self.tenant.outage=True
        self.assert_denied_without_png(self.request(),503)
        self.assertEqual(self.calls,["jwt"])
        self.assertEqual(self.tenant.calls,["member"])


if __name__=="__main__":
    unittest.main()
