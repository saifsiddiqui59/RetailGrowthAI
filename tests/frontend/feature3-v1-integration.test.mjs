import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'

const requireFrontend = createRequire(new URL('../../frontend/package.json', import.meta.url))
const sourcePath = fileURLToPath(new URL(
  '../../frontend/src/features/creative/PosterStudio.jsx', import.meta.url))

test('CPU v2 local editor can mount in legacy poster studio with no extra frontend dependency', async () => {
  const source = await readFile(sourcePath, 'utf8')
  const { transformWithEsbuild } = await import(requireFrontend.resolve('vite'))
  const transformed = await transformWithEsbuild(source, sourcePath, {loader:'jsx'})
  assert.ok(transformed.code.includes('Feature3StudioPanel'))
  assert.ok(source.includes('feature3ContextKey({'))
  assert.ok(source.includes('persisted && feature3ContextKey'))
  assert.ok(source.includes('imageMap={authenticatedModelImageMap}'))
  assert.ok(source.includes('approvedModels={approvedModels}'))
  assert.ok(source.includes('authenticatedModelImageMap = {}'))
  assert.ok(source.includes('approvedModels = []'))
  assert.ok(source.includes('local-only'))
  assert.ok(!source.includes("from 'react-konva'"))
})

test('existing v1 cloud save/render/select/download methods and consent gate preserved', async () => {
  const source = await readFile(sourcePath, 'utf8')
  for(const name of ['createPosterDraft(', 'createPosterRender(',
    'selectPosterBanner(', 'getPosterDownload(', 'listPosterDrafts(']) {
    assert.ok(source.includes(name), name + ' must remain in original studio')
  }
  assert.ok(source.includes('!allowedSources.includes(sourceAssetId)'))
  assert.ok(source.includes('!rights'))
  assert.ok(source.includes('remoteJob.status !== \'SUCCEEDED\''))
  assert.ok(source.includes('Cloud designs are saved only after explicit consent'))
  assert.ok(!source.includes('onSaveDesign='))
})
