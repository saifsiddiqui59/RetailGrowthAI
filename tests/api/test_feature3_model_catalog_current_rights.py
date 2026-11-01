"""F3-12 JWT-scoped backend approved-model catalog; offline fake RLS only.

These fixtures do NOT constitute approved synthetic likeness, per-image license,
actual signed customer, hosted DB migration, or private preview delivery.
"""
from pathlib import Path
import sys
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "azure-functions" / "campaign-api"))
from feature3_v2_store import Feature3V2Store


class CurrentModelCatalogTests(unittest.TestCase):
    def setUp(self):
        self.shop = str(uuid4())
        self.foreign = str(uuid4())
        self.model = str(uuid4())
        self.asset = str(uuid4())
        self.row = {
            "model_id":self.model, "owner_shop_id":self.shop,
            "media_asset_id":self.asset, "scope":"shop",
            "status":"APPROVED", "source_kind":"retailer_licensed",
            "label":" Approved adult model ", "image_sha256":"a"*64,
            "license_id":"REVIEWED-COMMERCIAL", "rights_verified":True,
            "synthetic_adult":True, "attribution":"Owner reviewed offline",
            "approved_uses":["poster","video_reference"],
        }
        self.rows=[self.row]
        self.auth_calls=[]
        self.query=[]
        self.authorized=True
        self.store=Feature3V2Store("https://fixture.supabase.co",
                                    "sb_publishable_OFFLINE_ONLY")
        def request(token,resource,*,query=None,body=None):
            self.query.append((token,resource,query,body))
            return self.rows
        self.store._request=request
        parent=self
        class Tenant:
            def assets(self,token,shop,ids):
                parent.auth_calls.append((token,shop,ids))
                return parent.authorized
        self.tenant=Tenant()

    def list(self):
        return self.store.list_models("fictional-signed-jwt",self.shop,self.tenant)

    def test_verified_shop_model_only_after_distinct_jwt_media_read(self):
        models=self.list()
        self.assertEqual(len(models),1)
        self.assertEqual(models[0]["model_id"],self.model)
        self.assertEqual(models[0]["media_asset_id"],self.asset)
        self.assertEqual(models[0]["approved_uses"],["poster"])
        self.assertEqual(models[0]["label"],"Approved adult model")
        self.assertTrue(models[0]["synthetic_adult"])
        self.assertEqual(self.auth_calls,[(
            "fictional-signed-jwt",self.shop,[self.asset])])
        self.assertIn("synthetic_adult",self.query[0][2]["select"])
        self.assertNotIn("storage_key",models[0])
        self.assertNotIn("signed_url",models[0])
        self.authorized=False
        self.assertEqual(self.list(),[])

    def test_bad_approval_or_foreign_source_never_reaches_private_media_reader(self):
        bad=[
            {"owner_shop_id":self.foreign},
            {"scope":"platform"},
            {"status":"PENDING_REVIEW"},
            {"rights_verified":False},
            {"rights_verified":1},
            {"synthetic_adult":False},
            {"synthetic_adult":1},
            {"synthetic_adult":None},
            {"source_kind":"unreviewed"},
            {"source_kind":[]},
            {"approved_uses":"poster"},
            {"approved_uses":["poster","admin"]},
            {"approved_uses":["poster","poster"]},
            {"approved_uses":["poster",None]},
            {"approved_uses":["video_reference"]},
            {"approved_uses":[]},
            {"approved_uses":{"poster":True}},
            {"license_id":"CODE_LICENSE_NOT_IMAGE_LICENSE"},
            {"license_id":[]},
            {"image_sha256":"invalid"},
            {"image_sha256":None},
            {"label":"  "},
            {"label":None},
            {"attribution":"x"*201},
            {"attribution":"danger\nlogged"},
            {"license_id":"CC-BY-4.0","attribution":"   "},
            {"license_id":"CC-BY-4.0","attribution":True},
            {"media_asset_id":"not-a-uuid"},
            {"model_id":"not-a-uuid"},
        ]
        for mutation in bad:
            self.rows=[{**self.row,**mutation}]
            self.auth_calls.clear()
            with self.subTest(mutation=repr(mutation)):
                self.assertEqual(self.list(),[])
            self.assertEqual(self.auth_calls,[])

    def test_forged_truthy_media_receipt_cannot_grant_catalog_read(self):
        for value in (1, {"authorized":True}, ["some-media"]):
            with self.subTest(value=repr(value)):
                self.authorized=value
                self.assertEqual(self.list(),[])
                self.assertEqual(len(self.auth_calls),1)
                self.auth_calls.clear()

    def test_invalid_rows_and_duplicate_model_id_do_not_block_valid_selection(self):
        extra={**self.row,"model_id":str(uuid4()),"media_asset_id":str(uuid4()),
               "approved_uses":["poster"],"license_id":"CC0-1.0"}
        self.rows=[None,False,[],{"scope":"shop"},self.row,self.row,extra]
        result=self.list()
        self.assertEqual(len(result),2)
        self.assertEqual([m["model_id"] for m in result],
                         [self.model,extra["model_id"]])
        self.assertEqual(len(self.auth_calls),2)
        self.assertEqual(len(self.query),1)

    def test_catalog_limit_is_not_reinterpreted_as_success(self):
        self.rows=[self.row]*51
        with self.assertRaisesRegex(Exception,"excessive model catalog"):
            self.list()
        self.assertEqual(self.auth_calls,[])


if __name__=="__main__":
    unittest.main()
