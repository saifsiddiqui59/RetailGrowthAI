'use strict';
const assert=require('node:assert/strict');
const {directorPrompt,compile,revise}=require('../director');
const {verifiedBrief,authoredCandidate}=require('./fixtures/diwali-premium-fixture');
const {previewOffline,readinessFromOffline}=require('../offline-acceptance');
const deny=(f,n)=>assert.throws(f,/FEATURE2_(?:CREATIVE_DIRECTION|OFFLINE_ACCEPTANCE)_INVALID/,n);
for(const duration of [15,30,60]){
  const input=verifiedBrief(duration);
  const mockedModelAnswer=authoredCandidate(duration);
  const prompt=directorPrompt(input);
  assert.equal(prompt.paid_call_made,false);
  assert.ok(prompt.user.includes('gold motifs across the front'));
  assert.ok(prompt.user.includes('eligible_product_skus'));
  assert.ok(prompt.user.includes('20% off selected kurtis'));
  const plan=compile(input,mockedModelAnswer);
  assert.equal(plan.creative_direction_v1.duration_seconds,duration);
  assert.equal(plan.motion_direction_v1.length,duration/5);
  assert.equal(plan.creative_direction_v1.scenes.length,duration/5);
  assert.equal(plan.creative_direction_v1.scenes[0].role,'hook');
  assert.equal(plan.creative_direction_v1.scenes.at(-1).role,'cta');
  assert.equal(plan.approval_record.approved,false);
  const summary=previewOffline(plan,{gpuEnabled:false});
  assert.equal(summary.editor_timeline.length,duration/5);
  assert.equal(summary.generated_video_files,0);
  assert.equal(summary.billable_calls,0);
  assert.equal(summary.hardware.gpu,'OFF');
  assert.equal(summary.can_start_gpu,false);
  assert.equal(summary.source_storyboard_scenes,duration/5);
  const scenes=new Set(plan.motion_direction_v1.map(s=>s.scene_goal));
  const actions=new Set(plan.motion_direction_v1.map(s=>s.choreography[1].human_action));
  const cameras=new Set(plan.motion_direction_v1.map(s=>s.camera.movement));
  assert.equal(scenes.size,duration/5,'each cinematic shot must be unique');
  assert.equal(actions.size,duration/5,'model must physically do something different in each shot');
  assert.equal(cameras.size,duration/5,'meaningful shot-to-shot camera direction must vary');
  for(const p of plan.motion_direction_v1){
    for(const verified of Object.values(input.media_grants[0].garment_facts))
      assert.ok(p.generation_prompt.toLowerCase().includes(verified.toLowerCase()),
        'garment fidelity contract missing '+verified);
    assert.ok(p.generation_prompt.length>=400,'focused detailed I2V instructions are substantial');
    assert.equal(p.choreography[0].start_seconds,0);
    assert.equal(p.choreography.at(-1).end_seconds,5);
    assert.equal(p.requested_profile.inference_approved,false);
  }
  const ready=readinessFromOffline(summary);
  assert.equal(ready.offline_source_scenario,'PASSED');
  assert.equal(ready.feature2_production_ready,false);
  assert.equal(ready.ready_to_activate_gpu,false);
  assert.ok(ready.blocking_gates.length>=6);
  deny(()=>previewOffline(plan,{gpuEnabled:true}),'GPU opt-in never succeeds');
  const altered=structuredClone(plan);
  altered.motion_direction_v1[0].generation_prompt+=' secretly swap approved image';
  deny(()=>previewOffline(altered),'F4 mock can never silently change a shot prompt');
  const broken=structuredClone(plan);
  broken.motion_direction_v1[1].shot_start_seconds=2.5;
  deny(()=>previewOffline(broken),'F4 mock must not accept noncontiguous edits');
  if(duration===30){
    const changed=structuredClone(mockedModelAnswer);
    changed.scenes[1].shots[0].camera.movement='gentle low-to-high dolly rise preserving the full garment silhouette';
    const updated=revise(input,plan,changed,{scenes:{'scene-2':'Raise the editorial camera slowly'}});
    assert.notEqual(updated.approval_record.plan_sha256,plan.approval_record.plan_sha256);
    assert.equal(updated.approval_record.approved,false);
    assert.equal(previewOffline(updated).can_start_gpu,false);
  }
  console.log(JSON.stringify({
    reel_duration_seconds:duration,
    scenes:plan.creative_direction_v1.scenes.length,
    motion_shots:plan.motion_direction_v1.length,
    editorial_status:'DRAFT',
    offline_preview:'PASS',paid_inference:0,gpu:'OFF',
    production_ready:false
  }));
}
console.log('Premium Diwali kurti 15/30/60s offline director→F4/F5 mock acceptance PASS; no GPU, no real retailer license, no media rendered');
