// A UI preference, not an authorization token. Always intersect the stored
// choice with the latest listShops() result, which is protected by Supabase RLS.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const ALLOWED_ROLES = new Set(['OWNER', 'EDITOR', 'VIEWER'])
const PREFIX = 'retailgrowthai-selected-business:'

export function selectionKey(userId) {
  return UUID.test(userId || '') ? PREFIX + userId : ''
}

export function readShopPreference(userId, storage) {
  const key = selectionKey(userId)
  if (!key) return ''
  try {
    const id = storage?.getItem(key)
    return UUID.test(id || '') ? id : ''
  } catch {
    // Private browsing policies can deny browser storage access.
    return ''
  }
}

export function authorizedShopId(shops, preferredId = '') {
  if (!Array.isArray(shops)) return ''
  const accessible = shops.filter(shop => shop && UUID.test(shop.id || '') &&
    shop.membership?.active === true && ALLOWED_ROLES.has(shop.membership?.role))
  return accessible.find(shop => shop.id === preferredId)?.id || accessible[0]?.id || ''
}

export function saveShopPreference(userId, shops, nextId, storage) {
  const key = selectionKey(userId)
  // An invalid or removed tenant must never be written or used for an API read.
  if (!key || !UUID.test(nextId || '') || authorizedShopId(shops, nextId) !== nextId) {
    return false
  }
  try { storage?.setItem(key, nextId) } catch { /* preference is optional */ }
  return true
}
