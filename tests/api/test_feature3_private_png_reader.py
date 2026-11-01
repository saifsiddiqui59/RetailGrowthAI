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
        self.asset_overrides={}
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
        return {
            "id": self.asset, "shop_id": self.shop,
            "storage_bucket": "retailgrowth-media", "source": "GENERATED",
            "object_path":self.path if not self.foreign else
                f"{str(uuid4())}/feature3/gpu/{job}/{self.sha}.png",
            "mime_type":"image/png",
            **self.asset_overrides,
        }


class Response:
    def __init__(self,url,data,*,redirect=False,status=200,
                 mime="image/png",content_length=None,on_read=None,
                 content_encoding=None):
        self.url=url+"/redirected" if redirect else url
        self.data=data
        self.status=status
        self.headers={"Content-Type":mime,
                      "Content-Length":str(len(data)) if content_length is None
                      else content_length}
        if content_encoding is not None:
            self.headers["Content-Encoding"]=content_encoding
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
        self.content_encoding=None
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
                        on_read=self.on_read,content_encoding=self.content_encoding)

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
        self.assertEqual(self.calls,["verify","get","verify"])
        self.assertEqual(self.tenant.calls,
                         ["member","job","asset","member","job","asset"])
        self.assertEqual(self.rights_called,2)

    def test_jwt_expires_during_binary_stream_denies_private_output(self):
        state={"expired":False}
        original=self.verify
        def verifier(token):
            if state["expired"]:
                raise RuntimeError("SECRET_JWT_DIAGNOSTIC_NEVER_EXPOSE")
            return original(token)
        self.verify=verifier
        self.reader=self.build()
        self.on_read=lambda:state.__setitem__("expired",True)
        with self.assertRaises(PrivateGeneratedDownloadDenied) as caught:
            self.read()
        self.assertNotIn("SECRET_JWT",str(caught.exception))
        self.assertEqual(self.calls,["verify","get"])
        self.assertEqual(self.tenant.calls.count("member"),2)
        self.assertEqual(self.rights_called,2)

    def test_jwt_actor_changes_after_binary_stream_denies_private_output(self):
        original=self.verify
        state={"switched":False}
        def verifier(token):
            return str(uuid4()) if state["switched"] else original(token)
        self.verify=verifier
        self.reader=self.build()
        self.on_read=lambda:state.__setitem__("switched",True)
        with self.assertRaises(PrivateGeneratedDownloadDenied):
            self.read()
        self.assertEqual(self.tenant.calls.count("member"),2)
        self.assertEqual(self.rights_called,2)

    def test_jwt_revoked_during_final_rights_check_denies_private_output(self):
        original_verify=self.verify
        original_rights=self.rights
        state={"revoked":False}
        def verifier(token):
            if state["revoked"]:
                raise PermissionError("sensitive verifier internal token")
            return original_verify(token)
        def rights_and_revoke(shop,job,asset):
            allowed=original_rights(shop,job,asset)
            if self.rights_called==2:
                state["revoked"]=True
            return allowed
        self.verify=verifier
        self.rights=rights_and_revoke
        self.reader=self.build()
        with self.assertRaises(PrivateGeneratedDownloadDenied) as caught:
            self.read()
        self.assertNotIn("sensitive verifier",str(caught.exception))
        self.assertEqual(self.rights_called,2)

    def test_failing_initial_jwt_verifier_never_leaks_or_reads_private_media(self):
        def broken(_token):
            raise RuntimeError("SECRET_AUTH_ADMIN_DIAGNOSTIC")
        self.verify=broken
        self.reader=self.build()
        with self.assertRaises(PrivateGeneratedDownloadDenied) as caught:
            self.read()
        self.assertNotIn("SECRET_AUTH_ADMIN",str(caught.exception))
        self.assertEqual(self.tenant.calls,[])
        self.assertNotIn("get",self.calls)

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

    def test_forged_generated_media_identity_and_private_bucket_denied_before_get(self):
        # Even a future misconfigured tenant store must not be able to return
        # a different asset or bucket by supplying a same-shaped SHA path.
        for field, bad in (
            ("id",str(uuid4())),
            ("shop_id",str(uuid4())),
            ("storage_bucket","public-media"),
            ("source","UPLOAD"),
            ("source","MODEL"),
            ("id",None),
            ("shop_id",None),
            ("storage_bucket",None),
            ("source",None),
        ):
            self.setUp()
            self.tenant.asset_overrides[field]=bad
            with self.subTest(field=field, value=bad), self.assertRaises(
                    PrivateGeneratedDownloadDenied):
                self.read()
            self.assertEqual(self.calls,["verify"])
            self.assertEqual(self.rights_called,0)
            self.assertEqual(self.tenant.calls,["member","job","asset"])

    def test_asset_identity_or_bucket_changed_after_private_get_denies_cached_png(self):
        # The post-stream authorization must check the full media row, not
        # merely repeat a URL or verify a SHA of already-read private bytes.
        for field,bad in (
            ("id",str(uuid4())),
            ("shop_id",str(uuid4())),
            ("storage_bucket","retailgrowth-public"),
            ("source","UPLOAD"),
        ):
            self.setUp()
            self.on_read=lambda field=field,bad=bad: self.tenant.asset_overrides.__setitem__(field,bad)
            with self.subTest(field=field), self.assertRaises(
                    PrivateGeneratedDownloadDenied):
                self.read()
            self.assertEqual(self.calls,["verify","get"])
            self.assertEqual(self.tenant.calls.count("asset"),2)
            self.assertEqual(self.rights_called,1)

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

    def test_plausible_http_content_length_mismatch_denied_before_second_rights(self):
        # Even a valid signed-path PNG must not return success when the private
        # HTTPS response advertises bytes it did not actually deliver.
        for announced in ("0",str(len(self.png)-1),str(len(self.png)+1),
                          "000"+str(len(self.png))+"0"):
            self.setUp()
            self.content_length=announced
            with self.subTest(length=announced),self.assertRaisesRegex(
                    PrivateGeneratedDownloadDenied,"length changed"):
                self.read()
            self.assertEqual(self.calls,["verify","get"])
            self.assertEqual(self.rights_called,1)
            self.assertEqual(self.tenant.calls.count("member"),1)

    def test_http_content_encoding_cannot_transform_immutable_private_png(self):
        for coding in ("gzip","br","deflate","x-gzip"):
            self.setUp()
            self.content_encoding=coding
            with self.subTest(coding=coding),self.assertRaises(
                    PrivateGeneratedDownloadDenied):
                self.read()
            self.assertEqual(self.rights_called,1)
            self.assertEqual(self.calls,["verify","get"])
        self.setUp()
        self.content_encoding="identity"
        self.assertEqual(self.read()["image_sha256"],self.sha)
        # Chunked/private response without an announced length is still
        # permitted when the real PNG SHA and current rights both match.
        self.setUp()
        self.content_length=None
        self.assertEqual(self.read()["image_sha256"],self.sha)

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


    def test_malformed_private_http_metadata_never_reaches_second_rights_read(self):
        # A future injected gateway may return typed, missing or throwing
        # headers. No raw TypeError or private binary may escape this reader.
        class BrokenHeaders:
            def get(self, _name):
                raise RuntimeError("SENSITIVE_STORAGE_HEADER_DIAGNOSTIC")
        cases = (
            None, [], "bad headers", BrokenHeaders(),
            {"Content-Type":False},
            {"Content-Type":["image/png"]},
            {"Content-Length":7},
            {"Content-Length":True},
            {"Content-Type":"image/png","Content-Encoding":[]},
        )
        for headers in cases:
            self.setUp()
            original = self.reader.transport
            def malformed(req, timeout):
                response = original(req, timeout)
                response.headers = headers
                return response
            self.reader.transport = malformed
            with self.subTest(headers=repr(headers)), self.assertRaises(
                    PrivateGeneratedDownloadDenied) as caught:
                self.read()
            self.assertNotIn("SENSITIVE_STORAGE",str(caught.exception))
            self.assertEqual(self.calls,["verify","get"])
            self.assertEqual(self.rights_called,1)
            self.assertEqual(self.tenant.calls.count("member"),1)

    def test_private_transport_missing_methods_or_runtime_exception_denied(self):
        for method in ("geturl","getcode","read"):
            self.setUp()
            original = self.reader.transport
            def malformed(req, timeout):
                response = original(req, timeout)
                setattr(response,method,None)
                return response
            self.reader.transport = malformed
            with self.subTest(method=method), self.assertRaises(
                    PrivateGeneratedDownloadDenied):
                self.read()
            self.assertEqual(self.rights_called,1)
            self.assertEqual(self.calls,["verify","get"])
        self.setUp()
        def unavailable(_req, timeout):
            raise RuntimeError("SENSITIVE_HTTP_TRANSPORT_INTERNAL")
        self.reader.transport = unavailable
        with self.assertRaises(PrivateGeneratedDownloadDenied) as caught:
            self.read()
        self.assertNotIn("SENSITIVE_HTTP",str(caught.exception))
        self.assertEqual(self.rights_called,1)

    def test_current_rights_outage_before_or_after_private_read_denied(self):
        for fail_on in (1,2):
            self.setUp()
            # setUp resets fixtures but does not shadow instance methods.
            # Bind the real implementation, not the previous loop's wrapper.
            original = RevocableReaderTests.rights.__get__(self, RevocableReaderTests)
            calls = [0]
            def unavailable(shop,job,asset):
                calls[0] += 1
                if calls[0] == fail_on:
                    raise TimeoutError("SENSITIVE_RIGHTS_SERVICE_FAILURE")
                return original(shop,job,asset)
            self.rights = unavailable
            self.reader = self.build()
            with self.subTest(fail_on=fail_on), self.assertRaises(
                    PrivateGeneratedDownloadDenied) as caught:
                self.read()
            self.assertNotIn("SENSITIVE_RIGHTS",str(caught.exception))
            self.assertEqual(calls[0],fail_on)
            self.assertEqual(self.calls,["verify"] if fail_on==1
                             else ["verify","get"])
            self.assertEqual(self.tenant.calls.count("member"),fail_on)

    def test_tenant_rls_outage_at_first_or_second_read_denied(self):
        for method in ("member","feature3_gpu_job","feature3_generated_asset"):
            for fail_on in (1,2):
                self.setUp()
                original = getattr(self.tenant,method)
                calls = [0]
                def unavailable(*args,**kwargs):
                    calls[0] += 1
                    if calls[0] == fail_on:
                        raise RuntimeError("SENSITIVE_RLS_DATABASE_FAILURE")
                    return original(*args,**kwargs)
                setattr(self.tenant,method,unavailable)
                with self.subTest(method=method,fail_on=fail_on), self.assertRaises(
                        PrivateGeneratedDownloadDenied) as caught:
                    self.read()
                self.assertNotIn("SENSITIVE_RLS",str(caught.exception))
                self.assertEqual(calls[0],fail_on)
                self.assertEqual(self.calls,["verify"] if fail_on==1
                                 else ["verify","get"])


if __name__=="__main__":
    unittest.main()
