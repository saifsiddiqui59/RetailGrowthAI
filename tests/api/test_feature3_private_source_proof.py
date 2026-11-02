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
    build_verified_gpu_off_preflight,
)


def image_bytes(kind="PNG"):
    out=BytesIO()
    Image.new("RGB",(320,400),"#e08943").save(out,format=kind)
    return out.getvalue()


class FakeResponse:
    def __init__(self,url,payload,*,mime,status,redirect=False,read_hook=None,content_length=None,content_encoding=None):
        self.url=url+("/evil" if redirect else "")
        self.payload=payload
        self.status=status
        self.read_hook=read_hook
        self.headers={"Content-Type":mime,
                      "Content-Length":str(len(payload)) if content_length is None else content_length}
        if content_encoding is not None:
            self.headers["Content-Encoding"]=content_encoding
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
        self.content_encoding=None
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
            read_hook=self.read_hook,content_length=self.length,
            content_encoding=self.content_encoding)

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
        self.assertEqual([x[0] for x in self.calls],["review","get","review"])
        self.assertNotIn("object_path",receipt)
        self.assertNotIn("url",receipt)
        self.assertNotIn("image_bytes",receipt)
        self.assertNotIn("provider_call_permitted",receipt)
        self.assertNotIn("gpu_started",receipt)

    def test_factory_connects_real_byte_verifier_to_gpu_off_job_plan(self):
        class FakeAdmin:
            def request(self,*_args,**_kwargs):
                raise AssertionError("No SQL lookup before explicitly checking")
        plan=build_verified_gpu_off_preflight(
            admin_store=FakeAdmin(),
            origin="https://fictional.supabase.co",
            backend_secret="sb_secret_"+"z"*36,
            review_authority=self.review,transport=self.transport)
        self.assertIsInstance(plan.proof,Feature3TrustedPrivateSourceProof)
        self.assertEqual(self.calls,[])
        # No source reader, paid provider, job or queue is started by wiring.

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
        self.assertEqual([x[0] for x in self.calls],["review","get","review"])

    def test_revision_change_after_first_review_denied(self):
        self.change_revision_second=True
        with self.assertRaisesRegex(SourceProofDenied,"changed"):
            self.proof(self.shop,self.row)

    def test_revoked_during_http_get_denied(self):
        self.read_hook=lambda:setattr(self,"authorized",False)
        with self.assertRaises(SourceProofDenied):
            self.proof(self.shop,self.row)
        self.assertEqual([x[0] for x in self.calls],["review","get","review"])

    def test_revoked_model_original_never_reaches_service_role_storage(self):
        # The SHA in an immutable model key is a *candidate* preflight digest.
        # An independent revoked/absent license denies before any private GET.
        for revoked in (False, True):
            self.setUp()
            self.authorized=revoked
            if revoked:
                self.revoke_second=True
                # The second review simulates revocation while bytes are read.
                with self.assertRaises(SourceProofDenied):
                    self.proof(self.shop,self.row)
                self.assertEqual([x[0] for x in self.calls],
                                 ["review","get","review"])
            else:
                with self.assertRaises(SourceProofDenied):
                    self.proof(self.shop,self.row)
                self.assertEqual([x[0] for x in self.calls],["review"])

    def test_generic_upload_without_immutable_digest_still_checks_twice(self):
        # Generic uploads have no registered SHA path; unlike immutable model
        # originals they cannot be independently authorized with a digest
        # until the service has read the bytes. Do not claim an early check.
        self.row["object_path"]=f"{self.shop}/retailer-original/original.png"
        self.assertEqual(self.proof(self.shop,self.row)["image_sha256"],self.sha)
        self.assertEqual([x[0] for x in self.calls],
                         ["get","review","review"])

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
            self.assertEqual([x[0] for x in self.calls],["review","get"])

    def test_true_private_content_length_must_match_real_read_bytes(self):
        for declared in ("0",str(len(self.png)-1),str(len(self.png)+1)):
            self.setUp()
            self.length=declared
            with self.subTest(length=declared),self.assertRaisesRegex(
                    SourceProofDenied,"length changed"):
                self.proof(self.shop,self.row)
            self.assertEqual([c[0] for c in self.calls],["review","get"])

    def test_encoded_original_transport_denied_before_rights_review(self):
        # Even if a mocked proxy supplies valid PNG bytes, a non-identity
        # content encoding is not immutable original-byte transport evidence.
        for encoding in ("gzip", "br", "deflate", "gzip, identity", "",
                         "unknown", 123):
            self.setUp()
            self.content_encoding=encoding
            # The private transport intentionally sanitizes the specific
            # denial to avoid exposing Storage details to its caller.
            with self.subTest(encoding=encoding),self.assertRaises(
                    SourceProofDenied):
                self.proof(self.shop,self.row)
            self.assertEqual([x[0] for x in self.calls],["review","get"])
        self.setUp()
        self.content_encoding=" identity "
        self.assertEqual(self.proof(self.shop,self.row)["image_sha256"],self.sha)

    def test_immutable_model_object_sha_rejects_replaced_decodable_image(self):
        out=BytesIO()
        Image.new("RGB",(320,400),"#4682b4").save(out,format="PNG")
        self.http_payload=out.getvalue()
        self.assertNotEqual(sha256(self.http_payload).hexdigest(),self.sha)
        # A fake reviewer returning any supplied SHA is NOT enough to convert
        # a replaced original into an approved model source.
        with self.assertRaisesRegex(SourceProofDenied,"immutable path SHA"):
            self.proof(self.shop,self.row)
        self.assertEqual([c[0] for c in self.calls],["review","get"])

    def test_invalid_model_original_namespace_and_digest_name_denied(self):
        for key in (
            f"{self.shop}/model-library/{self.model}/notasha.png",
            f"{self.shop}/model-library/platform/wrong/{self.sha}.png",
            f"{self.shop}/model-library/{self.sha}.png",
            f"{self.shop}/model-library/platform/{self.model}/nested/{self.sha}.png",
        ):
            self.setUp()
            self.row["object_path"]=key
            with self.subTest(key=key),self.assertRaises(SourceProofDenied):
                self.proof(self.shop,self.row)
            self.assertEqual(self.calls,[])

    def test_platform_model_original_sha_name_remains_accepted(self):
        self.row["object_path"]=(
            f"{self.shop}/model-library/platform/{self.model}/{self.sha}.png")
        self.assertEqual(self.proof(self.shop,self.row)["image_sha256"],self.sha)

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

    def test_malformed_registered_license_metadata_denied_before_storage(self):
        # A malformed row must never trigger even a private service-role GET.
        changes=[
            {"mime_type":["image/png"]},
            {"mime_type":None},
            {"license_name":["owned"]},
            {"license_name":None},
            {"license_url":"http://license.example/rights"},
            {"license_url":"https://user:pass@license.example/rights"},
            {"license_url":"https://license.example:444/rights"},
            {"license_url":"https://license.example/rights\\nInjected: yes".replace("\\n","\n")},
            {"license_url":"https://license.example/"+"a"*501},
            {"license_url":["https://license.example/rights"]},
            {"attribution":"independent\nfalse approval"},
            {"attribution":"x"*201},
            {"attribution":None},
            {"license_name":"cc0","license_url":None},
        ]
        for change in changes:
            self.setUp()
            self.row.update(change)
            with self.subTest(change=repr(change)),self.assertRaises(SourceProofDenied):
                self.proof(self.shop,self.row)
            self.assertEqual(self.calls,[])

    def test_valid_declared_license_url_never_substitutes_for_review(self):
        self.row["license_name"]="cc0"
        self.row["license_url"]="https://license.example/licenses/cc0"
        self.authorized=False
        with self.assertRaises(SourceProofDenied):
            self.proof(self.shop,self.row)
        self.assertEqual([c[0] for c in self.calls],["review"])
        self.calls.clear()
        self.authorized=True
        self.assertEqual(self.proof(self.shop,self.row)["image_sha256"],self.sha)
        self.assertEqual([c[0] for c in self.calls],["review","get","review"])

    def test_malformed_private_http_headers_never_reach_review(self):
        # Fake transports may return malformed header objects or typed values;
        # all such acknowledgements must fail closed, not cause an uncaught
        # AttributeError or bypass immutable-byte verification.
        for headers in (None, [], "not-headers",
                        {"Content-Type":7},
                        {"Content-Type":object()},
                        {"Content-Type":"image/png","Content-Length":7},
                        {"Content-Type":"image/png","Content-Encoding":[]},
                        {"Content-Type":"text/html"}):
            self.setUp()
            original=self.proof.transport
            def malformed(req,*,timeout):
                response=original(req,timeout=timeout)
                response.headers=headers
                return response
            self.proof.transport=malformed
            with self.subTest(headers=repr(headers)),self.assertRaises(SourceProofDenied):
                self.proof(self.shop,self.row)
            self.assertEqual([c[0] for c in self.calls],["review","get"])


    def test_missing_transport_methods_and_header_get_fail_closed(self):
        # Real private Storage reads must fail closed when a gateway or
        # injected transport does not implement the expected HTTP interface.
        # No malformed response can reach the post-read rights receipt.
        for missing in ("geturl", "getcode", "read"):
            self.setUp()
            original=self.proof.transport
            def malformed(req,*,timeout):
                response=original(req,timeout=timeout)
                setattr(response,missing,None)
                return response
            self.proof.transport=malformed
            with self.subTest(missing=missing), self.assertRaises(SourceProofDenied):
                self.proof(self.shop,self.row)
            self.assertEqual([c[0] for c in self.calls],["review","get"])

        self.setUp()
        original=self.proof.transport
        class FailingHeaders:
            def get(self,key):
                raise TypeError("malformed proxy header accessor")
        def malformed_headers(req,*,timeout):
            response=original(req,timeout=timeout)
            response.headers=FailingHeaders()
            return response
        self.proof.transport=malformed_headers
        with self.assertRaises(SourceProofDenied):
            self.proof(self.shop,self.row)
        self.assertEqual([c[0] for c in self.calls],["review","get"])

    def test_rights_authority_outage_denies_before_model_original_get(self):
        # A real review service outage must never fall back to trusting a
        # registered model's SHA key or retailer-declared license metadata.
        for failure in (TimeoutError, ConnectionError, RuntimeError):
            self.setUp()
            def unavailable(*_args):
                raise failure("sensitive rights backend details")
            self.proof.review=unavailable
            with self.subTest(failure=failure.__name__), self.assertRaisesRegex(
                    SourceProofDenied,"review unavailable"):
                self.proof(self.shop,self.row)
            self.assertEqual(self.calls,[])

    def test_generic_source_authority_outage_never_produces_attestation(self):
        # Generic keys lack an immutable pre-read digest; preserve this
        # explicit limitation and still reject an unavailable post-read
        # independent reviewer. No success receipt or GPU authorization.
        self.row["object_path"]=f"{self.shop}/retailer-original/original.png"
        def unavailable(*_args):
            raise TimeoutError("offline rights review")
        self.proof.review=unavailable
        with self.assertRaisesRegex(SourceProofDenied,"review unavailable"):
            self.proof(self.shop,self.row)
        self.assertEqual([c[0] for c in self.calls],["get"])


    def test_private_transport_runtime_failures_are_opaque_and_never_approved(self):
        # An injected proxy can fail at open, response status, header lookup
        # or byte read. No raw RuntimeError may escape the service-key boundary
        # or trigger a post-read current-rights approval.
        for stage in ("open", "status", "headers", "read"):
            self.setUp()
            original=self.proof.transport
            def broken(req, *, timeout):
                if stage=="open":
                    self.calls.append(("get",req.full_url))
                    raise RuntimeError("sensitive private gateway detail")
                response=original(req,timeout=timeout)
                def fail(*_args,**_kwargs):
                    raise RuntimeError("sensitive private gateway detail")
                if stage=="status":
                    response.getcode=fail
                elif stage=="headers":
                    class FailingHeaders:
                        def get(self,_key):
                            return fail()
                    response.headers=FailingHeaders()
                else:
                    response.read=fail
                return response
            self.proof.transport=broken
            with self.subTest(stage=stage),self.assertRaisesRegex(
                    SourceProofDenied,"byte read unavailable"):
                self.proof(self.shop,self.row)
            self.assertEqual([x[0] for x in self.calls],["review","get"])


if __name__=="__main__":
    unittest.main()
