import test from 'node:test'
import assert from 'node:assert/strict'
import {randomUUID} from 'node:crypto'
import {readFileSync} from 'node:fs'
import {
  scopedFeature3GeneratedHistory,validateFeature3GeneratedHistory,
  filteredFeature3GeneratedHistory,FEATURE3_HISTORY_FILTERS,
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

test('bounded status filters operate only on strict current-shop private metadata',()=>{
  assert.deepEqual(FEATURE3_HISTORY_FILTERS,
    ['ALL','QUEUED','RUNNING','SUCCEEDED','FAILED'])
  assert.equal(Object.isFrozen(FEATURE3_HISTORY_FILTERS),true)
  const original=validateFeature3GeneratedHistory(SHOP,JOBS)
  assert.deepEqual(filteredFeature3GeneratedHistory(SHOP,original,'ALL'),original)
  for(const status of ['QUEUED','RUNNING','SUCCEEDED','FAILED']){
    const matching=filteredFeature3GeneratedHistory(SHOP,original,status)
    assert.equal(matching.length,1)
    assert.equal(matching[0].status,status)
    assert.equal(matching[0].shop_id,SHOP)
    assert.equal(Object.isFrozen(matching),true)
    assert.equal(Object.isFrozen(matching[0]),true)
    assert.equal('url' in matching[0],false)
    assert.equal('approved_model' in matching[0],false)
  }
  assert.equal(original.length,4)
})
test('filter cannot rescue foreign, malformed or forged finished job rows',()=>{
  for(const bad of ['PUBLISHED','APPROVED','../../other','','all',null]){
    assert.throws(()=>filteredFeature3GeneratedHistory(SHOP,JOBS,bad))
  }
  assert.throws(()=>filteredFeature3GeneratedHistory(OTHER,JOBS,'SUCCEEDED'))
  assert.throws(()=>filteredFeature3GeneratedHistory(SHOP,
    [{...JOBS[2],signed_url:'https://evil.example/asset'}],'SUCCEEDED'))
  assert.deepEqual(filteredFeature3GeneratedHistory(SHOP,[],'SUCCEEDED'),[])
})
test('React history filter cancels pending binary work and frees local previews',()=>{
  const jsx=readFileSync(new URL(
    '../../frontend/src/features/creative/Feature3GeneratedHistory.jsx',
    import.meta.url),'utf8')
  assert.match(jsx,/aria-label="Filter private generated jobs by status"/)
  assert.match(jsx,/clearImage\(\)\s+setFilter\(event.target.value\)/)
  assert.match(jsx,/visibleJobs\.some\(row=>row.id===image.jobId/)
  assert.match(jsx,/setFilter\('ALL'\)/)
  assert.match(jsx,/registry\.current\.clear\(\)/)
  assert.match(jsx,/Generated — unreviewed/)
  assert.doesNotMatch(jsx,/getGeneratedImageDownload\(/)
})

test('F3-13 private history state envelope never forwards signed URLs or approval flags',()=>{
  const clean=scopedFeature3GeneratedHistory({
    shopId:SHOP,jobs:JOBS,busy:true,message:'Checking private jobs',
  },SHOP)
  assert.deepEqual(Object.keys(clean).sort(),['busy','jobs','message','shopId'])
  assert.equal(clean.busy,true)
  assert.equal(clean.message,'Checking private jobs')
  assert.equal(clean.jobs.length,4)
  assert.equal(Object.isFrozen(clean),true)

  for(const injected of [
    {signed_url:'https://evil.invalid/private.png'},
    {object_path:'foreign-shop/private.png'},
    {approved:true},
    {publishApproved:true},
    {provider:'external'},
    {message:{url:'https://evil.invalid'}},
    {message:'x'.repeat(241)},
    {busy:{approved:true}},
  ]) {
    const result=scopedFeature3GeneratedHistory({
      shopId:SHOP,jobs:JOBS,busy:false,message:'',...injected,
    },SHOP)
    assert.deepEqual(result.jobs,[])
    assert.equal(result.message,'')
    assert.equal(result.busy,false)
    assert.equal(Object.keys(result).length,4)
  }
  const minimal=scopedFeature3GeneratedHistory({shopId:SHOP,jobs:JOBS},SHOP)
  assert.equal(minimal.jobs.length,4)
  assert.equal(minimal.message,'')
  assert.equal(minimal.busy,false)
})
