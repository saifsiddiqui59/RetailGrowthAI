import test from 'node:test'
import assert from 'node:assert/strict'
import {randomUUID} from 'node:crypto'
import {
  scopedFeature3GeneratedHistory,validateFeature3GeneratedHistory,
} from '../../frontend/src/features/creative/feature3-generated-history.mjs'

const SHOP=randomUUID(), OTHER=randomUUID()
const JOBS=['QUEUED','RUNNING','SUCCEEDED','FAILED'].map(status=>({
  id:randomUUID(),shop_id:SHOP,status,
}))

test('private generated history validates only own-shop exact metadata rows',()=>{
  const rows=validateFeature3GeneratedHistory(SHOP,JOBS)
  assert.equal(rows.length,4)
  assert.deepEqual(rows.map(x=>x.status),['QUEUED','RUNNING','SUCCEEDED','FAILED'])
  assert.equal(Object.isFrozen(rows),true)
  assert.equal(Object.isFrozen(rows[0]),true)
  assert.equal(rows.some(x=>'url' in x),false)
  assert.equal(rows.some(x=>'output_asset_id' in x),false)
})
test('foreign shop and revoked identity never retain stale private job history',()=>{
  const state={shopId:SHOP,jobs:JOBS,busy:false,message:'tenant private'}
  assert.equal(scopedFeature3GeneratedHistory(state,SHOP).jobs.length,4)
  assert.equal(scopedFeature3GeneratedHistory(state,OTHER).jobs.length,0)
  assert.equal(scopedFeature3GeneratedHistory(state,OTHER).message,'')
  assert.equal(scopedFeature3GeneratedHistory(state,'not-a-uuid').jobs.length,0)
  assert.equal(scopedFeature3GeneratedHistory(null,SHOP).jobs.length,0)
})
test('deny extra download URLs, keys, spoofed approvals, foreign and duplicate records',()=>{
  const changes=[
    [{...JOBS[0],shop_id:OTHER}],
    [{...JOBS[0],url:'https://foreign.example/private'}],
    [{...JOBS[0],object_path:'other/private.png'}],
    [{...JOBS[0],approved_model:true}],
    [{...JOBS[0],gpu_submission_enabled:true}],
    [{...JOBS[0],status:'PUBLISHED'}],
    [{...JOBS[0],id:'../../shop'}],
    [JOBS[0],JOBS[0]],
    Array.from({length:21},()=>({id:randomUUID(),shop_id:SHOP,status:'FAILED'})),
    [null], [false],
  ]
  for(const rows of changes) {
    assert.throws(()=>validateFeature3GeneratedHistory(SHOP,rows))
    assert.equal(scopedFeature3GeneratedHistory({shopId:SHOP,jobs:rows},SHOP).jobs.length,0)
  }
})
test('zero generated jobs is a valid safe empty response; malformed access is not',()=>{
  assert.deepEqual(validateFeature3GeneratedHistory(SHOP,[]),[])
  for(const value of [null,false,{},'not rows',undefined]) {
    assert.throws(()=>validateFeature3GeneratedHistory(SHOP,value))
  }
})
