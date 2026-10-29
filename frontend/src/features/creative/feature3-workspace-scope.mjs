/** Browser presentation fences for authenticated, day-scoped Feature3 drafts.
 * These guards never grant shop access. Current JWT/RLS and image rights are
 * checked independently by the existing backend before any durable write.
 */
export function scopedFeature3WorkspaceValue(state, scope, fallback, provider = undefined) {
  if (typeof scope !== 'string' || !scope ||
      !state || typeof state !== 'object' || Array.isArray(state) ||
      state.scope !== scope || (provider !== undefined && state.provider !== provider) ||
      !Object.hasOwn(state, 'value')) return fallback
  return state.value
}

export function currentFeature3WorkspaceRequest(active, scope, api, nonce, currentNonce) {
  return Boolean(scope && api && active &&
    active.scopeKey === scope && active.feature3Api === api &&
    Number.isSafeInteger(nonce) && nonce > 0 && nonce === currentNonce)
}
