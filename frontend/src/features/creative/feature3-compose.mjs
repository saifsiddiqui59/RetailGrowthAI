/** CPU-only compositional planner for Feature #3. Mirrors Pillow studio_v2.
 * These are editing suggestions, NOT an authorization boundary: only server
 * RLS, registered media and approved content decide save/render/publish.
 */
import { FEATURE3_SCHEMA, FEATURE3_TEMPLATES, FEATURE3_FORMATS,
  validateFeature3Design } from './feature3-design.mjs'

const PALETTES = Object.freeze({
  fashion: ['#C05F43', '#FCF4EC'], luxury: ['#A98A4B', '#F5F0E5'],
  streetwear: ['#F4511E', '#F2F2F2'], ethnic: ['#A93E4A', '#FFF1DB'],
  festival: ['#CE8831', '#FFF3DB'], restaurant: ['#B54A28', '#FCF2E5'],
  general: ['#286B6A', '#F2F7F6'], new_arrivals: ['#4469A3', '#F5F7FF'],
  clearance: ['#D63E32', '#FFF1EE'], seasonal: ['#55744E', '#F5F7EA'],
})
const IMAGE_RECTS = Object.freeze({
  luxury: [.12, .17, .76, .43], streetwear: [0, .15, 1, .48],
  ethnic: [.08, .16, .84, .46], festival: [.07, .19, .86, .43],
  restaurant: [.07, .16, .86, .48], clearance: [0, .15, 1, .48],
})
const LABELS = Object.freeze({
  fashion: 'THE STYLE EDIT', luxury: 'THE EDIT',
  streetwear: 'BOLD STYLE', ethnic: 'THE ETHNIC EDIT',
  festival: 'FESTIVE EDIT', restaurant: 'MENU SPOTLIGHT',
  general: 'DISCOVER MORE', new_arrivals: 'THE LATEST EDIT',
  clearance: 'SHOP THE EDIT', seasonal: 'SEASONAL EDIT',
})
const HINTS = Object.freeze({
  festival: ['diwali', 'navratri', 'festival', 'christmas'],
  ethnic: ['ethnic', 'saree', 'kurta'],
  streetwear: ['streetwear', 'sneaker'],
  restaurant: ['restaurant', 'food', 'menu'],
  luxury: ['luxury', 'premium', 'boutique'],
  clearance: ['clearance'],
  new_arrivals: ['new arrival'],
  seasonal: ['summer', 'winter', 'seasonal'],
})
function text(value, max) {
  if (typeof value !== 'string' || !value.trim() || value.length > max ||
    /[\x00-\x1f]/.test(value)) throw Error('Invalid required campaign text')
  return value.trim()
}
const txt = (id, x, y, w, h, value, color, font_size, bold) => ({
  id, type: 'text', x, y, w, h, text: value, color, font_size, bold,
})
const rect = (id, x, y, w, h, color) => ({
  id, type: 'rect', x, y, w, h, color,
})

export function selectFeature3Template(prompt) {
  const words = text(prompt, 800).toLowerCase()
  for (const [template, terms] of Object.entries(HINTS)) {
    if (terms.some(term => words.includes(term))) return template
  }
  return 'fashion'
}

export function composeFeature3Poster({
  shopId, mode, prompt, businessName, headline = null,
  cta = 'Visit our store', approvedOffer = null, sourceAssetId = null,
  authorizedAssetIds = [], logoAssetId = null, template = null, format = 'square',
  accent = '#C05F43', background = '#FCF4EC',
}) {
  text(prompt, 800)
  const name = text(businessName, 70)
  const title = text(headline || 'Explore ' + name, 100)
  const action = text(cta, 100)
  if (!['text', 'image'].includes(mode)) throw Error('Invalid poster creation mode')
  // The browser's filtered list is necessary for UX, never sufficient for
  // authorization: server still checks RLS and live media rights on render.
  if (mode === 'image' && (!sourceAssetId ||
      !Array.isArray(authorizedAssetIds) ||
      !authorizedAssetIds.includes(sourceAssetId))) {
    throw Error('Image-to-poster needs registered authorized shop media')
  }
  if (sourceAssetId && (!Array.isArray(authorizedAssetIds) ||
    !authorizedAssetIds.includes(sourceAssetId))) throw Error('Unregistered image')
  if (logoAssetId && (!Array.isArray(authorizedAssetIds) ||
    !authorizedAssetIds.includes(logoAssetId))) throw Error('Unregistered brand logo')
  const chosen = template ?? selectFeature3Template(prompt)
  if (!FEATURE3_TEMPLATES.includes(chosen) || !FEATURE3_FORMATS[format]) {
    throw Error('Unsupported poster template or format')
  }
  if (accent === '#C05F43' && background === '#FCF4EC') {
    [accent, background] = PALETTES[chosen]
  }
  const [ix, iy, iw, ih] = IMAGE_RECTS[chosen] ?? [.07, .16, .86, .47]
  const titleSize = ['streetwear', 'clearance'].includes(chosen) ? 58 :
    chosen === 'luxury' ? 48 : 52
  const layers = [
    txt('brand', .07, .055, .86, .07, name.toUpperCase(), '#23232B', 37, true),
    rect('accent-rule', chosen === 'streetwear' ? 0 : .07, .135,
      chosen === 'clearance' ? .86 : .23, .012, accent),
  ]
  if (logoAssetId) {
    layers[0].w = .68
    layers.push({ id: 'logo', type: 'image', x: .79, y: .03, w: .14,
      h: .085, asset_id: logoAssetId })
  }
  if (sourceAssetId) {
    layers.push({ id: 'product', type: 'image', x: ix, y: iy, w: iw, h: ih,
      asset_id: sourceAssetId })
  } else {
    layers.push(rect('decorative', ix, iy, iw, ih, accent))
    layers.push(txt('concept-label', .13, .38, .74, .12,
      LABELS[chosen], '#FFFFFF', 62, true))
  }
  layers.push(txt('headline', .07, .665, .86, .12, title, '#23232B',
    titleSize, true))
  // Prices, discounts and conditions are supplied ONLY by approved merchant
  // campaign fields, never extracted from untrusted free-form prompts.
  if (approvedOffer !== null && approvedOffer !== undefined) {
    layers.push(txt('offer', .07, .80, .86, .075,
      text(approvedOffer, 85), accent, 44, true))
  }
  layers.push(txt('cta', .07, .92, .86, .06, action, '#23232B', 27, false))
  return validateFeature3Design({
    schema: FEATURE3_SCHEMA, shop_id: shopId, format,
    template: chosen, background, layers,
  })
}
