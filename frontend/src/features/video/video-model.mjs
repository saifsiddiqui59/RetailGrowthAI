// Feature #4 UI-only plan helpers. Never treat these as backend authorization.
export const VIDEO_MODES = Object.freeze([
  ['text', 'Text-to-video'],
  ['image', 'Product image animation'],
  ['poster', 'Poster-to-video'],
  ['media', 'Uploaded clips + photos'],
  ['music_sync', 'Music-synchronized Reel'],
])
export const VIDEO_TEMPLATES = Object.freeze([
  ['streetwear', 'Streetwear Beat Cut'],
  ['cinematic', 'Cinematic Fashion'],
  ['festival', 'Festival Sale'],
])
export const VIDEO_ANIMATIONS = Object.freeze(['subtle_zoom', 'pop', 'fade', 'slide', 'glow'])
export const VIDEO_TRANSITIONS = Object.freeze(['fade', 'slide', 'cut'])
const LIMITS = { text: null, image: ['image'], poster: ['poster'], media: ['image', 'poster', 'video'], music_sync: ['image', 'poster', 'video'] }
const valid = (n) => typeof n === 'number' && Number.isFinite(n)

export function compatibleMedia(mode, assets, shopId = null) {
  return (Array.isArray(assets) ? assets : []).filter(item =>
    item && item.authorized === true && typeof item.id === 'string' &&
    /^[a-zA-Z0-9_-]{1,100}$/.test(item.id) &&
    (shopId === null || item.shop_id === shopId) &&
    LIMITS[mode]?.includes(item.kind))
}

export function makeVideoDraft({ shopId, mode = 'image', template = 'streetwear',
  duration = 15, mediaAssets = [] }) {
  if (!VIDEO_MODES.some(([key]) => key === mode) || !VIDEO_TEMPLATES.some(([key]) => key === template) ||
      ![15, 30, 60].includes(duration)) throw Error('Invalid video configuration')
  const media = compatibleMedia(mode, mediaAssets, shopId)
  return {
    version: 'rg_video_v2', shop_id: shopId, mode, template, duration_seconds: duration,
    output: { width: 1080, height: 1920, fps: 30 },
    scenes: Array.from({ length: 3 }, (_, i) => ({
      start: i * duration / 3, duration: duration / 3,
      headline: ['Your brand story', 'Discover the collection', 'Visit us today'][i],
      animation_preset: 'subtle_zoom', transition: 'fade',
      ...(mode !== 'text' && media.length ? { asset_id: media[i % media.length].id } : {}),
    })),
    cta: 'Visit our store', music_asset_id: null, voiceover_asset_id: null,
  }
}

export function recalculateScenes(scenes) {
  let elapsed = 0
  return scenes.map(scene => {
    const next = { ...scene, start: elapsed }
    elapsed += Number(scene.duration)
    return next
  })
}

// Retiming is a pure draft edit: preserve approved text, asset IDs, offers and order.
export function retimeVideoDraft(plan, duration) {
  if (!plan || !Array.isArray(plan.scenes) || !plan.scenes.length ||
      ![15, 30, 60].includes(duration) || ![15, 30, 60].includes(plan.duration_seconds) ||
      plan.scenes.some(scene => !valid(scene.duration) || scene.duration < .5)) {
    throw Error('Invalid timeline for retiming')
  }
  let elapsed = 0
  const scenes = plan.scenes.map((scene, index) => {
    const length = index === plan.scenes.length - 1 ? duration - elapsed
      : Math.round(scene.duration * duration / plan.duration_seconds * 1000) / 1000
    if (length < .5) throw Error('Scenes would be shorter than half a second')
    const copy = { ...scene, start: elapsed, duration: length }
    elapsed = Math.round((elapsed + length) * 1000) / 1000
    return copy
  })
  return { ...plan, duration_seconds: duration, scenes }
}

export function shiftVideoScene(scenes, from, move) {
  if (!Array.isArray(scenes) || !Number.isInteger(from) || ![-1, 1].includes(move) ||
      from < 0 || from >= scenes.length || from + move < 0 || from + move >= scenes.length) return scenes
  const copy = scenes.map(scene => ({ ...scene }))
  const [selected] = copy.splice(from, 1)
  copy.splice(from + move, 0, selected)
  return recalculateScenes(copy)
}

