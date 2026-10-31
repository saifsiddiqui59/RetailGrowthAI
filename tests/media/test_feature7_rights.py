"""Signed real-private-video rights + ASR provenance gate, isolated source tests.

Current-media callback is an authorized server FIXTURE, not real JWT/RLS or
hosted Supabase. Real ffprobe/FFmpeg validate exact privately staged MP4 bytes.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
JS=r"""
import fs from 'node:fs';
import {normalizeWhisperx} from './video-engine/feature7/transcript_adapter.mjs';
import {sealTranscriptEvidence} from './video-engine/feature7/transcript_evidence.mjs';
import {sealMediaRightsEvidence} from './video-engine/feature7/media_rights_evidence.mjs';
import {prepareAuthoritativePrivateReview} from './video-engine/feature7/authoritative_private_review.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const item=p.media[0];
const asrKey=Buffer.alloc(32,0xaa);
const rightsKey=Buffer.alloc(32,0xbb);
const normalized=normalizeWhisperx({
  asset_id:item.asset_id,shop_id:p.shop_id,source_sha256:item.expected_sha256,
  source_duration_seconds:16,transcript:item.whisperx_json
});
item.asr_evidence=sealTranscriptEvidence({data:{
  shop_id:p.shop_id,asset_id:item.asset_id,job_id:p.job_id,
  source_sha256:item.expected_sha256,
  transcript_sha256:normalized.transcript_sha256,
  model_id:'supplied_reference_test',
  issued_at_ms:p.now_ms,expires_at_ms:p.now_ms+60000
},key:asrKey,now_ms:p.now_ms});
item.rights_evidence=sealMediaRightsEvidence({data:{
  shop_id:p.shop_id,asset_id:item.asset_id,job_id:p.job_id,
  source_sha256:item.expected_sha256,
  rights_revision:p.current.rights_revision,
  media_type:'video',mime_type:'video/mp4',relative_path:item.relative_path,
  issued_at_ms:p.now_ms,expires_at_ms:p.now_ms+60000
},key:rightsKey,now_ms:p.now_ms});
if(p.attack==='revoked')p.current.active=false;
if(p.attack==='foreign_shop')p.current.shop_id='foreign-shop';
if(p.attack==='rights_revision')p.current.rights_revision='revision-2';
if(p.attack==='bad_source')item.expected_sha256='f'.repeat(64);
if(p.attack==='different_job')p.job_id='another-job';
if(p.attack==='expired')p.now_ms+=61000;
if(p.attack==='forged_mac')item.rights_evidence.mac='0'.repeat(64);
if(p.attack==='fake_grant')item.grant={
  source:'retailer_upload',rights_status:'APPROVED',
  shop_id:p.shop_id,asset_id:item.asset_id,issued_by:'trusted_server',
  active:true,sha256:item.expected_sha256,relative_path:item.relative_path
};
if(p.attack==='broll_revoked')p.current_broll.active=false;
if(p.attack==='broll_foreign_shop')p.current_broll.shop_id='foreign-shop';
if(p.attack==='broll_changed_sha')p.current_broll.sha256='f'.repeat(64);
if(p.attack==='broll_changed_revision')p.current_broll.rights_revision='revision-2';
if(p.attack==='broll_bad_mime')p.current_broll.mime_type='application/octet-stream';
if(p.attack==='broll_forged_issued_by')p.broll_grants[0].issued_by='trusted_server';
const r=prepareAuthoritativePrivateReview({
  ...p,asr_key:asrKey,rights_key:rightsKey,
  getCurrentApprovedBroll:p.no_broll_loader ? undefined : ({shop_id,asset_id})=>{
    p.broll_rights_checks=(p.broll_rights_checks??0)+1;
    if(p.attack==='broll_missing_registry' ||
      shop_id!==p.shop_id || asset_id!==p.current_broll?.asset_id)
      return null;
    if(p.attack==='broll_revoked_during_review' &&
      p.broll_rights_checks>1)
      return {...p.current_broll,active:false};
    if(p.attack==='broll_revision_during_review' &&
      p.broll_rights_checks>1)
      return {...p.current_broll,rights_revision:'revision-2'};
    if(p.attack==='broll_keywords_during_review' &&
      p.broll_rights_checks>1)
      return {...p.current_broll,keywords:['changed']};
    return p.current_broll;
  },
  getCurrentApprovedVideo:()=>{
    p.rights_checks=(p.rights_checks??0)+1;
    if(p.attack==='revoked_during_review' && p.rights_checks>1)
      return {...p.current,active:false};
    return p.current;
  }
});
process.stdout.write(JSON.stringify(r));
"""

@unittest.skipUnless(all(shutil.which(x) for x in ("node","ffmpeg","ffprobe")),
  "Node and FFmpeg required")
class Feature7AuthoritativeRightsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='f7-rights-test-')
        cls.root=Path(cls.temp.name)
        cls.clip=cls.root/'private.mp4'
        video=subprocess.run(['ffmpeg','-v','error','-y',
           '-f','lavfi','-i','color=c=blue:s=160x288:r=10:d=16',
           '-f','lavfi','-i','sine=frequency=440:sample_rate=16000:duration=16',
           '-c:v','libx264','-preset','ultrafast','-c:a','aac',
           '-b:a','64k','-t','16',str(cls.clip)],
           capture_output=True,text=True,timeout=90)
        if video.returncode:raise RuntimeError(video.stderr)
        cls.sha=hashlib.sha256(cls.clip.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    @classmethod
    def payload(cls):
        current={'shop_id':'shop-demo','asset_id':'asset-demo',
           'source':'retailer_upload','rights_status':'APPROVED',
           'active':True,'media_type':'video','mime_type':'video/mp4',
           'relative_path':cls.clip.name,'sha256':cls.sha,'has_audio':True,
           'rights_revision':'revision-1'}
        return {'shop_id':'shop-demo','campaign_id':'campaign-demo',
          'job_id':'job-demo','root':str(cls.root),
          'now_ms':1700000000000,'current':current,
          'draft':{'shop_id':'shop-demo','campaign_id':'campaign-demo',
            'duration_seconds':15,'scenes':[{
              'asset_id':'asset-demo','asset_type':'video',
              'source_feature':'retailer','start':0,'duration':15
            }]},
          'media':[{'scene_index':0,'asset_id':'asset-demo',
            'relative_path':cls.clip.name,'expected_sha256':cls.sha,
            'whisperx_json':{'segments':[{'words':[
              {'word':'Hello','start':0.2,'end':0.4},
              {'word':'shop.','start':0.5,'end':0.8}
            ]}]}}],
          'broll_grants':[]}

    @classmethod
    def broll_payload(cls):
        p=cls.payload()
        sha='a'*64
        p['current_broll']={
            'shop_id':'shop-demo','asset_id':'cutaway-demo',
            'source':'retailer_upload','rights_status':'APPROVED',
            'active':True,'media_type':'image','mime_type':'image/png',
            'sha256':sha,'rights_revision':'broll-rev-1',
            'keywords':['hello']
        }
        # Untrusted request supplies an ID and expected registry generation,
        # not a permission or trusted_server marker.
        p['broll_grants']=[{
            'asset_id':'cutaway-demo','expected_sha256':sha,
            'rights_revision':'broll-rev-1'
        }]
        p['media'][0]['broll_candidates']=[{
            'startIdx':0,'endIdx':0,'mode':'inset','assetId':'cutaway-demo'
        }]
        return p

    def js(self,p):
        return subprocess.run(['node','--input-type=module','-e',JS],
          input=json.dumps(p),cwd=ROOT,capture_output=True,text=True,timeout=60)

    def test_approved_current_registry_rights_plus_asr_and_bytes(self):
        good=self.js(self.payload())
        self.assertEqual(good.returncode,0,good.stderr[-1000:])
        data=json.loads(good.stdout)
        self.assertTrue(data['media_rights_evidence_verified'])
        self.assertTrue(data['transcript_evidence_verified'])
        self.assertTrue(data['rights_rechecked_against_authoritative_registry'])
        self.assertEqual(data['media_evidence'][0]['source_sha256'],self.sha)
        self.assertFalse(data['approved'])
        self.assertFalse(data['renderable'])
        self.assertTrue(data['media_evidence'][0]['source_duration_seconds']>=15)

    def test_revoked_foreign_stale_rights_spoofing_and_expiry_fail(self):
        for attack in ('revoked','foreign_shop','rights_revision','bad_source',
          'different_job','expired','forged_mac','revoked_during_review'):
            with self.subTest(attack=attack):
                p=self.payload();p['attack']=attack
                r=self.js(p)
                self.assertNotEqual(r.returncode,0,r.stdout)

    def test_forged_plain_grant_cannot_override_revoked_registry(self):
        p=self.payload();p['attack']='revoked'
        p['media'][0]['grant']={
          'issued_by':'trusted_server','active':True,
          'rights_status':'APPROVED','shop_id':'shop-demo',
          'asset_id':'asset-demo'}
        r=self.js(p)
        self.assertNotEqual(r.returncode,0,r.stdout)

    def test_broll_resolved_from_current_registry_not_submitted_grant(self):
        p=self.broll_payload()
        # Caller-controlled display/permission properties are ignored.
        p['broll_grants'][0].update({
            'issued_by':'trusted_server','active':False,
            'rights_status':'REVOKED','shop_id':'foreign-shop',
            'keywords':['forged']
        })
        r=self.js(p)
        self.assertEqual(r.returncode,0,r.stderr[-1000:])
        data=json.loads(r.stdout)
        self.assertEqual(data['broll_advisory'][0]['asset_id'],'cutaway-demo')
        self.assertEqual(data['owned_cutaways_advisory'][0]['asset_id'],
                         'cutaway-demo')
        self.assertFalse(data['approved'])
        self.assertFalse(data['renderable'])

    def test_broll_forged_revoked_foreign_stale_and_drift_fail_closed(self):
        for attack in (
            'broll_missing_registry','broll_revoked','broll_foreign_shop',
            'broll_changed_sha','broll_changed_revision','broll_bad_mime',
            'broll_revoked_during_review','broll_revision_during_review',
            'broll_keywords_during_review','broll_forged_issued_by'
        ):
            with self.subTest(attack=attack):
                p=self.broll_payload()
                p['attack']=attack
                if attack=='broll_forged_issued_by':
                    p['no_broll_loader']=True
                r=self.js(p)
                self.assertNotEqual(r.returncode,0,r.stdout)

    def test_broll_missing_or_malformed_reference_fails_closed(self):
        for change in ('missing_sha','wrong_revision','duplicate'):
            with self.subTest(change=change):
                p=self.broll_payload()
                if change=='missing_sha':
                    del p['broll_grants'][0]['expected_sha256']
                elif change=='wrong_revision':
                    p['broll_grants'][0]['rights_revision']='stale-rev'
                else:
                    p['broll_grants'].append(dict(p['broll_grants'][0]))
                r=self.js(p)
                self.assertNotEqual(r.returncode,0,r.stdout)

if __name__=='__main__':unittest.main()
