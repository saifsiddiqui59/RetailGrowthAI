// Tenant-safe bridge: Timeline Studio's real editing primitives -> existing rg_video_v2.
// Upstream editing engine copyright (c) 2026 MartinDelophy (MIT).
// This module does not authorize assets, rewrite approved scripts or export media.
import { getVisualSegmentTimeline, reorderTimelineItems } from './vendor/timeline.js'
import { splitVisualSegmentState } from './vendor/timelineCut.js'
import { recalculateScenes, validateVideoDraft } from './video-model.mjs'

function recalc(scenes, duration) {
  const next = recalculateScenes(scenes)
  const sum = next.reduce((n, s) => n + s.duration, 0)
  if (next.length > 12 || next.some(s => !Number.isFinite(s.duration) || s.duration < 0.5) ||
      Math.abs(sum - duration) > 0.001) throw Error('Timeline edits must preserve the approved 15/30/60 second duration')
  return next
}
export function studioRanges(draft) {
  return getVisualSegmentTimeline(draft.scenes.map((scene, index) =>
    ({ id: String(index), duration: scene.duration })))
}
export function studioReorder(draft, from, to) {
  if (!Number.isInteger(from) || !Number.isInteger(to) || from < 0 ||
      to < 0 || from >= draft.scenes.length || to >= draft.scenes.length) throw Error('Invalid clip reorder')
  return { ...draft, scenes: recalc(reorderTimelineItems(draft.scenes, from, to), draft.duration_seconds) }
}
export function studioSplit(draft, index, offset, mediaAssets) {
  const scene = draft.scenes[index]
  if (!scene || !Number.isFinite(offset) || offset < 0.5 || scene.duration - offset < 0.5 ||
      draft.scenes.length >= 12) throw Error('Split requires at least 0.5s per clip and at most 12 clips')
  const media = (mediaAssets || []).find(a => a.id === scene.asset_id &&
    a.shop_id === draft.shop_id && a.authorized === true)
  if (draft.mode !== 'text' && !media) throw Error('Cannot split an unapproved media source')
  const isVideo = media?.kind === 'video'
  // HyperFrames places approved scene SFX at the scene's first 0-2 seconds.
  // Splitting inside that window would change its true export duration, and
  // copying the SFX to both new clips would cause an unauthorized replay.
  const fxSeconds = Math.min(2, scene.duration)
  if (scene.sfx_asset_id != null && offset < fxSeconds - 0.001) {
    throw Error('Split would cut through the approved 2-second sound effect')
  }
  const parts = splitVisualSegmentState({
    type: isVideo ? 'video' : 'image',
    sourceStart: isVideo ? (scene.trim_start || 0) : 0,
    playbackRate: 1, duration: scene.duration,
  }, offset, scene.duration - offset)
  // Preserve EXACT approved claim, caption and asset identity in both pieces.
  const scenes = [ ...draft.scenes.slice(0, index),
    ...parts.map((part, partIndex) => {
      const { sfx_asset_id, ...rest } = scene
      return {
        ...rest, duration: part.duration,
        ...(partIndex === 0 && sfx_asset_id != null ? { sfx_asset_id } : {}),
        ...(isVideo ? { trim_start: part.sourceStart } : {}),
      }
    }),
    ...draft.scenes.slice(index + 1),
  ]
  return { ...draft, scenes: recalc(scenes, draft.duration_seconds) }
}
// Duplicate the VISUAL content in place by replaying the first half twice.
// Preserve the fixed 15/30/60s output contract and review-locked offer/copy.
// A source video intentionally restarts from its approved in-point, rather than
// pretending source footage exists beyond the authorized media duration.
export function studioDuplicate(draft, index, mediaAssets = []) {
  const scene = draft.scenes?.[index]
  if (!Number.isInteger(index) || !scene || draft.scenes.length >= 12 ||
      !Number.isFinite(scene.duration) || scene.duration < 1) {
    throw Error('Duplication needs a clip of at least 1 second and fewer than 12 scenes')
  }
  const media = mediaAssets.find(a => a.id === scene.asset_id &&
    a.shop_id === draft.shop_id && a.authorized === true &&
    ['image','poster','video'].includes(a.kind))
  if (draft.mode !== 'text' && !media) throw Error('Cannot duplicate a foreign or unapproved clip')
  const first = Math.round(scene.duration * 500) / 1000
  const second = Math.round((scene.duration - first) * 1000) / 1000
  if (first < .5 || second < .5) throw Error('Duplicate clips must remain at least 0.5 seconds')
  if (scene.sfx_asset_id != null && first < Math.min(2, scene.duration)) {
    throw Error('Duplication would truncate an approved 2-second scene sound effect')
  }
  const {sfx_asset_id, ...withoutEffect} = scene
  const copy = { ...withoutEffect, duration: second,
    ...(media?.kind === 'video' ? {trim_start: scene.trim_start || 0} : {}) }
  const original = {...scene, duration: first}
  return { ...draft, scenes: recalc([
    ...draft.scenes.slice(0,index), original, copy,
    ...draft.scenes.slice(index+1)
  ],draft.duration_seconds) }
}

