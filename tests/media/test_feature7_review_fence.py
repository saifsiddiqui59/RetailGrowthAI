"""Source-only Feature7 approval, stale-revision, fake review and F4 handoff tests."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from test_feature7_semantic import sample

ROOT=Path(__file__).resolve().parents[2]

JS=r"""
import fs from 'node:fs';
import crypto from 'node:crypto';
import {proposeUploadedFootageEdits} from './video-engine/feature7/autobroll_semantics.mjs';
import {sealHumanEditApproval,buildFeature4EditHandoff}
  from './video-engine/feature7/review_fence.mjs';
const request=JSON.parse(fs.readFileSync(0,'utf8'));
const key=Buffer.from('cd'.repeat(32),'hex');
const {input,operation='good',bad={}}=request;
const proposal=proposeUploadedFootageEdits(input);
const draft=input.draft;
if(bad.mutate_candidate)proposal.scenes[0].trim_start=3601;
if(bad.mute_candidate)proposal.scenes[0].mute_source=true;
const context={
 shop_id:input.shop_id,campaign_id:input.campaign_id,
 reviewer_id:'human-owner-1',active_membership:true,
 role:'OWNER',video_rights_current:true,revision:2,
 source_snapshot_sha256:'a'.repeat(64)
};
if(bad.context_role)context.role=bad.context_role;
if(bad.context_rights===false)context.video_rights_current=false;
if(bad.context_shop)context.shop_id=bad.context_shop;
const originalHash=request.canonical_hash;
if(operation==='seal'){
 let receipt=sealHumanEditApproval({proposal,draft,context,key,
   approval_id:'approved-feature7-001',
   canonical_draft_sha256:originalHash,now_ms:request.now_ms??1000000});
 process.stdout.write(JSON.stringify({receipt,proposal}));
}else {
 const receipt=sealHumanEditApproval({proposal,draft,context,key,
   approval_id:'approved-feature7-001',
   canonical_draft_sha256:originalHash,now_ms:1000000});
 if(bad.signed_bad_time){
   // Test-only: construct a correctly MAC'd but invalid timestamp payload.
   // A production caller must never have access to this service key.
   const {mac:ignored,...payload}=receipt;
   if(bad.signed_bad_time==='string_epoch')payload.issued_at_ms='1000000';
   if(bad.signed_bad_time==='zero_ttl')payload.expires_at_ms=payload.issued_at_ms;
   if(bad.signed_bad_time==='fractional_expiry')payload.expires_at_ms+=0.5;
   const mac=crypto.createHmac('sha256',key).update(
     'retailgrowth.feature7.review.v1\n'+JSON.stringify(payload)).digest('hex');
   receipt={...payload,mac};
 }
 if(bad.stale_revision)context.revision=3;
 if(bad.expired)request.now_ms=1700000;
 if(bad.different_owner)context.reviewer_id='foreign-user';
 if(bad.tamper_receipt)receipt.mac='0'.repeat(64);
 if(bad.tamper_after_review)proposal.scenes[0].trim_start+=0.1;
 const out=buildFeature4EditHandoff({proposal,draft,context,receipt,
   canonical_draft_sha256:originalHash,key,now_ms:request.now_ms??1000000});
 process.stdout.write(JSON.stringify(out));
}
"""

@unittest.skipUnless(shutil.which('node'),'Node required')
class Feature7ReviewFenceTests(unittest.TestCase):
    def run_js(self,data):
        draft=data['input']['draft']
        data['canonical_hash']=hashlib.sha256(json.dumps(
            draft,sort_keys=True,ensure_ascii=False,separators=(',',':'),
            allow_nan=False).encode()).hexdigest()
        return subprocess.run(['node','--input-type=module','-e',JS],
          input=json.dumps(data),capture_output=True,text=True,cwd=ROOT,timeout=10)

    def test_reviewed_trim_emits_only_feature4_exact_fields(self):
        r=self.run_js({'input':sample()})
        self.assertEqual(r.returncode,0,r.stderr)
        result=json.loads(r.stdout)
        edits=result['approved_edits']
        self.assertEqual(set(edits),{'source_feature','approved','approval_id',
          'timeline_version','shop_id','campaign_id','draft_sha256','scenes'})
        self.assertTrue(edits['approved'])
        self.assertEqual(edits['timeline_version'],'creative_reel_v1')
        self.assertFalse(edits['scenes'][0]['mute_source'])
        self.assertEqual(result['snapshot_edit_plan'],{
          'source_feature':'feature7','approved':True,
          'approval_id':'approved-feature7-001',
          'timeline_version':'creative_reel_v1'})
        self.assertTrue(result['requires_authoritative_db_persistence'])
        self.assertTrue(result['no_render_performed'])

    def test_current_reviewer_and_media_must_be_authorized(self):
        for bad in [
            {'context_role':'VIEWER'},
            {'context_rights':False},
            {'context_shop':'foreign-shop'},
            {'context_role':'ANONYMOUS'},
            {'mute_candidate':True},
            {'mutate_candidate':True},
        ]:
            with self.subTest(bad=bad):
                r=self.run_js({'input':sample(),'bad':bad})
                self.assertNotEqual(r.returncode,0,r.stdout)

    def test_reject_replay_after_revocation_stale_revision_or_tamper(self):
        for bad in [
            {'stale_revision':True},
            {'expired':True},
            {'different_owner':True},
            {'tamper_receipt':True},
            {'tamper_after_review':True},
        ]:
            with self.subTest(bad=bad):
                r=self.run_js({'input':sample(),'bad':bad})
                self.assertNotEqual(r.returncode,0,r.stdout)

    def test_receipt_expiry_never_overflows_safe_integer_clock(self):
        maximum=9007199254740991
        ttl=600000
        for now in (-1, 1000000.5, maximum-ttl+1, maximum):
            with self.subTest(now=now):
                r=self.run_js({'input':sample(),'operation':'seal','now_ms':now})
                self.assertNotEqual(r.returncode,0,r.stdout)
        r=self.run_js({'input':sample(),'operation':'seal',
                       'now_ms':maximum-ttl})
        self.assertEqual(r.returncode,0,r.stderr)
        receipt=json.loads(r.stdout)['receipt']
        self.assertEqual(receipt['expires_at_ms'],maximum)

    def test_even_validly_signed_malformed_receipt_times_are_denied(self):
        for invalid in ('string_epoch','zero_ttl','fractional_expiry'):
            with self.subTest(invalid=invalid):
                r=self.run_js({'input':sample(),
                               'bad':{'signed_bad_time':invalid}})
                self.assertNotEqual(r.returncode,0,r.stdout)
                self.assertIn('Stale, revoked or cross-tenant review',r.stderr)

    def test_unreviewed_json_never_yields_executable_decision(self):
        r=self.run_js({'input':sample(),'operation':'seal'})
        self.assertEqual(r.returncode,0,r.stderr)
        data=json.loads(r.stdout)
        self.assertFalse(data['proposal']['renderable'])
        self.assertFalse(data['proposal']['approved'])
        self.assertTrue(data['receipt']['mac'])
        self.assertEqual(data['receipt']['revision'],2)


if __name__=='__main__': unittest.main()
