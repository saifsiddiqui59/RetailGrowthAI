'use strict';
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const {approveCreativeDraft}=require('../handoff-approval');
const {auditFeature4Consumer,F4_PRESENT_SOURCE}=require('../consumer-compat');
const key=Buffer.alloc(48,'s');
const garment={color:'red',neckline:'round',sleeves:'long',hem:'straight',embroidery:'gold'};
const shop='11111111-1111-4111-8111-111111111111';
const campaign='22222222-2222-4222-8222-222222222222';
const media='33333333-3333-4333-8333-333333333333';
const creative={
  contract:'creative_direction_v1',version:1,shop_id:shop,campaign_id:campaign,
  source_generated_media:false,provider_output_guaranteed:false,
  reference_media_requests:[{feature:3,asset_id:media,same_shop_required:true,rights_review_required:true}],
  scenes:[{id:'s1'}],duration_seconds:15
};
const motion={contract:'motion_direction_v1',shop_id:shop,campaign_id:campaign,
  shot_id:'shot1',reference_media_id:media,product_sku:'KURTI-01',garment_lock:garment,
  duration_seconds:5,requested_profile:{inference_approved:false,kind:'image_to_video'},
  generation_prompt:'A premium realistic red kurti advertisement showing natural human movement and precise camera choreography.'};
const planHash=crypto.createHash('sha256').update(JSON.stringify({creative,source_media:[garment]})).digest('hex');
const bundle={creative_direction_v1:creative,motion_direction_v1:[motion],
  approval_record:{plan_sha256:planHash,review_status:'DRAFT',approved:false,can_publish:false,can_run_paid_motion:false}};
const reviewer={id:'authorized-owner',shop_id:shop,role:'OWNER',
  server_verified:true,current_member:true,completed_claims_review:true,
  completed_media_rights_review:true,completed_storyboard_review:true,completed_script_review:true};
const receipt=approveCreativeDraft(bundle,reviewer,key);
const audit=auditFeature4Consumer(bundle,receipt,key,shop);
assert.equal(F4_PRESENT_SOURCE.accepted_motion_model,'hunyuanvideo-1.5-480p');
assert.equal(audit.compatibility,'BLOCKED_UNTIL_CONSUMER_INTERFACE_RATIFIED');
assert.ok(audit.issues.includes('F4_CURRENT_F5_PROFILE_IS_HUNYUAN_480P_NOT_APPROVED_WAN_2_2'));
assert.ok(audit.issues.includes('F4_REVIEWED_SOURCE_DIRECTION_SHAPE_IS_DIFFERENT'));
assert.equal(audit.may_queue_paid_motion,false);
const bad=structuredClone(bundle);
bad.motion_direction_v1[0].generation_prompt='unreviewed garment swap';
assert.throws(()=>auditFeature4Consumer(bad,receipt,key,shop),/CREATIVE_HANDOFF_REJECTED/);
console.log('feature2 current F4/5 consumer mismatch confirmed BLOCKED, no paid dispatch');