export function validateVideoDraft(plan, mediaAssets = [], musicAssets = []) {
  const errors = []
  if (!plan || plan.version !== 'rg_video_v2') return ['Unsupported timeline version']
  if (typeof plan.shop_id !== 'string' || !plan.shop_id) return ['Selected tenant is required']
  if (!VIDEO_MODES.some(([key]) => key === plan.mode)) errors.push('Choose a video mode')
  if (!VIDEO_TEMPLATES.some(([key]) => key === plan.template)) errors.push('Choose a template')
  if (![15, 30, 60].includes(plan.duration_seconds)) errors.push('Duration must be 15, 30 or 60 seconds')
  if (!Array.isArray(plan.scenes) || !plan.scenes.length || plan.scenes.length > 12) return [...errors, 'Expected 1–12 scenes']
  const authorizedMedia = compatibleMedia(plan.mode, mediaAssets, plan.shop_id)
  const allowed = new Set(authorizedMedia.map(media => media.id))
  let time = 0
  for (const [index, scene] of plan.scenes.entries()) {
    if (!valid(scene.start) || !valid(scene.duration) || scene.duration < .5 ||
        Math.abs(scene.start - time) > .001) errors.push('Scenes must be sequential and at least half a second')
    if (typeof scene.headline !== 'string' || !scene.headline.trim() || scene.headline.length > 110) {
      errors.push('Every scene needs an approved headline (max 110 characters)')
    }
    if (plan.mode !== 'text' && !allowed.has(scene.asset_id)) errors.push('Scene ' + (index + 1) + ' needs authorized same-shop media')
    const source = authorizedMedia.find(asset => asset.id === scene.asset_id)
    if (scene.trim_start != null) {
      if (source?.kind !== 'video' || !valid(scene.trim_start) ||
          scene.trim_start < 0 || scene.trim_start > 180) {
        errors.push('Scene ' + (index + 1) + ' has invalid approved video trim')
      }
    }
    if (scene.mute_source != null && (source?.kind !== 'video' || typeof scene.mute_source !== 'boolean')) {
      errors.push('Scene ' + (index + 1) + ' has unsupported source audio mute')
    }
    if (source?.kind === 'video' && valid(source.duration_seconds) &&
        source.duration_seconds > 0 &&
        (scene.trim_start || 0) + scene.duration > source.duration_seconds + .02) {
      errors.push('Scene ' + (index + 1) + ' exceeds verified video source duration')
    }
    if (scene.animation_preset != null && !VIDEO_ANIMATIONS.includes(scene.animation_preset)) {
      errors.push('Scene ' + (index + 1) + ' has an unapproved motion preset')
    }
    if (scene.transition != null && !VIDEO_TRANSITIONS.includes(scene.transition)) {
      errors.push('Scene ' + (index + 1) + ' has an unapproved transition')
    }
    if (scene.poster_overlay_asset_id != null) {
      const poster = mediaAssets.find(item => item?.authorized === true &&
        item?.kind === 'poster' && item?.id === scene.poster_overlay_asset_id &&
        item?.shop_id === plan.shop_id)
      if (!poster || poster.id === scene.asset_id) {
        errors.push('Scene ' + (index + 1) + ' needs a distinct authorized promotional poster')
      }
    }
    if (scene.sfx_asset_id != null && !musicAssets.some(track =>
        track?.id === scene.sfx_asset_id && track?.authorized === true &&
        track?.kind === 'audio' && track?.shop_id === plan.shop_id)) {
      errors.push('Scene ' + (index + 1) + ' needs a same-shop licensed audio effect')
    }
    if (scene.offer != null && (typeof scene.offer !== 'string' || scene.offer.length > 70)) {
      errors.push('Offer text must be approved (max 70 characters)')
    }
    time += Number(scene.duration)
  }
  if (Math.abs(time - plan.duration_seconds) > .001) errors.push('Scenes must fill the selected duration')
  if (typeof plan.cta !== 'string' || !plan.cta.trim() || plan.cta.length > 110) errors.push('Enter an approved CTA')
  if (plan.voiceover_asset_id != null && !musicAssets.some(a =>
      a?.id === plan.voiceover_asset_id && a?.authorized === true &&
      a?.kind === 'audio' && a?.shop_id === plan.shop_id)) {
    errors.push('Select an approved same-shop full-Reel narration recording')
  }
  if (plan.music_asset_id != null && !musicAssets.some(m =>
      m?.id === plan.music_asset_id && m?.authorized === true &&
      m?.kind === 'audio' && m?.shop_id === plan.shop_id)) {
    errors.push('Select a rights-cleared music track')
  }
  if (plan.voiceover_asset_id != null && musicAssets.some(a =>
      a?.id === plan.voiceover_asset_id && a?.authorized === true &&
      a?.shop_id === plan.shop_id && a?.kind === 'audio' &&
      valid(a.duration_seconds) && a.duration_seconds + .06 < plan.duration_seconds)) {
    errors.push('Approved full-Reel narration does not cover the full video duration')
  }
  if (plan.mode === 'music_sync' &&
      (!plan.music_asset_id || !Array.isArray(plan.beats) || plan.beats.length < 2)) {
    errors.push('Beat-sync requires an approved soundtrack and server-derived beats')
  }
  return [...new Set(errors)]
}

/** Preview exactly the authorized source-video excerpt used by the existing
 *  HyperFrames data-media-start/data-duration renderer. No URLs or rights
 *  approvals may be derived here; the private-media adapter owns URL checks.
 */
export function sourceClipPlaybackWindow(scene, source) {
  if (!scene || !source || source.kind !== 'video' || source.authorized !== true) return null
  const start = scene.trim_start ?? 0
  if (!valid(start) || start < 0 || start > 180 ||
      !valid(scene.duration) || scene.duration < .5) {
    throw Error('Preview has an invalid verified source trim')
  }
  const end = Math.round((start + scene.duration) * 1000) / 1000
  if (valid(source.duration_seconds) && source.duration_seconds > 0 &&
      end > source.duration_seconds + .02) {
    throw Error('Source preview exceeds verified video length')
  }
  return Object.freeze({start, end})
}
