/** Prevent decoded tenant-owned images reaching another shop on the
 * intervening paint before React effect teardown. Does not grant RLS rights.
 */
export function scopedFeature3Preview(preview, shopId, currentApi = null) {
  if (!preview || preview.scope !== shopId ||
      (currentApi !== null && preview.api !== currentApi) ||
      !Array.isArray(preview.models) || !preview.imageMap ||
      typeof preview.imageMap !== 'object') {
    return {models:[], imageMap:{}, busy:false, message:''}
  }
  return preview
}


/** Release one failed, previously opened private model preview immediately.
 * Successful candidates stay owned by the host's scoped unmount/reload cleanup.
 * No remote URL or signed Storage link is ever eligible for release.
 */
export function discardFailedPrivateModelPreview(opened, url, revokeURL = value => URL.revokeObjectURL(value)) {
  if (!Array.isArray(opened) || typeof url !== 'string' || !url.startsWith('blob:') ||
      typeof revokeURL !== 'function') throw Error('Only local model-preview Blob cleanup allowed')
  const index = opened.indexOf(url)
  if (index < 0) return false
  // Preserve the ownership ledger on revoke failure so caller cleanup can
  // retry without losing the only reference to a private local URL.
  revokeURL(url)
  opened.splice(index, 1)
  return true
}
