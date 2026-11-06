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


/** Per-browser-session model preview URL ledger.
 * Revoke failures keep exact URL ownership for later retries without allowing
 * those pixels to remain in an authorized React presentation state.
 * Never caches media bytes, JWTs, signed links or external image origins.
 */
export function createFeature3PrivateModelUrlLedger(
  revokeURL = url => URL.revokeObjectURL(url)
) {
  if (typeof revokeURL !== 'function') throw Error('Private URL cleanup required')
  const owned = new Set()
  const valid = value => typeof value === 'string' &&
    value.startsWith('blob:') && value.length < 4096 &&
    !/[\s\x00-\x1f\x7f]/.test(value)
  const releaseOne = url => {
    if(!owned.has(url))return false
    revokeURL(url)
    owned.delete(url)
    return true
  }
  const releaseMany = urls => {
    if(!Array.isArray(urls))throw Error('Owned private URL list required')
    let failed=false
    for(const url of new Set(urls)) {
      if(!owned.has(url))continue
      try {releaseOne(url)} catch {failed=true}
    }
    if(failed)throw Error('Private model preview cleanup pending')
    return owned.size
  }
  return Object.freeze({
    track(url) {
      if(!valid(url) || owned.has(url))throw Error('Only new local private Blob URLs allowed')
      owned.add(url)
      return url
    },
    release:releaseOne,
    releaseMany,
    releaseAll() {return releaseMany([...owned])},
    pendingCount() {return owned.size},
    owns(url) {return owned.has(url)},
  })
}
