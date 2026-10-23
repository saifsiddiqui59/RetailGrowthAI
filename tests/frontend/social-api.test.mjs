import test from 'node:test'
import assert from 'node:assert/strict'
import {createSocialApi, trustedConsentUrl} from '../../frontend/src/features/social/social-api.mjs'

const SHOP='10000000-0000-4000-8000-000000000001'

test('authenticated social read uses HTTPS, user JWT and tenant id only',async()=>{
  const calls=[]
  const api=createSocialApi({baseUrl:'https://api.retail.example',
    tokenProvider:async()=> 'user-jwt',
    fetchImpl:async(url,opts)=>{calls.push({url,opts});return {
      ok:true,async json(){return {accounts:[]}}
    }}})
  assert.deepEqual(await api.listAccounts(SHOP),{accounts:[]})
  assert.equal(calls[0].url,'https://api.retail.example/api/social/accounts?shop_id='+SHOP)
  assert.equal(calls[0].opts.headers.Authorization,'Bearer user-jwt')
  assert.equal(calls[0].opts.body,undefined)
  assert.equal(api.publish,undefined)
})
test('rejects insecure origin, wrong IDs and provider error leakage',async()=>{
  assert.throws(()=>createSocialApi({baseUrl:'http://evil.example',tokenProvider:()=> 'x'}))
  const api=createSocialApi({baseUrl:'https://api.retail.example',tokenProvider:()=> 'x',
    fetchImpl:async()=>({ok:false,status:500,async json(){
      return {error:'Bearer secret-token from vendor'}
    }})})
  await assert.rejects(()=>api.listJobs(SHOP),e=>{
    assert.doesNotMatch(e.message,/secret-token/)
    return true
  })
  assert.throws(()=>api.listJobs('../escape'),/Invalid shop or job ID/)
})

test('owner OAuth writes use only authenticated same-origin backend POST',async()=>{
  const requests=[]
  const api=createSocialApi({baseUrl:'https://api.retail.example',
    tokenProvider:async()=> 'signed-in-user-jwt',
    fetchImpl:async(url,opts)=>{
      requests.push({url,opts})
      return {ok:true,async json(){return {connection_status:'CONNECTED'}}}
    }})
  await api.startOAuth(SHOP,'youtube')
  await api.completeOAuth(SHOP,'youtube','state','code')
  await api.disconnectAccount(SHOP,'11111111-1111-4111-8111-111111111111')
  assert.deepEqual(requests.map(v=>v.url),[
    'https://api.retail.example/api/social/oauth/start',
    'https://api.retail.example/api/social/oauth/complete',
    'https://api.retail.example/api/social/oauth/disconnect',
  ])
  assert.ok(requests.every(v=>v.opts.method==='POST'))
  assert.ok(requests.every(v=>v.opts.headers.Authorization==='Bearer signed-in-user-jwt'))
  const payload = JSON.parse(requests[1].opts.body)
  assert.deepEqual(payload,{shop_id:SHOP,provider:'youtube',state:'state',code:'code'})
  assert.equal('access_token' in payload,false)
  assert.equal(api.publish,undefined)
  assert.throws(()=>api.startOAuth(SHOP,'untrusted'),/Unsupported/)
  assert.throws(()=>api.completeOAuth(SHOP,'youtube','state',''),/Invalid OAuth/)
})

