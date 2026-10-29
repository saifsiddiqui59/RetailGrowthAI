import test from 'node:test'
import assert from 'node:assert/strict'
import { analyzeImprovementPriorities } from '../../frontend/src/features/testing/trace-guidance.mjs'

const event=(feature,status,event_seq,action='step',details={})=>
  ({feature,status,event_seq,action,summary:'Observed stage response',details})
const F2_OUTPUT={improved_prompt:'A complete safe draft about verified boutique products',
 provider_mode:'deterministic'}
const F4_OUTPUT={status:'SUCCEEDED',
 render_job_id:'33333333-3333-4333-8333-333333333333',
 output_asset_id:'44444444-4444-4444-8444-444444444444'}


test('failed stage stays first priority even after a later PASS',()=>{
  const result=analyzeImprovementPriorities([
    event('F2','PASS',1,'prompt-improvement'),
    event('F2','FAIL',2,'campaign-planning'),
    event('F2','PASS',3,'late-planning'),
    event('F3','NOT_RUN',4,'poster-model'),
  ])
  assert.equal(result.attention.length,1)
  assert.equal(result.attention[0].feature,'F2')
  assert.equal(result.attention[0].category,'EXECUTION_FAILURE')
  assert.equal(result.attention[0].first_problem.action,'campaign-planning')
  assert.equal(result.entries.find(x=>x.feature==='F3').category,'NOT_RUN')
  assert.equal(result.untested_features,5)
})

test('unknown FFmpeg remains uncertain; recommendation says inspect, not rerun',()=>{
  const result=analyzeImprovementPriorities([
    event('F2','PASS',1,'prompt-improvement'),
    event('F4','UNKNOWN',2,'ffmpeg-submission'),
    event('F7','NOT_RUN',3,'smart-editor'),
  ])
  const f=result.attention[0]
  assert.equal(f.category,'UNCONFIRMED_RESULT')
  assert.equal(f.feature,'F4')
  assert.match(f.recommended_action,/before resubmitting/i)
  assert.doesNotMatch(f.recommended_action,/automatically retry/i)
})

test('low human quality targets completed feature without making technical stage fail',()=>{
  const result=analyzeImprovementPriorities([
    event('F4','PASS',1,'ffmpeg-result',F4_OUTPUT),
    event('F4','QUALITY_REVIEW',2,'human-quality-review',{score:1}),
    event('F2','PASS',3,'prompt-improvement',F2_OUTPUT),
    event('F2','QUALITY_REVIEW',4,'human-quality-review',{score:5}),
  ])
  assert.equal(result.attention.length,1)
  assert.equal(result.attention[0].category,'LOW_HUMAN_QUALITY')
  assert.equal(result.attention[0].status,'PASS')
  assert.equal(result.attention[0].latest_human_score,1)
  assert.equal(result.entries.find(x=>x.feature==='F2').category,'REVIEWED_OUTPUT')
})

test('an unobserved or NOT_RUN feature is NEVER an improvement failure',()=>{
 const result=analyzeImprovementPriorities([
   event('F1','PASS',1,'tenant-and-rights'),
   event('F2','PASS',2,'prompt-improvement'),
   event('F3','NOT_RUN',3,'poster-model'),
   event('F5','NOT_RUN',4,'premium-motion'),
   event('F4','NOT_RUN',5,'ffmpeg-reel'),
   event('F7','NOT_RUN',6,'smart-editor'),
 ])
 assert.deepEqual(result.attention,[])
 assert.equal(result.untested_features,4)
 assert.equal(result.observed_features,2)
 assert.equal(result.entries.find(x=>x.feature==='F3').completed_steps,0)
})

test('ignore forged/unbounded statuses and reject low score without actual output',()=>{
 const result=analyzeImprovementPriorities([
  event('F5','QUALITY_REVIEW',1,'human-quality-review',{score:1}),
  event('F5','NOT_RUN',2,'premium-motion'),
  event('F2','SUCCESS',3,'untrusted'),
  event('F2','PASS',-1,'badseq'),
 ])
 assert.equal(result.attention.length,0)
 assert.equal(result.entries.find(x=>x.feature==='F5').category,'NOT_RUN')
 assert.equal(result.entries.find(x=>x.feature==='F5').latest_human_score,null)
 assert.equal(result.entries.find(x=>x.feature==='F2').category,'UNOBSERVED')
})

test('all empty events present no executed feature, rating or fake diagnosis',()=>{
 const result=analyzeImprovementPriorities([])
 assert.equal(result.attention.length,0)
 assert.equal(result.untested_features,6)
 assert.equal(result.observed_features,0)
 assert.ok(result.entries.every(x=>x.status==='UNOBSERVED'))
})

test('human reviewer can isolate weak audio without claiming a codec or worker failure',()=>{
 const result=analyzeImprovementPriorities([
   event('F4','PASS',1,'ffmpeg-result',F4_OUTPUT),
   event('F4','QUALITY_REVIEW',2,'human-quality-review',{score:1,dimension:'audio'}),
 ])
 const item=result.attention[0]
 assert.equal(item.category,'LOW_HUMAN_QUALITY')
 assert.equal(item.status,'PASS')
 assert.equal(item.latest_human_dimension,'audio')
 assert.match(item.reason,/Voiceover and music mix 1\/5/)
 assert.match(item.recommended_action,/Listen for intelligible speech/)
})

test('an accepted job submission without a finished Reel cannot become a low-quality video',()=>{
 const report=analyzeImprovementPriorities([
  event('F4','PASS',1,'ffmpeg-submission',{render_job_id:F4_OUTPUT.render_job_id}),
  event('F4','QUALITY_REVIEW',2,'human-quality-review',{score:1,dimension:'audio'}),
 ])
 assert.equal(report.attention.length,0)
 assert.equal(report.entries.find(x=>x.feature==='F4').latest_human_score,null)
})
