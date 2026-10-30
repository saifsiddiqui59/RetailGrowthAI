"""Feature3 no-URL binary HTTP adapter, synthetic PNG and fake signed rights."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest
from uuid import uuid4
from zlib import crc32
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
        self.assertNotIn("object_path",str(headers).lower())
        self.assertNotIn("signedurl",str(headers).lower())
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
    def test_valid_sha_does_not_make_non_png_or_trailing_bytes_downloadable(self):
        # A forged or broken reader can supply a self-consistent SHA; the HTTP
        # boundary must still reject non-PNG bytes and trailing payloads.
        original=self.reader.png
        for forged in (b"x"*128,original+b"trailing-private-data",
                       original[:-12]):
            self.reader.png=forged
            with self.subTest(length=len(forged)):
                status,body,headers=self.call()
                self.assertEqual(status,503)
                self.assertEqual(body,b"")
                self.assert_private_headers(headers)
        self.reader.png=original
        self.assertEqual(self.call()[0],200)

    def test_self_consistent_sha_cannot_hide_png_chunk_crc_or_structure_damage(self):
        # The fake reader recalculates SHA from its own bytes, simulating a
        # compromised receipt. The HTTP boundary must still reject corruption.
        original=self.reader.png
        # Corrupt a real IHDR CRC without touching the canonical IEND framing.
        corrupt_crc=bytearray(original)
        corrupt_crc[29]^=1
        # Duplicate the original IHDR before the first IDAT. Both copies have
        # individually correct CRCs but PNG requires exactly one IHDR.
        ihdr_chunk=original[8:33]
        duplicate_ihdr=original[:33]+ihdr_chunk+original[33:]
        # Change the first chunk's type while retaining valid-looking IEND.
        invalid_first=bytearray(original)
        invalid_first[12:16]=b"tEXt"
        for forged in (bytes(corrupt_crc),duplicate_ihdr,bytes(invalid_first)):
            self.reader.png=forged
            with self.subTest(case=forged[:36].hex()):
                status,body,headers=self.call()
                self.assertEqual(status,503)
                self.assertEqual(body,b"")
                self.assert_private_headers(headers)
        self.reader.png=original
        self.assertEqual(self.call()[0],200)

    def test_unknown_critical_and_interleaved_idat_fail_closed(self):
        # These receipts have self-consistent SHA values and correct chunk CRCs.
        original=self.reader.png
        def chunk(kind,payload):
            return (len(payload).to_bytes(4,"big")+kind+payload+
                    (crc32(kind+payload)&0xffffffff).to_bytes(4,"big"))
        ihdr=original[:33]
        idat=original[33:-12]
        self.assertEqual(idat[4:8],b"IDAT")
        payload=idat[8:-4]
        split=max(1,len(payload)//2)
        first=chunk(b"IDAT",payload[:split])
        second=chunk(b"IDAT",payload[split:])
        ancillary=chunk(b"tEXt",b"note\x00synthetic")
        unknown_critical=chunk(b"ABCD",b"forged")
        valid_split=ihdr+first+second+original[-12:]
        self.reader.png=valid_split
        self.assertEqual(self.call()[0],200)
        for forged in (
            ihdr+unknown_critical+idat+original[-12:],
            ihdr+first+ancillary+second+original[-12:],
            ihdr+idat+chunk(b"PLTE",b"\x00\x00\x00")+original[-12:],
        ):
            self.reader.png=forged
            with self.subTest(forged_sha=sha256(forged).hexdigest()):
                status,body,headers=self.call()
                self.assertEqual(status,503)
                self.assertEqual(body,b"")
                self.assert_private_headers(headers)
        self.reader.png=original
        self.assertEqual(self.call()[0],200)

    def test_pathological_png_chunk_count_is_denied(self):
        # Repeated valid ancillary chunks must not turn private download into
        # unbounded CPU work, even with a matching forged receipt SHA.
        original=self.reader.png
        kind=b"tEXt"
        payload=b"k\x00v"
        crc=(crc32(kind+payload)&0xffffffff).to_bytes(4,"big")
        chunk=len(payload).to_bytes(4,"big")+kind+payload+crc
        self.reader.png=original[:33]+chunk*4097+original[33:]
        status,body,headers=self.call()
        self.assertEqual(status,503)
        self.assertEqual(body,b"")
        self.assert_private_headers(headers)
        self.reader.png=original
        self.assertEqual(self.call()[0],200)

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