test('consent navigation permits only official OAuth hosts and exact paths',()=>{
  const good='https://accounts.google.com/o/oauth2/v2/auth?state=abc&redirect_uri=https%3A%2F%2Fstudio.example%2Fcallback'
  assert.equal(trustedConsentUrl(good,'youtube'),good)
  const page='https://www.facebook.com/v26.0/dialog/oauth?state=abc&redirect_uri=https%3A%2F%2Fstudio.example%2Fcallback'
  assert.equal(trustedConsentUrl(page,'facebook'),page)
  for (const bad of [
    'http://accounts.google.com/o/oauth2/v2/auth?state=abc&redirect_uri=x',
    'https://accounts.google.com.evil.test/o/oauth2/v2/auth?state=abc&redirect_uri=x',
    'https://accounts.google.com/o/oauth2/v2/auth?redirect_uri=x',
    'https://accounts.google.com/o/oauth2/v2/auth?state=abc&redirect_uri=x#fragment',
    'https://www.facebook.com/v26.0/oauth/access_token?state=x&redirect_uri=x',
  ]) assert.throws(()=>trustedConsentUrl(bad, bad.includes('facebook')?'facebook':'youtube'))
})

test('authenticated retailer publishing draft/approval/cancel never directly posts',async()=>{
  const calls=[]
  const api=createSocialApi({baseUrl:'https://api.retail.example',
    tokenProvider:async()=> 'signed-in-shop-jwt',
    fetchImpl:async(url,opts)=>{
      calls.push({url,opts})
      return {ok:true,async json(){return {id:'ok',status:'DRAFT'}}}
    }})
  const day='12000000-0000-4000-8000-000000000001'
  const account='11000000-0000-4000-8000-000000000001'
  const job='13000000-0000-4000-8000-000000000001'
  await api.listDays(SHOP)
  await api.createDraft({shopId:SHOP,dayId:day,accountId:account,
    provider:'linkedin',caption:'Reviewed campaign text',
    day:'2026-10-26',clock:'10:00',timezone:'Asia/Kolkata',
    idempotencyKey:'review-unique-key-0001'})
  await api.approveDraft(SHOP,job,1)
  await api.cancelDraft(SHOP,job,1)
  assert.deepEqual(calls.map(c=>c.url),[
    'https://api.retail.example/api/social/days?shop_id='+SHOP,
    'https://api.retail.example/api/social/jobs/create',
    'https://api.retail.example/api/social/jobs/approve',
    'https://api.retail.example/api/social/jobs/cancel',
  ])
  assert.deepEqual(calls.map(c=>c.opts.method),['GET','POST','POST','POST'])
  assert.ok(calls.every(c=>c.opts.headers.Authorization==='Bearer signed-in-shop-jwt'))
  assert.deepEqual(JSON.parse(calls[1].opts.body),{
    shop_id:SHOP,day_id:day,account_id:account,provider:'linkedin',
    caption:'Reviewed campaign text',media_asset_id:null,
    day:'2026-10-26',clock:'10:00',timezone:'Asia/Kolkata',
    idempotency_key:'review-unique-key-0001',
  })
  assert.deepEqual(JSON.parse(calls[2].opts.body),
    {shop_id:SHOP,job_id:job,revision:1})
  assert.equal(api.publish,undefined)
  assert.equal(api.postToProvider,undefined)
})

test('authoring client refuses invalid provider, IDs, revision and non-reviewed captions',()=>{
  const api=createSocialApi({baseUrl:'https://api.retail.example',
    tokenProvider:async()=> 'test',fetchImpl:async()=>{throw Error('no calls')}})
  const day='12000000-0000-4000-8000-000000000001'
  const account='11000000-0000-4000-8000-000000000001'
  const job='13000000-0000-4000-8000-000000000001'
  const valid={shopId:SHOP,dayId:day,accountId:account,
    provider:'facebook',caption:'Post draft',day:'2026-10-26',
    clock:'10:00',timezone:'Asia/Kolkata',idempotencyKey:'unique-key-123456'}
  assert.throws(()=>api.createDraft({...valid,provider:'evil'}),/Unsupported/)
  assert.throws(()=>api.createDraft({...valid,dayId:'../cross-tenant'}),/Invalid/)
  assert.throws(()=>api.createDraft({...valid,caption:''}),/Invalid/)
  assert.throws(()=>api.approveDraft(SHOP,job,0),/revision/)
  assert.throws(()=>api.cancelDraft(SHOP,job,NaN),/revision/)
})
