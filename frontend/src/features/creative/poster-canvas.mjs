// Browser-only design-preview utility. No remote media, file uploads or publishing.
export const POSTER_TEMPLATES = Object.freeze(['editorial', 'bold', 'minimal'])
export const POSTER_SIZES = Object.freeze({ square: [1080, 1080], portrait: [1080, 1350] })
const HEX = /^#[0-9a-fA-F]{6}$/

export function posterText(day) {
  if (!day || typeof day.topic !== 'string' ||
      typeof day.instagram?.reel?.cta !== 'string') {
    throw new Error('Choose a valid campaign day before creating a poster.')
  }
  return {
    title: day.topic.trim().slice(0, 140),
    cta: day.instagram.reel.cta.trim().slice(0, 110),
    dayIndex: day.day_index,
  }
}

export function posterOptions({ template, size, brand, accent, background, offer }) {
  if (!POSTER_TEMPLATES.includes(template) || !POSTER_SIZES[size]) {
    throw new Error('Select a supported poster layout and size.')
  }
  if (!HEX.test(accent) || !HEX.test(background)) {
    throw new Error('Colors must use valid hex codes.')
  }
  const clean = (value, max) => String(value ?? '').trim().slice(0, max)
  const business = clean(brand, 70)
  if (!business) throw new Error('Enter your business name.')
  return { template, size, brand: business, accent, background, offer: clean(offer, 110) }
}

export function coverCrop(iw, ih, dw, dh) {
  if (![iw, ih, dw, dh].every(x => Number.isFinite(x) && x > 0)) {
    throw new Error('Invalid product photo dimensions.')
  }
  const ratio = Math.max(dw / iw, dh / ih)
  const sourceW = dw / ratio
  const sourceH = dh / ratio
  return [(iw - sourceW) / 2, (ih - sourceH) / 2, sourceW, sourceH]
}

function contrast(hex) {
  const v = [1, 3, 5].map(n => parseInt(hex.slice(n, n + 2), 16) / 255)
  return (v[0] * .2126 + v[1] * .7152 + v[2] * .0722) >= .56 ? '#171921' : '#ffffff'
}

function wrap(ctx, text, maxWidth, maxLines = 2) {
  const words = String(text).split(/\s+/).filter(Boolean)
  const result = []
  let line = ''
  for (const word of words) {
    const trial = (line ? line + ' ' : '') + word
    if (ctx.measureText(trial).width <= maxWidth) { line = trial; continue }
    if (line) { result.push(line); line = word }
    else {
      let prefix = ''
      for (const char of word) {
        if (ctx.measureText(prefix + char + '…').width > maxWidth) break
        prefix += char
      }
      result.push(prefix + '…')
      line = ''
    }
    if (result.length >= maxLines) break
  }
  if (line && result.length < maxLines) result.push(line)
  if (result.length === maxLines && words.join(' ') !== result.join(' ')) {
    let last = result[maxLines - 1].replace(/…$/, '')
    while (last && ctx.measureText(last + '…').width > maxWidth) last = last.slice(0, -1)
    result[maxLines - 1] = last.trimEnd() + '…'
  }
  return result
}

function lines(ctx, text, x, y, maxWidth, fontSize, maxLines = 2) {
  const rendered = wrap(ctx, text, maxWidth, maxLines)
  for (const value of rendered) {
    ctx.fillText(value, x, y)
    y += fontSize + 12
  }
  return y
}

function photograph(ctx, image, x, y, w, h) {
  if (image) {
    const [sx, sy, sw, sh] = coverCrop(image.width, image.height, w, h)
    ctx.drawImage(image, sx, sy, sw, sh, x, y, w, h)
  } else {
    const g = ctx.createLinearGradient(x, y, x + w, y + h)
    g.addColorStop(0, '#c2b19c')
    g.addColorStop(1, '#49445b')
    ctx.fillStyle = g
    ctx.fillRect(x, y, w, h)
    ctx.fillStyle = 'rgba(255,255,255,.88)'
    ctx.font = 'bold 32px system-ui, sans-serif'
    ctx.fillText('ADD YOUR PRODUCT PHOTO', x + 36, y + h / 2)
  }
}

