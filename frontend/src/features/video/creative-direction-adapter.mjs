// Feature #2 controls all creative direction, voice lines, offers and motion briefs.
// Proposed read-only F2 handoff adapter. No trust is conferred by browser approval.
import { compatibleMedia, validateVideoDraft } from './video-model.mjs'
const id = value => typeof value === 'string' && /^[A-Za-z0-9_-]{1,100}$/.test(value)
// Read-only preview of the Feature2-reviewed timed transcript. Server approval
// and audio provenance MUST be independently verified before a render.
export function checkedPreviewCaptionCues(cues,duration) {
  if(cues == null) return []
  if(!Array.isArray(cues) || cues.length<1 || cues.length>60 ||
     ![15,30,60].includes(duration)) throw Error('Unsupported approved spoken subtitles')
  let priorMs=0
  return cues.map(c=>{
    if(!c || typeof c!=='object' || Array.isArray(c) ||
       Object.keys(c).sort().join(',')!=='duration,start,text' ||
       typeof c.start!=='number' || !Number.isFinite(c.start) ||
       typeof c.duration!=='number' || !Number.isFinite(c.duration) ||
       c.start<0 || c.duration<.2 || c.duration>6 ||
       c.start!==Math.round(c.start*1000)/1000 ||
       c.duration!==Math.round(c.duration*1000)/1000 ||
       Math.round(c.start*1000)<priorMs ||
       Math.round(c.start*1000)+Math.round(c.duration*1000)>duration*1000 ||
       typeof c.text!=='string' || c.text!==c.text.trim() ||
       !c.text.length || c.text.length>90 || /[<>\x00-\x1F\x7F]/.test(c.text)) {
      throw Error('Feature2 spoken subtitle has unsafe or overlapping timecodes')
    }
    priorMs=Math.round(c.start*1000)+Math.round(c.duration*1000)
    return {start:c.start,duration:c.duration,text:c.text}
  })
}

export function inspectCreativeDirection(packageData, { shopId, mediaAssets = [], musicAssets = [] } = {}) {
  if (!packageData || typeof packageData !== 'object' || Array.isArray(packageData) ||
      packageData.version !== 'creative_direction_v1' ||
      packageData.source_feature !== 'feature2' || packageData.approved !== true ||
      packageData.shop_id !== shopId || !id(packageData.approval_id) ||
      !id(packageData.campaign_id) || ![15, 30, 60].includes(packageData.duration_seconds) ||
      !Array.isArray(packageData.scenes) || packageData.scenes.length < 1 ||
      packageData.scenes.length > 12 || !id(packageData.review_hash)) {
    throw Error('Trusted, versioned Feature #2 creative direction is required')
  }
  const creative = packageData.scenes
  const assets = compatibleMedia('media', mediaAssets, shopId)
  let position = 0
  const scenes = creative.map((shot, index) => {
    const source = assets.find(a => a.id === shot?.asset_id)
    const overlay = shot?.poster_overlay_asset_id
    const legalPoster = overlay == null || mediaAssets.some(a =>
      a.id === overlay && a.shop_id === shopId && a.authorized === true &&
      a.kind === 'poster' && overlay !== shot.asset_id)
    const videoSource = source?.kind === 'video'
    if (!shot || !Number.isFinite(shot.duration) || shot.duration < 0.5 ||
        typeof shot.headline !== 'string' || !shot.headline.trim() ||
        shot.headline.length > 110 || typeof shot.asset_id !== 'string' ||
        !assets.some(a => a.id === shot.asset_id) ||
        !['fade', 'slide', 'cut'].includes(shot.transition) ||
        !['subtle_zoom', 'fade', 'slide', 'pop', 'glow'].includes(shot.animation_preset) ||
        !legalPoster ||
        (shot.trim_start != null && (!videoSource ||
          typeof shot.trim_start !== 'number' || !Number.isFinite(shot.trim_start) ||
          shot.trim_start < 0 || shot.trim_start > 180 ||
          (typeof source.duration_seconds === 'number' &&
           source.duration_seconds > 0 && shot.trim_start + shot.duration > source.duration_seconds + .02))) ||
        (shot.mute_source != null && (!videoSource || typeof shot.mute_source !== 'boolean')) ||
        (shot.offer != null && (typeof shot.offer !== 'string' || shot.offer.length > 70)) ||
        (shot.sfx_asset_id != null && !musicAssets.some(track =>
          track.id === shot.sfx_asset_id && track.shop_id === shopId &&
          track.authorized === true && track.kind === 'audio'))) {
      throw Error('Feature #2 scene '+(index + 1)+' needs approved assets and renderable effects')
    }
    const s = { start: position, duration: shot.duration, asset_id: shot.asset_id,
      headline: shot.headline, transition: shot.transition, animation_preset: shot.animation_preset,
      ...(shot.offer ? { offer: shot.offer } : {}),
      ...(shot.sfx_asset_id ? { sfx_asset_id: shot.sfx_asset_id } : {}),
      ...(overlay != null ? { poster_overlay_asset_id: overlay } : {}),
      ...(shot.trim_start != null ? { trim_start: shot.trim_start } : {}),
      ...(shot.mute_source != null ? { mute_source: shot.mute_source } : {}) }
    position = Math.round((position + s.duration) * 1000) / 1000
    return s
  })
  if (Math.abs(position - packageData.duration_seconds) > 0.001 ||
      typeof packageData.cta !== 'string' || !packageData.cta.trim() ||
      packageData.cta.length > 110 || !['cinematic','streetwear','festival'].includes(packageData.template) ||
      (packageData.music_asset_id && !musicAssets.some(a => a.id === packageData.music_asset_id &&
        a.authorized === true && a.shop_id === shopId && a.kind === 'audio'))) {
    throw Error('Feature #2 direction has unsupported timeline, CTA or licensed soundtrack')
  }
  if (packageData.voiceover_asset_id != null &&
      !musicAssets.some(a => a.id === packageData.voiceover_asset_id &&
        a.shop_id === shopId && a.authorized === true && a.kind === 'audio')) {
    throw Error('Feature #2 narration is not rights-authorized for this shop')
  }
  const sourceScript=packageData.script
  if(sourceScript != null && (sourceScript.source_feature!=='feature2' ||
      sourceScript.approved!==true || sourceScript.approval_id!==packageData.approval_id)) {
    throw Error('Feature2 spoken transcript revision is not approved')
  }
  const captionCues=checkedPreviewCaptionCues(sourceScript?.transcript,packageData.duration_seconds)
  if(captionCues.length && !packageData.voiceover_asset_id) {
    throw Error('Spoken subtitles require reviewed narration media')
  }
  const draft = { version: 'rg_video_v2', shop_id: shopId, mode: 'media',
    template: packageData.template, duration_seconds: packageData.duration_seconds,
    output: { width: 1080, height: 1920, fps: 30 }, scenes,
    cta: packageData.cta, music_asset_id: packageData.music_asset_id || null,
    voiceover_asset_id: packageData.voiceover_asset_id || null }
  const issues = validateVideoDraft(draft, mediaAssets, musicAssets)
  if (issues.length) throw Error(issues.join('; '))
  // Full original package (including camera details and motion prompts) stays
  // independently persisted by Feature2/coordinator, NEVER in an editable browser draft.
  return { draft, approvalId: packageData.approval_id, campaignId: packageData.campaign_id,
    reviewHash: packageData.review_hash, captionCues, readOnly: true }
}
