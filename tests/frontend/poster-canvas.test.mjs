import test from 'node:test'
import assert from 'node:assert/strict'
import {
  POSTER_TEMPLATES, POSTER_SIZES, posterText, posterOptions,
  coverCrop, drawPoster,
} from '../../frontend/src/features/creative/poster-canvas.mjs'

const day = {
  id: 'day1', day_index: 1, topic: 'Meet the everyday collection',
  instagram: { reel: { cta: 'Visit our store' } },
}
const options = {
  template: 'editorial', size: 'square', brand: 'Everyday Clothing',
  accent: '#B96349', background: '#F6F0E8', offer: '',
}

function fakeCanvas() {
  const calls = []
  const ctx = {
    clearRect(...a) { calls.push(['clearRect', ...a]) },
    fillRect(...a) { calls.push(['fillRect', ...a]) },
    fillText(...a) { calls.push(['fillText', ...a]) },
    drawImage(...a) { calls.push(['drawImage', ...a]) },
    measureText(value) { return { width: String(value).length * 15 } },
    createLinearGradient() { return { addColorStop() {} } },
    set fillStyle(value) { calls.push(['fillStyle', value]) },
    set font(value) { calls.push(['font', value]) },
  }
  const canvas = { width: 0, height: 0, getContext: () => ctx }
  return { canvas, calls }
}

test('all six poster layouts generate full-size canvas and stay local', () => {
  for (const template of POSTER_TEMPLATES) {
    for (const [size, dimensions] of Object.entries(POSTER_SIZES)) {
      const { canvas, calls } = fakeCanvas()
      const result = drawPoster(canvas, { width: 500, height: 750 }, day, { ...options, template, size })
      assert.deepEqual([canvas.width, canvas.height], dimensions)
      assert.deepEqual([result.width, result.height], dimensions)
      assert.equal(result.title, day.topic)
      assert.ok(calls.some(call => call[0] === 'drawImage'), 'expected licensed local photo layer')
      assert.ok(calls.some(call => call[0] === 'fillText' && String(call[1]).includes('Visit our store')),
        'expected real campaign CTA layer')
    }
  }
})

test('photo-less concept is visible but not a licensed generated photo', () => {
  const { canvas, calls } = fakeCanvas()
  drawPoster(canvas, null, day, options)
  assert.ok(calls.some(call => call[0] === 'fillText' && call[1] === 'ADD YOUR PRODUCT PHOTO'))
  assert.ok(!calls.some(call => call[0] === 'drawImage'))
})

test('approved offer copy appears only when explicitly supplied', () => {
  const basic = fakeCanvas()
  drawPoster(basic.canvas, null, day, options)
  assert.ok(!basic.calls.some(call => call[0] === 'fillText' && String(call[1]).includes('20%')))
  const approved = fakeCanvas()
  drawPoster(approved.canvas, null, day, { ...options, offer: '20% off this weekend' })
  assert.ok(approved.calls.some(call => call[0] === 'fillText' && String(call[1]).includes('20%')))
})

test('input validation rejects bogus campaigns, unsafe colors and unsupported presets', () => {
  assert.deepEqual(posterText(day), { title: day.topic, cta: 'Visit our store', dayIndex: 1 })
  assert.throws(() => posterText({}), /valid campaign day/)
  assert.throws(() => posterOptions({ ...options, brand: '' }), /business name/)
  assert.throws(() => posterOptions({ ...options, accent: 'javascript:bad' }), /Colors/)
  assert.throws(() => posterOptions({ ...options, template: 'fake' }), /supported poster/)
  assert.throws(() => posterOptions({ ...options, size: 'fake' }), /supported poster/)
})

test('center crop fills destination without changing image aspect ratio', () => {
  assert.deepEqual(coverCrop(600, 1200, 300, 300), [0, 300, 600, 600])
  assert.deepEqual(coverCrop(1200, 600, 300, 300), [300, 0, 600, 600])
  assert.throws(() => coverCrop(0, 600, 300, 300), /Invalid/)
})
