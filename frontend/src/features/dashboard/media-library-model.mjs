const ALLOWED_TYPES = new Set(['all', 'image/png', 'image/jpeg', 'image/webp'])
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
    typeof row.mime_type === 'string' &&
    (requestedType === 'all' || row.mime_type === requestedType) &&
    (!term || (row.id + ' ' + row.license_name + ' ' + row.mime_type).toLowerCase().includes(term)))
}
