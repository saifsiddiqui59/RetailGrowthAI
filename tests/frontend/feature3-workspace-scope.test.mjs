import test from 'node:test'
import assert from 'node:assert/strict'
import { randomUUID } from 'node:crypto'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { feature3ContextKey } from '../../frontend/src/features/creative/feature3-context.mjs'
import {
  scopedFeature3WorkspaceValue,currentFeature3WorkspaceRequest,
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
  assert.match(source,/const setMessage=value=>setMessageState\\(\\{scope:scopeKey,provider:feature3Api,value\\}\\)/)
  assert.match(source,/const setBusy=value=>setBusyState\\(\\{scope:scopeKey,provider:feature3Api,value\\}\\)/)
  const api={session:'owner'},replacement={session:'other'}
  const busy={scope,provider:api,value:true}
  const status={scope,provider:api,value:'Private save still pending'}
  assert.equal(scopedFeature3WorkspaceValue(busy,scope,false,api),true)
  assert.equal(scopedFeature3WorkspaceValue(status,scope,'',api),'Private save still pending')
  assert.equal(scopedFeature3WorkspaceValue(busy,scope,false,replacement),false)
  assert.equal(scopedFeature3WorkspaceValue(status,scope,'',replacement),'')
})
