import test from 'node:test'
import assert from 'node:assert/strict'
import { composeFeature3Poster } from '../../frontend/src/features/creative/feature3-compose.mjs'
import {
  encodeFeature3LocalBackup, decodeFeature3LocalBackup,
} from '../../frontend/src/features/creative/feature3-local-backup.mjs'

const shopId = '10000000-0000-4000-8000-000000000131'
const campaignId = '10000000-0000-4000-8000-000000000132'
const dayId = '10000000-0000-4000-8000-000000000133'
const assetId = '10000000-0000-4000-8000-000000000134'
const context = { shopId, campaignId, dayId }
const poster = composeFeature3Poster({
  shopId, mode:'image', prompt:'Diwali fashion',
  businessName:'Budget Kurti Boutique', sourceAssetId:assetId,
  authorizedAssetIds:[assetId], approvedOffer:'20% OFF selected styles',
})
test('local poster JSON backs up editable design with immutable campaign/day and no cloud approval', () => {
  const payload = encodeFeature3LocalBackup(poster, context)
  const wrapper = JSON.parse(payload)
  assert.equal(wrapper.version, 'retailgrowth.local.poster-draft.v2')
  assert.equal(wrapper.context_key, [shopId, campaignId, dayId].join('/'))
  assert.equal(wrapper.approved, false)
  assert.equal(wrapper.cloud_saved, false)
  assert.deepEqual(decodeFeature3LocalBackup(payload, context, [assetId]), poster)
})
test('refuse stale different day or campaign even within same shop', () => {
  const payload = encodeFeature3LocalBackup(poster, context)
  assert.throws(() => decodeFeature3LocalBackup(payload, {
    ...context, dayId:'10000000-0000-4000-8000-000000000135',
  }, [assetId]), /different campaign\/day/)
  assert.throws(() => decodeFeature3LocalBackup(payload, {
    ...context, campaignId:'10000000-0000-4000-8000-000000000135',
  }, [assetId]), /different campaign\/day/)
  assert.throws(() => decodeFeature3LocalBackup(payload, {
    ...context, shopId:'10000000-0000-4000-8000-000000000135',
  }, [assetId]), /different campaign\/day/)
})
test('revoked image rights and forged cloud-saved status fail closed', () => {
  const payload = encodeFeature3LocalBackup(poster, context)
  assert.throws(() => decodeFeature3LocalBackup(payload, context, []), /Shop\/media access/)
  const forged = JSON.parse(payload)
  forged.cloud_saved = true
  assert.throws(() => decodeFeature3LocalBackup(
    JSON.stringify(forged), context, [assetId]), /different campaign\/day/)
  forged.cloud_saved = false
  forged.approved = true
  assert.throws(() => decodeFeature3LocalBackup(
    JSON.stringify(forged), context, [assetId]), /different campaign\/day/)
})
test('reject unknown schema keys, oversized JSON and unbound raw v2 files', () => {
  const payload = encodeFeature3LocalBackup(poster, context)
  assert.throws(() => decodeFeature3LocalBackup(JSON.stringify(poster),
    context, [assetId]), /different campaign\/day/)
  assert.throws(() => decodeFeature3LocalBackup(payload + ' '.repeat(25001),
    context, [assetId]), /Invalid local draft backup/)
  assert.throws(() => encodeFeature3LocalBackup(poster, {
    ...context, shopId:'10000000-0000-4000-8000-000000000135',
  }), /Valid shop\/campaign\/day/)
  const more = JSON.parse(payload)
  more.externalUrl = 'https://example.com/unsafe'
  assert.throws(() => decodeFeature3LocalBackup(
    JSON.stringify(more), context, [assetId]), /different campaign\/day/)
})
