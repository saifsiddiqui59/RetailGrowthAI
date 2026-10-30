// Additive browser document contract for Feature #3; does not change Part 1 API.
// Mirror of poster-engine/studio_v2.py validated allowlist, not a public URL loader.
export const FEATURE3_SCHEMA = 'retailgrowth.poster.v2'
export const FEATURE3_FORMATS = Object.freeze({
  square: [1080, 1080], portrait: [1080, 1350], story: [1080, 1920],
})
export const FEATURE3_TEMPLATES = Object.freeze([
  'fashion', 'luxury', 'streetwear', 'ethnic', 'festival', 'restaurant',
  'general', 'new_arrivals', 'clearance', 'seasonal',
])
const HEX = /^#[0-9a-fA-F]{6}$/
const ID = /^[a-zA-Z0-9_-]{1,100}$/
const fail = message => { throw new Error(message) }
function checkedText(value, max) {
  if (typeof value !== 'string' || !value.trim() || value.length > max || /[\x00-\x1f]/.test(value)) fail('Invalid poster text')
  return value.trim()
}
export function validateFeature3Design(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw) ||
    Object.keys(raw).sort().join('|') !==
    ['background', 'format', 'layers', 'schema', 'shop_id', 'template'].sort().join('|') ||
    raw.schema !== FEATURE3_SCHEMA || !FEATURE3_FORMATS[raw.format] ||
    !FEATURE3_TEMPLATES.includes(raw.template) || !HEX.test(raw.background)) fail('Invalid design schema')
  if (!ID.test(checkedText(raw.shop_id, 100))) fail('Invalid tenant ID')
  if (!Array.isArray(raw.layers) || raw.layers.length < 1 || raw.layers.length > 24) fail('Invalid layer count')
  const seen = new Set()
  const layers = raw.layers.map(item => {
    if (!item || !['rect', 'text', 'image'].includes(item.type)) fail('Invalid layer type')
    const props = ['id', 'type', 'x', 'y', 'w', 'h']
    if (item.type === 'text') props.push('text', 'color', 'font_size', 'bold')
    if (item.type === 'image') props.push('asset_id')
    if (item.type === 'rect') props.push('color')
    if (Object.keys(item).sort().join('|') !== props.sort().join('|')) fail('Unknown layer property')
    if (!ID.test(checkedText(item.id, 48)) || seen.has(item.id)) fail('Duplicate or invalid layer ID')
    seen.add(item.id)
    for (const key of ['x', 'y', 'w', 'h']) {
      if (typeof item[key] !== 'number' || !Number.isFinite(item[key]) ||
        item[key] < 0 || item[key] > 1) fail('Invalid position or size')
    }
    if (item.w < .01 || item.h < .01 || item.x + item.w > 1.00001 ||
      item.y + item.h > 1.00001) fail('Layer outside poster')
    if (item.type === 'text') {
      checkedText(item.text, 160)
      if (!HEX.test(item.color) || !Number.isInteger(item.font_size) ||
        item.font_size < 12 || item.font_size > 150 || typeof item.bold !== 'boolean')
        fail('Invalid typography')
    }
    if (item.type === 'rect' && !HEX.test(item.color)) fail('Invalid fill')
    if (item.type === 'image' && (typeof item.asset_id !== 'string' ||
      !ID.test(item.asset_id))) fail('Image must use an authorized asset ID')
    return { ...item }
  })
  return { ...raw, layers }
}
export function newFeature3History(design) {
  return { past: [], present: validateFeature3Design(design), future: [] }
}
export function editFeature3(history, transform) {
  const changed = validateFeature3Design(transform(structuredClone(history.present)))
  if (JSON.stringify(changed) === JSON.stringify(history.present)) return history
  return { past: [...history.past.slice(-24), history.present],
    present: changed, future: [] }
}
export function undoFeature3(history) {
  if (!history.past.length) return history
  return { past: history.past.slice(0, -1),
    present: history.past.at(-1), future: [history.present, ...history.future].slice(0, 25) }
}
export function redoFeature3(history) {
  if (!history.future.length) return history
  return { past: [...history.past, history.present].slice(-25),
    present: history.future[0], future: history.future.slice(1) }
}
export function updateFeature3Layer(history, id, patch) {
  if (!history.present.layers.some(l => l.id === id)) fail('Unknown layer')
  if (!patch || Object.keys(patch).some(k => ![
    'x', 'y', 'w', 'h', 'text', 'color', 'font_size', 'bold', 'asset_id',
  ].includes(k))) fail('Unknown property')
  return editFeature3(history, document => ({
    ...document, layers: document.layers.map(layer => layer.id === id
      ? { ...layer, ...patch } : layer),
  }))
}
export function moveFeature3Layer(history, id, delta) {
  if (!Number.isInteger(delta)) fail('Invalid layer move')
  return editFeature3(history, doc => {
    const index = doc.layers.findIndex(l => l.id === id)
    if (index < 0) fail('Unknown layer')
    const to = Math.max(0, Math.min(doc.layers.length - 1, index + delta))
    const [layer] = doc.layers.splice(index, 1)
    doc.layers.splice(to, 0, layer)
    return doc
  })
}

export function addFeature3Layer(history, type, assetId = null, authorizedAssetIds = []) {
  if (!['text', 'rect', 'image'].includes(type)) throw Error('Unsupported layer type')
  const number = Array.from({ length: 25 }, (_, i) => 'custom-' + (i + 1))
    .find(id => history.present.layers.every(layer => layer.id !== id))
  if (!number || history.present.layers.length >= 24) throw Error('Layer limit exceeded')
  const placement = { id: number, type, x: .12, y: .33, w: .76, h: .10 }
  let layer
  if (type === 'text') layer = { ...placement, text: 'Your headline',
    color: '#171921', font_size: 42, bold: true }
  else if (type === 'rect') layer = { ...placement, y: .48, h: .08,
    color: '#C05F43' }
  else {
    if (typeof assetId !== 'string' || !Array.isArray(authorizedAssetIds) ||
      !authorizedAssetIds.includes(assetId)) throw Error('Registered private media required')
    layer = { ...placement, y: .17, h: .48, asset_id: assetId }
  }
  return editFeature3(history, doc => ({ ...doc,
    layers: [...doc.layers, layer] }))
}
export function removeFeature3Layer(history, id) {
  if (history.present.layers.length <= 1) throw Error('Cannot remove last layer')
  if (!history.present.layers.some(layer => layer.id === id)) throw Error('Unknown layer')
  return editFeature3(history, doc => ({ ...doc,
    layers: doc.layers.filter(layer => layer.id !== id) }))
}
export function replaceFeature3Image(history, id, assetId, authorizedAssetIds) {
  if (typeof assetId !== 'string' || !Array.isArray(authorizedAssetIds) ||
    !authorizedAssetIds.includes(assetId)) throw Error('Only registered, authorized images')
  const layer = history.present.layers.find(item => item.id === id)
  if (!layer || layer.type !== 'image') throw Error('Select an image layer first')
  return updateFeature3Layer(history, id, { asset_id: assetId })
}
