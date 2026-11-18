import test from 'node:test'
import assert from 'node:assert/strict'
import {inspectHumanQuality,compareHumanQualityAspects}
 from '../../frontend/src/features/testing/trace-quality-analysis.mjs'

const F2_OUTPUT={provider_mode:'deterministic',
 improved_prompt:'A complete real output about approved fashion styles'}
const F4_OUTPUT={status:'SUCCEEDED',
 render_job_id:'33333333-3333-4333-8333-333333333333',
 output_asset_id:'44444444-4444-4444-8444-444444444444'}
const e=(feature,status,event_seq,details={},action='step')=>{
 if(status==='PASS'&&action==='step'){
  if(feature==='F2')return {feature,status,event_seq,action:'prompt-improvement',
   details:{...F2_OUTPUT,...details}}
  if(feature==='F4')return {feature,status,event_seq,action:'ffmpeg-result',
   details:{...F4_OUTPUT,...details}}
 }
 return {feature,status,event_seq,details,action}
}
test('human ratings require a previous completed real output',()=>{
 const data=[
  e('F4','QUALITY_REVIEW',1,{score:1,dimension:'audio'}),
  e('F4','NOT_RUN',2),
  e('F2','PASS',3),
  e('F2','QUALITY_REVIEW',4,{score:4,dimension:'claim_accuracy'}),
  e('F4','PASS',5),
  e('F4','QUALITY_REVIEW',6,{score:2,dimension:'audio'}),
 ]
 const results=inspectHumanQuality(data)
 assert.equal(results.length,2)
 assert.equal(results.find(x=>x.feature==='F4').latest_score,2)
 assert.equal(results.find(x=>x.feature==='F2').dimension,'claim_accuracy')
 assert.ok(results.every(x=>x.source==='human_reviewer_only'))
})
test('legacy reviews without dimensions default to overall and invalid explicit dimensions are rejected',()=>{
 const data=[
   e('F4','PASS',1),
   e('F4','QUALITY_REVIEW',2,{score:4}),
   e('F4','QUALITY_REVIEW',3,{score:3,dimension:'nonsense'}),
   e('F4','QUALITY_REVIEW',4,{score:5,dimension:'overall'}),
   e('F4','QUALITY_REVIEW',5,{score:10,dimension:'overall'}),
 ]
 const item=inspectHumanQuality(data)[0]
 assert.deepEqual([item.dimension,item.latest_score,item.sample_count,item.mean_score],['overall',5,2,4.5])
})
test('scores for different aspects must never be compared as an improvement',()=>{
 const baseline=[e('F4','PASS',1),e('F4','QUALITY_REVIEW',2,{score:4,dimension:'captions'})]
 const current=[e('F4','PASS',1),e('F4','QUALITY_REVIEW',2,{score:1,dimension:'audio'})]
 const change=compareHumanQualityAspects(current,baseline)[0]
 assert.equal(change.comparable,false)
 assert.equal(change.change,null)
 assert.equal(change.dimension,'audio')
})
test('same feature and same aspect can be compared without claiming AI causality',()=>{
 const baseline=[e('F2','PASS',1),e('F2','QUALITY_REVIEW',2,{score:2,dimension:'storyboard'})]
 const current=[e('F2','PASS',1),e('F2','QUALITY_REVIEW',2,{score:4,dimension:'storyboard'})]
 const change=compareHumanQualityAspects(current,baseline)[0]
 assert.deepEqual([change.comparable,change.change,change.baseline_latest_score],[true,2,2])
 assert.equal(change.comparison_basis,'same_feature_and_human_quality_aspect_only')
})
test('no receipts yields no invented quality judgments',()=>{
 assert.deepEqual(inspectHumanQuality([]),[])
 assert.deepEqual(compareHumanQualityAspects([],[]),[])
})

test('a submitted but unfinished Reel cannot be reviewed as if the private MP4 exists',()=>{
 const events=[
  e('F4','PASS',1,{render_job_id:F4_OUTPUT.render_job_id},'ffmpeg-submission'),
  e('F4','QUALITY_REVIEW',2,{score:1,dimension:'audio'}),
 ]
 assert.deepEqual(inspectHumanQuality(events),[])
})
