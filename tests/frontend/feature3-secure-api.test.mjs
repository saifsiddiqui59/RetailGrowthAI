import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { createFeature3Api } from '../../frontend/src/features/creative/feature3-api.mjs'

const sid='a1000000-0000-4000-8000-000000000001'
const cid='a1000000-0000-4000-8000-000000000002'
const did='a1000000-0000-4000-8000-000000000003'
const pid='a1000000-0000-4000-8000-000000000004'
const poster={schema:'retailgrowth.poster.v2',shop_id:sid,format:'square',
  template:'fashion',background:'#FFFFFF',
  layers:[{id:'headline',type:'text',x:0.1,y:0.1,w:0.8,h:0.15,
  text:'Shop our new collection',color:'#222222',font_size:34,bold:true}]}
const ok=(data,status=200)=>({ok:true,status,json:async()=>data})
const draftHistoryRow=Object.freeze({
  id:pid,shop_id:sid,campaign_id:cid,day_id:did,revision:2,status:'DRAFT',
  design:poster,server_document_sha256:'a'.repeat(64),variation_of:null,
})

function setup(handler) {
  const calls=[]
  const api=createFeature3Api({
    baseUrl:'https://retailgrowth.invalid',tokenProvider:async()=> 'user-jwt',
    fetchImpl:async (url,options)=>{
      calls.push({url,options})
      assert.match(url,/^https:\/\/retailgrowth.invalid\/api\//)
      assert.equal(options.headers.Authorization,'Bearer user-jwt')
      assert.equal(options.redirect,'error')
      return handler(url,options)
    },
  })
  return {api,calls}
}
test('create v2 poster once and require matching tenant, draft and digest',async()=>{
  const {api,calls}=setup(()=>ok({design_id:pid,revision:1,
    shop_id:sid,campaign_id:cid,day_id:did,status:'DRAFT',
    rendered:false,server_document_sha256:'a'.repeat(64)}))
  const response=await api.saveDesign(sid,cid,did,poster)
  assert.equal(response.design_id,pid)
  assert.equal(calls.length,1)
  assert.equal(calls[0].options.method,'POST')
  const sent=JSON.parse(calls[0].options.body)
  assert.equal(sent.expected_revision,0)
  assert.equal(sent.design.shop_id,sid)
  assert.ok(!('approved' in sent))
})
test('no retry of uncertain POST or 503',async()=>{
  const {api,calls}=setup(async()=>{throw TypeError('network lost after write')})
  await assert.rejects(api.saveDesign(sid,cid,did,poster),TypeError)
  assert.equal(calls.length,1)
  const second=setup(()=>({ok:false,status:503,json:async()=>({error:'SERVICE_NOT_CONFIGURED'})}))
  await assert.rejects(second.api.saveDesign(sid,cid,did,poster))
  assert.equal(second.calls.length,1)
})
test('reject wrong shop, stale revision, invented approval and malicious response',async()=>{
  const {api,calls}=setup(()=>ok({design_id:pid,revision:1,
    shop_id:'a1000000-0000-4000-8000-000000000099',campaign_id:cid,
    day_id:did,status:'DRAFT',rendered:false,
    server_document_sha256:'a'.repeat(64)}))
  await assert.rejects(api.saveDesign(sid,cid,did,poster),/Untrusted/)
  await assert.rejects(api.saveDesign(sid,cid,did,{...poster,shop_id:cid}))
  await assert.rejects(api.saveDesign(sid,cid,did,poster,{expectedRevision:2}))
  await assert.rejects(api.saveDesign(sid,cid,did,{...poster,approved:true}))
  assert.equal(calls.length,1)
})
test('RLS history requires precise campaign/day and refuses foreign rows',async()=>{
  const good=setup(()=>ok({shop_id:sid,campaign_id:cid,day_id:did,
    designs:[{...draftHistoryRow}]}))
  assert.equal((await good.api.listDesigns(sid,cid,did)).length,1)
  const bad=setup(()=>ok({shop_id:sid,campaign_id:cid,day_id:did,
    designs:[{...draftHistoryRow,shop_id:cid}]}))
  await assert.rejects(bad.api.listDesigns(sid,cid,did),/Untrusted/)
})
test('mounted Poster Studio preserves local fallback and opt-in feature3Api branch',async()=>{
  const req=createRequire(new URL('../../frontend/package.json',import.meta.url))
  const {transformWithEsbuild}=await import(req.resolve('vite'))
  const dir='../../frontend/src/features/creative/'
  for(const name of ['Feature3SecureDraftWorkspace.jsx','Feature3StudioPanel.jsx','PosterStudio.jsx']){
    const src=await readFile(new URL(dir+name,import.meta.url),'utf8')
    await transformWithEsbuild(src,name,{loader:'jsx'})
  }
  const host=await readFile(new URL(dir+'PosterStudio.jsx',import.meta.url),'utf8')
  const workspace=await readFile(new URL(dir+'Feature3SecureDraftWorkspace.jsx',import.meta.url),'utf8')
  assert.match(host,/feature3Api = null/)
  assert.match(host,/showCpuStudio && \(feature3Api/)
  assert.match(workspace,/listDesigns\(shopId, campaignId, dayId\)/)
  assert.match(workspace,/saveDesign\(/)
  assert.match(workspace,/status !== 'DRAFT'/)
  assert.ok(!workspace.includes('fetch('))
})


test('F3-09 signed history validates exact versioned records and review states',async()=>{
  const payload=rows=>({shop_id:sid,campaign_id:cid,day_id:did,designs:rows})
  const rows=['DRAFT','APPROVED','REJECTED'].map((status,i)=>({
    ...draftHistoryRow,id:[pid,'a1000000-0000-4000-8000-000000000005',
      'a1000000-0000-4000-8000-000000000006'][i],status,
  }))
  const good=setup(()=>ok(payload(rows)))
  const received=await good.api.listDesigns(sid,cid,did)
  assert.deepEqual(received.map(row=>row.status),['DRAFT','APPROVED','REJECTED'])
  assert.equal(Object.isFrozen(received),true)
  assert.ok(received.every(Object.isFrozen))
  assert.equal(received[0].design.shop_id,sid)
  assert.equal(good.calls.length,1)
})
test('F3-09 private history denies duplicate and forged rows before UI cache',async()=>{
  const variants=[
    [draftHistoryRow,draftHistoryRow],
    [{...draftHistoryRow,revision:0}],
    [{...draftHistoryRow,revision:true}],
    [{...draftHistoryRow,id:'../foreign'}],
    [{...draftHistoryRow,variation_of:'https://foreign.example'}],
    [{...draftHistoryRow,server_document_sha256:'NOT_A_DIGEST'}],
    [{...draftHistoryRow,shop_id:cid}],
    [{...draftHistoryRow,design:{...poster,shop_id:cid}}],
    [{...draftHistoryRow,design:{...poster,layers:[{type:'image',url:'https://evil.invalid'}]}}],
    [{...draftHistoryRow,status:'PUBLISHED'}],
    [{...draftHistoryRow,signed_url:'https://evil.invalid'}],
    [{...draftHistoryRow,object_path:'foreign/secret.png'}],
    [{...draftHistoryRow,approved_for_publication:true}],
    [null],
  ]
  for(const rows of variants){
    const {api}=setup(()=>ok({shop_id:sid,campaign_id:cid,day_id:did,designs:rows}))
    await assert.rejects(api.listDesigns(sid,cid,did),/Untrusted|Invalid|Duplicate|Unknown|layer/i)
  }
  for(const malformed of [
    {shop_id:sid,campaign_id:cid,day_id:did,designs:[],signed_url:'https://evil.invalid'},
    {shop_id:sid,campaign_id:cid,day_id:did,designs:null},
  ]){
    const {api}=setup(()=>ok(malformed))
    await assert.rejects(api.listDesigns(sid,cid,did),/Untrusted/)
  }
})
test('F3-09 workspace displays review states but edits only DRAFT',async()=>{
  const source=await readFile(new URL(
    '../../frontend/src/features/creative/Feature3SecureDraftWorkspace.jsx',import.meta.url),'utf8')
  assert.match(source,/Private poster review states/)
  assert.match(source,/Server status: APPROVED \(not published\)/)
  assert.match(source,/Server status: REJECTED \(read-only\)/)
  assert.match(source,/saved\.filter\(d=>d\.status==='DRAFT'\)/)
  assert.match(source,/if \(chosen\.status !== 'DRAFT'\)/)
  assert.doesNotMatch(source,/publishPoster|approvePoster/)
})
