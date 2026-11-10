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
    async arrayBuffer(){return Uint8Array.from(binary).buffer},
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
