import test from 'node:test'
import assert from 'node:assert/strict'
import { approvedFeature3Inputs, feature3ContextKey } from '../../frontend/src/features/creative/feature3-context.mjs'

const shopId = '10000000-0000-4000-8000-000000000001'
const campaignId = '10000000-0000-4000-8000-000000000002'
const dayId = '10000000-0000-4000-8000-000000000003'
const context = { shopId, campaignId, dayId }
const brandKit = { shopId, businessName: 'Boutique', accentColor: '#C05F43' }
const approved = {
  review_state: 'APPROVED', shop_id: shopId,
  campaign_id: campaignId, day_id: dayId,
  approved_version: 2, headline: 'New Diwali Styles', cta: 'Visit store',
  offer_text: '20% OFF APPROVED ITEMS',
}

test('matching verified brand and approved campaign/day can feed local poster', () => {
  const result = approvedFeature3Inputs(approved, context, brandKit)
  assert.equal(result.brand.businessName, 'Boutique')
  assert.equal(result.approved.offer_text, '20% OFF APPROVED ITEMS')
  assert.ok(feature3ContextKey(context))
})

test('stale day, another campaign and mismatched tenant never load approved offer', () => {
  for (const altered of [
    { day_id: '10000000-0000-4000-8000-000000000004' },
    { campaign_id: '10000000-0000-4000-8000-000000000004' },
    { shop_id: '10000000-0000-4000-8000-000000000004' },
    { review_state: 'DRAFT' },
    { approved_version: 0 },
    { headline: '' },
    { offer_text: 'x'.repeat(86) },
  ]) {
    assert.equal(approvedFeature3Inputs({ ...approved, ...altered }, context, brandKit)
      .approved, null)
  }
})

test('forged cross-shop brand kit and missing verified context cannot initialize editor', () => {
  assert.equal(approvedFeature3Inputs(approved, context, {
    ...brandKit, shopId: '10000000-0000-4000-8000-000000000004',
  }).brand, null)
  assert.equal(feature3ContextKey({ ...context, dayId: 'bad' }), '')
  assert.equal(approvedFeature3Inputs(approved,
    { ...context, dayId: undefined }, brandKit).approved, null)
})

test('missing or malformed workspace context fails closed without crashing the editor', () => {
  for (const invalid of [null, undefined, [], 123, 'not a workspace']) {
    assert.equal(feature3ContextKey(invalid), '')
    assert.equal(approvedFeature3Inputs(approved, invalid, brandKit).approved, null)
  }
})

test('control characters and bidi overrides never appear as approved poster copy', () => {
  for (const field of ['headline', 'cta', 'offer_text']) {
    for (const unsafe of ['Sale\nterms', 'SALE\u202e90% OFF', 'Offer\u2066hidden\u2069']) {
      assert.equal(approvedFeature3Inputs({ ...approved, [field]: unsafe },
        context, brandKit).approved, null)
    }
  }
  assert.equal(approvedFeature3Inputs(approved, context, {
    ...brandKit, businessName: 'Store\u202eSpoof',
  }).brand, null)
  assert.equal(approvedFeature3Inputs({
    ...approved, approved_version: Number.MAX_SAFE_INTEGER,
  }, context, brandKit).approved, null)
  assert.equal(approvedFeature3Inputs({
    ...approved, headline: 'नई दिवाली कलेक्शन', cta: 'आज आएं',
  }, context, brandKit).approved.headline, 'नई दिवाली कलेक्शन')
})
