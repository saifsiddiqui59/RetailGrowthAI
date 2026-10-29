import test from 'node:test'
import assert from 'node:assert/strict'
import {createTraceStore} from '../../frontend/src/features/testing/trace-store.mjs'

const shop='11111111-1111-4111-8111-111111111111'
const job='22222222-2222-4222-8222-222222222222'
const sid='33333333-3333-4333-8333-333333333333'
const row=()=>({
  id:sid,shop_id:shop,job_id:job,feature:'F2',operation:'planning.complete',
  status:'SUCCEEDED',attempt:1,elapsed_ms:450,metadata:{generated_days:7,planner_mode:'dev_mock'},
  recorded_at:'2026-10-29T00:00:00Z',
})
const reply=()=>({source:'trusted_backend_persisted',shop_id:shop,job_id:job,events:[row()]})
function client(fetchImpl,tokenProvider=async()=> 'user-session-jwt'){
  return createTraceStore({supabaseUrl:'https://tenant.supabase.co',
    publishableKey:'sb_publishable_test',tokenProvider,fetchImpl})
}
const http=(status,content)=>({ok:status>=200&&status<300,status,
  json:async()=>content})

test('private trusted reads use existing user JWT, not a service credential',async()=>{
  let observed
  const store=client(async(url,init)=>{
    observed={url,init}
    return http(200,reply())
  })
  const spans=await store.readTrustedWorkerSpans(shop,job,30)
  assert.equal(spans.length,1)
  assert.equal(spans[0].status,'SUCCEEDED')
  assert.equal(observed.url,'https://tenant.supabase.co/rest/v1/rpc/retail_feature_worker_spans')
  assert.equal(observed.init.method,'POST')
  assert.equal(observed.init.headers.Authorization,'Bearer user-session-jwt')
  assert.equal(observed.init.headers.apikey,'sb_publishable_test')
  assert.deepEqual(JSON.parse(observed.init.body),{
    p_shop_id:shop,p_job_id:job,p_limit:30,
  })
  assert.ok(!observed.init.url)
  assert.ok(!JSON.stringify(observed.init).includes('service_role'))
})

test('hosted RPC absent or denied never masquerades as worker success',async()=>{
  for(const code of [403,404,406,503]){
    const store=client(async()=>http(code,{message:'mock backend failure'}))
    await assert.rejects(()=>store.readTrustedWorkerSpans(shop,job),
      /not deployed|not authorized|cannot currently be verified/i)
  }
})

test('cross-tenant, wrong job, unknown source and bad schema responses fail closed',async()=>{
  const mutations=[
    {...reply(),shop_id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'},
    {...reply(),job_id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'},
    {...reply(),source:'browser_observed'},
    {...reply(),events:[{...row(),job_id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'}]},
    {...reply(),events:[{...row(),feature:'F5'}]},
    {...reply(),events:[{...row(),operation:'planning.failed'}]},
    {...reply(),events:[{...row(),status:'FAILED'}]},
    {...reply(),events:[{...row(),attempt:0}]},
    {...reply(),events:[{...row(),elapsed_ms:-1}]},
    {...reply(),events:[{...row(),id:'not-a-uuid'}]},
    {...reply(),events:[{...row(),metadata:{jwt:'private'}}]},
  ]
  for(const result of mutations){
    const store=client(async()=>http(200,result))
    await assert.rejects(()=>store.readTrustedWorkerSpans(shop,job),
      /Unverified|trusted read contract/)
  }
})

test('invalid scoped resource IDs and unbounded reads stop before network',async()=>{
  let calls=0
  const store=client(async()=>{calls++;return http(200,reply())})
  await assert.rejects(()=>store.readTrustedWorkerSpans('bad',job))
  await assert.rejects(()=>store.readTrustedWorkerSpans(shop,'bad'))
  await assert.rejects(()=>store.readTrustedWorkerSpans(shop,job,51))
  assert.equal(calls,0)
})

test('no signed user JWT stops before sending a Supabase request',async()=>{
  let calls=0
  const store=client(async()=>{calls++;return http(200,reply())},async()=>null)
  await assert.rejects(()=>store.readTrustedWorkerSpans(shop,job),/Sign in/)
  assert.equal(calls,0)
})
