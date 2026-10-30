import test from 'node:test'
import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import {createRequire} from 'node:module'

const frontendRequire = createRequire(new URL('../../frontend/package.json', import.meta.url))
const creative = '../../frontend/src/features/creative/'
test('manual rights-scoped Feature3 host compiles, defaults off and never fetches third-party images',async()=>{
  const host=await readFile(new URL(creative+'Feature3PosterHost.jsx',import.meta.url),'utf8')
  const dashboard=await readFile(new URL('../../frontend/src/features/campaigns/CampaignDashboard.jsx',import.meta.url),'utf8')
  const {transformWithEsbuild}=await import(frontendRequire.resolve('vite'))
  await transformWithEsbuild(host,'Feature3PosterHost.jsx',{loader:'jsx'})
  await transformWithEsbuild(dashboard,'CampaignDashboard.jsx',{loader:'jsx'})
  assert.match(host,/VITE_FEATURE3_V2_ENABLED === 'true'/)
  assert.match(host,/MAX_MODEL_PREVIEWS = 5/)
  assert.match(host,/client\.downloadPrivateImage\(scope, model\.media_asset_id\)/)
  assert.match(host,/globalThis\.crypto\.subtle\.digest\('SHA-256'/)
  assert.match(host,/fingerprint !== model\.image_sha256/)
  assert.match(host,/api\.listModels\(scope\)/)
  assert.match(host,/scopedFeature3Preview/)
  assert.match(host,/current/)
  assert.match(host,/isCurrent/)
  assert.match(host,/nonce\.current/)
  assert.match(host,/URL\.revokeObjectURL/)
  assert.match(host,/cloneElement\(children/)
  assert.ok(!host.includes('fetch('))
  assert.ok(!host.includes('localStorage'))
  assert.ok(!host.includes('service_role'))
  assert.match(dashboard,/<Feature3PosterHost client=\{client\} shopId=\{shopId\}>/)
  assert.match(dashboard,/<PosterStudio key=/)
})
test('private model RLS metadata and local decode never grant provider approval',async()=>{
  const js=await readFile(new URL(creative+'feature3-api.mjs',import.meta.url),'utf8')
  assert.match(js,/model\.scope!=='shop'/)
  assert.match(js,/model\.owner_shop_id!==sid/)
  assert.match(js,/model\.status!=='APPROVED'/)
  assert.match(js,/server_document_sha256/)
  assert.ok(!js.includes('retry('))
})
