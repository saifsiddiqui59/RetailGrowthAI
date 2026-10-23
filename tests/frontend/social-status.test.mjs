import test from 'node:test'
import assert from 'node:assert/strict'
import { socialStatusForShop } from '../../frontend/src/features/social/social-status.mjs'

const SHOP = 'a1000000-0000-4000-8000-000000000001'
const FOREIGN = 'a2000000-0000-4000-8000-000000000001'

test('status dashboard counts only the current shop and warns on uncertain receipts', () => {
  const summary = socialStatusForShop([
    { shop_id: SHOP, id: '1', provider: 'linkedin', status: 'RECONCILE',
      last_error_code: 'PROVIDER_RESULT_UNCERTAIN' },
    { shop_id: SHOP, id: '2', provider: 'facebook', status: 'PUBLISHED',
      remote_post_id: 'db-confirmed-only' },
    { shop_id: SHOP, id: '3', provider: 'instagram', status: 'FAILED',
      last_error_code: 'Bearer private-token-do-not-show' },
    { shop_id: FOREIGN, id: '4', provider: 'youtube', status: 'RECONCILE',
      last_error_code: 'TOKEN_FROM_OTHER_TENANT' },
    { shop_id: SHOP, id: '5', provider: 'linkedin', status: 'NOT_A_REAL_STATE' },
  ], SHOP)
  assert.equal(summary.total, 3)
  assert.equal(summary.counts.PUBLISHED, 1)
  assert.equal(summary.counts.RECONCILE, 1)
  assert.equal(summary.counts.FAILED, 1)
  assert.equal(summary.attention.length, 2)
  assert.deepEqual(summary.attention[0], {
    id: '1', provider: 'linkedin', status: 'RECONCILE',
    code: 'PROVIDER_RESULT_UNCERTAIN',
  })
  assert.equal(summary.attention[1].code, null)
  assert.equal(JSON.stringify(summary).includes('private-token'), false)
  assert.equal(JSON.stringify(summary).includes('OTHER_TENANT'), false)
})

test('invalid input has no guessed or cross-shop metrics', () => {
  for (const data of [null, {}, 'bad', []]) {
    const summary = socialStatusForShop(data, SHOP)
    assert.equal(summary.total, 0)
    assert.deepEqual(summary.attention, [])
  }
  assert.equal(socialStatusForShop([{shop_id: FOREIGN, status: 'FAILED'}], SHOP).total, 0)
  assert.equal(socialStatusForShop([{shop_id: SHOP, status: 'FAILED'}], '').total, 0)
})
