/** Offline, no-extra-package local poster draft PNG renderer.
 *
 * Draft-only approximation: the authoritative server Pillow rendering,
 * media rights and human-approved offer gates still apply to cloud exports.
 * Never use this to generate a publish/approval receipt.
 */
import { FEATURE3_FORMATS, validateFeature3Design } from './feature3-design.mjs'

const MAX_SOURCE_PIXELS = 24_000_000
const FONT_FAMILY = '"DejaVu Sans", Arial, sans-serif'

function availableImage(image) {
  return image && image.complete === true &&
    Number.isInteger(image.naturalWidth) && image.naturalWidth > 0 &&
    Number.isInteger(image.naturalHeight) && image.naturalHeight > 0 &&
    image.naturalWidth * image.naturalHeight <= MAX_SOURCE_PIXELS
}

function splitWrappedLines(ctx, value, maxWidth) {
  const lines = []
  let line = ''
  for (const word of value.split(/\s+/u)) {
    const combined = line ? line + ' ' + word : word
    if (ctx.measureText(combined).width <= maxWidth) {
      line = combined
      continue
    }
    if (line) {
      lines.push(line)
      line = ''
    }
    // Long SKU or discount tokens must wrap rather than disappear.
    for (const char of word) {
      if (line && ctx.measureText(line + char).width > maxWidth) {
        lines.push(line)
        line = ''
      }
      line += char
    }
  }
  if (line) lines.push(line)
  return lines
}

function drawExactDraftText(ctx, layer, x, y, width, height, factor) {
  // All text is shown or the export is refused. It is a draft approximation,
  // not the official Pillow font/layout review.
  for (let size = Math.max(8, Math.round(layer.font_size * factor));
       size >= 8; size -= 1) {
    ctx.font = `${layer.bold ? 'bold ' : ''}${size}px ${FONT_FAMILY}`
    const lines = splitWrappedLines(ctx, layer.text, width)
    const lineHeight = Math.max(9, Math.round(size * 1.24))
    if (lines.length && lines.every(line => ctx.measureText(line).width <= width) &&
        lines.length * lineHeight <= height) {
      ctx.fillStyle = layer.color
      ctx.textBaseline = 'top'
      for (let index = 0; index < lines.length; index++) {
        ctx.fillText(lines[index], x, y + index * lineHeight)
      }
      return
    }
  }
  throw new Error('Poster text cannot fit without clipping. Enlarge the text layer.')
}

function drawAuthorizedPhoto(ctx, layer, image, x, y, width, height) {
  const iw = image.naturalWidth
  const ih = image.naturalHeight
  if (layer.id === 'logo') {
    const ratio = Math.min(width / iw, height / ih)
    const dw = iw * ratio
    const dh = ih * ratio
    ctx.drawImage(image, x + (width - dw) / 2, y + (height - dh) / 2, dw, dh)
    return
  }
  const zoom = Math.max(width / iw, height / ih)
  const sourceW = width / zoom
  const sourceH = height / zoom
  ctx.drawImage(image, (iw - sourceW) / 2, (ih - sourceH) / 2,
    sourceW, sourceH, x, y, width, height)
}

export function renderFeature3LocalDraft(canvas, draft, authorizedImages = {}) {
  const document = validateFeature3Design(draft)
  if (!canvas || typeof canvas.getContext !== 'function' ||
      !authorizedImages || typeof authorizedImages !== 'object') {
    throw new Error('A local canvas and already-authorized media map are required')
  }
  const [width, height] = FEATURE3_FORMATS[document.format]
  const images = {}
  // Check ALL image layers first; avoid partial outputs if an asset was revoked.
  for (const layer of document.layers) {
    if (layer.type !== 'image' || images[layer.asset_id]) continue
    const image = authorizedImages[layer.asset_id]
    if (!availableImage(image)) {
      throw new Error('Registered private product media is unavailable for draft preview')
    }
    images[layer.asset_id] = image
  }
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d', { alpha: false })
  if (!ctx || typeof ctx.measureText !== 'function') {
    throw new Error('2D canvas is unavailable')
  }
  ctx.fillStyle = document.background
  ctx.fillRect(0, 0, width, height)
  for (const layer of document.layers) {
    const x = Math.round(layer.x * width)
    const y = Math.round(layer.y * height)
    const w = Math.round(layer.w * width)
    const h = Math.round(layer.h * height)
    if (layer.type === 'rect') {
      ctx.fillStyle = layer.color
      ctx.fillRect(x, y, w, h)
    } else if (layer.type === 'image') {
      drawAuthorizedPhoto(ctx, layer, images[layer.asset_id], x, y, w, h)
    } else {
      drawExactDraftText(ctx, layer, x, y, w, h, width / 1080)
    }
  }
  return {
    width, height, format: 'png',
    shop_id: document.shop_id,
    draft_only: true, approved: false, inference: false,
  }
}
