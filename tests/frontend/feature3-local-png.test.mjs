import test from 'node:test'
import assert from 'node:assert/strict'
import { composeFeature3Poster } from '../../frontend/src/features/creative/feature3-compose.mjs'
import { renderFeature3LocalDraft } from '../../frontend/src/features/creative/feature3-local-png.mjs'

const shopId = '00000000-0000-4000-8000-000000000f31'
const mediaId = '00000000-0000-4000-8000-000000000f32'

function fakeCanvas() {
  const ops = []
  const ctx = {
    font: '32px sans-serif', fillStyle: '#000000', textBaseline: 'alphabetic',
    measureText(value) { return { width: [...value].length * 9 } },
    fillRect(...args) { ops.push(['rect', ...args]) },
    fillText(...args) { ops.push(['text', ...args]) },
    drawImage(...args) { ops.push(['image', ...args]) },
  }
  return {
    ops, width: 0, height: 0,
    getContext(type) {
      assert.equal(type, '2d')
      return ctx
    },
  }
}
function design(overrides={}) {
  return composeFeature3Poster({
    shopId, mode: 'text', prompt: 'Festival 80% OFF fictional',
    businessName: 'Budget Boutique', approvedOffer: null,
    cta: 'Visit shop', format: 'square', ...overrides,
  })
}
test('offline draft PNG renders 1080 square, all text and no fabricated promotion', () => {
  const canvas = fakeCanvas()
  const receipt = renderFeature3LocalDraft(canvas, design())
  assert.deepEqual([canvas.width, canvas.height], [1080, 1080])
  assert.equal(receipt.draft_only, true)
  assert.equal(receipt.approved, false)
  assert.equal(receipt.inference, false)
  assert.ok(canvas.ops.some(x => x[0] === 'text' && x[1].includes('BUDGET BOUTIQUE')))
  assert.equal(canvas.ops.some(x => x[0] === 'text' && x[1].includes('80% OFF')), false)
  assert.equal(canvas.ops.some(x => x[0] === 'image'), false)
})
test('locally approved image is fit by cover geometry, without fetching URLs', () => {
  const canvas = fakeCanvas()
  const image = { complete: true, naturalWidth: 600, naturalHeight: 400 }
  const draft = design({
    mode: 'image', sourceAssetId: mediaId, authorizedAssetIds: [mediaId],
    approvedOffer: '20% OFF APPROVED STYLES', format: 'portrait',
  })
  const result = renderFeature3LocalDraft(canvas, draft, { [mediaId]: image })
  assert.equal(result.shop_id, shopId)
  assert.deepEqual([canvas.width, canvas.height], [1080, 1350])
  const photos = canvas.ops.filter(x => x[0] === 'image')
  assert.equal(photos.length, 1)
  assert.equal(photos[0][1], image)
  assert.equal(photos[0].length, 10) // drawImage nine-argument cover form
  assert.ok(canvas.ops.some(x => x[0] === 'text' && x[1] === '20% OFF APPROVED STYLES'))
})
test('cut-off draft text is rejected, never silently exported', () => {
  const small = design()
  const header = small.layers.find(x => x.type === 'text')
  header.w = .01
  header.h = .01
  assert.throws(() => renderFeature3LocalDraft(fakeCanvas(), small), /without clipping/)
})
test('expired/unregistered/oversized source images fail before any pixel is drawn', () => {
  const draft = design({ mode: 'image', sourceAssetId: mediaId,
    authorizedAssetIds: [mediaId] })
  const canvas = fakeCanvas()
  assert.throws(() => renderFeature3LocalDraft(canvas, draft), /unavailable/)
  assert.equal(canvas.ops.length, 0)
  assert.throws(() => renderFeature3LocalDraft(fakeCanvas(), draft, {
    [mediaId]: { complete:true, naturalWidth:7000, naturalHeight:7000 },
  }), /unavailable/)
})
test('optional logo is contained and does not overwrite the product cover', () => {
  const logoId = '00000000-0000-4000-8000-000000000f33'
  const draft = design({ mode: 'image', sourceAssetId: mediaId,
    logoAssetId: logoId, authorizedAssetIds: [mediaId, logoId] })
  const canvas = fakeCanvas()
  renderFeature3LocalDraft(canvas, draft, {
    [mediaId]: { complete:true, naturalWidth:600, naturalHeight:400 },
    [logoId]: { complete:true, naturalWidth:250, naturalHeight:60 },
  })
  const imageOps = canvas.ops.filter(x => x[0] === 'image')
  assert.equal(imageOps.length, 2)
  assert.equal(imageOps.find(x => x[1].naturalWidth === 250).length, 6)
  assert.equal(imageOps.find(x => x[1].naturalWidth === 600).length, 10)
})
