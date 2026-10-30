// F4-06: UI-only, fail-closed audio mix indicators. HyperFrames is authoritative.
// Browser media metadata is NOT a decoded source-audio probe or a rights grant.
// Never claim an editable DAW gain or preview parity from these indicators.
function authorized(id, shopId, assets) {
  return id != null && Array.isArray(assets) && assets.some(asset =>
    asset?.id === id && asset?.shop_id === shopId &&
    asset?.authorized === true && asset?.kind === 'audio')
}

export function fixedAudioMixDisplay(draft, mediaAssets = [], audioAssets = []) {
  const shopId = draft?.shop_id
  const scenes = Array.isArray(draft?.scenes) ? draft.scenes : []
  const music = authorized(draft?.music_asset_id, shopId, audioAssets)
  const narration = authorized(draft?.voiceover_asset_id, shopId, audioAssets)
  // A verified server ffprobe result is NOT present in the browser draft.
  // If any unmuted video is selected, the renderer may use 0.12 or 0.55
  // depending on whether that actual video has an audio stream.
  const unverifiedVisualMedia = scenes.some(scene =>
    scene?.asset_id != null && (!Array.isArray(mediaAssets) ||
    !mediaAssets.some(asset => asset?.id === scene.asset_id &&
      asset?.shop_id === shopId && asset?.authorized === true &&
      ['image', 'poster', 'video'].includes(asset?.kind))))
  const uncertainSourceAudio = scenes.some(scene =>
    scene?.mute_source !== true && Array.isArray(mediaAssets) &&
    mediaAssets.some(asset => asset?.id === scene?.asset_id &&
      asset?.kind === 'video'))
  const musicGain = !music ? null : unverifiedVisualMedia ? null :
    narration ? 0.12 : uncertainSourceAudio ? null : 0.55
  return {
    music,
    narration,
    musicGain,
    musicGainVerifiedByBrowser: false,
    musicGainUnknownUntilServerProbe: music && musicGain === null && !unverifiedVisualMedia,
    musicGainBlockedByMedia: music && unverifiedVisualMedia,
    narrationGain: narration ? 1 : null,
    sceneSfxGain: 0.25,
    sceneSfxMaximumSeconds: 2,
  }
}
