/** Authenticated-host model catalog adapter. Source-only UI contract.
 * A catalog row is NEVER authorization. Existing private imageMap is the
 * only source of raster pixels for the browser; server must independently
 * reload current RLS, license, approval and asset rights at final rendering.
 * Intentionally no fetch, URL, Blob keys, API tokens or browser-side approval.
 */
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
const IMAGE_ID = /^[a-zA-Z0-9_-]{1,100}$/
const SHA = /^[a-f0-9]{64}$/
const USES = new Set(['poster', 'try_on', 'video_reference'])
const LICENSES = new Set(['CC0-1.0', 'CC-BY-4.0', 'REVIEWED-COMMERCIAL'])

export const APPROVED_MODEL_SCHEMA = 'retailgrowth.model-library.v1'

export function availableApprovedModels(rows, shopId, imageMap = {}, usage = 'poster') {
  if (!Array.isArray(rows) || !UUID.test(shopId) || !USES.has(usage) ||
      !imageMap || typeof imageMap !== 'object' || Array.isArray(imageMap)) return []
  const result = [], seen = new Set()
  for (const row of rows.slice(0, 500)) {
    if (!row || typeof row !== 'object' || Array.isArray(row) ||
        row.schema !== APPROVED_MODEL_SCHEMA || row.status !== 'APPROVED' ||
        row.synthetic_adult !== true || !UUID.test(row.model_id) ||
        !UUID.test(row.owner_shop_id) || !SHA.test(row.image_sha256) ||
        (row.scope !== 'shop' && row.scope !== 'platform') ||
        (row.scope === 'shop' && row.owner_shop_id !== shopId) ||
        !LICENSES.has(row.license_id) ||
        !Array.isArray(row.approved_uses) ||
        row.approved_uses.length < 1 || row.approved_uses.length > USES.size ||
        row.approved_uses.some(value => typeof value !== 'string' || !USES.has(value)) ||
        new Set(row.approved_uses).size !== row.approved_uses.length ||
        !row.approved_uses.includes(usage) ||
        typeof row.label !== 'string' || row.label.trim().length < 1 ||
        row.label.length > 64 || !IMAGE_ID.test(row.media_asset_id) ||
        seen.has(row.model_id)) continue
    if (row.license_id === 'CC-BY-4.0' &&
        (typeof row.attribution !== 'string' || !row.attribution.trim())) continue
    // Only host-supplied authenticated, already-decoded private media allowed.
    const image = Object.prototype.hasOwnProperty.call(imageMap, row.media_asset_id)
      ? imageMap[row.media_asset_id] : null
    if (!image?.complete || !(image.naturalWidth > 0) ||
        !(image.naturalHeight > 0)) continue
    seen.add(row.model_id)
    result.push(Object.freeze({
      modelId: row.model_id, mediaAssetId: row.media_asset_id,
      label: row.label.trim(), scope: row.scope,
      attribution: typeof row.attribution === 'string' ? row.attribution : '',
      imageSha256: row.image_sha256,
    }))
  }
  return Object.freeze(result)
}

/** No approval flag or private path is exported in the client-side selection. */
export function selectedApprovedModel(models, id) {
  return Array.isArray(models) ? models.find(m => m.modelId === id) || null : null
}
