import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'

const requireFrontend = createRequire(new URL('../../frontend/package.json', import.meta.url))
const path = fileURLToPath(new URL('../../frontend/src/features/creative/Feature3KonvaEditor.jsx', import.meta.url))

test('unmounted Feature3 React Konva editor is valid JSX (without enabling dependencies)', async () => {
  // Vite is an already pinned frontend dev dependency. This is syntax-only
  // validation: it does not assert the optional Konva dependency is installed,
  // the UI is mounted, or pixel parity with the Pillow render pipeline.
  const { transformWithEsbuild } = await import(requireFrontend.resolve('vite'))
  const source = await readFile(path, 'utf8')
  const transformed = await transformWithEsbuild(source, path, { loader: 'jsx' })
  assert.ok(transformed.code.includes('Stage'))
  assert.ok(transformed.code.includes('Save private draft'))
  assert.ok(transformed.code.includes('Replace selected photo'))
})

test('isolated creation studio has responsive and approval-gated JSX', async () => {
  const { transformWithEsbuild } = await import(requireFrontend.resolve('vite'))
  const panelPath = fileURLToPath(new URL(
    '../../frontend/src/features/creative/Feature3StudioPanel.jsx', import.meta.url))
  const source = await readFile(panelPath, 'utf8')
  const compiled = await transformWithEsbuild(source, panelPath, { loader: 'jsx' })
  assert.ok(compiled.code.includes('Text-to-Poster'))
  assert.ok(compiled.code.includes('Image-to-Poster'))
  assert.ok(compiled.code.includes('Generate editable poster'))
  assert.ok(compiled.code.includes('Feature3KonvaEditor'))
  assert.ok(source.includes('repeat(auto-fit,minmax(min(100%,180px),1fr))'))
  assert.ok(source.includes('approvedContent?.review_state'))
  assert.ok(source.includes('approvedOffer: approved ? approvedContent.offer_text : null'))
})
