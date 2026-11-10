import test from 'node:test'
import assert from 'node:assert/strict'
import { reconcileSubmittedDraft } from '../../frontend/src/features/trends/trend-draft-reconcile.mjs'

const SHOP = '10000000-0000-4000-8000-000000000001'
const OTHER = '20000000-0000-4000-8000-000000000002'
const NONCE = '30000000-0000-4000-8000-000000000003'
const ID = '40000000-0000-4000-8000-000000000004'
const TREND = 'a'.repeat(32)
function saved(overrides={}) {
  return {
    id: ID, shop_id: SHOP, trend_id: TREND, review_state: 'DRAFT',
    content: { submission_id: NONCE, campaign: {shop_id: SHOP},
      review: {status:'DRAFT',can_publish:false} }, ...overrides,
  }
}
const input = {shopId:SHOP,trendId:TREND,submissionId:NONCE}

test('one immutable saved nonce corroborates an otherwise lost Azure 201 without posting again',()=>{
  assert.equal(reconcileSubmittedDraft([saved()],input),ID)
  assert.equal(reconcileSubmittedDraft([],input),null)
  assert.equal(reconcileSubmittedDraft([saved({content:{...saved().content,submission_id:OTHER}})],input),null)
})

test('deny ambiguous, cross-shop, forged source, and publishable results',()=>{
  assert.throws(()=>reconcileSubmittedDraft([saved(),saved({id:OTHER})],input),/Ambiguous/)
  for (const row of [
    saved({shop_id:OTHER}),
    saved({trend_id:'b'.repeat(32)}),
    saved({review_state:'APPROVED'}),
    saved({id:'unsafe'}),
    saved({content:{...saved().content,campaign:{shop_id:OTHER}}}),
    saved({content:{...saved().content,review:{status:'DRAFT',can_publish:true}}}),
  ]) assert.throws(()=>reconcileSubmittedDraft([row],input),/Untrusted|cross-tenant/)
})

test('malformed readback cannot be interpreted as a confirmed save',()=>{
  for(const rows of [null, {}, 'not-an-array']) {
    assert.throws(()=>reconcileSubmittedDraft(rows,input))
  }
  assert.throws(()=>reconcileSubmittedDraft([], {...input,submissionId:'invalid'}))
  assert.throws(()=>reconcileSubmittedDraft([], {...input,shopId:OTHER.slice(0,-1)}))
})
