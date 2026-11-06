// F2-19/F2-20 signed read-only status + original private WAV client.
// Real source module, intercepted network. No live JWT, audio provider,
// model inference, public asset URL, DB migration or cloud write.
import test from 'node:test'
import assert from 'node:assert/strict'
import {createHash,webcrypto} from 'node:crypto'
import {readFileSync} from 'node:fs'
import {fileURLToPath} from 'node:url'
import {resolve,dirname} from 'node:path'
import {createFeature2PrivateVoiceReader} from '../../frontend/src/features/voiceover/feature2-private-http.mjs'

const SHOP='11111111-1111-4111-8111-111111111111'
const CAMP='22222222-2222-4222-8222-222222222222'
const JOB='55555555-5555-4555-8555-555555555555'
const ASSET='44444444-4444-4444-8444-444444444444'
const PLAN='b'.repeat(64)
const WAV=new Uint8Array(280)
WAV.set(Buffer.from('RIFF'),0)
WAV.set(Buffer.from('WAVE'),8)
WAV.set(Buffer.from('fmt '),12)
WAV.set(Buffer.from('data'),36)
const SHA=createHash('sha256').update(WAV).digest('hex')
if(!globalThis.crypto?.subtle)globalThis.crypto=webcrypto

const validStatus=()=>({
  schema:'retailgrowth.feature2-private-voice-job-status.v1',
  shop_id:SHOP,campaign_id:CAMP,request_key:JOB,creative_plan_sha256:PLAN,
  provider:'kokoro-onnx',status:'AWAITING_HUMAN_REVIEW',
  private:true,can_publish:false,automatically_retried:false,
  azure_fallback_used:false,paid_api_calls:0,terminal:true,
  original_audio_sha256:SHA,audio_asset_id:ASSET,
  review_status:'PENDING_HUMAN_LISTEN_AND_RIGHTS',
})
const jobScope={shop_id:SHOP,campaign_id:CAMP,request_key:JOB,
                creative_plan_sha256:PLAN}
const assetScope={shop_id:SHOP,campaign_id:CAMP,audio_asset_id:ASSET,
                  original_audio_sha256:SHA}

function client(fetcher,{enabled=true,tokenProvider=async()=> 'test-token'}={}){
  return createFeature2PrivateVoiceReader({
    baseUrl:'https://api.example.dev/api',enabled,tokenProvider,fetcher})
}
function httpStatus(body=validStatus(),headers={}){
  return new Response(JSON.stringify(body),{
    status:200,headers:{'Content-Type':'application/json',...headers}})
}
function httpWav(bytes=WAV,headers={}){
  return new Response(bytes,{
    status:200,headers:{
      'Content-Type':'audio/wav','Cache-Control':'private, no-store',...headers}})
}

test('F2-19 private voice status authenticates once and validates complete receipt',async()=>{
  const network=[]
  const api=client(async (url,init)=>{
    network.push([url,init])
    return httpStatus()
  })
  const row=await api.getPrivateStatus(jobScope)
  assert.equal(row.status,'AWAITING_HUMAN_REVIEW')
  assert.equal(row.can_publish,false)
  assert.equal(network.length,1)
  assert.equal(network[0][0],
    'https://api.example.dev/api/shops/'+SHOP+'/campaigns/'+CAMP+
    '/feature2-voice-jobs/'+JOB)
  assert.equal(network[0][1].method,'GET')
  assert.equal(network[0][1].headers.Authorization,'Bearer test-token')
  assert.equal(network[0][1].cache,'no-store')
  assert.equal(network[0][1].redirect,'error')
  assert.equal(network[0][1].credentials,'omit')
  assert.equal(network[0][1].headers.Accept,'application/json')
})

test('F2-20 bounded original WAV is SHA matched and cannot auto-play',async()=>{
  const urls=[]
  const api=client(async (url,init)=>{
    urls.push([url,init])
    return httpWav()
  })
  const data=await api.getOriginalWav(assetScope)
  assert.equal(data.schema,'retailgrowth.feature2-private-original-wav-read.v1')
  assert.equal(data.asset_id,ASSET)
  assert.equal(data.original_audio_sha256,SHA)
  assert.equal(data.private,true)
  assert.equal(data.can_publish,false)
  assert.equal(data.audio_bytes.byteLength,WAV.length)
  assert.deepEqual(data.audio_bytes,WAV)
  assert.equal(urls.length,1)
  assert.equal(urls[0][0],
    'https://api.example.dev/api/shops/'+SHOP+'/campaigns/'+CAMP+
    '/feature2-original-wav/'+ASSET+'/'+SHA)
  assert.equal(urls[0][1].headers.Accept,'audio/wav')
  assert.ok(!urls[0][0].includes('storage/v1/object/public'))
})

