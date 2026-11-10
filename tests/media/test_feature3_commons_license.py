"""The official-source adapter is tested offline; live CC0 file is opt-in."""
import hashlib
from io import BytesIO
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import Mock
from uuid import uuid4

from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"poster-engine"))
from feature3_commons_license_v1 import (
    verify_commons_cc0_garment, LicenseProofDenied
)

class FakeResponse:
    def __init__(self, url, data, content_type="application/json"):
        self._url=url;self.data=data
        self.headers={"Content-Type":content_type}
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def geturl(self):return self._url
    def read(self,size=-1):return self.data[:size]

class LicenseProofTests(unittest.TestCase):
    def setUp(self):
        self.shop,self.media=str(uuid4()),str(uuid4())
        out=BytesIO()
        Image.new("RGB",(512,768),(171,33,76)).save(out,"PNG")
        self.png=out.getvalue()
        self.title="File:Bengal mundari saree photos.png"
        self.info={"query":{"pages":[{"title":self.title,
            "imageinfo":[{"size":len(self.png),
                          "sha1":hashlib.sha1(self.png).hexdigest(),
                          "extmetadata":{
                             "LicenseShortName":{"value":"CC0 1.0"},
                             "LicenseUrl":{"value":"http://creativecommons.org/publicdomain/zero/1.0/deed.en"}}}]}]}}
        self.calls=[]
        def transport(req,timeout):
            self.calls.append(req.full_url)
            return FakeResponse(req.full_url,json.dumps(self.info).encode())
        self.transport=transport

    def verify(self,**changes):
        args=dict(shop_id=self.shop,media_asset_id=self.media,image_bytes=self.png,
                  commons_file_title=self.title,tenant_private_authorized=True,
                  transport=self.transport)
        args.update(changes)
        return verify_commons_cc0_garment(**args)

    def test_valid_exact_official_hash_and_cc0_remains_not_model_approval(self):
        r=self.verify()
        self.assertEqual(r["license"],"CC0-1.0")
        self.assertTrue(r["official_source_hash_matched"])
        self.assertEqual(r["image_sha256"],hashlib.sha256(self.png).hexdigest())
        self.assertEqual(r["dimensions"],[512,768])
        for prop in ("model_likeness_release_verified","retailer_product_ownership_verified",
                     "virtual_tryon_approved","gpu_authorized"):
            self.assertFalse(r[prop])
        self.assertTrue(self.calls[0].startswith("https://commons.wikimedia.org/w/api.php?"))
        self.assertEqual(len(self.calls),1)

    def test_wikimedia_imageinfo_base36_sha1(self):
        n=int(hashlib.sha1(self.png).hexdigest(),16)
        digits="0123456789abcdefghijklmnopqrstuvwxyz"
        text=""
        while n: text=digits[n%36]+text;n//=36
        self.info["query"]["pages"][0]["imageinfo"][0]["sha1"]=text
        self.assertTrue(self.verify()["official_source_hash_matched"])

    def test_retailer_claim_or_foreign_tenant_cannot_bypass_signed_private_access(self):
        for update in (dict(tenant_private_authorized=False),
                       dict(shop_id=str(uuid4()).upper()),
                       dict(image_bytes="not binary"),
                       dict(commons_file_title="File:../../evil.png"),
                       dict(commons_file_title="https://elsewhere.test/photo.png")):
            with self.subTest(update=update),self.assertRaises(LicenseProofDenied):
                self.verify(**update)
        self.assertEqual(self.calls,[])

    def test_independently_mismatched_image_cannot_obtain_license_proof(self):
        for change in ("size","sha1","LicenseShortName","LicenseUrl","title"):
            self.info={"query":{"pages":[{"title":self.title,
                "imageinfo":[{"size":len(self.png),
                 "sha1":hashlib.sha1(self.png).hexdigest(),
                 "extmetadata":{"LicenseShortName":{"value":"CC0 1.0"},
                    "LicenseUrl":{"value":"https://creativecommons.org/publicdomain/zero/1.0/"}}}]}]}}
            item=self.info["query"]["pages"][0]["imageinfo"][0]
            if change=="size": item["size"]=len(self.png)-1
            elif change=="sha1": item["sha1"]="a"*40
            elif change=="title": self.info["query"]["pages"][0]["title"]="File:Another photo.png"
            else: item["extmetadata"][change]["value"]="https://not-cc0.example/test"
            with self.subTest(change=change),self.assertRaises(LicenseProofDenied):
                self.verify()

    def test_redirect_unknown_content_type_and_unbounded_json_denied(self):
        for case in ("redirect","html","oversized"):
            def remote(req,timeout):
                if case=="redirect": return FakeResponse("https://third-party.example/redirect",b"{}")
                if case=="html": return FakeResponse(req.full_url,b"{}",content_type="text/html")
                return FakeResponse(req.full_url,b"a"*100000)
            with self.subTest(case=case),self.assertRaises(LicenseProofDenied):
                self.verify(transport=remote)

    def test_bogus_or_too_small_image_denied_without_network(self):
        for image in (b"not an image"*20,b"x"*99):
            with self.subTest(image=image),self.assertRaises(LicenseProofDenied):
                self.verify(image_bytes=image)
        self.assertEqual(self.calls,[])


if __name__=="__main__":
    unittest.main()
