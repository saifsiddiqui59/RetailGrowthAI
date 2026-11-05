import test from 'node:test'
import assert from 'node:assert/strict'
import { randomUUID } from 'node:crypto'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { feature3ContextKey } from '../../frontend/src/features/creative/feature3-context.mjs'
import {
  scopedFeature3WorkspaceValue,currentFeature3WorkspaceRequest,
  createFeature3WorkspaceReadGate,feature3DraftMediaReady,
} from '../../frontend/src/features/creative/feature3-workspace-scope.mjs'

const shop=randomUUID(), otherShop=randomUUID()
const campaign=randomUUID(), day=randomUUID(), anotherDay=randomUUID()
const scope=feature3ContextKey({shopId:shop,campaignId:campaign,dayId:day})
const changedDay=feature3ContextKey({shopId:shop,campaignId:campaign,dayId:anotherDay})
const foreign=feature3ContextKey({shopId:otherShop,campaignId:campaign,dayId:day})

test('show only same-shop, same-campaign, same-day saved drafts, jobs and messages',()=>{
  const oldDrafts={scope,value:[{id:randomUUID(),status:'DRAFT',private:true}]}
  const oldJobs={scope,value:[{id:randomUUID(),status:'SUCCEEDED',private:true}]}
  const oldMessage={scope,value:'old tenant saved successfully'}
  for(const row of [oldDrafts,oldJobs,oldMessage]){
    assert.strictEqual(scopedFeature3WorkspaceValue(row,scope,null),row.value)
    assert.equal(scopedFeature3WorkspaceValue(row,changedDay,null),null)
    assert.equal(scopedFeature3WorkspaceValue(row,foreign,null),null)
  }
  assert.deepEqual(scopedFeature3WorkspaceValue(oldDrafts,changedDay,[]),[])
  assert.equal(scopedFeature3WorkspaceValue(null,scope,'hidden'),'hidden')
  assert.equal(scopedFeature3WorkspaceValue(oldDrafts,'','hidden'),'hidden')
})

test('in-flight response cannot overwrite a different day, account/API or newer request',()=>{
  const api={id:'signed source'},replacement={id:'new session'}
  let active={scopeKey:scope,feature3Api:api}
  const attempt=1
  assert.equal(currentFeature3WorkspaceRequest(active,scope,api,attempt,attempt),true)
  active={scopeKey:changedDay,feature3Api:api}
  assert.equal(currentFeature3WorkspaceRequest(active,scope,api,attempt,attempt),false)
  active={scopeKey:foreign,feature3Api:api}
  assert.equal(currentFeature3WorkspaceRequest(active,scope,api,attempt,attempt),false)
  active={scopeKey:scope,feature3Api:replacement}
  assert.equal(currentFeature3WorkspaceRequest(active,scope,api,attempt,attempt),false)
  active={scopeKey:scope,feature3Api:api}
  assert.equal(currentFeature3WorkspaceRequest(active,scope,api,attempt,attempt+1),false)
  assert.equal(currentFeature3WorkspaceRequest(active,scope,api,0,0),false)
})

