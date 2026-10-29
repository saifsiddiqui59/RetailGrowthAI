import test from 'node:test'
import assert from 'node:assert/strict'
import { summarizeTrace, compareTraceRuns, aggregateFeatureHistory } from '../../frontend/src/features/testing/trace-diagnostics.mjs'

const e = (feature, status, seq, action='step', details={}, duration_ms=null) =>
 ({ feature, status, event_seq:seq, action, summary:'Observed result', details, duration_ms })

test('localizes the FIRST failed or ambiguous handoff even with later success', () => {
 const report=summarizeTrace([
   e('F1','PASS',1,'membership',{},8),
   e('F2','PASS',2,'prompt',{},40),
   e('F2','UNKNOWN',3,'planner-post',{},100),
   e('F2','PASS',4,'late-receipt',{},200),
   e('F3','NOT_RUN',5,'poster'),
 ])
 assert.equal(report.first_problem.feature,'F2')
 assert.equal(report.first_problem.action,'planner-post')
 assert.equal(report.features.find(f=>f.id==='F2').status,'UNKNOWN')
 assert.equal(report.features.find(f=>f.id==='F3').status,'NOT_RUN')
 assert.equal(report.features.find(f=>f.id==='F7').status,'UNOBSERVED')
})

test('human quality does not change API execution verdict or masquerade as provider score', () => {
 const report=summarizeTrace([
   e('F4','PASS',1,'ffmpeg',{},1234),
   e('F4','QUALITY_REVIEW',2,'quality',{score:1,note:'Too basic'}),
   e('F4','QUALITY_REVIEW',3,'quality',{score:9,note:'Forged invalid score'}),
 ])
 const f=report.features.find(f=>f.id==='F4')
 assert.equal(f.status,'PASS')
 assert.equal(f.quality_latest,1)
 assert.equal(f.quality_count,1)
 assert.equal(f.duration_ms,1234)
})

test('comparison never manufactures a baseline, quality or latency improvement', () => {
 const comparison=compareTraceRuns([e('F2','PASS',1,'draft',{},600)],[
    e('F2','PASS',1,'draft',{},500),
    e('F2','QUALITY_REVIEW',2,'review',{score:4}),
 ])
 const f=comparison.find(x=>x.id==='F2')
 assert.equal(f.duration_delta_ms,100)
 assert.equal(f.score_delta,null)
 assert.equal(f.baseline_score,4)
 assert.equal(f.score,null)
})

test('aggregate counts NOT_RUN and UNKNOWN separately and calculates bounded observed p95', () => {
 const observed=aggregateFeatureHistory([
   {events:[e('F2','PASS',1,'draft',{},100),e('F2','QUALITY_REVIEW',2,'review',{score:2})]},
   {events:[e('F2','PASS',1,'draft',{},200),e('F2','QUALITY_REVIEW',2,'review',{score:4})]},
   {events:[e('F2','UNKNOWN',1,'draft')]},
   {events:[e('F2','NOT_RUN',1,'draft')]},
 ])
 const f=observed.find(x=>x.id==='F2')
 assert.deepEqual([f.passed,f.failed,f.uncertain,f.skipped,f.p95_ms,f.quality_mean], [2,0,1,1,200,3])
})

test('empty data remains unobserved rather than falsely passing', () => {
 const summary=summarizeTrace([])
 assert.equal(summary.status,'UNOBSERVED')
 assert.ok(summary.features.every(x=>x.status==='UNOBSERVED'))
})

test('completed F2 prompt remains PASS when its optional campaign substage was NOT_RUN',()=>{
 const events=[
   e('F1','PASS',1,'tenant-and-rights'),
   e('F2','PASS',2,'prompt-improvement'),
   e('F2','NOT_RUN',3,'campaign-planning'),
   e('F3','NOT_RUN',4,'poster-model'),
   e('F4','NOT_RUN',5,'ffmpeg-reel'),
 ]
 const f=summarizeTrace(events).features.find(row=>row.id==='F2')
 assert.equal(f.status,'PASS')
 assert.equal(f.observed_steps,2)
 assert.equal(f.first_problem,null)
 const historical=aggregateFeatureHistory([{events}]).find(row=>row.id==='F2')
 assert.equal(historical.passed,1)
 assert.equal(historical.skipped,0)
})
