import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createTrendApi } from '../../frontend/src/features/trends/trend-api.mjs'

const SHOP='10000000-0000-4000-8000-000000000001'
const OTHER='20000000-0000-4000-8000-000000000002'
const TREND='a'.repeat(32)
const NONCE='30000000-0000-4000-8000-000000000003'

const tracked = () => {
  const calls=[]
  const api=createTrendApi({
    baseUrl:'https://retail.test.azurewebsites.net',
    tokenProvider:async()=>'real-user-jwt-not-service',
    fetchImpl:async(url,opts)=>{
      calls.push({url,opts})
      return {ok:true,status:200,json:async()=>({shop_id:SHOP,status:'DRAFT',
        review_status:'NEEDS_REVIEW',provider_mode:'approved_llm',can_publish:false,
        usage:{paid_inference_calls:1,actual_paid_cost_usd:0.00042}})}
    },
  })
  return {api,calls}
}

test('real AI routes are distinct and always signed; never issue paid call automatically',async()=>{
  const {api,calls}=tracked()
  assert.equal(calls.length,0)
  const prompt=await api.improvePromptWithAI(SHOP,'Write seven styling posts',
    ['linkedin_post'],'en-IN')
  assert.equal(prompt.provider_mode,'approved_llm')
  assert.equal(calls.length,1)
  assert.match(calls[0].url,/\/improve-prompt-ai$/)
  assert.equal(calls[0].opts.headers.Authorization,'Bearer real-user-jwt-not-service')
  assert.deepEqual(JSON.parse(calls[0].opts.body),{
    original_prompt:'Write seven styling posts',
    output_formats:['linkedin_post'],language:'en-IN',
  })
  assert.throws(()=>api.improvePromptWithAI(SHOP,'',['linkedin_post']))
  assert.throws(()=>api.improvePromptWithAI(OTHER,'abc',['linkedin_post'],'xx-XX'))
  assert.equal(calls.length,1)
})

test('real AI one-POST draft validates current authorized shop, trend and nonce',async()=>{
  const {api,calls}=tracked()
  const campaign={shop_id:SHOP,brief:'seven wardrobe lessons',media_asset_ids:[OTHER]}
  assert.throws(()=>api.createDraftWithAI(SHOP,'unverified',campaign))
  assert.throws(()=>api.createDraftWithAI(SHOP,TREND,{...campaign,shop_id:OTHER}))
  assert.throws(()=>api.createDraftWithAI(SHOP,TREND,campaign,'invalid-nonce'))
  assert.equal(calls.length,0)
  await api.createDraftWithAI(SHOP,TREND,campaign,NONCE)
  assert.equal(calls.length,1)
  assert.match(calls[0].url,/\/content-drafts-ai$/)
  assert.deepEqual(JSON.parse(calls[0].opts.body),{
    trend_id:TREND,campaign,submission_id:NONCE,
  })
  assert.equal(calls[0].opts.redirect,'error')
  assert.equal(calls[0].opts.cache,'no-store')
  assert.equal(calls[0].opts.headers.Authorization,'Bearer real-user-jwt-not-service')
})

test('opt-in starts OFF, requires human selection and retains no blind retry behavior',()=>{
  const src=readFileSync(new URL('../../frontend/src/features/trends/TrendWorkspace.jsx', import.meta.url),'utf8')
  assert.match(src,/useState\(false\)/)
  assert.match(src,/\[realAiEnabled, setRealAiEnabled\] = useState\(false\)/)
  assert.match(src,/Use real Azure AI model \(requires approved shop budget\)/)
  assert.match(src,/realAiEnabled\s*\? await api\.improvePromptWithAI/)
  assert.match(src,/realAiEnabled\s*\? await api\.createDraftWithAI/)
  assert.match(src,/setRealAiEnabled\(event\.target\.checked\)/)
  assert.match(src,/reconcileSubmittedDraft/)
  assert.match(src,/No new draft was submitted|No new draft was submitted|no automatic retry/)
  assert.match(src,/verified matching trend/i)
  assert.match(src,/Free local template mode selected/)
})
