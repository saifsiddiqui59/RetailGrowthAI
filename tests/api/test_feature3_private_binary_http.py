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
    def test_noncanonical_route_scope_denied_before_private_reader(self):
        # No implicit normalization of a URL's tenant/job identity.
        from uuid import UUID
        shop, job = self.shop, self.job
        malformed = (
            (shop.upper() if shop.upper()!=shop else shop+"A", job), (shop.replace("-", ""), job),
            ("{" + shop + "}", job), (shop, job.upper() if job.upper()!=job else job+"A"),
            (shop, job.replace("-", "")), (object(), job),
            (shop, UUID(job)),
        )
        for bad_shop, bad_job in malformed:
            with self.subTest(shop=repr(bad_shop), job=repr(bad_job)):
                status, body, headers = self.api.handle(
                    method="GET", authorization="Bearer signed-retailer-test",
                    shop_id=bad_shop, job_id=bad_job)
                self.assertEqual((status, body), (404, b""))
                self.assert_private_headers(headers)
        self.assertEqual(self.reader.calls, [])

    def test_ambiguous_bearer_token_denied_before_reader(self):
        for token in ("signed,other-token", "signed;other-token",
                      'signed"other-token', "signed\\\\other-token",
                      "signed\u0080other-token"):
            with self.subTest(token=repr(token)):
                status, body, headers = self.call(auth="Bearer " + token)
                self.assertEqual((status, body), (401, b""))
                self.assert_private_headers(headers)
        self.assertEqual(self.reader.calls, [])

    def test_noncanonical_media_receipt_denies_private_bytes(self):
        original = self.reader.media
        for forged in (original.upper() if original.upper()!=original else original+"A", original.replace("-", ""),
                       "{" + original + "}"):
            self.reader.extra = {"media_asset_id": forged}
            with self.subTest(forged=forged):
                status, body, headers = self.call()
                self.assertEqual((status, body), (503, b""))
                self.assert_private_headers(headers)
        self.reader.extra = {}

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
    def test_spoofed_receipt_identity_cannot_authorize_private_bytes(self):
        # Injected rights adapters must not authorize using attacker __eq__.
        class AlwaysEqual:
            def __eq__(self, other):
                return True
        class SpoofedString(str):
            def __eq__(self, other):
                return True
        for key in ("shop_id", "job_id", "media_asset_id"):
            for forged in (AlwaysEqual(), SpoofedString("foreign")):
                self.reader.extra = {key: forged}
                with self.subTest(key=key, forged=type(forged).__name__):
                    status, body, headers = self.call()
                    self.assertEqual((status, body), (503, b""))
                    self.assert_private_headers(headers)
        self.reader.extra = {}
        self.assertEqual(self.call()[0], 200)

    def test_spoofed_http_method_and_mime_cannot_bypass_primitive_checks(self):
        # Python equality overrides must not turn a foreign method into GET,
        # or an untrusted Content-Type into the approved PNG media type.
        class EqualToGet:
            def __eq__(self, other):
                return other == "GET"
        class EqualToPng:
            def __eq__(self, other):
                return other == "image/png"
        class SpoofedMethod(str):
            def __eq__(self, other):
                return True
        for forged in (EqualToGet(), SpoofedMethod("POST")):
            with self.subTest(method=type(forged).__name__):
                status, body, headers = self.call(method=forged)
                self.assertEqual((status, body), (405, b""))
                self.assertEqual(headers["Allow"], "GET")
        self.assertEqual(self.reader.calls, [])
        for forged in (EqualToPng(),):
            self.reader.extra = {"mime_type": forged}
            status, body, headers = self.call()
            self.assertEqual((status, body), (503, b""))
            self.assert_private_headers(headers)
        self.reader.extra = {}
        self.assertEqual(self.call()[0], 200)

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

    def test_palette_rules_fail_closed_even_with_matching_receipt_sha(self):
        # Synthetic PNGs: the fake reader recomputes SHA for every variant.
        original=self.reader.png
        def chunk(kind,payload):
            return (len(payload).to_bytes(4,"big")+kind+payload+
                    (crc32(kind+payload)&0xffffffff).to_bytes(4,"big"))
        rgb_ihdr=original[:33]
        rgb_rest=original[33:]
        # Truecolor may carry a valid optional palette.
        valid_rgb=rgb_ihdr+chunk(b"PLTE",b"\x00\x11\x22")+rgb_rest
        self.reader.png=valid_rgb
        self.assertEqual(self.call()[0],200)

        indexed=BytesIO()
        palette_image=Image.new("P",(320,400),0)
        palette_image.putpalette([0,17,34]*256)
        palette_image.save(indexed,format="PNG")
        indexed_png=indexed.getvalue()
        self.assertIn(b"PLTE",indexed_png)
        self.reader.png=indexed_png
        self.assertEqual(self.call()[0],200)
        palette_offset=indexed_png.index(b"PLTE")-4
        palette_length=int.from_bytes(indexed_png[palette_offset:palette_offset+4],"big")
        palette_end=palette_offset+12+palette_length
        # Indexed PNG must have a palette, even if IDAT and SHA are valid.
        missing_palette=indexed_png[:palette_offset]+indexed_png[palette_end:]

        gray=BytesIO()
        Image.new("L",(320,400),128).save(gray,format="PNG")
        gray_png=gray.getvalue()
        for forged in (
            rgb_ihdr+chunk(b"PLTE",b"")+rgb_rest,
            rgb_ihdr+chunk(b"PLTE",b"\x00\x11")+rgb_rest,
            rgb_ihdr+chunk(b"PLTE",b"\x00\x11\x22"*257)+rgb_rest,
            gray_png[:33]+chunk(b"PLTE",b"\x00\x11\x22")+gray_png[33:],
            missing_palette,
        ):
            self.reader.png=forged
            with self.subTest(sha=sha256(forged).hexdigest()):
                status,body,headers=self.call()
                self.assertEqual(status,503)
                self.assertEqual(body,b"")
                self.assert_private_headers(headers)
        self.reader.png=original
        self.assertEqual(self.call()[0],200)

    def test_crc_valid_ancillary_metadata_never_leaks_from_private_http(self):
        # Defense in depth: a compromised rights reader may return PNG bytes
        # with a valid digest but embedded private EXIF/text/profile metadata.
        original = self.reader.png
        def chunk(kind, payload):
            return (len(payload).to_bytes(4, "big") + kind + payload +
                    (crc32(kind + payload) & 0xffffffff).to_bytes(4, "big"))
        for kind, payload in (
            (b"tEXt", b"Comment\\x00synthetic-private-value"),
            (b"zTXt", b"Comment\\x00\\x00compressed"),
            (b"iTXt", b"Comment\\x00\\x00\\x00\\x00\\x00private"),
            (b"eXIf", b"synthetic-exif"),
            (b"iCCP", b"Profile\\x00\\x00synthetic"),
            (b"tIME", bytes((26, 1, 1, 0, 0, 0, 0))),
        ):
            self.reader.png = original[:33] + chunk(kind, payload) + original[33:]
            with self.subTest(kind=kind):
                status, body, headers = self.call()
                self.assertEqual((status, body), (503, b""))
                self.assert_private_headers(headers)
        self.reader.png = original
        self.assertEqual(self.call()[0], 200)

    def test_empty_idat_only_png_is_rejected_despite_valid_crc_and_sha(self):
        # An untrusted reader can forge a self-consistent receipt for a PNG
        # containing only empty IDAT chunks. No private bytes may be returned.
        original = self.reader.png
        def chunk(kind, payload):
            return (len(payload).to_bytes(4, "big") + kind + payload +
                    (crc32(kind + payload) & 0xffffffff).to_bytes(4, "big"))
        ihdr = original[:33]
        iend = original[-12:]
        for count in (1, 2, 10):
            forged = ihdr + chunk(b"IDAT", b"") * count + iend
            self.reader.png = forged
            with self.subTest(empty_chunks=count):
                status, body, headers = self.call()
                self.assertEqual((status, body), (503, b""))
                self.assert_private_headers(headers)
        # A zero-length IDAT chunk alongside actual image data remains valid.
        self.reader.png = ihdr + chunk(b"IDAT", b"") + original[33:]
        self.assertEqual(self.call()[0], 200)
        self.reader.png = original
        self.assertEqual(self.call()[0], 200)

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
