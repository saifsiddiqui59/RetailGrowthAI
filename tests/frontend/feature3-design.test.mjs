import test from 'node:test'
import assert from 'node:assert/strict'
import { FEATURE3_SCHEMA, FEATURE3_TEMPLATES, validateFeature3Design,
  newFeature3History, updateFeature3Layer, moveFeature3Layer,
  undoFeature3, redoFeature3, addFeature3Layer, removeFeature3Layer,
  replaceFeature3Image } from '../../frontend/src/features/creative/feature3-design.mjs'

const design = {
  schema: FEATURE3_SCHEMA, shop_id: 'shop_alpha',
  format: 'square', template: FEATURE3_TEMPLATES[0],
  background: '#FFFFFF',
  layers: [
    { id: 'product', type: 'image', asset_id: 'private_asset_1', x: .1, y: .1, w: .8, h: .6 },
    { id: 'offer', type: 'text', text: '20% OFF', color: '#AA0000',
      font_size: 40, bold: true, x: .1, y: .8, w: .8, h: .1 },
  ],
}

test('poster editing is versioned, immutable and supports undo redo', () => {
  const initial = newFeature3History(design)
  const moved = updateFeature3Layer(initial, 'offer', { x: .2 })
  assert.equal(initial.present.layers[1].x, .1)
  assert.equal(moved.present.layers[1].x, .2)
  assert.equal(undoFeature3(moved).present.layers[1].x, .1)
  assert.equal(redoFeature3(undoFeature3(moved)).present.layers[1].x, .2)
  assert.equal(moveFeature3Layer(moved, 'offer', -1).present.layers[0].id, 'offer')
})

test('poster browser contract blocks arbitrary urls, cross-layer overflow and unverified IDs', () => {
  assert.throws(() => validateFeature3Design({ ...design,
    layers: [{ ...design.layers[0], image_url: 'https://evil.example' }] }))
  assert.throws(() => validateFeature3Design({ ...design, shop_id: '../evil' }))
  assert.throws(() => validateFeature3Design({ ...design, layers: [
    { ...design.layers[0], x: .9 },
  ] }))
  assert.throws(() => updateFeature3Layer(newFeature3History(design), 'offer', {
    asset_id: 'other_shop',
  }))
  assert.throws(() => updateFeature3Layer(newFeature3History(design), 'missing', { x: .1 }))
})

test('add, remove, replace authorized image, and undo without overriding previous draft', () => {
  let history = newFeature3History(design)
  history = addFeature3Layer(history, 'text')
  assert.equal(history.present.layers.at(-1).text, 'Your headline')
  history = addFeature3Layer(history, 'rect')
  assert.equal(history.present.layers.at(-1).type, 'rect')
  history = addFeature3Layer(history, 'image', 'shop-safe-img', ['shop-safe-img'])
  assert.equal(history.present.layers.at(-1).asset_id, 'shop-safe-img')
  assert.throws(() => replaceFeature3Image(
    history, 'product', 'other-shop-image', ['shop-safe-img']), /[Rr]egistered/)
  history = replaceFeature3Image(history, 'product', 'shop-safe-img', ['shop-safe-img'])
  assert.equal(history.present.layers[0].asset_id, 'shop-safe-img')
  const oldCount = history.present.layers.length
  history = removeFeature3Layer(history, 'custom-3')
  assert.equal(history.present.layers.length, oldCount - 1)
  assert.equal(undoFeature3(history).present.layers.length, oldCount)
  assert.throws(() => addFeature3Layer(history, 'image',
    'external://photo', ['shop-safe-img']), /[Rr]egistered/)
})
