'use strict';
// Does NOT call real Feature4 or Feature5; export a lossless editor *preview*
// and mock motion-dispatch denial for CI with a GPU_OFF fixture.
// Real Feature4 PR #322 has not ratified this contract, and real Feature5
// first-frame, lease, cost and provider-profile acceptance remain blocked.
const {createHash}=require('node:crypto');
function error(s){throw new Error('FEATURE2_OFFLINE_ACCEPTANCE_INVALID: '+s)}
function previewOffline(bundle,{gpuEnabled=false}={}){
  if(gpuEnabled!==false)error('GPU must remain disabled during Feature2 source acceptance');
  const plan=bundle&&bundle.creative_direction_v1;
  const shots=bundle&&bundle.motion_direction_v1;
  const review=bundle&&bundle.approval_record;
  if(!plan||plan.contract!=='creative_direction_v1'||!Array.isArray(shots)||
     !review||review.approved!==false||review.can_publish!==false||
     review.can_run_paid_motion!==false)error('Only original unapproved draft plans can enter offline preview');
  if(plan.duration_seconds!==15&&plan.duration_seconds!==30&&plan.duration_seconds!==60)
    error('Unsupported Reel duration');
  if(plan.aspect_ratio!=='9:16'||shots.length<3||shots.length>12)
    error('Unrecognized portrait Reel or shot count');
  // The same object can be shared between plan.scenes[*].shots and
  // motion_direction_v1. Equality checks alone miss simultaneous mutation.
  // Recompute the ORIGINAL source compiler fingerprint before any mock handoff.
  if(!Array.isArray(plan.reference_media_requests)||!plan.reference_media_requests.length)
    error('Missing signed source lineage');
  const source_media=plan.reference_media_requests.map(ref=>{
    const source=shots.find(shot=>shot.reference_media_id===ref.asset_id);
    if(!source||!source.garment_lock||ref.same_shop_required!==true||
       ref.rights_review_required!==true)
      error('Missing approved source media reference');
    return source.garment_lock;
  });
  const expected=createHash('sha256')
    .update(JSON.stringify({creative:plan,source_media})).digest('hex');
  if(review.plan_sha256!==expected)
    error('Creative plan or motion inputs changed after the original review');
  const editorTimeline=[];
  let time=0;
  for(let i=0;i<shots.length;i++){
    const shot=shots[i];
    if(!shot||shot.contract!=='motion_direction_v1'||shot.shop_id!==plan.shop_id||
       shot.campaign_id!==plan.campaign_id||shot.shot_start_seconds!==time||
       shot.duration_seconds<=0||shot.duration_seconds>5||
       !shot.reference_media_id||!shot.garment_lock||
       !Array.isArray(shot.choreography)||shot.choreography.length<2||
       !shot.generation_prompt||shot.generation_prompt.length<180||
       shot.requested_profile?.inference_approved!==false||
       shot.requested_profile?.provider_profile_verified!==false)
       error('Ineligible or unverified shot '+i);
    const matching=plan.scenes.flatMap(s=>s.shots||[]).find(s=>s.shot_id===shot.shot_id);
    if(!matching||matching.motion_direction?.generation_prompt!==shot.generation_prompt||
       matching.motion_direction?.reference_facts_sha256!==shot.reference_facts_sha256)
      error('Editorial storyboard and motion directions mismatch');
    editorTimeline.push({
      shot_id:shot.shot_id,scene_id:shot.scene_id,
      source_media_id:shot.reference_media_id,
      start_seconds:time,duration_seconds:shot.duration_seconds,
      original_generation_prompt_sha256:createHash('sha256').update(shot.generation_prompt).digest('hex'),
      prompt_length:shot.generation_prompt.length,
      camera:shot.camera,
      choreography:shot.choreography,
      garment_lock:shot.garment_lock,
      edit_status:'PREVIEW_ONLY_NO_REAL_CLIP',
      inference_status:'SKIPPED_GPU_OFF',
    });
    time+=shot.duration_seconds;
  }
  if(time!==plan.duration_seconds)error('Offline timeline does not cover the full Reel');
  return {
    contract:'feature2_offline_acceptance_v1',
    shop_id:plan.shop_id,campaign_id:plan.campaign_id,
    duration_seconds:plan.duration_seconds,
    original_editorial_sha256:review.plan_sha256,
    source_storyboard_scenes:plan.scenes.length,
    editor_timeline:editorTimeline,
    voice_sync:plan.audio_sync.state,
    hardware:{gpu:'OFF',premium_model:'NOT_STARTED'},
    feature4:'MOCK_ONLY_CONSUMER_NOT_RATIFIED',
    feature5:'MOCK_ONLY_NO_PROVIDER_CALL',
    generated_video_files:0, billable_calls:0,
    approved:false, can_publish:false, can_start_gpu:false
  };
}
function readinessFromOffline(preview){
  // This is a source-only readiness summary, never a signed approval or a
  // dispatch credential. Reject a mutated preview that upgrades mock/blocked
  // consumers, speech, rendering or reviewer state to a false success.
  const shots=preview?.editor_timeline;
  const count=preview?.duration_seconds/5;
  if(!preview||preview.contract!=='feature2_offline_acceptance_v1'||
     preview.hardware?.gpu!=='OFF'||preview.hardware?.premium_model!=='NOT_STARTED'||
     preview.billable_calls!==0||preview.generated_video_files!==0||
     preview.approved!==false||preview.can_publish!==false||
     preview.can_start_gpu!==false||
     preview.feature4!=='MOCK_ONLY_CONSUMER_NOT_RATIFIED'||
     preview.feature5!=='MOCK_ONLY_NO_PROVIDER_CALL'||
     !['ESTIMATED_PENDING_REAL_SPEECH_ALIGNMENT',
       'WORD_TIMES_MATCH_PENDING_AUDIO_PROVENANCE'].includes(preview.voice_sync)||
     ![15,30,60].includes(preview.duration_seconds)||
     !/^[a-f0-9]{64}$/.test(preview.original_editorial_sha256||'')||
     !Array.isArray(shots)||shots.length!==count||
     preview.source_storyboard_scenes!==count||
     shots.some((shot,i)=>!shot||shot.start_seconds!==i*5||
       shot.duration_seconds!==5||
       shot.edit_status!=='PREVIEW_ONLY_NO_REAL_CLIP'||
       shot.inference_status!=='SKIPPED_GPU_OFF'||
       !/^[a-f0-9]{64}$/.test(shot.original_generation_prompt_sha256||'')||
       typeof shot.shot_id!=='string'||!shot.shot_id||
       typeof shot.source_media_id!=='string'||!shot.source_media_id))
    error('Missing zero-cost offline acceptance proof');
  return {
    feature:'Feature2',
    offline_source_scenario:'PASSED',
    capability:'PROFESSIONAL_STORYBOARD_SOURCE_COMPILER',
    ready_to_activate_gpu:false,
    feature2_production_ready:false,
    blocking_gates:[
      'PRODUCTION_NODE_RUNTIME_AND_MIT_SOURCE_NOT_PACKAGED',
      'CURRENT_AUTHENTIC_SHOP_JWT_RLS_SOURCE_READERS_NOT_WIRED',
      'ACTUAL_APPROVED_PRODUCT_MEDIA_AND_DISCOUNT_UNVERIFIED',
      'FEATURE4_FEATURE5_VERSIONED_MOTION_CONSUMER_INCOMPATIBLE',
      'REAL_AZURE_AI_PLAN_AND_INDEPENDENT_EDITORIAL_REVIEW_MISSING',
      'REAL_VOICE_AND_VISUAL_GARMENT_FIDELITY_UNVERIFIED',
      'HOSTED_SIGNED_DRAFT_AND_249_RELIABILITY_NOT_ACCEPTED',
      'SEPARATE_GPU_SPEND_AND_OPERATOR_APPROVAL_NOT_GRANTED'
    ]
  };
}
module.exports={previewOffline,readinessFromOffline};
