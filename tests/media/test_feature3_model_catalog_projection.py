"""Private catalog adapter tests with synthetic authoritative callbacks only."""
from pathlib import Path
import sys
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
from model_catalog_projection_v2 import approved_model_picker_items
from model_library_v2 import ModelLibraryDenied

SHA = 'd'*64


class ModelPickerTests(unittest.TestCase):
    def setUp(self):
        self.shop = str(uuid4())
        self.other = str(uuid4())
        self.id = str(uuid4())
        self.authorized = True
        self.image_allowed = True
        self.model = dict(
            schema="retailgrowth.model-library.v1", model_id=self.id,
            owner_shop_id=self.shop, scope="shop", status="APPROVED",
            synthetic_adult=True, image_sha256=SHA,
            storage_key=f"{self.shop}/model-library/{self.id}/{SHA}.png",
            license_id="CC-BY-4.0", attribution="Synthetic example © Test — CC BY 4.0",
            label="Reusable fashion reference", approved_uses=["poster", "video_reference"],
        )
        self.reads = []

    def use(self, shop, model_id, purpose, image_sha):
        self.reads.append((shop, model_id, purpose, image_sha))
        return self.authorized

    def private_media(self, shop, receipt):
        return {
            "authorized": self.image_allowed, "private": True,
            "requesting_shop_id": shop, "image_sha256": receipt['image_sha256'],
            "media_asset_id": "registered_shop_media_123",
        }

    def run_picker(self, models=None, **kwargs):
        arguments = dict(
            models=[self.model] if models is None else models,
            requesting_shop_id=self.shop,
            authorize_model_use=self.use, resolve_private_media=self.private_media,
        )
        arguments.update(kwargs)
        return approved_model_picker_items(**arguments)

    def test_project_only_approved_registered_private_previews_no_blob_keys(self):
        rows = self.run_picker()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['media_asset_id'], 'registered_shop_media_123')
        self.assertEqual(rows[0]['image_sha256'], SHA)
        self.assertEqual(rows[0]['approved_uses'], ['poster'])
        self.assertNotIn('storage_key', rows[0])
        self.assertNotIn('source_uri', rows[0])
        self.assertNotIn('signed_url', rows[0])
        self.assertEqual(self.reads[0][2], 'poster')

    def test_deny_cross_shop_and_unapproved_and_revoked(self):
        self.assertEqual(self.run_picker(requesting_shop_id=self.other), [])
        for status in ["PENDING_REVIEW", "REVOKED", "REJECTED"]:
            self.assertEqual(self.run_picker(models=[{**self.model, "status": status}]), [])
        self.authorized = False
        self.assertEqual(self.run_picker(), [])

    def test_shared_catalog_reuses_same_bytes_but_requires_requester_permission(self):
        shared = {**self.model, 'scope': 'platform',
                  'storage_key': f'{self.shop}/model-library/platform/{self.id}/{SHA}.png'}
        entries = self.run_picker(models=[shared], requesting_shop_id=self.other)
        self.assertEqual(len(entries), 1)
        self.assertEqual(self.reads[-1][0], self.other)
        self.image_allowed = False
        self.assertEqual(self.run_picker(models=[shared], requesting_shop_id=self.other), [])

    def test_bad_private_media_receipt_never_produces_selectable_model(self):
        invalid = (
            {'authorized': True, 'private': False, 'requesting_shop_id': self.shop,
             'image_sha256': SHA, 'media_asset_id': 'registered'},
            {'authorized': True, 'private': True, 'requesting_shop_id': self.other,
             'image_sha256': SHA, 'media_asset_id': 'registered'},
            {'authorized': True, 'private': True, 'requesting_shop_id': self.shop,
             'image_sha256': '0'*64, 'media_asset_id': 'registered'},
            {'authorized': True, 'private': True, 'requesting_shop_id': self.shop,
             'image_sha256': SHA, 'media_asset_id': 'https://evil.example'},
        )
        for receipt in invalid:
            with self.subTest(receipt=receipt):
                self.assertEqual(self.run_picker(resolve_private_media=lambda *_:receipt), [])

    def test_server_rejects_forged_use_or_license_before_private_media_lookup(self):
        bad_rows=(
            {"license_id":"UNKNOWN"},
            {"license_id":None},
            {"license_id":[]},
            {"approved_uses":["poster","admin"]},
            {"approved_uses":["poster","poster"]},
            {"approved_uses":["poster",None]},
            {"approved_uses":{"poster":True}},
            {"license_id":"CC-BY-4.0","attribution":42},
            {"license_id":"CC-BY-4.0","attribution":"  "},
        )
        for mutation in bad_rows:
            self.setUp()
            private_reads=[]
            def private(shop,model):
                private_reads.append((shop,model))
                return self.private_media(shop,model)
            with self.subTest(mutation=repr(mutation)):
                self.assertEqual(self.run_picker(
                    models=[{**self.model,**mutation}],
                    resolve_private_media=private),[])
            self.assertEqual(private_reads,[])
            self.assertEqual(self.reads,[])

    def test_malformed_catalog_rows_do_not_break_valid_shop_model(self):
        self.setUp()
        malformed=[None,False,123,[],{"schema":"invalid"},self.model]
        rows=self.run_picker(models=malformed)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["model_id"],self.id)
        self.assertEqual(self.reads,[(self.shop,self.id,"poster",SHA)])

    def test_duplicate_rows_and_item_cap(self):
        self.assertEqual(len(self.run_picker(models=[self.model, self.model])), 1)
        with self.assertRaises(ModelLibraryDenied):
            self.run_picker(max_items=0)
        with self.assertRaises(ModelLibraryDenied):
            self.run_picker(max_items=True)
        with self.assertRaises(ModelLibraryDenied):
            self.run_picker(models="browser supplied rows")

if __name__ == '__main__':
    unittest.main()
