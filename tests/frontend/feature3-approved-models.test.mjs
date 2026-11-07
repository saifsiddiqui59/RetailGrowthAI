import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import {
  availableApprovedModels, selectedApprovedModel,
} from '../../frontend/src/features/creative/feature3-approved-models.mjs'

const shop = '202f252a-2f49-4dd6-9860-5deea40c1c34'
const other = 'cc5a1a3a-c392-4a52-b5a9-ea7891084074'
const modelId = 'eb4f0c1e-cadd-4dad-a553-b81c092934c6'
const sharedId = 'f8a4dfb2-a755-4342-87a2-3bd52fdd56cb'
const preview = { complete: true, naturalWidth: 720, naturalHeight: 1080 }
const imageMap = { registered_private_model: preview, shared_registered_model: preview }
const privateModel = {
  schema: 'retailgrowth.model-library.v1',
  model_id: modelId, owner_shop_id: shop, scope: 'shop',
  status: 'APPROVED', synthetic_adult: true, image_sha256: 'a'.repeat(64),
  approved_uses: ['poster', 'video_reference'],
  label: 'Shop sample', media_asset_id: 'registered_private_model',
  license_id: 'CC-BY-4.0', attribution: 'synthetic fixture — CC BY 4.0',
}
const sharedModel = { ...privateModel, model_id: sharedId, owner_shop_id: other,
  scope: 'platform', media_asset_id: 'shared_registered_model',
  label: 'Shared sample' }

test('use only approved host-provided stills with existing loaded private media', () => {
  const models = availableApprovedModels([privateModel, sharedModel], shop, imageMap)
  assert.equal(models.length, 2)
  assert.equal(models[0].modelId, modelId)
  assert.equal(models[0].mediaAssetId, 'registered_private_model')
  assert.equal(models[1].scope, 'platform')
  assert.equal(selectedApprovedModel(models, sharedId).label, 'Shared sample')
  assert.equal(selectedApprovedModel(models, 'nonexistent'), null)
  assert.equal('private_storage_key' in models[0], false)
  assert.equal('source_url' in models[0], false)
  assert.equal('approved' in models[0], false)
})

test('reject tenant leakage, no current image, unreviewed or license-invalid model', () => {
  const variants = [
    { ...privateModel, status: 'PENDING_REVIEW' },
    { ...privateModel, status: 'REVOKED' },
    { ...privateModel, owner_shop_id: other },
    { ...privateModel, synthetic_adult: false },
    { ...privateModel, approved_uses: ['try_on'] },
    { ...privateModel, image_sha256: 'bad-hash' },
    { ...privateModel, license_id: undefined },
    { ...privateModel, license_id: 'UNVERIFIED' },
    { ...privateModel, license_id: 'CC-BY-4.0', attribution: '  ' },
    { ...privateModel, approved_uses: ['poster', 'unreviewed_paid_inference'] },
    { ...privateModel, approved_uses: ['poster', 'poster'] },
    { ...privateModel, approved_uses: ['poster', null] },
    { ...privateModel, approved_uses: ['poster', 'try_on', 'video_reference', 'poster'] },
    { ...privateModel, media_asset_id: 'unregistered_model' },
    { ...privateModel, attribution: '' },
    { ...privateModel, media_asset_id: '../../escape' },
    { ...privateModel, model_id: 'not-uuid' },
  ]
  for (const item of variants) {
    assert.equal(availableApprovedModels([item], shop, imageMap).length, 0,
      JSON.stringify(item))
  }
  assert.equal(availableApprovedModels([privateModel], other, imageMap).length, 0)
  assert.equal(availableApprovedModels([privateModel], shop, {}).length, 0)
  assert.equal(availableApprovedModels([privateModel], shop, {
    registered_private_model: { complete: false, naturalWidth: 100, naturalHeight: 100 },
  }).length, 0)
  assert.equal(availableApprovedModels([privateModel], shop, imageMap, 'dangerous').length, 0)
})

test('no duplicate saved models, no browser mutation of returned selection', () => {
  const models = availableApprovedModels([privateModel, privateModel], shop, imageMap)
  assert.equal(models.length, 1)
  assert.ok(Object.isFrozen(models))
  assert.ok(Object.isFrozen(models[0]))
  assert.throws(() => { models[0].mediaAssetId = 'evil' }, TypeError)
  assert.throws(() => { models.push(privateModel) }, TypeError)
})

test('Studio preserves source-review-only browser catalog but adds approved still selector', async () => {
  const req = createRequire(new URL('../../frontend/package.json', import.meta.url))
  const { transformWithEsbuild } = await import(req.resolve('vite'))
  const url = new URL('../../frontend/src/features/creative/Feature3StudioPanel.jsx', import.meta.url)
  const jsx = await readFile(url, 'utf8')
  await transformWithEsbuild(jsx, url.pathname, { loader: 'jsx' })
  assert.match(jsx, /Saved AI model poster \(CPU\)/)
  assert.match(jsx, /availableApprovedModels\(approvedModels, shopId, imageMap\)/)
  assert.match(jsx, /mode === 'model' \? 'image' : mode/)
  assert.match(jsx, /sourceAssetId/)
  assert.match(jsx, /Server must revalidate media and model rights/i)
  assert.ok(!jsx.includes('http://'))
  assert.ok(!jsx.includes('fetch('))
})

test('model catalog permits only explicitly reviewed license IDs and unique bounded uses', () => {
  for (const license_id of ['CC0-1.0', 'CC-BY-4.0', 'REVIEWED-COMMERCIAL']) {
    const row = { ...privateModel, license_id }
    assert.equal(availableApprovedModels([row], shop, imageMap).length, 1)
  }
  assert.equal(availableApprovedModels([
    { ...privateModel, approved_uses: ['poster', 'try_on', 'video_reference'] },
  ], shop, imageMap, 'try_on').length, 1)
  assert.equal(availableApprovedModels([
    { ...privateModel, approved_uses: ['poster', 'try_on', 'video_reference'] },
  ], shop, imageMap, 'video_reference').length, 1)
  assert.equal(availableApprovedModels([
    { ...privateModel, approved_uses: [] },
  ], shop, imageMap).length, 0)
})
