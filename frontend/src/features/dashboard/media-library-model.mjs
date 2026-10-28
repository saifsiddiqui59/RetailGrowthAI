const ALLOWED_TYPES = new Set(['all', 'image/png', 'image/jpeg', 'image/webp'])
const ALLOWED_SOURCES = new Set(['UPLOAD','STOCK','GENERATED'])
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

export function mediaLabel(id) {
  return UUID.test(id || '') ? 'Image ' + id.slice(0, 8) : 'Image record'
}

// Local defence in depth: Supabase enforces RLS; do not render accidental
// cross-shop responses, invalid asset identifiers, or unverifiable rights.
export function filterAssets(rows, shopId, search = '', type = 'all') {
  if (!Array.isArray(rows) || !UUID.test(shopId || '')) return []
  const requestedType = ALLOWED_TYPES.has(type) ? type : 'all'
  const term = String(search || '').trim().slice(0, 80).toLowerCase()
  return rows.filter(row =>
    row && row.shop_id === shopId && UUID.test(row.id || '') &&
    typeof row.license_name === 'string' && row.license_name.trim() &&
    ALLOWED_SOURCES.has(row.source) &&
    ALLOWED_TYPES.has(row.mime_type) && row.mime_type !== 'all' &&
    (requestedType === 'all' || row.mime_type === requestedType) &&
    (!term || (row.id + ' ' + row.license_name + ' ' + row.mime_type).toLowerCase().includes(term)))
}

/**
 * Safe reference adapter for planned STOCK/GENERATED integration.
 * A registered row is NOT proof of third-party licensing or private-byte access.
 * Only the existing self-owned UPLOAD flow may enable on-demand preview.
 */
export function mediaPreviewAccess(asset, shopId) {
  const valid=Boolean(asset && UUID.test(shopId||'') && asset.shop_id===shopId &&
    UUID.test(asset.id||'') && ALLOWED_SOURCES.has(asset.source) &&
    ALLOWED_TYPES.has(asset.mime_type) && asset.mime_type!=='all' &&
    typeof asset.license_name==='string' && Boolean(asset.license_name.trim()))
  if(!valid)return {allowed:false,reason:'unverified'}
  if(asset.source!=='UPLOAD')return {allowed:false,reason:'rights-and-private-access-required'}
  return {allowed:true,reason:'private-upload-only'}
}

/**
 * Paginate only already tenant-validated media records. The backend currently
 * reads at most the newest 100 rows; this MUST NOT claim full library totals.
 * Client-only navigation adds no Supabase requests, exposure of object paths,
 * signed URLs, or extra RLS access.
 */
export function paginateVerifiedAssets(assets, page, size = 12) {
  const rows = Array.isArray(assets) ? assets : []
  const pageSize = Number.isSafeInteger(size) && size > 0 && size <= 24 ? size : 12
  const count = rows.length
  const pages = Math.max(1, Math.ceil(count / pageSize))
  const requested = Number.isSafeInteger(page) ? page : 1
  const current = Math.min(Math.max(requested, 1), pages)
  const start = (current - 1) * pageSize
  return { page: current, pages, total: count, first: count ? start+1 : 0,
    last: Math.min(start+pageSize, count), items: rows.slice(start,start+pageSize) }
}
