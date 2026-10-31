'use strict';

// Source-only projection for the exact *current draft* Feature4 PR #322
// nine-key motion input. It cannot authorize F4/F5 dispatch: the actual
// consumer hardcodes Hunyuan 1.5 480p while F2 is Wan-oriented.
// Keep all original F2 data in fidelity_requirements and refuse truncation.
const crypto=require('node:crypto');
const {verifyCreativeApproval}=require('./handoff-approval');
const _UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const _SAFE=/^[A-Za-z0-9_-]{1,100}$/;
const _KEYS=['prompt','negative_prompt','source_asset_id','duration_seconds',
  'shot_id','choreography','camera','lighting','fidelity_requirements'].sort();
function reject(reason){throw Error('F2_F4_PROJECTION_BLOCKED: '+reason)}
function stringify(value){
  try {return JSON.stringify(value)} catch {reject('Non-JSON approved creative direction')}
}
function sha(value){return crypto.createHash('sha256').update(stringify(value)).digest('hex')}
function projectReviewedCreativeForF4(bundle,receipt,secret,shopId,sourceSnapshot){
  verifyCreativeApproval(bundle,receipt,secret,shopId);
  const plan=bundle.creative_direction_v1;
  // Requires actual server-provided media evidence in the eventual handler:
  // do not accept sourceSnapshot directly from a browser. This module only
  // runs in offline source tests; a real adapter must re-fetch JWT/RLS.
  if(!_UUID.test(shopId)||!_UUID.test(plan.campaign_id)||
     !_UUID.test(sourceSnapshot?.approval_id)||
     sourceSnapshot.shop_id!==shopId||
     sourceSnapshot.campaign_id!==plan.campaign_id||
     sourceSnapshot.review_hash!==receipt.plan_sha256||
     sourceSnapshot.source!=='VERIFIED_SERVER_TEST_ONLY'|| !sourceSnapshot.assets||
     typeof sourceSnapshot.assets!=='object')
    reject('Missing source-fetched same-shop UUID approval snapshot');
  const scenes=[], trace=[];
  for(const motion of bundle.motion_direction_v1){
    const asset=sourceSnapshot.assets[motion.reference_media_id];
    if(!_UUID.test(motion.reference_media_id)||
      !asset||asset.shop_id!==shopId||asset.approved!==true||
      asset.private!==true||asset.commercial_rights!==true||
      asset.kind!=='image'|| !/^[a-f0-9]{64}$/.test(asset.original_media_sha256)||
      motion.reference_facts_sha256!==sha({
        media_id:motion.reference_media_id,
        original_media_sha256:asset.original_media_sha256,
        garment:motion.garment_lock,shop_id:shopId
      }))
      reject('Source image bytes/rights need current server review');
    if(motion.duration_seconds!==5||!_SAFE.test(motion.shot_id)||
       typeof motion.generation_prompt!=='string'||motion.generation_prompt.length>1500||
       motion.generation_prompt.length<180|| !Array.isArray(motion.negative_constraints))
      reject('Lossless Feature4 projection cannot fit current 5s/1500-character profile');
    const detail={
      prompt:motion.generation_prompt,
      negative_prompt:motion.negative_constraints.join('; '),
      source_asset_id:motion.reference_media_id,
      duration_seconds:motion.duration_seconds,shot_id:motion.shot_id,
      choreography:motion.choreography,camera:motion.camera,lighting:motion.lighting,
      fidelity_requirements:{
        source_feature:'feature2',
        original_motion_direction_v1:motion,
        source_motion_sha256:sha(motion),
        approved_source_sha256:asset.original_media_sha256
      }
    };
    if(detail.negative_prompt.length>800|| stringify(detail).length>9000||
       stringify(detail).includes('https://')||stringify(detail).includes('file://'))
      reject('Do not truncate original motion prompt, negatives, references or shot facts');
    if(stringify(Object.keys(detail).sort())!==stringify(_KEYS))
      reject('Feature4 nine-field shape changed');
    // Only an integrity-checked draft projection, never a fabricated
    // reviewer-approval result that F4 could dispatch.
    scenes.push({motion_direction_v1:detail});
    trace.push({shot_id:motion.shot_id,original_sha256:sha(motion),
      full_details_preserved: true, reference_sha256:asset.original_media_sha256});
  }
  return {
    contract:'feature2_to_feature4_projection_candidate_v1',
    direction:{
      version:'creative_direction_v1',source_feature:'feature2',
      shop_id:shopId,campaign_id:plan.campaign_id,
      approval_id:sourceSnapshot.approval_id,review_hash:receipt.plan_sha256,
      approved:false,scenes
    },
    snapshot:{
      shop_id:shopId,campaign_id:plan.campaign_id,
      approval_id:sourceSnapshot.approval_id,
      review_hash:receipt.plan_sha256,approved:false,
      assets:sourceSnapshot.assets
    },
    trace,can_call_current_feature4:false,can_queue_paid_motion:false,
    can_start_gpu:false,reason:'F4_HUNYUAN_480P_AND_APPROVAL_CONTRACT_NOT_RATIFIED'
  };
}
module.exports={projectReviewedCreativeForF4};
