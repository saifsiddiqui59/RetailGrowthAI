/** Prevent decoded tenant-owned images reaching another shop on the
 * intervening paint before React effect teardown. Does not grant RLS rights.
 */
export function scopedFeature3Preview(preview, shopId) {
  if (!preview || preview.scope !== shopId ||
      !Array.isArray(preview.models) || !preview.imageMap ||
      typeof preview.imageMap !== 'object') {
    return {models:[], imageMap:{}, busy:false, message:''}
  }
  return preview
}
