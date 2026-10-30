"""Feature7 review timeline timing, legal media ID and audio preservation tests."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from test_feature7_semantic import sample

ROOT=Path(__file__).resolve().parents[2]
JS="""
import fs from 'node:fs';
import {proposeUploadedFootageEdits} from './video-engine/feature7/autobroll_semantics.mjs';
import {buildReviewTimeline} from './video-engine/feature7/review_timeline.mjs';
const data=JSON.parse(fs.readFileSync(0,'utf8'));
const proposal=proposeUploadedFootageEdits(data);
if(data.modify==='foreign_caption')proposal.captions_advisory[0].clipId='other-asset';
if(data.modify==='caption_overflow')proposal.captions_advisory[0].timeline_end_ms=99000;
if(data.modify==='caption_html')proposal.captions_advisory[0].words[0].text='<script>';
if(data.modify==='caption_bidi')proposal.captions_advisory[0].words[0].text='Sale\\u202e!'; 
if(data.modify==='caption_c1')proposal.captions_advisory[0].words[0].text='Sale\\u0085'; 
if(data.modify==='caption_unpaired_surrogate')proposal.captions_advisory[0].words[0].text='Sale\\ud800';
if(data.modify==='outside_broll')proposal.broll_advisory[0].timeline_end_ms=99000;
if(data.modify==='fake_media')proposal.broll_advisory[0].asset_id='unknown';
const grants=data.grants.map(g=>({...g}));
if(data.modify==='revoked_broll')grants[1].active=false;
if(data.modify==='foreign_shop')grants[0].shop_id='other';
const output=buildReviewTimeline({proposal,draft:data.draft,
 approved_asset_grants:grants});
process.stdout.write(JSON.stringify(output));
"""

@unittest.skipUnless(shutil.which('node'),'Node required')
class ReviewTimelineTests(unittest.TestCase):
    def go(self,data):
        return subprocess.run(['node','--input-type=module','-e',JS],
          input=json.dumps(data),cwd=ROOT,text=True,capture_output=True,timeout=10)

    def test_timing_is_contiguous_and_review_only(self):
        result=self.go(sample())
        self.assertEqual(result.returncode,0,result.stderr)
        x=json.loads(result.stdout)
        self.assertEqual(x['duration_ms'],15000)
        self.assertEqual(x['scenes'][0]['start_ms'],0)
        self.assertEqual(x['scenes'][0]['end_ms'],15000)
        self.assertTrue(x['original_audio_preserved'])
        self.assertFalse(x['renderable'])
        self.assertFalse(x['approved'])
        self.assertGreater(len(x['captions']),0)
        self.assertEqual(len(x['broll']),1)
        self.assertEqual(x['broll'][0]['asset_id'],'owned-broll-a')
        self.assertTrue(all(not s['muted'] for s in x['scenes']))
        self.assertTrue(all(not c['feature4_renderer_ready'] for c in x['captions']))
        self.assertTrue(all(not c['feature4_renderer_ready'] for c in x['broll']))

    def test_security_and_timing_edits_fail_closed(self):
        for mutation in ['foreign_caption','caption_overflow','caption_html',
          'caption_bidi','caption_c1','caption_unpaired_surrogate',
          'outside_broll','fake_media','revoked_broll','foreign_shop']:
            with self.subTest(mutation=mutation):
                p=sample();p['modify']=mutation
                bad=self.go(p)
                self.assertNotEqual(bad.returncode,0,bad.stdout)

    def test_deterministic_review_fingerprint(self):
        a=self.go(sample());b=self.go(sample())
        self.assertEqual(a.returncode,0,a.stderr)
        self.assertEqual(b.returncode,0,b.stderr)
        self.assertEqual(json.loads(a.stdout)['review_sha256'],
            json.loads(b.stdout)['review_sha256'])


if __name__=='__main__':unittest.main()