export function studioTrimPair(draft, index, delta, mediaAssets = []) {
  if (!Number.isInteger(index) || !Number.isFinite(delta) || index < 0 ||
      index >= draft.scenes.length - 1) throw Error('Select an internal clip boundary')
  const a = draft.scenes[index], b = draft.scenes[index + 1]
  const durationA = Math.round((a.duration + delta) * 1000) / 1000
  const durationB = Math.round((b.duration - delta) * 1000) / 1000
  if (durationA < 0.5 || durationB < 0.5) throw Error('Each clip must remain at least 0.5 seconds')
  // Fixed-gain HyperFrames scene SFX plays for min(2s, scene duration).
  // Shortening an approved 2s effect to 1s (or extending a shorter effect)
  // silently changes the sound. Reject the boundary edit, never retime audio.
  if ((a.sfx_asset_id != null && Math.min(2, a.duration) !== Math.min(2, durationA)) ||
      (b.sfx_asset_id != null && Math.min(2, b.duration) !== Math.min(2, durationB))) {
    throw Error('Boundary trim would change an approved scene sound-effect duration')
  }
  // Left-hand VIDEO can gain duration: verify the newly exposed frames exist
  // whenever a trusted/probed source duration is available.
  const leftMedia = mediaAssets.find(asset => asset.id === a.asset_id &&
    asset.shop_id === draft.shop_id && asset.authorized === true)
  if (leftMedia?.kind === 'video' && typeof leftMedia.duration_seconds === 'number' &&
      Number.isFinite(leftMedia.duration_seconds) && leftMedia.duration_seconds > 0 &&
      (a.trim_start || 0) + durationA > leftMedia.duration_seconds + 0.02) {
    throw Error('Boundary trim exceeds verified source video duration')
  }
  // A right-hand VIDEO clip must start later in its source if its timeline
  // start is pushed right. Otherwise moving the boundary silently replays the
  // original frames and the editor's timing is not reproduced by FFmpeg.
  const rightMedia = mediaAssets.find(a => a.id === b.asset_id &&
    a.shop_id === draft.shop_id && a.authorized === true)
  const isVideo = rightMedia?.kind === 'video' || b.trim_start != null
  const rightStart = b.trim_start || 0
  const nextRightStart = Math.round((rightStart + delta) * 1000) / 1000
  if (isVideo && nextRightStart < 0) {
    throw Error('Cannot extend video before its source begins')
  }
  return { ...draft, scenes: recalc(draft.scenes.map((scene, i) => i === index ?
    { ...scene, duration: durationA } : i === index + 1 ?
      { ...scene, duration: durationB,
        ...(isVideo ? {trim_start:nextRightStart} : {}) } : scene), draft.duration_seconds) }
}
export function studioSourceTrim(draft, index, seconds, mediaAssets) {
  const scene = draft.scenes[index]
  const source = (mediaAssets || []).find(m => m.id === scene?.asset_id &&
    m.kind === 'video' && m.shop_id === draft.shop_id && m.authorized === true)
  if (!source || !Number.isFinite(seconds) || seconds < 0 || seconds > 180) {
    throw Error('Source trim is only allowed on the current tenant’s approved video')
  }
  if (typeof source.duration_seconds === 'number' && Number.isFinite(source.duration_seconds) &&
      seconds + scene.duration > source.duration_seconds + 0.02) {
    throw Error('Video trim exceeds verified source length')
  }
  return { ...draft, scenes: draft.scenes.map((item, i) =>
    i === index ? { ...item, trim_start: seconds } : item) }
}
// The UI is never the authorizing store. This catches accidental cross-shop
// preview/edits early; the trusted compiler revalidates all grants at render time.
export function studioValidatedDraft(draft, mediaAssets, musicAssets) {
  if (!draft || typeof draft.shop_id !== 'string' || !Array.isArray(draft.scenes)) {
    throw Error('Missing or invalid tenant timeline')
  }
  const media = Array.isArray(mediaAssets) ? mediaAssets : []
  const music = Array.isArray(musicAssets) ? musicAssets : []
  const sameShop = (id, records, allowedKinds) => {
    if (!records.some(a => a.id === id && a.shop_id === draft.shop_id &&
        a.authorized === true && allowedKinds.includes(a.kind))) {
      throw Error('Foreign, unlicensed or revoked media cannot enter this timeline')
    }
  }
  for (const scene of draft.scenes) {
    if (draft.mode !== 'text') {
      sameShop(scene.asset_id, media, ['image', 'poster', 'video'])
    }
    if (scene.poster_overlay_asset_id != null) {
      sameShop(scene.poster_overlay_asset_id, media, ['poster'])
    }
    if (scene.sfx_asset_id != null) {
      sameShop(scene.sfx_asset_id, music, ['audio'])
    }
    if (scene.trim_start != null) {
      const asset = media.find(a => a.id === scene.asset_id && a.shop_id === draft.shop_id)
      if (!asset || asset.kind !== 'video' || typeof scene.trim_start !== 'number' ||
          !Number.isFinite(scene.trim_start) || scene.trim_start < 0 ||
          scene.trim_start > 180) throw Error('Invalid approved video trim')
    }
    const asset = media.find(a => a.id === scene.asset_id && a.shop_id === draft.shop_id)
    const duration = asset?.duration_seconds
    // Duration is server-probed media metadata, when available. A missing value
    // is NOT interpreted as unlimited footage: final worker probes the source.
    if (asset?.kind === 'video' && typeof duration === 'number' &&
        Number.isFinite(duration) && duration > 0 &&
        (scene.trim_start || 0) + scene.duration > duration + 0.02) {
      throw Error('Video trim exceeds verified source length')
    }
  }
  if (draft.music_asset_id != null) sameShop(draft.music_asset_id, music, ['audio'])
  if (draft.voiceover_asset_id != null) sameShop(draft.voiceover_asset_id, music, ['audio'])
  const issues = validateVideoDraft(draft, mediaAssets, musicAssets)
  if (issues.length) throw Error(issues.join('; '))
  return draft
}
