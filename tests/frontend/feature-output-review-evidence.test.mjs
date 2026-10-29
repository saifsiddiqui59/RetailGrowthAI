import test from 'node:test'
import assert from 'node:assert/strict'
import {isObservedCompletedOutput,hasObservedCompletedOutput}
 from '../../frontend/src/features/testing/trace-output-evidence.mjs'
const CAMPAIGN='11111111-1111-4111-8111-111111111111'
const RENDER='22222222-2222-4222-8222-222222222222'
const ASSET='33333333-3333-4333-8333-333333333333'
const receipt=(feature,action,details,status='PASS',event_seq=1)=>
 ({feature,action,details,status,event_seq})
test('one accepted planning or render POST cannot masquerade as a creative output',()=>{
 for(const e of [
   receipt('F2','campaign-submission',{campaign_id:CAMPAIGN}),
   receipt('F4','ffmpeg-submission',{render_job_id:RENDER}),
   receipt('F4','ffmpeg-result',{render_job_id:RENDER,status:'QUEUED'}),
   receipt('F4','ffmpeg-result',{render_job_id:RENDER,status:'SUCCEEDED'}),
   receipt('F4','ffmpeg-result',{render_job_id:RENDER,
     status:'SUCCEEDED',output_asset_id:'not-a-uuid'}),
   receipt('F3','poster-model',{output_asset_id:ASSET}),
   receipt('F5','premium-motion',{output_asset_id:ASSET}),
   receipt('F7','smart-editor',{output_asset_id:ASSET}),
 ]) assert.equal(isObservedCompletedOutput(e),false)
})
test('Feature2 needs an actual deterministic prompt or complete seven-day readback',()=>{
 const prompt=receipt('F2','prompt-improvement',{
   provider_mode:'deterministic',improved_prompt:'Actual reviewed prompt copy'})
 const campaign=receipt('F2','campaign-planning',{
   campaign_id:CAMPAIGN,first_day_id:RENDER,generated_days:7},'PASS',2)
 assert.equal(isObservedCompletedOutput(prompt),true)
 assert.equal(isObservedCompletedOutput(campaign),true)
 assert.equal(isObservedCompletedOutput({...campaign,details:{...campaign.details,generated_days:6}}),false)
 assert.equal(hasObservedCompletedOutput([prompt,campaign],'F2',2),true)
 assert.equal(hasObservedCompletedOutput([prompt,campaign],'F2',1),false)
})
test('Part1 F4 completion requires authenticated job status and private output asset ID',()=>{
 const done=receipt('F4','ffmpeg-result',{
  render_job_id:RENDER,status:'SUCCEEDED',output_asset_id:ASSET})
 assert.equal(isObservedCompletedOutput(done),true)
 assert.equal(isObservedCompletedOutput({...done,status:'UNKNOWN'}),false)
 assert.equal(hasObservedCompletedOutput([done],'F4',2),true)
})
