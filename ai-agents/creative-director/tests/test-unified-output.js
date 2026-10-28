'use strict';
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const {approveCreativeDraft,verifyCreativeApproval,editorHandoff}=require('../handoff-approval');
const {auditFeature4Consumer}=require('../consumer-compat');
const {previewOffline,readinessFromOffline}=require('../offline-acceptance');
const {projectReviewedCreativeForF4}=require('../feature4-source-projection');
const KEY=Buffer.alloc(48,67);
const chunks=[];
process.stdin.on('data',buf=>chunks.push(buf));
process.stdin.on('end',()=>{
  try {
    const payload=JSON.parse(Buffer.concat(chunks).toString('utf8'));
    const b=payload.bundle;
    const c=b.creative_direction_v1;
    const reviewer={id:payload.reviewer_id,shop_id:c.shop_id,role:'OWNER',
      server_verified:true,current_member:true,
      completed_claims_review:true,completed_media_rights_review:true,
      completed_storyboard_review:true,completed_script_review:true};
    const mock=previewOffline(b,{gpuEnabled:false});
    assert.equal(mock.can_start_gpu,false);
    assert.equal(mock.billable_calls,0);
    assert.equal(mock.generated_video_files,0);
    const report=readinessFromOffline(mock);
    assert.equal(report.feature2_production_ready,false);
    assert.equal(report.offline_source_scenario,'PASSED');
    const receipt=approveCreativeDraft(b,reviewer,KEY);
    assert.equal(verifyCreativeApproval(b,receipt,KEY,c.shop_id),true);
    const handoff=editorHandoff(b,receipt,KEY,c.shop_id);
    assert.equal(handoff.can_publish,false);
    assert.equal(handoff.can_dispatch_paid_motion,false);
    assert.equal(handoff.motion_direction_v1.length,c.duration_seconds/5);
    const sourceAssets={};
    for(const motion of b.motion_direction_v1){
      sourceAssets[motion.reference_media_id]={
        shop_id:c.shop_id,kind:'image',approved:true,private:true,commercial_rights:true,
        original_media_sha256:'a'.repeat(64)
      };
    }
    const snapshot={
      source:'VERIFIED_SERVER_TEST_ONLY',
      shop_id:c.shop_id,campaign_id:c.campaign_id,
      review_hash:receipt.plan_sha256,approval_id:'66666666-6666-4666-8666-666666666666',
      assets:sourceAssets
    };
    const projection=projectReviewedCreativeForF4(b,receipt,KEY,c.shop_id,snapshot);
    assert.equal(projection.direction.version,'creative_direction_v1');
    assert.equal(projection.direction.source_feature,'feature2');
    assert.equal(projection.direction.approved,false);
    assert.equal(projection.snapshot.approved,false);
    assert.equal(projection.can_call_current_feature4,false);
    assert.equal(projection.can_start_gpu,false);
    assert.equal(projection.direction.scenes.length,c.duration_seconds/5);
    const required=['prompt','negative_prompt','source_asset_id','duration_seconds',
      'shot_id','choreography','camera','lighting','fidelity_requirements'].sort();
    for(let i=0;i<b.motion_direction_v1.length;i++){
      const original=b.motion_direction_v1[i];
      const mapped=projection.direction.scenes[i].motion_direction_v1;
      assert.deepEqual(Object.keys(mapped).sort(),required);
      assert.deepEqual(mapped.fidelity_requirements.original_motion_direction_v1,original);
      assert.equal(mapped.prompt,original.generation_prompt);
      assert.equal(mapped.source_asset_id,original.reference_media_id);
      assert.equal(projection.trace[i].full_details_preserved,true);
    }
    const foreignSnapshot=structuredClone(snapshot);
    foreignSnapshot.assets[b.motion_direction_v1[0].reference_media_id].shop_id=
      '99999999-9999-4999-8999-999999999999';
    assert.throws(()=>projectReviewedCreativeForF4(b,receipt,KEY,c.shop_id,foreignSnapshot),
      /F2_F4_PROJECTION_BLOCKED/);
    const changedSource=structuredClone(snapshot);
    changedSource.assets[b.motion_direction_v1[0].reference_media_id].original_media_sha256=
      'f'.repeat(64);
    assert.throws(()=>projectReviewedCreativeForF4(b,receipt,KEY,c.shop_id,changedSource),
      /F2_F4_PROJECTION_BLOCKED/);
    const wrongApproval=structuredClone(snapshot);
    wrongApproval.review_hash='0'.repeat(64);
    assert.throws(()=>projectReviewedCreativeForF4(b,receipt,KEY,c.shop_id,wrongApproval),
      /F2_F4_PROJECTION_BLOCKED/);

    const compat=auditFeature4Consumer(b,receipt,KEY,c.shop_id);
    assert.equal(compat.compatibility,'BLOCKED_UNTIL_CONSUMER_INTERFACE_RATIFIED');
    assert.equal(compat.may_queue_paid_motion,false);
    const replaced=structuredClone(b);
    replaced.motion_direction_v1[0].generation_prompt+=' unauthorized wardrobe color change';
    assert.throws(()=>editorHandoff(replaced,receipt,KEY,c.shop_id),
      /CREATIVE_HANDOFF_REJECTED/,'A hash-signed brief must not allow altered motion');
    const foreign={...reviewer,shop_id:'99999999-9999-4999-8999-999999999999'};
    assert.throws(()=>approveCreativeDraft(b,foreign,KEY),/CREATIVE_HANDOFF_REJECTED/);
    const withoutRights={...reviewer,completed_media_rights_review:false};
    assert.throws(()=>approveCreativeDraft(b,withoutRights,KEY),/CREATIVE_HANDOFF_REJECTED/);
    process.stdout.write(JSON.stringify({
      result:'OFFLINE_ACCEPTED_NOT_PRODUCTION_READY',
      duration_seconds:c.duration_seconds,shots:mock.editor_timeline.length,
      signed_creative_sha256:receipt.plan_sha256,
      source_visual_clips_generated:0,billed_calls:0,
      gpu_started:false,ready_to_publish:false,
      consumer_compatibility:compat.compatibility,
    })+'\n');
  } catch(err) {
    process.stderr.write('Feature2 offline unified integration failed: '+err.stack+'\n');
    process.exitCode=1;
  }
});
