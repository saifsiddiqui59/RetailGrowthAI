import test from 'node:test'
import assert from 'node:assert/strict'
import {createSocialApi} from '../../frontend/src/features/social/social-api.mjs'

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
