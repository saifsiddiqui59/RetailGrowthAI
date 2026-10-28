'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const h = require('../handoff-approval');
const KEY = Buffer.alloc(32, 'K');
function bundle() {
  const garment = {color:'deep red',neckline:'round neck',sleeves:'long sleeves',hem:'straight hem',embroidery:'gold floral motifs'};
  const creative = {
    contract:'creative_direction_v1',version:1,shop_id:'shop-403',campaign_id:'campaign-403',
    source_generated_media:false,provider_output_guaranteed:false,
    duration_seconds:15,aspect_ratio:'9:16',scenes:[{id:'s1'}],
    reference_media_requests:[{feature:3,asset_id:'approved-f3-image',same_shop_required:true,rights_review_required:true}]
  };
  const motion = {
    contract:'motion_direction_v1',shop_id:creative.shop_id,campaign_id:creative.campaign_id,
    scene_id:'s1',shot_id:'shot-a',reference_media_id:'approved-f3-image',
    garment_lock:garment,product_sku:'KURTI-RED-001',
    requested_profile:{inference_approved:false},generation_prompt:'An approved complete deep red kurti shot'
  };
  const sha=crypto.createHash('sha256').update(JSON.stringify({creative,source_media:[garment]})).digest('hex');
  return {creative_direction_v1:creative,motion_direction_v1:[motion],
    approval_record:{plan_sha256:sha,review_status:'DRAFT',approved:false,
      can_publish:false,can_run_paid_motion:false}};
}
const reviewer={id:'user-approver',shop_id:'shop-403',role:'OWNER',
  server_verified:true,current_member:true,completed_claims_review:true,
  completed_media_rights_review:true,completed_storyboard_review:true,completed_script_review:true};
const original=bundle();
const receipt=h.approveCreativeDraft(original,reviewer,KEY);
assert.equal(h.verifyCreativeApproval(original,receipt,KEY,'shop-403'),true);
const approved=h.editorHandoff(original,receipt,KEY,'shop-403');
assert.equal(approved.contract,'feature2_to_feature4_handoff_v1');
assert.equal(approved.can_dispatch_paid_motion,false);
assert.equal(approved.feature5_provider_and_cost_must_be_approved,true);
assert.strictEqual(approved.motion_direction_v1[0].generation_prompt,
  original.motion_direction_v1[0].generation_prompt);
const fails=(fn,label)=>assert.throws(fn,/CREATIVE_HANDOFF_REJECTED/,label);
const tampered=structuredClone(original);
tampered.motion_direction_v1[0].garment_lock.color='blue';
fails(()=>h.editorHandoff(tampered,receipt,KEY,'shop-403'),'garment swap after signed review');
const tamperedShot=structuredClone(original);
tamperedShot.motion_direction_v1[0].generation_prompt='unapproved video request';
fails(()=>h.editorHandoff(tamperedShot,receipt,KEY,'shop-403'),'prompt edit after approval');
fails(()=>h.editorHandoff(original,receipt,KEY,'foreign-shop'),'cross-tenant read');
fails(()=>h.editorHandoff(original,{...receipt,hmac_sha256:'0'.repeat(64)},KEY,'shop-403'),'fabricated signature');
const other=structuredClone(reviewer);
other.role='VIEWER';
fails(()=>h.approveCreativeDraft(original,other,KEY),'viewer cannot approve');
const noRights=structuredClone(reviewer);
noRights.completed_media_rights_review=false;
fails(()=>h.approveCreativeDraft(original,noRights,KEY),'unreviewed rights');
const noMembership=structuredClone(reviewer);
noMembership.current_member=false;
fails(()=>h.approveCreativeDraft(original,noMembership,KEY),'revoked member');
const forgedBudget=structuredClone(original);
forgedBudget.motion_direction_v1[0].requested_profile.inference_approved=true;
fails(()=>h.editorHandoff(forgedBudget,receipt,KEY,'shop-403'),'no silent model approval');
fails(()=>h.approveCreativeDraft(original,reviewer,'weak-secret'),'weak secret');
console.log('Feature2 -> Feature4/5 editorial-only HMAC handoff test PASS; model and publication OFF');
