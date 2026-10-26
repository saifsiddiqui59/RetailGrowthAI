import { useCallback, useEffect, useState } from 'react'
import { authorizedShopId, readShopPreference, saveShopPreference } from './tenant-shop-selection.mjs'

// Shared, per-principal browser-session workspace choice. Never pass an
// arbitrary value from storage to PostgREST: resolution requires an active,
// RLS-verified membership provided by useAuthorizedShops.
export function useSelectedShop({ user, shops }) {
  const userId = user?.id || ''
  const [preferred, setPreferred] = useState(() =>
    readShopPreference(userId, globalThis.sessionStorage))
  useEffect(() => {
    setPreferred(readShopPreference(userId, globalThis.sessionStorage))
  }, [userId])
  const shopId = authorizedShopId(shops, preferred)
  const selectShop = useCallback((id) => {
    if (!saveShopPreference(userId, shops, id, globalThis.sessionStorage)) return false
    setPreferred(id)
    return true
  }, [userId, shops])
  return { shopId, selectShop }
}
