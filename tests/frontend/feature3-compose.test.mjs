import test from 'node:test'
import assert from 'node:assert/strict'
import { composeFeature3Poster, selectFeature3Template } from '../../frontend/src/features/creative/feature3-compose.mjs'

const approved = {
  shopId: '00000000-0000-4000-8000-000000000a33',
  mode: 'image',
  prompt: 'Diwali premium ethnic clothing',
  businessName: 'Test Boutique',
  headline: 'Celebrate in style',
  cta: 'Discover festive edit',
  sourceAssetId: '00000000-0000-4000-8000-000000000a34',
  authorizedAssetIds: ['00000000-0000-4000-8000-000000000a34'],
  approvedOffer: '20% OFF',
  template: 'festival',
  format: 'square',
}

test('template choice uses deterministic, free, offline campaign hint rules', () => {
  assert.equal(selectFeature3Template('Our Diwali collection'), 'festival')
  assert.equal(selectFeature3Template('luxury boutique'), 'luxury')
  assert.equal(selectFeature3Template('new arrivals today'), 'new_arrivals')
  assert.equal(selectFeature3Template('formal fashion'), 'fashion')
})

test('authorized photo-to-poster emits safe, editable pixel-independent layers', () => {
  const design = composeFeature3Poster(approved)
  assert.equal(design.template, 'festival')
  assert.equal(design.format, 'square')
  assert.equal(design.shop_id, approved.shopId)
  assert.equal(design.layers.find(x => x.id === 'offer')?.text, '20% OFF')
  assert.equal(design.layers.find(x => x.id === 'product')?.asset_id, approved.sourceAssetId)
  assert.equal(design.background, '#FFF3DB')
})

test('text-to-poster uses no invented offers or unapproved images', () => {
  const result = composeFeature3Poster({
    ...approved, mode: 'text', sourceAssetId: null,
    authorizedAssetIds: [], approvedOffer: null,
    prompt: 'Black Friday 75% OFF summer styles',
  })
  assert.equal(result.layers.find(x => x.id === 'product'), undefined)
  assert.equal(result.layers.find(x => x.id === 'offer'), undefined)
})

test('unregistered images and arbitrary template/network inputs fail closed', () => {
  assert.throws(() => composeFeature3Poster({
    ...approved, authorizedAssetIds: ['other-shop-asset'],
  }), /authorized shop media/)
  assert.throws(() => composeFeature3Poster({
    ...approved, mode: 'text', sourceAssetId: 'https://example.org/image.jpg',
  }), /Unregistered image/)
  assert.throws(() => composeFeature3Poster({
    ...approved, template: 'injected-template',
  }), /Unsupported/)
  assert.throws(() => composeFeature3Poster({
    ...approved, businessName: '\u0000bad',
  }), /Invalid required/)
})

test('optional shop-approved brand logo is preserved as a separate image layer', () => {
  const logo = '00000000-0000-4000-8000-000000000a35'
  const result = composeFeature3Poster({
    ...approved, logoAssetId: logo,
    authorizedAssetIds: [...approved.authorizedAssetIds, logo],
  })
  assert.equal(result.layers.find(l => l.id === 'logo').asset_id, logo)
  assert.equal(result.layers.find(l => l.id === 'brand').w, .68)
  assert.throws(() => composeFeature3Poster({
    ...approved, logoAssetId: logo,
  }), /Unregistered brand logo/)
})
