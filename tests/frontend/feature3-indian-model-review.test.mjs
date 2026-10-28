import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import {
  SOURCE_REVISION, INDIAN_MODEL_CANDIDATES,
  getIndianModelCandidate, indianModelReviewUrl,
  createIndianModelReviewPacket,
} from '../../frontend/src/features/creative/feature3-indian-model-review.mjs'

test('eight real upstream identity definitions are pinned at one immutable commit', () => {
  assert.match(SOURCE_REVISION, /^[a-f0-9]{40}$/)
  assert.equal(INDIAN_MODEL_CANDIDATES.length, 8)
  assert.equal(new Set(INDIAN_MODEL_CANDIDATES.map(c => c.id)).size, 8)
  for (const item of INDIAN_MODEL_CANDIDATES) {
    assert.match(item.id, /^P[0-9]{3}$/)
    assert.match(item.metadataGitBlobSha, /^[a-f0-9]{40}$/)
    assert.match(item.imageGitBlobs.studio_posture, /^[a-f0-9]{40}$/)
    assert.match(item.imageGitBlobs.studio_portrait, /^[a-f0-9]{40}$/)
    assert.equal(item.status, 'PENDING_SOURCE_AND_IMAGE_LICENSE_REVIEW')
    assert.match(indianModelReviewUrl(item.id), new RegExp(SOURCE_REVISION))
  }
  assert.equal(INDIAN_MODEL_CANDIDATES.filter(c => c.metadataPresentation === 'female').length, 5)
  assert.equal(INDIAN_MODEL_CANDIDATES.filter(c => c.metadataPresentation === 'male').length, 3)
  assert.equal(getIndianModelCandidate('P999'), null)
  assert.equal(indianModelReviewUrl('../P009'), null)
  assert.equal(indianModelReviewUrl('P009', 'metadata.json'), null)
})

test('review packet is noncommercial/nonpublishable and cannot assert imported or approved', () => {
  for (const person of INDIAN_MODEL_CANDIDATES) {
    for (const kind of ['studio_posture', 'studio_portrait']) {
      const packet = createIndianModelReviewPacket(person.id, kind)
      assert.equal(packet.source_revision, SOURCE_REVISION)
      assert.equal(packet.person_id, person.id)
      assert.equal(packet.image_git_blob_sha, person.imageGitBlobs[kind])
      assert.equal(packet.metadata_git_blob_sha, person.metadataGitBlobSha)
      assert.equal(packet.source_url, indianModelReviewUrl(person.id, kind))
      assert.equal(packet.status, 'PENDING_SOURCE_AND_IMAGE_LICENSE_REVIEW')
      for (const field of ['licensed_for_retailgrowth', 'rights_evidence_verified',
        'visual_quality_approved', 'commercially_reusable',
        'saved_to_private_library', 'approved', 'published']) {
        assert.equal(packet[field], false, field)
      }
      assert.equal(packet.generation_gpu_calls, 0)
    }
  }
  assert.throws(() => createIndianModelReviewPacket('P001'))
  assert.throws(() => createIndianModelReviewPacket('P009', 'logo'))
})

test('model reviewer is mounted and remains source review only, with Create New separate', async () => {
  const requireFrontend = createRequire(new URL('../../frontend/package.json', import.meta.url))
  const { transformWithEsbuild } = await import(requireFrontend.resolve('vite'))
  const widgetUrl = new URL('../../frontend/src/features/creative/Feature3ModelLibraryReview.jsx', import.meta.url)
  const panelUrl = new URL('../../frontend/src/features/creative/Feature3StudioPanel.jsx', import.meta.url)
  const widget = await readFile(widgetUrl, 'utf8')
  const panel = await readFile(panelUrl, 'utf8')
  assert.ok((await transformWithEsbuild(widget, widgetUrl.pathname, {loader:'jsx'})).code.includes('Download curator review packet'))
  assert.ok((await transformWithEsbuild(panel, panelUrl.pathname, {loader:'jsx'})).code.includes('Explore existing AI fashion models'))
  assert.ok(panel.includes("import Feature3ModelLibraryReview"))
  assert.ok(panel.includes('showModelLibrary && <Feature3ModelLibraryReview'))
  assert.ok(widget.includes('Create New AI Model'))
  assert.ok(widget.includes('rights are still awaiting'))
  assert.ok(widget.includes('getIndianModelCandidate'))
  assert.ok(!widget.includes('fetch('))
  assert.ok(!widget.includes('img src='))
  assert.ok(!widget.includes('onImport'))
})
