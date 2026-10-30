import test from 'node:test'
import assert from 'node:assert/strict'
import {createHash,randomUUID,webcrypto} from 'node:crypto'
import {createFeature3PrivatePNGClient} from '../../frontend/src/features/creative/feature3-private-png-client.mjs'

if (!globalThis.crypto) globalThis.crypto=webcrypto
const SHOP=randomUUID(), JOB=randomUUID(), MEDIA=randomUUID()
const API='https://fictional.azurewebsites.net'
const URL=API+'/api/shops/'+SHOP+'/feature3-gpu-jobs/'+JOB+'/private-png'
const MAGIC=[137,80,78,71,13,10,26,10]
const BYTES=Uint8Array.from([...MAGIC,...Array.from({length:120},()=>4)])
const HASH=createHash('sha256').update(BYTES).digest('hex')
const expectedHeaders={
  'content-length':String(BYTES.length),'content-type':'image/png',
  'cache-control':'no-store, private, max-age=0',
  'x-content-type-options':'nosniff','x-feature3-shop-id':SHOP,
  'x-feature3-job-id':JOB,'x-feature3-media-asset-id':MEDIA,
  'x-feature3-image-sha256':HASH,
}
function fakeResponse({headers={},binary=BYTES,status=200,url=URL,redirected=false}={}) {
  const all={...expectedHeaders,...headers}
  return {ok:status===200,status,url,redirected,
    headers:{get(name){return Object.hasOwn(all,name.toLowerCase())?
      all[name.toLowerCase()]:null}},
    body:new ReadableStream({start(controller){
      controller.enqueue(Uint8Array.from(binary))
      controller.close()
    }}),
  }
}
function setup(response=fakeResponse(),jwt='mock-signed-retailer-token') {
  const calls=[]
  const api=createFeature3PrivatePNGClient({
    baseUrl:API,tokenProvider:async()=>jwt,
    fetchImpl:async(...args)=>{calls.push(args);return response},
  })
  return {api,calls}
}
test('one private JWT GET yields SHA-verified same-shop Blob, never a signed link',async()=>{
  const {api,calls}=setup()
  const output=await api.get(SHOP,JOB)
  assert.equal(calls.length,1)
  assert.equal(calls[0][0],URL)
  assert.deepEqual(calls[0][1],{
    method:'GET',cache:'no-store',redirect:'error',
    credentials:'omit',referrerPolicy:'no-referrer',
    headers:{Authorization:'Bearer mock-signed-retailer-token',Accept:'image/png'},
  })
  assert.equal(output.shopId,SHOP)
  assert.equal(output.jobId,JOB)
  assert.equal(output.mediaAssetId,MEDIA)
  assert.equal(output.imageSha256,HASH)
  assert.equal(output.blob.type,'image/png')
  assert.equal(output.blob.size,BYTES.length)
  assert.equal(output.private,true)
  assert.equal(output.publishApproved,false)
  assert.equal(output.approvedModel,false)
  assert.equal('url' in output,false)
  assert.equal('objectPath' in output,false)
  assert.ok(Object.isFrozen(output))
})
test('foreign shop/status, signed URL response or tampered SHA denies',async()=>{
  const bad=[
    {headers:{'x-feature3-shop-id':randomUUID()}},
    {headers:{'x-feature3-job-id':randomUUID()}},
    {headers:{'x-feature3-media-asset-id':'../bad'}},
    {headers:{'x-feature3-image-sha256':'c'.repeat(64)}},
    {headers:{'content-type':'image/svg+xml'}},
    {headers:{'cache-control':'public, max-age=86400'}},
    {headers:{'x-content-type-options':'off'}},
    {headers:{location:'https://evil.invalid/download'}},
    {headers:{'content-length':'30000000'}},
    {headers:{'content-length':'unexpected'}},
    {binary:Uint8Array.from([...MAGIC,...Array.from({length:120},()=>5)])},
    {binary:Uint8Array.from([...Array.from({length:BYTES.length},()=>1)])},
    {status:403},{status:503},{redirected:true},
    {url:'https://evil.invalid/signed'},
  ]
  for(const option of bad){
    const {api,calls}=setup(fakeResponse(option))
    await assert.rejects(api.get(SHOP,JOB))
    assert.equal(calls.length,1)
  }
})
test('no foreign UUID or malformed JWT reaches any binary request',async()=>{
  for(const bad of ['',null,{},randomUUID().toUpperCase(),'../../shop']){
    const {api,calls}=setup()
    await assert.rejects(api.get(bad,JOB))
    assert.equal(calls.length,0)
  }
  // A different canonical shop id is valid syntax but never an authorized
  // media receipt. It reaches the server for its independent JWT/RLS check.
  const {api:otherApi,calls:otherCalls}=setup()
  await assert.rejects(otherApi.get(randomUUID(),JOB))
  assert.equal(otherCalls.length,1)
  for(const jwt of ['', 'bad', 'sb_secret_invalid', 'sb_publishable_invalid',
                    'bad\r\nsecret', 'x'.repeat(9000)]){
    const {api,calls}=setup(fakeResponse(),jwt)
    await assert.rejects(api.get(SHOP,JOB))
    assert.equal(calls.length,0)
  }
})
test('no plain HTTP, credentialed, path, query or fragment API origin',()=>{
  for(const baseUrl of [
    'http://fictional.azurewebsites.net',
    'https://user:pass@fictional.azurewebsites.net',
    'https://fictional.azurewebsites.net/path',
    'https://fictional.azurewebsites.net/?token=evil',
    'https://fictional.azurewebsites.net/#secret',
  ]) {
    assert.throws(()=>createFeature3PrivatePNGClient({
      baseUrl,tokenProvider:async()=>'',fetchImpl:async()=>null,
    }))
  }
})

test('malicious excess stream bytes cancel immediately without unbounded arrayBuffer',async()=>{
  const response=fakeResponse()
  let cancellations=0
  response.body=new ReadableStream({
    start(controller){
      controller.enqueue(BYTES)
      controller.enqueue(new Uint8Array(256))
      // Do not close: the client must actively cancel upon exceeding its cap.
    },
    cancel(){cancellations++},
  })
  const {api,calls}=setup(response)
  await assert.rejects(api.get(SHOP,JOB),/byte stream denied/)
  assert.equal(calls.length,1)
  assert.equal(cancellations,1)
})
test('truncated, missing or malformed private body stream fails closed',async()=>{
  const short=fakeResponse()
  short.body=new ReadableStream({start(c){c.enqueue(BYTES.slice(0,100));c.close()}})
  await assert.rejects(setup(short).api.get(SHOP,JOB),/bytes changed/)
  const missing=fakeResponse()
  missing.body=null
  await assert.rejects(setup(missing).api.get(SHOP,JOB),/streaming unavailable/)
  const corrupt=fakeResponse()
  corrupt.body={getReader:()=>({
    read:async()=>({done:false,value:'untrusted bytes'}),
    cancel:async()=>{},
    releaseLock:()=>{},
  })}
  await assert.rejects(setup(corrupt).api.get(SHOP,JOB),/byte stream denied/)
})
test('bounded stream supports fragmented valid PNG while preserving SHA proof',async()=>{
  const response=fakeResponse()
  response.body=new ReadableStream({start(c){
    c.enqueue(BYTES.slice(0,3))
    c.enqueue(BYTES.slice(3,17))
    c.enqueue(BYTES.slice(17))
    c.close()
  }})
  const result=await setup(response).api.get(SHOP,JOB)
  assert.equal(result.imageSha256,HASH)
  assert.equal(result.blob.size,BYTES.length)
})
