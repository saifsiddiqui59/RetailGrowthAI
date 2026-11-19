import test from 'node:test'
import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import {scopedFeature3Preview, discardFailedPrivateModelPreview, createFeature3PrivateModelUrlLedger} from '../../frontend/src/features/creative/feature3-private-preview.mjs'

const one='a1000000-0000-4000-8000-000000000001'
const two='b1000000-0000-4000-8000-000000000002'
test('Feature3 current tenant retains its own private decoded pixels', () => {
  const original={scope:one,models:[{model_id:'model-1'}],
    imageMap:{'asset-1':{secret:true}},busy:true,message:'shop one'}
  assert.strictEqual(scopedFeature3Preview(original,one),original)
})
test('shop switch hides all previous model media synchronously before effect cleanup', () => {
  const previous={scope:one,models:[{model_id:'model-1'}],
    imageMap:{'asset-1':{secret:true}},busy:true,message:'shop one'}
  const next=scopedFeature3Preview(previous,two)
  assert.deepEqual(next,{models:[],imageMap:{},busy:false,message:''})
  assert.notStrictEqual(next.models,previous.models)
  assert.notStrictEqual(next.imageMap,previous.imageMap)
})
test('fail-closed on invalid or unscoped async preview state',()=>{
  for (const bad of [null,{},[],{scope:one,models:null,imageMap:{}},
                    {scope:one,models:[],imageMap:null}]) {
    assert.deepEqual(scopedFeature3Preview(bad,one),
      {models:[],imageMap:{},busy:false,message:''})
  }
})

test('failed private image decoder immediately revokes only failed Blob and prevents later double revoke',()=>{
  const first='blob:https://fixture.test/private-one'
  const valid='blob:https://fixture.test/private-two'
  const opened=[first,valid]
  const revoked=[]
  assert.equal(discardFailedPrivateModelPreview(opened,first,u=>revoked.push(u)),true)
  assert.deepEqual(opened,[valid])
  assert.deepEqual(revoked,[first])
  assert.equal(discardFailedPrivateModelPreview(opened,first,u=>revoked.push(u)),false)
  assert.deepEqual(revoked,[first])
  assert.deepEqual(opened,[valid])
})
test('never use external or unowned image URLs as private preview cleanup input',()=>{
  const valid='blob:https://fixture.test/valid'
  const opened=[valid]
  const revoked=[]
  for (const bad of ['https://evil.example/asset','/storage/private/key',null]) {
    assert.throws(()=>discardFailedPrivateModelPreview(opened,bad,u=>revoked.push(u)))
  }
  assert.equal(discardFailedPrivateModelPreview(opened,'blob:https://other.example/unknown',u=>revoked.push(u)),false)
  assert.deepEqual(opened,[valid])
  assert.deepEqual(revoked,[])
})

test('same-shop JWT/API identity rotation hides old decoded model pixels before effect cleanup',()=>{
  const apiA={session:'fictional-test-A'}
  const apiB={session:'fictional-test-B'}
  const previous={scope:one,api:apiA,models:[{model_id:'private-model'}],
    imageMap:{'asset-1':{secret:true}},busy:false,message:'private'}
  assert.strictEqual(scopedFeature3Preview(previous,one,apiA),previous)
  assert.deepEqual(scopedFeature3Preview(previous,one,apiB),
    {models:[],imageMap:{},busy:false,message:''})
  assert.deepEqual(scopedFeature3Preview({...previous,api:null},one,apiA),
    {models:[],imageMap:{},busy:false,message:''})
})

test('F3-10 private-model Blob revocation failures keep the owned URL for an explicit retry',()=>{
  const privateURL='blob:https://fixture.test/retry-private'
  const opened=[privateURL]
  assert.throws(()=>discardFailedPrivateModelPreview(opened,privateURL,()=>{
    throw Error('Browser revoke unavailable')
  }),/Browser revoke unavailable/)
  assert.deepEqual(opened,[privateURL])
  const revoked=[]
  assert.equal(discardFailedPrivateModelPreview(opened,privateURL,url=>revoked.push(url)),true)
  assert.deepEqual(revoked,[privateURL])
  assert.deepEqual(opened,[])
})


test('F3-10 private model URL ledger removes only successful revocations and preserves failed handles',()=>{
  const first='blob:https://fixture.test/private-1'
  const second='blob:https://fixture.test/private-2'
  const calls=[]
  let deny=true
  const ledger=createFeature3PrivateModelUrlLedger(url=>{
    calls.push(url)
    if(url===second && deny)throw Error('Browser revoke failed')
  })
  ledger.track(first)
  ledger.track(second)
  assert.equal(ledger.pendingCount(),2)
  assert.throws(()=>ledger.releaseAll(),/cleanup pending/)
  assert.equal(ledger.pendingCount(),1)
  assert.equal(ledger.owns(first),false)
  assert.equal(ledger.owns(second),true)
  assert.equal(ledger.release(first),false)
  deny=false
  assert.equal(ledger.releaseAll(),0)
  assert.equal(ledger.pendingCount(),0)
  assert.deepEqual(calls,[first,second,second])
})
test('F3-10 private ledger denies foreign URLs, duplicate handles and forged owner input',()=>{
  const calls=[]
  const ledger=createFeature3PrivateModelUrlLedger(url=>calls.push(url))
  const one='blob:https://fixture.test/owned'
  for(const bad of ['https://attacker.invalid/private','/storage/private.png',
    'javascript:alert(1)','data:image/png,evil','blob:\nforged',null,{}]){
    assert.throws(()=>ledger.track(bad))
  }
  ledger.track(one)
  assert.throws(()=>ledger.track(one))
  assert.equal(ledger.release('blob:https://other.invalid/not-owned'),false)
  assert.throws(()=>ledger.releaseMany(null))
  assert.equal(ledger.releaseMany([one,one]),0)
  assert.deepEqual(calls,[one])
  assert.equal(ledger.releaseAll(),0)
  assert.throws(()=>createFeature3PrivateModelUrlLedger(null))
})
test('F3-10 source host hides old model pixels before release and fences same-tick loads',async()=>{
  const source=await readFile(new URL('../../frontend/src/features/creative/Feature3PosterHost.jsx',import.meta.url),'utf8')
  assert.match(source,/createFeature3PrivateModelUrlLedger/)
  assert.match(source,/modelReadTicket\.current!==null/)
  assert.match(source,/previewLedger\.current\.track\(candidateURL\)/)
  assert.match(source,/previewLedger\.current\.releaseMany\(opened\)/)
  assert.match(source,/cleanup pending/)
  assert.ok(source.indexOf('setPreview({...empty(scope), api:provider, busy:true})')<
    source.indexOf('release()\n      const rows = await api.listModels(scope)'))
  assert.ok(!source.includes('urls.current'))
  assert.ok(!source.includes('opened.forEach'))
})
