"""Feature3 saved-model handoff: synthetic identities and no paid inference."""
from pathlib import Path
import sys
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'poster-engine'))
from model_library_v2 import ModelLibraryDenied
from model_reference_v2 import (
    prepare_private_model_reference, reference_can_reuse_cached_result,
)

MODEL_SHA = 'a' * 64
GARMENT_SHA = 'b' * 64


class ModelReferenceTests(unittest.TestCase):
    def setUp(self):
        self.shop = str(uuid4())
        self.other = str(uuid4())
        self.model_id = str(uuid4())
        self.version = 1
        self.authorized = True
        self.calls = []
        self.model = {
            'schema': 'retailgrowth.model-library.v1',
            'model_id': self.model_id, 'owner_shop_id': self.shop,
            'status': 'APPROVED', 'scope': 'shop',
            'synthetic_adult': True, 'image_sha256': MODEL_SHA,
            'storage_key': f'{self.shop}/model-library/{self.model_id}/{MODEL_SHA}.png',
            'license_id': 'CC-BY-4.0', 'attribution': 'synthetic test — CC BY 4.0',
            'approved_uses': ['poster', 'try_on', 'video_reference'],
        }

    def grant(self, shop, model_id, usage, image_sha):
        self.calls.append((shop, model_id, usage, image_sha))
        return {'authorized': self.authorized, 'rights_revision': self.version}

    def prepare(self, **kwargs):
        fields = dict(model=self.model, requesting_shop_id=self.shop,
                      usage='poster', authorize_reference=self.grant)
        fields.update(kwargs)
        return prepare_private_model_reference(**fields)

    def test_same_private_model_reused_across_features_no_model_generation(self):
        poster = self.prepare()
        try_on = self.prepare(usage='try_on', garment_image_sha256=GARMENT_SHA)
        video = self.prepare(usage='video_reference', render_profile='feature5-i2v-v1')
        for receipt, purpose in [(poster, 'poster'), (try_on, 'try_on'),
                                 (video, 'video_reference')]:
            self.assertEqual(receipt['usage'], purpose)
            self.assertEqual(receipt['rights_revision'], 1)
            self.assertEqual(receipt['model_id'], self.model_id)
            self.assertFalse(receipt['generation_executed'])
            self.assertFalse(receipt['gpu_spend_authorized'])
            self.assertTrue(receipt['media_access_requires_current_rights'])
            self.assertTrue(receipt['private_storage_key'].startswith(self.shop + '/'))
        self.assertEqual(len({poster['cache_fingerprint'], try_on['cache_fingerprint'],
                              video['cache_fingerprint']}), 3)
        self.assertEqual(poster['cache_fingerprint'], self.prepare()['cache_fingerprint'])

    def test_shop_revocation_and_wrong_tenant_denied_every_time(self):
        with self.assertRaisesRegex(ModelLibraryDenied, 'Another shop'):
            self.prepare(requesting_shop_id=self.other)
        self.authorized = False
        with self.assertRaisesRegex(ModelLibraryDenied, 'rights'):
            self.prepare()
        self.model['status'] = 'PENDING_REVIEW'
        with self.assertRaisesRegex(ModelLibraryDenied, 'unreviewed'):
            self.prepare()

    def test_shared_model_always_shop_fences_cache_and_rights(self):
        self.model['scope'] = 'platform'
        self.model['storage_key'] = f'{self.shop}/model-library/platform/{self.model_id}/{MODEL_SHA}.png'
        a = self.prepare()
        b = self.prepare(requesting_shop_id=self.other)
        self.assertNotEqual(a['cache_fingerprint'], b['cache_fingerprint'])
        self.assertEqual(self.calls[-1][0], self.other)

    def test_rights_version_and_garment_and_pose_invalidate_reuse(self):
        before = self.prepare(usage='try_on', garment_image_sha256=GARMENT_SHA)
        self.assertTrue(reference_can_reuse_cached_result(
            receipt=before, previous_fingerprint=before['cache_fingerprint'],
            media_still_authorized=lambda *_: True))
        self.assertFalse(reference_can_reuse_cached_result(
            receipt=before, previous_fingerprint=before['cache_fingerprint'],
            media_still_authorized=lambda *_: False))
        self.version = 2
        after = self.prepare(usage='try_on', garment_image_sha256=GARMENT_SHA)
        self.assertNotEqual(before['cache_fingerprint'], after['cache_fingerprint'])
        self.assertFalse(reference_can_reuse_cached_result(
            receipt=after, previous_fingerprint=before['cache_fingerprint'],
            media_still_authorized=lambda *_: True))
        other_pose = self.prepare(usage='try_on', garment_image_sha256=GARMENT_SHA,
                                  pose='three_quarter')
        self.assertNotEqual(other_pose['cache_fingerprint'], after['cache_fingerprint'])
        other_garment = self.prepare(usage='try_on', garment_image_sha256='c'*64)
        self.assertNotEqual(other_garment['cache_fingerprint'], after['cache_fingerprint'])

    def test_untrusted_false_or_invalid_authorizer_responses_deny(self):
        for grant in ({'authorized': True, 'rights_revision': True},
                      {'authorized': True, 'rights_revision': 0},
                      {'authorized': True, 'rights_revision': '1'},
                      {'authorized': False, 'rights_revision': 1},
                      {'authorized': True, 'rights_revision': -4},
                      None):
            with self.subTest(grant=grant):
                with self.assertRaisesRegex(ModelLibraryDenied, 'rights'):
                    self.prepare(authorize_reference=lambda *_: grant)

    def test_garment_and_profile_and_cache_inputs_are_strict(self):
        invalid = [
            {'usage': 'try_on'}, {'usage': 'poster', 'garment_image_sha256': GARMENT_SHA},
            {'usage': 'video_reference', 'garment_image_sha256': GARMENT_SHA},
            {'usage': 'try_on', 'garment_image_sha256': 'http://untrusted.test/a'},
            {'pose': '../../private'}, {'render_profile': 'expensive GPU mode'},
        ]
        for item in invalid:
            with self.subTest(item=item):
                with self.assertRaises(ModelLibraryDenied):
                    self.prepare(**item)
        with self.assertRaises(ModelLibraryDenied):
            reference_can_reuse_cached_result(
                receipt={'schema': 'not-a-receipt'}, previous_fingerprint='a'*64,
                media_still_authorized=lambda *_: True)

if __name__ == '__main__':
    unittest.main()
