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
