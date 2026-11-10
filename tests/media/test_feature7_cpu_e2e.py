"""Feature7 independent CPU-only upload->review->approval handoff, no real model.

All grants, reviewer identities and word timings are explicitly TEST-ONLY
fixtures: this proves local components compose, NOT SaaS authentication, real
WhisperX inference, a deployed video editor, or customer-owned rights.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'video-engine'/'feature7'))
from review_journal import CurrentReviewContext, LocalReviewJournal, ReviewStateError

INTAKE=r"""
import fs from 'node:fs';
import {stagePrivateFootageCPU} from './video-engine/feature7/private_intake_cpu.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const o=stagePrivateFootageCPU({...p,
 getCurrentIntakeAuthorization:()=>({
  shop_id:p.shop_id,asset_id:p.asset_id,role:'EDITOR',
  active_membership:true,intake_authorized:true,
  video_rights_declared:true,max_bytes:32*1024*1024})});
process.stdout.write(JSON.stringify(o));
"""
REVIEW=r"""
import fs from 'node:fs';
import {feature7CpuOnlyEnv} from './video-engine/feature7/cpu_readiness.mjs';
import {preparePrivateReview} from './video-engine/feature7/private_review_pipeline.mjs';
import {createReviewSession,adjustTrimStart,proposeReviewDecision}
 from './video-engine/feature7/review_actions.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
feature7CpuOnlyEnv({FEATURE7_GPU_ENABLED:'0',FEATURE7_ALLOW_PAID_INFERENCE:'0'});
const result=preparePrivateReview(p);
let state=createReviewSession({draft:p.draft,proposal:result,
 media_evidence:result.media_evidence,
 reviewer_view:{shop_id:p.shop_id,campaign_id:p.campaign_id,
   reviewer_id:'fixture-editor',active_membership:true,role:'EDITOR',
   revision:0}});
state=adjustTrimStart(state,0,0.25);
const request=proposeReviewDecision(state,{
 action:'REQUEST_APPROVAL',confirmed:true});
process.stdout.write(JSON.stringify({
 proposal:result,request,review_only:true,gpu_started:false}));
"""
HANDOFF=r"""
import fs from 'node:fs';
import {sealHumanEditApproval,buildFeature4EditHandoff}
 from './video-engine/feature7/review_fence.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const key=Buffer.alloc(32,0x63);
const context={
 shop_id:p.shop_id,campaign_id:p.campaign_id,
 reviewer_id:'fixture-editor',role:'EDITOR',
 active_membership:true,video_rights_current:true,
 revision:1,source_snapshot_sha256:p.media_sha256
};
const signed=sealHumanEditApproval({
 proposal:p.proposal,draft:p.draft,context,
 approval_id:p.approval_id,canonical_draft_sha256:p.canonical_sha,
 key,now_ms:1700000000100});
const result=buildFeature4EditHandoff({
 proposal:p.proposal,draft:p.draft,context,
 receipt:signed,canonical_draft_sha256:p.canonical_sha,key,
 now_ms:1700000000200});