export function drawPoster(canvas, image, day, rawOptions) {
  const info = posterText(day)
  const options = posterOptions(rawOptions)
  const [w, h] = POSTER_SIZES[options.size]
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Canvas rendering is unavailable in this browser.')
  ctx.clearRect(0, 0, w, h)
  ctx.fillStyle = options.background
  ctx.fillRect(0, 0, w, h)
  const ink = contrast(options.background)
  const accentInk = contrast(options.accent)
  const margin = 70
  if (options.template === 'bold') {
    const photoH = Math.round(h * .57)
    photograph(ctx, image, 0, 0, w, photoH)
    ctx.fillStyle = options.accent
    ctx.fillRect(0, photoH, w, h - photoH)
    ctx.fillStyle = options.background
    ctx.fillRect(margin, 56, 460, 62)
    ctx.fillStyle = ink
    ctx.font = 'bold 30px system-ui, sans-serif'
    ctx.fillText(options.brand.toUpperCase().slice(0, 23), margin + 24, 97)
    ctx.fillStyle = accentInk
    ctx.font = 'bold 67px system-ui, sans-serif'
    let next = lines(ctx, info.title, margin, photoH + 100, w - margin * 2, 67, 2)
    if (options.offer) {
      ctx.font = 'bold 36px system-ui, sans-serif'
      next = lines(ctx, options.offer, margin, next + 8, w - margin * 2, 36, 1)
    }
    ctx.font = 'bold 32px system-ui, sans-serif'
    ctx.fillText(info.cta.slice(0, 48), margin, h - 70)
  } else if (options.template === 'minimal') {
    ctx.fillStyle = options.accent
    ctx.fillRect(margin, 75, w - margin * 2, 6)
    ctx.fillStyle = ink
    ctx.font = 'bold 33px system-ui, sans-serif'
    ctx.fillText(options.brand.toUpperCase().slice(0, 29), margin, 145)
    const photoH = Math.round(h * .49)
    photograph(ctx, image, margin, 198, w - margin * 2, photoH)
    ctx.font = 'bold 58px system-ui, sans-serif'
    let next = lines(ctx, info.title, margin, 198 + photoH + 98, w - margin * 2, 58, 2)
    if (options.offer) {
      ctx.fillStyle = options.accent
      ctx.font = 'bold 33px system-ui, sans-serif'
      next = lines(ctx, options.offer, margin, next + 5, w - margin * 2, 33, 1)
    }
    ctx.fillStyle = options.accent
    ctx.fillRect(margin, h - 116, w - margin * 2, 3)
    ctx.fillStyle = ink
    ctx.font = '32px system-ui, sans-serif'
    ctx.fillText(info.cta.slice(0, 48), margin, h - 68)
  } else {
    ctx.fillStyle = options.accent
    ctx.fillRect(margin, 105, 92, 9)
    ctx.fillStyle = ink
    ctx.font = 'bold 30px system-ui, sans-serif'
    ctx.fillText(options.brand.toUpperCase().slice(0, 31), margin + 110, 118)
    const photoH = Math.round(h * .47)
    photograph(ctx, image, margin, 156, w - margin * 2, photoH)
    ctx.font = 'bold 60px system-ui, sans-serif'
    let next = lines(ctx, info.title, margin, 156 + photoH + 99, w - margin * 2, 60, 2)
    if (options.offer) {
      ctx.fillStyle = options.accent
      ctx.font = 'bold 34px system-ui, sans-serif'
      next = lines(ctx, options.offer, margin, next + 8, w - margin * 2, 34, 1)
    }
    ctx.fillStyle = options.accent
    ctx.fillRect(margin, h - 125, w - margin * 2, 70)
    ctx.fillStyle = accentInk
    ctx.font = 'bold 31px system-ui, sans-serif'
    ctx.fillText(info.cta.slice(0, 48), margin + 24, h - 80)
  }
  return { width: w, height: h, title: info.title, size: options.size, template: options.template }
}