test('F2-19 rejects forged success/publishing and stale scope',async()=>{
  for(const evil of [
    {...validStatus(),can_publish:true},
    {...validStatus(),paid_api_calls:1},
    {...validStatus(),status:'PUBLISHED'},
    {...validStatus(),original_audio_sha256:'not-a-sha'},
    {...validStatus(),shop_id:CAMP},
  ]){
    const api=client(async()=>httpStatus(evil))
    await assert.rejects(api.getPrivateStatus(jobScope))
  }
})

test('F2-19/20 disabled reader refuses network access',async()=>{
  let count=0
  const api=client(async()=>{count++;return httpStatus()},{enabled:false})
  await assert.rejects(api.getPrivateStatus(jobScope))
  await assert.rejects(api.getOriginalWav(assetScope))
  assert.equal(count,0)
})

test('F2-19/20 reject weak origin, mismatched UUID and unexpected paths',async()=>{
  for(const badUrl of [
    'http://api.example.dev/api',
    'https://api.example.dev/api?q=secret',
    'https://user:pass@api.example.dev/api',
    'https://evil.example.dev/path/other',
  ]){
    assert.throws(()=>createFeature2PrivateVoiceReader({
      baseUrl:badUrl,tokenProvider:async()=> 'signed',
      fetcher:async()=>httpStatus(),enabled:true}))
  }
  let called=0
  const api=client(async()=>{called++;return httpStatus()})
  await assert.rejects(api.getPrivateStatus({...jobScope,shop_id:'invalid-shop'}))
  await assert.rejects(api.getOriginalWav({...assetScope,
    original_audio_sha256:'../../etc/passwd'}))
  assert.equal(called,0)
  // Cross-tenant UUID is syntactically valid; real authenticated RLS server
  // must deny it. Do not pretend the browser knows every authorized shop.
  const remote=client(async()=>{called++;return new Response(null,{status:404})})
  await assert.rejects(remote.getPrivateStatus({...jobScope,shop_id:CAMP}))
  assert.equal(called,1)
})

test('F2-19 token changes during private JSON read: fail closed',async()=>{
  let n=0
  const api=client(async()=>httpStatus(),{
    tokenProvider:async()=>++n>=3?'other-token':'test-token'})
  await assert.rejects(api.getPrivateStatus(jobScope))
})

test('F2-20 token changes during WAV streaming: fail closed',async()=>{
  let n=0
  const api=client(async()=>httpWav(),{
    tokenProvider:async()=>++n>=3?'other-token':'test-token'})
  await assert.rejects(api.getOriginalWav(assetScope))
})

test('F2-20 rejects wrong bytes, missing no-store, MIME and unexpected redirects',async()=>{
  for(const bad of [
    httpWav(WAV,{'Cache-Control':'public,max-age=3600'}),
    httpWav(WAV,{'Content-Type':'text/html'}),
    httpWav(new Uint8Array(50)),
    httpWav(new Uint8Array(280)),
    new Response(null,{status:302,headers:{Location:'https://evil.invalid/wav'}}),
  ]){
    const api=client(async()=>bad)
    await assert.rejects(api.getOriginalWav(assetScope))
  }
})

test('F2-20 rejects streaming past the cap before allocating a single huge buffer',async()=>{
  const chunk=new Uint8Array(500_000)
  const stream=new ReadableStream({
    start(controller){
      for(let i=0;i<41;i++)controller.enqueue(chunk)
      controller.close()
    }
  })
  const fake={
    status:200,ok:true,
    headers:new Headers({
      'Content-Type':'audio/wav',
      'Cache-Control':'private, no-store',
    }),
    body:stream,
  }
  const api=client(async()=>fake)
  await assert.rejects(api.getOriginalWav(assetScope))
})

test('F2-20 LocalVoicePanel sends exact original WAV SHA and creative scope',()=>{
  const root=resolve(dirname(fileURLToPath(import.meta.url)),
    '../../frontend/src/features/voiceover/LocalVoicePanel.jsx')
  const jsx=readFileSync(root,'utf8')
  assert.match(jsx,/original_audio_sha256:saved\.original_audio_sha256/)
  assert.match(jsx,/creative_plan_sha256:planSha256/)
  assert.match(jsx,/verifyLocalPrivatePlayback/)
})
