import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'

const front = createRequire(new URL('../../frontend/package.json', import.meta.url))
const dir = '../../frontend/src/features/creative/'

test('pinned Konva release matches React 19.3 and advanced editor is optional', async () => {
  const pkg = JSON.parse(await readFile(new URL('../../frontend/package.json', import.meta.url), 'utf8'))
  assert.equal(pkg.dependencies['react'], '19.3.1')
  assert.equal(pkg.dependencies['react-konva'], '19.3.2')
  assert.equal(pkg.dependencies.konva, '10.9.0')
  assert.equal(typeof front.resolve('react-konva'), 'string')
  assert.equal(typeof front.resolve('konva'), 'string')
  const jsx = await readFile(new URL(dir + 'Feature3StudioPanel.jsx', import.meta.url), 'utf8')
  const { transformWithEsbuild } = await import(front.resolve('vite'))
  await transformWithEsbuild(jsx, 'Feature3StudioPanel.jsx', { loader: 'jsx' })
  assert.match(jsx, /lazy\(\(\) => import\('\.\/Feature3KonvaEditor\.jsx'\)\)/)
  assert.match(jsx, /Advanced drag-and-resize editor \(local\)/)
  assert.match(jsx, /<Suspense fallback=/)
  assert.match(jsx, /imageMap=\{imageMap\} context=\{context\}/)
  assert.ok(!jsx.includes('onSaveDraft={onSaveDesign} />\n          </Suspense>'))
})

test('Konva local backups cannot impersonate reviewed/saved/foreign-day designs', async () => {
  const src = await readFile(new URL(dir + 'Feature3KonvaEditor.jsx', import.meta.url), 'utf8')
  const { transformWithEsbuild } = await import(front.resolve('vite'))
  await transformWithEsbuild(src, 'Feature3KonvaEditor.jsx', {loader:'jsx'})
  assert.match(src, /encodeFeature3LocalBackup\(design, context\)/)
  assert.match(src, /decodeFeature3LocalBackup\(/)
  assert.match(src, /context, authorizedIds/)
  assert.ok(!src.includes('localStorage'))
  assert.ok(!src.includes('fetch('))
  assert.ok(!src.includes('src={'))
})
