// Pure UI-only beat-coordinate preview; server must verify beat grid, music rights,
// shop membership and approved snapshot independently before rendering.
export function proposedBeatMarkers(draft, musicAssets = []) {
  if (!draft || draft.mode !== 'music_sync' ||
      ![15,30,60].includes(draft.duration_seconds) ||
      !Array.isArray(draft.beats) || draft.beats.length < 2 ||
      draft.beats.length > 300 || !Array.isArray(musicAssets) ||
      typeof draft.music_asset_id !== 'string' ||
      !musicAssets.some(a => a?.authorized === true && a.kind === 'audio' &&
        a.id === draft.music_asset_id && a.shop_id === draft.shop_id)) return []
  let previous = -1
  for (const b of draft.beats) {
    if (typeof b !== 'number' || !Number.isFinite(b) ||
        b <= previous || b < 0 || b >= draft.duration_seconds ||
        b !== Math.round(b * 1000) / 1000) return []
    previous = b
  }
  const stride = Math.ceil(draft.beats.length / 120)
  return draft.beats.filter((_, i) => i % stride === 0)
}
