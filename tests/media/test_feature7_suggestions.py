"""Offline Feature7 owner-only semantic ranking and B-roll guidance tests."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
JS="""
import fs from 'node:fs';
import {suggestRetakeSelections,suggestOwnedCutaways} from
 './video-engine/feature7/semantic_suggestions.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify({
  retakes:suggestRetakeSelections(p),
  cutaways:suggestOwnedCutaways(p)
}));
"""


def fixture():
    return {
      'shop_id':'shop-alpha',
      'footage':[
        {'shop_id':'shop-alpha','scene_index':0,'asset_id':'take-a',
         'words':[
           {'word':'Our','startMs':100,'endMs':300},
           {'word':'new','startMs':320,'endMs':500},
           {'word':'shirts.','startMs':550,'endMs':870}
         ]},
        {'shop_id':'shop-alpha','scene_index':1,'asset_id':'take-b',
         'words':[
           {'word':'Our','startMs':100,'endMs':300},
           {'word':'new','startMs':320,'endMs':500},
           {'word':'shirts.','startMs':550,'endMs':870},
           {'word':'Available','startMs':900,'endMs':1200}
         ]},
      ],
      'words':[
         {'word':'Our','startMs':100,'endMs':300},
         {'word':'shirts','startMs':350,'endMs':650},
         {'word':'are','startMs':700,'endMs':900},
         {'word':'ready','startMs':920,'endMs':1200}
       ],
       'approved_assets':[
         {'shop_id':'shop-alpha','asset_id':'photo-shirts',
          'source':'retailer_upload','issued_by':'trusted_server',
          'rights_status':'APPROVED','active':True,'media_type':'image',
          'keywords':['shirts','cotton']}
       ],
       'max_cues':2
    }


@unittest.skipUnless(shutil.which('node'),'Node required')
class Feature7SemanticSuggestionsTests(unittest.TestCase):
    def go(self,doc):
        return subprocess.run(['node','--input-type=module','-e',JS],
            input=json.dumps(doc),text=True,capture_output=True,cwd=ROOT,timeout=10)

    def test_retake_and_owned_broll_are_review_only(self):
        run=self.go(fixture())
        self.assertEqual(run.returncode,0,run.stderr)
        data=json.loads(run.stdout)
        self.assertEqual(len(data['retakes']),1)
        retake=data['retakes'][0]
        self.assertEqual(retake['recommended_source_scene_index'],1)
        self.assertTrue(retake['human_review_required'])
        self.assertEqual(retake['discarded_scene_ids'],[])
        self.assertFalse(retake['output_executable_by_feature4'])
        self.assertEqual(len(data['cutaways']),1)
        self.assertEqual(data['cutaways'][0]['asset_id'],'photo-shirts')
        self.assertEqual(data['cutaways'][0]['startIdx'],1)
        self.assertTrue(data['cutaways'][0]['human_review_required'])

    def test_foreign_and_recalled_broll_rejected(self):
        for mutate in [
          lambda p:p['approved_assets'][0].update(shop_id='foreign'),
          lambda p:p['approved_assets'][0].update(active=False),
          lambda p:p['approved_assets'][0].update(rights_status='REVOKED'),
          lambda p:p['approved_assets'][0].update(issued_by='browser'),
          lambda p:p['approved_assets'][0].update(source='pexels'),
          lambda p:p['footage'][0].update(shop_id='foreign'),
        ]:
            with self.subTest(mutate=mutate):
                doc=fixture()
                mutate(doc)
                self.assertNotEqual(self.go(doc).returncode,0)

    def test_no_match_keeps_cutaways_empty(self):
        data=fixture()
        data['approved_assets'][0]['keywords']=['microwave']
        result=self.go(data)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['cutaways'],[])


if __name__=='__main__':
    unittest.main()
