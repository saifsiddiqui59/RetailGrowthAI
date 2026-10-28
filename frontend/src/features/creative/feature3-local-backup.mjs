/** Local backup envelope pinned to an exact signed-in campaign day.
 *
 * No network, storage or cloud save. A trusted host should still reauthorize
 * the campaign, source media and content after importing the draft.
 */
import { feature3ContextKey } from './feature3-context.mjs'
import { validateFeature3Design } from './feature3-design.mjs'

const VERSION = 'retailgrowth.local.poster-draft.v2'

export function encodeFeature3LocalBackup(document, context) {
  const key = feature3ContextKey(context)
  const design = validateFeature3Design(document)
  if (!key || design.shop_id !== context.shopId) {
    throw Error('Valid shop/campaign/day required for local backup')
  }
  return JSON.stringify({
    version: VERSION,
    context_key: key,
    design,
    approved: false,
    cloud_saved: false,
  }, null, 2)
}

export function decodeFeature3LocalBackup(raw, context, authorizedAssetIds=[]) {
  if (typeof raw !== 'string' || raw.length < 1 || raw.length > 25000 ||
      !Array.isArray(authorizedAssetIds) ||
      authorizedAssetIds.some(x => typeof x !== 'string')) {
    throw Error('Invalid local draft backup')
  }
  const contextKey = feature3ContextKey(context)
  if (!contextKey) throw Error('Verified campaign/day required before reopening')
  let envelope
  try { envelope = JSON.parse(raw) } catch {
    throw Error('Invalid draft JSON')
  }
  if (!envelope || typeof envelope !== 'object' || Array.isArray(envelope) ||
      Object.keys(envelope).sort().join(',') !==
        ['approved','cloud_saved','context_key','design','version'].sort().join(',') ||
      envelope.version !== VERSION || envelope.context_key !== contextKey ||
      envelope.approved !== false || envelope.cloud_saved !== false) {
    throw Error('Local draft belongs to a different campaign/day or version')
  }
  const design = validateFeature3Design(envelope.design)
  if (design.shop_id !== context.shopId ||
      design.layers.some(layer => layer.type === 'image' &&
        !authorizedAssetIds.includes(layer.asset_id))) {
    throw Error('Shop/media access changed since draft backup')
  }
  return design
}