process.stdout.write(JSON.stringify(result));
"""

@unittest.skipUnless(all(shutil.which(x) for x in ("node","ffmpeg","ffprobe")),
                     "Requires Node, FFmpeg and ffprobe")
class Feature7CpuE2eTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='feature7-e2e-cpu-')
        cls.root=Path(cls.temp.name)
        cls.src=cls.root/'source-original.mp4'
        p=subprocess.run(['ffmpeg','-v','error','-y',
          '-f','lavfi','-i','color=c=purple:s=160x288:r=10:d=16',
          '-f','lavfi','-i','sine=frequency=440:sample_rate=16000:duration=16',
          '-t','16','-c:v','libx264','-preset','ultrafast',
          '-c:a','aac','-b:a','64k',str(cls.src)],
          capture_output=True,text=True,timeout=90)
        if p.returncode:raise RuntimeError(p.stderr)
        cls.private=cls.root/'private'
        cls.private.mkdir()
        cls.sha=hashlib.sha256(cls.src.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def node(self,script,p):
        return subprocess.run(['node','--input-type=module','-e',script],
            cwd=ROOT,input=json.dumps(p),text=True,capture_output=True,timeout=90)

    def test_full_offline_intake_human_review_single_use_and_f4_handoff(self):
        source={'source_path':str(self.src),'private_root':str(self.private),
          'shop_id':'demo-shop','asset_id':'demo-asset',
          'expected_sha256':self.sha}
        intake=self.node(INTAKE,source)
        self.assertEqual(intake.returncode,0,intake.stderr)
        staged=json.loads(intake.stdout)
        self.assertFalse(staged['approved'])
        self.assertFalse(staged['gpu_started'])
        draft={'shop_id':'demo-shop','campaign_id':'demo-campaign',
          'duration_seconds':15,
          'scenes':[{'asset_id':'demo-asset','asset_type':'video',
           'source_feature':'retailer','duration':15,'start':0}]}
        # Test-only simulated independently approved video and reference
        # word transcript, never produced by actual external ASR or DB.
        grant={'shop_id':'demo-shop','asset_id':'demo-asset',
          'issued_by':'trusted_server','source':'retailer_upload',
          'rights_status':'APPROVED','active':True,
          'media_type':'video','mime_type':'video/mp4',
          'sha256':self.sha,'relative_path':staged['relative_path'],
          'has_audio':True}
        p={'shop_id':'demo-shop','campaign_id':'demo-campaign',
          'root':str(self.private),'draft':draft,
          'media':[{'scene_index':0,'asset_id':'demo-asset',
            'grant':grant,'relative_path':staged['relative_path'],
            'expected_sha256':self.sha,
            'whisperx_json':{'segments':[{'words':[
              {'word':'Welcome','start':0.5,'end':0.8},
              {'word':'to','start':0.85,'end':1.0},
              {'word':'the','start':1.05,'end':1.2},
              {'word':'shop.','start':1.3,'end':1.5}
            ]}]}}],
          'broll_grants':[]}
        review=self.node(REVIEW,p)
        self.assertEqual(review.returncode,0,review.stderr[-1700:])
        response=json.loads(review.stdout)
        packet=response['request']
        self.assertEqual(packet['action'],'REQUEST_APPROVAL')
        self.assertFalse(packet['approved'])
        self.assertFalse(packet['renderable'])
        self.assertTrue(packet['requires_authoritative_server_transaction'])
        self.assertEqual(packet['edited_proposal']['scenes'][0]['trim_start'],0.25)
        self.assertFalse(packet['edited_proposal']['scenes'][0]['mute_source'])
        candidate_sha=hashlib.sha256(json.dumps(
            packet['edited_proposal'],ensure_ascii=False,sort_keys=True,
            separators=(',',':')).encode()).hexdigest()
        draft_sha=hashlib.sha256(json.dumps(draft,ensure_ascii=False,
            sort_keys=True,separators=(',',':')).encode()).hexdigest()
        ctx=CurrentReviewContext('demo-shop','demo-campaign','fixture-editor',
          'EDITOR',True,True,self.sha)
        store=LocalReviewJournal(self.root/'review.sqlite')
        try:
            stage=store.stage(context=ctx,draft_sha256=draft_sha,
              candidate_sha256=candidate_sha,now_ms=1700000000000)
            self.assertEqual(stage['status'],'PENDING')
            approved=store.approve(review_id=stage['review_id'],
              context=ctx,expected_revision=0,candidate_sha256=candidate_sha,
              confirmed_by_human=True,now_ms=1700000000100)
            claim=store.claim_for_feature4(review_id=stage['review_id'],
              approval_id=approved['approval_id'],context=ctx,
              draft_sha256=draft_sha,candidate_sha256=candidate_sha,
              expected_revision=1,now_ms=1700000000200)
            self.assertEqual(claim['status'],'CLAIMED_ONCE')
            with self.assertRaises(ReviewStateError):
                store.claim_for_feature4(review_id=stage['review_id'],
                  approval_id=approved['approval_id'],context=ctx,
                  draft_sha256=draft_sha,candidate_sha256=candidate_sha,
                  expected_revision=1,now_ms=1700000000201)
        finally:
            store.close()
        handoff=self.node(HANDOFF,{
          'shop_id':'demo-shop','campaign_id':'demo-campaign',
          'media_sha256':self.sha,'draft':draft,
          'proposal':packet['edited_proposal'],
          'approval_id':approved['approval_id'],'canonical_sha':draft_sha})
        self.assertEqual(handoff.returncode,0,handoff.stderr[-1400:])
        result=json.loads(handoff.stdout)
        edits=result['approved_edits']
        self.assertTrue(edits['approved'])
        self.assertEqual(edits['approval_id'],approved['approval_id'])
        self.assertEqual(edits['draft_sha256'],draft_sha)
        self.assertEqual(edits['scenes'][0]['trim_start'],0.25)
        self.assertTrue(result['requires_authoritative_db_persistence'])
        self.assertTrue(result['no_render_performed'])
        self.assertEqual(hashlib.sha256(self.src.read_bytes()).hexdigest(),self.sha)

    def test_repeated_submission_of_same_video_has_no_implicit_overwrite(self):
        src={'source_path':str(self.src),'private_root':str(self.private),
          'shop_id':'another-shop','asset_id':'same-asset',
          'expected_sha256':self.sha}
        a=self.node(INTAKE,src);b=self.node(INTAKE,src)
        self.assertEqual(a.returncode,0,a.stderr)
        self.assertNotEqual(b.returncode,0)

if __name__=='__main__':unittest.main()