test('mounted private workspace compiles and fences every async metadata/receipt path',async()=>{
  const file=new URL('../../frontend/src/features/creative/Feature3SecureDraftWorkspace.jsx',import.meta.url)
  const source=await readFile(file,'utf8')
  const require=createRequire(new URL('../../frontend/package.json',import.meta.url))
  const {transformWithEsbuild}=await import(require.resolve('vite'))
  await transformWithEsbuild(source,file.pathname,{loader:'jsx'})
  assert.match(source,/currentFeature3WorkspaceRequest/)
  assert.match(source,/pendingHistory\.current/)
  assert.match(source,/pendingJobs\.current/)
  assert.match(source,/activeScope\.current\.scopeKey===requestKey/)
  assert.match(source,/scopedFeature3WorkspaceValue\(savedState,scopeKey,\[\],feature3Api\)/)
  assert.match(source,/scopedFeature3WorkspaceValue\(generatedState,scopeKey,\[\],feature3Api\)/)
  assert.match(source,/scopedFeature3WorkspaceValue\(reopenedState,scopeKey,null,feature3Api\)/)
  assert.match(source,/ticket\.current=\{scope,provider,designId:response\.design_id/)
  assert.match(source,/chosen\.campaign_id!==campaignId/)
  assert.match(source,/chosen\.day_id!==dayId/)
  assert.match(source,/Save not confirmed\. Do not retry blindly/)
  assert.doesNotMatch(source,/fetch\(/)
})


test('same shop/day and replaced signed API session hides previous private state on first paint',()=>{
  const prior={session:1},fresh={session:2}
  for(const value of [[{private:true}],'old private receipt',true]){
    const state={scope,provider:prior,value}
    assert.strictEqual(scopedFeature3WorkspaceValue(state,scope,null,prior),value)
    assert.strictEqual(scopedFeature3WorkspaceValue(state,scope,null,fresh),null)
    assert.strictEqual(scopedFeature3WorkspaceValue({scope,value},scope,null,fresh),null)
  }
})

test('mounted workspace fences same-day provider, CAS and signed links before effects',async()=>{
  const source=await readFile(new URL('../../frontend/src/features/creative/Feature3SecureDraftWorkspace.jsx',import.meta.url),'utf8')
  assert.match(source,/generatedLink\?\.provider===feature3Api/)
  assert.match(source,/ticket\.current\.provider!==provider/)
  assert.match(source,/pending\.current\.provider===feature3Api/)
  assert.match(source,/scopedFeature3WorkspaceValue\(savedState,scopeKey,\[\],feature3Api\)/)
})

test('workspace busy and status setters preserve signed API identity for current first paint', async()=>{
  const source=await readFile(new URL('../../frontend/src/features/creative/Feature3SecureDraftWorkspace.jsx',import.meta.url),'utf8')
  assert.ok(source.includes('const setMessage=value=>setMessageState({scope:scopeKey,provider:feature3Api,value})'))
  assert.ok(source.includes('const setBusy=value=>setBusyState({scope:scopeKey,provider:feature3Api,value})'))
  const api={session:'owner'},replacement={session:'other'}
  const busy={scope,provider:api,value:true}
  const status={scope,provider:api,value:'Private save still pending'}
  assert.equal(scopedFeature3WorkspaceValue(busy,scope,false,api),true)
  assert.equal(scopedFeature3WorkspaceValue(status,scope,'',api),'Private save still pending')
  assert.equal(scopedFeature3WorkspaceValue(busy,scope,false,replacement),false)
  assert.equal(scopedFeature3WorkspaceValue(status,scope,'',replacement),'')
})

test('F3-09 private draft/history/download reads are single-flight synchronously',()=>{
  const gate=createFeature3WorkspaceReadGate(),provider={name:'signed mock'}
  const first=gate.begin(scope,provider,'drafts')
  assert.ok(first)
  assert.equal(Object.isFrozen(first),true)
  assert.equal(gate.busy(),true)
  for(const kind of ['drafts','generated-jobs','download']){
    assert.equal(gate.begin(scope,provider,kind),null,
      'second click cannot start another private GET before React rerenders')
  }
  assert.equal(gate.begin(foreign,{name:'other'},'download'),null)
  assert.equal(gate.isCurrent(first,scope,provider),true)
  assert.equal(gate.isCurrent(first,foreign,provider),false)
  assert.equal(gate.isCurrent(first,scope,{name:'new JWT'}),false)
  assert.equal(gate.release(first),true)
  assert.equal(gate.busy(),false)
  assert.equal(gate.release(first),false)
  const next=gate.begin(scope,provider,'generated-jobs')
  assert.ok(next)
  assert.equal(gate.release(first),false)
  assert.equal(gate.isCurrent(next,scope,provider),true)
  assert.equal(gate.release(next),true)
  assert.equal(gate.begin(scope,provider,'unreviewed-paid-GPU'),null)
  assert.equal(gate.begin('',provider,'download'),null)
  assert.equal(gate.begin(scope,null,'download'),null)
})

test('F3-13 cancelled old tenant/JWT read cannot unlock newer private work',async()=>{
  const gate=createFeature3WorkspaceReadGate(),apiA={signed:'A'},apiB={signed:'B'}
  const old=gate.begin(scope,apiA,'download')
  let finish
  const pending=new Promise(resolve=>{finish=resolve})
  const late=pending.then(receipt=>gate.isCurrent(old,scope,apiA)?receipt:null)
    .finally(()=>gate.release(old))
  gate.cancel()
  const fresh=gate.begin(foreign,apiB,'drafts')
  finish({url:'blob:https://foreign.example/unauthorized'})
  assert.equal(await late,null,'old async receipt must be discarded')
  assert.equal(gate.busy(),true,'stale finally cannot release current read')
  assert.equal(gate.isCurrent(fresh,foreign,apiB),true)
  assert.equal(gate.release(fresh),true)
  assert.equal(gate.busy(),false)
})

test('F3-09 mounted CPU workspace gates all private reads and save/reopen against same-tick clicks',async()=>{
  const source=await readFile(new URL(
    '../../frontend/src/features/creative/Feature3SecureDraftWorkspace.jsx',import.meta.url),'utf8')
  for (const kind of ['drafts','generated-jobs','download']) {
    assert.match(source,new RegExp("readGate\\.current\\.begin\\([^\\n]+"+kind))
  }
  assert.match(source,/readGate\.current\.cancel\(\)/)
  assert.equal((source.match(/readGate\.current\.release\(guard\)/g)||[]).length,3)
  assert.equal((source.match(/readGate\.current\.isCurrent\(guard/g)||[]).length,3)
  assert.match(source,/if \(disabled \|\| busy \|\| readGate\.current\.busy\(\)/)
  assert.match(source,/if \(disabled \|\| readGate\.current\.busy\(\)/)
  assert.match(source,/No v2 private poster drafts exist for this day/)
  assert.doesNotMatch(source,/fetch\(/)
})


test('F3-09 private draft media must be an own registered image with decoded dimensions',()=>{
  const image={complete:true,naturalWidth:1080,naturalHeight:1350}
  const draft=id=>({layers:[{type:'text'}, {type:'image',asset_id:id}]})
  assert.equal(feature3DraftMediaReady(draft('owned'),{owned:image}),true)
  const nullPrototype=Object.create(null)
  nullPrototype.owned=image
  assert.equal(feature3DraftMediaReady(draft('owned'),nullPrototype),true)
  assert.equal(feature3DraftMediaReady({layers:[{type:'text'}]},{}),true)
  for(const key of ['owned','constructor','toString','__proto__']){
    const inherited=Object.create({[key]:image})
    assert.equal(feature3DraftMediaReady(draft(key),inherited),false,
      'A prototype property cannot authorize a private registered image')
  }
  for(const invalid of [null,{}, {complete:false,naturalWidth:1080,naturalHeight:1350},
    {complete:'true',naturalWidth:1080,naturalHeight:1350},
    {complete:true,naturalWidth:'1080',naturalHeight:1350},
    {complete:true,naturalWidth:0,naturalHeight:1350},
    {complete:true,naturalWidth:1080,naturalHeight:Infinity}]){
    assert.equal(feature3DraftMediaReady(draft('owned'),{owned:invalid}),false)
  }
  assert.equal(feature3DraftMediaReady(draft('owned'),null),false)
  assert.equal(feature3DraftMediaReady(draft('owned'),[]),false)
  assert.equal(feature3DraftMediaReady(null,{}),false)
  assert.equal(feature3DraftMediaReady({layers:[null]},{}),false)
})

test('F3-09 private draft save and reopen both use the same own-image grant fence',async()=>{
  const source=await readFile(new URL('../../frontend/src/features/creative/Feature3SecureDraftWorkspace.jsx',import.meta.url),'utf8')
  assert.match(source,/!feature3DraftMediaReady\(design,imageMap\)/)
  assert.match(source,/!feature3DraftMediaReady\(submitted,imageMap\)/)
  assert.doesNotMatch(source,/imageMap\[layer\.asset_id\]/)
})
