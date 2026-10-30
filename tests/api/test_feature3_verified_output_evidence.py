"""Source-only actual private generated PNG and operator evidence reader tests."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest
from uuid import uuid4

from PIL import Image
from PIL.PngImagePlugin import PngInfo

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from feature3_verified_output_evidence import (
    Feature3VerifiedOutputEvidenceReader,Feature3EvidenceReadDenied,
)
from admin_store import AdminStore


def real_png():
    buf=BytesIO()
    Image.new("RGB",(320,400),"#4e799c").save(buf,format="PNG")
    return buf.getvalue()


class FakeHTTP:
    def __init__(self,url,blob,status,mime,redirect=False,content_length=None,read_hook=None,content_encoding=None):
        self._url=url+("/redirect" if redirect else "")
        self.blob=blob
        self.status=status
        self.read_hook=read_hook
        self.headers={"Content-Type":mime,
                      "Content-Length":str(len(blob)) if content_length is None else content_length}
        if content_encoding is not None:
            self.headers["Content-Encoding"]=content_encoding
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def geturl(self):return self._url
    def getcode(self):return self.status
    def read(self,maxbytes):
        if self.read_hook:self.read_hook()
        return self.blob[:maxbytes]


class FakeStore:
    origin="https://fixture.supabase.co"
    secret="sb_secret_"+"x"*40
    def __init__(self,shop,job,asset,blob):
        self.shop,self.job,self.asset=shop,job,asset
        self.digest=sha256(blob).hexdigest()
        self.evidence={
            "shop_id":shop,"job_id":job,"media_asset_id":asset,
            "image_sha256":self.digest,
            "object_path":f"{shop}/feature3/gpu/{job}/{self.digest}.png",
            "object_bytes":len(blob),"attempt":1,"review_status":"UNREVIEWED",
            "private":True}
        self.calls=[]
        self.flip_second=False
        self.denied=False
    def request(self,path,*,method="GET",data=None):
        self.calls.append(("rpc",path,method,data))
        if path!="rpc/feature3_read_gpu_private_evidence" or method!="POST":
            raise AssertionError("Unsafe operator RPC or method")
        if data!={"p_shop_id":self.shop,"p_job_id":self.job,
                 "p_media_asset_id":self.asset}:
            return None
        if self.denied:return None
        result=dict(self.evidence)
        if self.flip_second and len(self.calls)>=2:
            result["object_bytes"]+=1
        return result


class ProofTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.job,self.asset=[str(uuid4()) for _ in range(3)]
        self.png=real_png()
        self.store=FakeStore(self.shop,self.job,self.asset,self.png)
        self.http_calls=[]
        self.blob=self.png
        self.mime="image/png"
        self.status=200
        self.redirect=False
        self.length=None
        self.on_read=None
        self.content_encoding=None
        self.reader=Feature3VerifiedOutputEvidenceReader(
            admin_store=self.store,transport=self.transport)

    def transport(self,req,*,timeout):
        self.http_calls.append(req)
        self.assertEqual(timeout,15)
        self.assertEqual(req.get_method(),"GET")
        self.assertEqual(req.get_header("Apikey"),self.store.secret)
        self.assertEqual(req.get_header("Cache-control"),"no-store")
        self.assertEqual(req.get_header("Accept"),"image/png")
        self.assertIn("/storage/v1/object/retailgrowth-media/",req.full_url)
        self.assertIn(self.store.evidence["object_path"],req.full_url)
        return FakeHTTP(req.full_url,self.blob,self.status,self.mime,
                        redirect=self.redirect,content_length=self.length,
                        read_hook=self.on_read,content_encoding=self.content_encoding)

    def test_actual_verified_png_matches_sql_twice_no_signed_url(self):
        result=self.reader(self.shop,self.job,self.asset)
        self.assertEqual(result,{
            "shop_id":self.shop,"job_id":self.job,"media_asset_id":self.asset,
            "image_sha256":self.store.digest,"private":True,
            "attempt":1,"review_status":"UNREVIEWED"})
        self.assertEqual(len(self.store.calls),2)
        self.assertEqual(len(self.http_calls),1)
        self.assertNotIn("object_path",result)
        self.assertNotIn("url",result)
        self.assertNotIn("image_bytes",result)
        self.assertNotIn("authorized_to_retry",result)

    def test_second_sql_read_detects_changed_output(self):
        self.store.flip_second=True
        with self.assertRaisesRegex(Feature3EvidenceReadDenied,"changed"):
            self.reader(self.shop,self.job,self.asset)
        self.assertEqual(len(self.http_calls),1)
        self.assertEqual(len(self.store.calls),2)

    def test_missing_or_foreign_rpc_evidence_denied_without_storage_io(self):
        self.store.denied=True
        with self.assertRaises(Feature3EvidenceReadDenied):
            self.reader(self.shop,self.job,self.asset)
        self.assertEqual(self.http_calls,[])
        self.store.denied=False
        for change,value in (
            ("shop_id",str(uuid4())),("media_asset_id",str(uuid4())),
            ("private",False),("attempt",2),("review_status","APPROVED"),
            ("image_sha256","Z"*64),
            ("object_path",f"{str(uuid4())}/feature3/gpu/{self.job}/{self.store.digest}.png"),
            ("object_bytes",26*1024*1024),
            ("external_url","https://evil.invalid")):
            old=dict(self.store.evidence)
            self.store.evidence[change]=value
            with self.subTest(field=change),self.assertRaises(Feature3EvidenceReadDenied):
                self.reader(self.shop,self.job,self.asset)
            self.store.evidence=old
            self.assertEqual(self.http_calls,[])

    def test_wrong_blob_sha_invalid_png_or_truncated_bytes_denied(self):
        for bad in (b"not png"*60,real_png()[:-17],
                    self.png+b"extraneous byte"):
            self.setUp()
            self.blob=bad
            with self.subTest(n=len(bad)),self.assertRaises(Feature3EvidenceReadDenied):
                self.reader(self.shop,self.job,self.asset)
            self.assertEqual(len(self.store.calls),1)

    def test_redirect_non200_mime_or_bad_content_length_denied(self):
        for flag,value in (("redirect",True),("status",302),
                           ("mime","text/html"),("length","invalid"),
                           ("length",str(26*1024*1024))):
            self.setUp()
            setattr(self,flag,value)
            with self.subTest(flag=flag),self.assertRaises(Feature3EvidenceReadDenied):
                self.reader(self.shop,self.job,self.asset)
            self.assertEqual(len(self.store.calls),1)

    def test_rejects_encoded_or_malformed_storage_headers_before_sql_recheck(self):
        for field,value in (("content_encoding","gzip"),
                            ("content_encoding","br"),
                            ("content_encoding",17),
                            ("mime",42)):
            self.setUp()
            setattr(self,field,value)
            with self.subTest(field=field,value=value),self.assertRaises(
                    Feature3EvidenceReadDenied):
                self.reader(self.shop,self.job,self.asset)
            self.assertEqual(len(self.store.calls),1)
        self.setUp()
        self.content_encoding="IDENTITY"
        self.assertEqual(self.reader(self.shop,self.job,self.asset)["image_sha256"],
                         self.store.digest)

    def test_png_xmp_metadata_denied_even_with_matching_sql_sha(self):
        meta=PngInfo()
        meta.add_text("XML:com.adobe.xmp","<xmp>untrusted metadata</xmp>")
        out=BytesIO()
        Image.new("RGB",(320,400),"#4e799c").save(out,format="PNG",pnginfo=meta)
        self.blob=out.getvalue()
        digest=sha256(self.blob).hexdigest()
        self.store.digest=digest
        self.store.evidence.update({
            "image_sha256":digest,
            "object_path":f"{self.shop}/feature3/gpu/{self.job}/{digest}.png",
            "object_bytes":len(self.blob)})
        with self.assertRaisesRegex(Feature3EvidenceReadDenied,"unsuitable"):
            self.reader(self.shop,self.job,self.asset)
        self.assertEqual(len(self.store.calls),1)

    def test_same_shop_wrong_object_token_and_api_key_fails_closed(self):
        with self.assertRaises(Feature3EvidenceReadDenied):
            self.reader(str(uuid4()),self.job,self.asset)
        with self.assertRaises(Feature3EvidenceReadDenied):
            self.reader(self.shop,self.job,str(uuid4()))
        with self.assertRaises(ValueError):
            Feature3VerifiedOutputEvidenceReader(admin_store=object(),
                                                 transport=self.transport)
        other=FakeStore(self.shop,self.job,self.asset,self.png)
        other.secret="sb_publishable_FAKE"
        with self.assertRaises(ValueError):
            Feature3VerifiedOutputEvidenceReader(admin_store=other,
                                                 transport=self.transport)
        other.secret=self.store.secret
        other.origin="https://fixture.supabase.co.bad.example"
        with self.assertRaises(ValueError):
            Feature3VerifiedOutputEvidenceReader(admin_store=other,
                                                 transport=self.transport)

    def test_actual_admin_service_route_post_only_and_unknown_denied(self):
        class NoIO:
            def __call__(self,*a,**kw):
                raise AssertionError("Unreviewed service path must never send HTTP")
        store=AdminStore("https://fixture.supabase.co",self.store.secret,transport=NoIO())
        for method in ("GET","PATCH","DELETE","PUT"):
            with self.subTest(method=method),self.assertRaises(ValueError):
                store.request("rpc/feature3_read_gpu_private_evidence",method=method)
        with self.assertRaises(ValueError):
            store.request("rpc/feature3_settle_or_refund_unknown",method="POST",data={})

if __name__=="__main__":
    unittest.main()
