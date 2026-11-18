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

/**
 * Synchronous, component-local single-flight gate for private Feature3 GETs.
 * React busy state may not commit before the next click. This gate is only
 * a concurrency guard; server JWT, RLS and current asset rights remain the
 * authority. No request is retried or cancelled at the network layer.
 */
export function createFeature3WorkspaceReadGate() {
  const allowed = new Set(['drafts', 'generated-jobs', 'download'])
  let active = null
  return Object.freeze({
    begin(scope, provider, kind) {
      if (active || typeof scope !== 'string' || !scope || !provider ||
          !allowed.has(kind)) return null
      const ticket = Object.freeze({scope, provider, kind})
      active = ticket
      return ticket
    },
    isCurrent(ticket, scope, provider) {
      return Boolean(ticket && active === ticket &&
        ticket.scope === scope && ticket.provider === provider)
    },
    release(ticket) {
      if (ticket === null || active !== ticket) return false
      active = null
      return true
    },
    cancel() {
      active = null
    },
    busy() {
      return active !== null
    },
  })
}

/**
 * Presentation-only check: an inherited JS prototype property is never an
 * approved private image for restoring or saving a tenant-scoped draft.
 * The backend still independently verifies JWT/RLS and current media grants.
 */
export function feature3DraftMediaReady(design, imageMap) {
  if (!design || !Array.isArray(design.layers)) return false
  return design.layers.every(layer => {
    if (!layer || typeof layer !== 'object') return false
    if (layer.type !== 'image') return true
    if (typeof layer.asset_id !== 'string' || !imageMap ||
        typeof imageMap !== 'object' || Array.isArray(imageMap) ||
        !Object.hasOwn(imageMap, layer.asset_id)) return false
    const image = imageMap[layer.asset_id]
    return Boolean(image && image.complete === true &&
      Number.isFinite(image.naturalWidth) && image.naturalWidth > 0 &&
      Number.isFinite(image.naturalHeight) && image.naturalHeight > 0)
  })
}
