/** Render-time tenant/expiry fence for already issued short-lived private PNG URLs.
 * Client controls cannot invalidate an already copied Storage token; the
 * server's JWT/RLS checks and 60-second expiry remain the authoritative gates.
 */
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
export const SAFE_CLIENT_LIFETIME_MS=55_000

export function scopedFeature3GeneratedLink(value,shopId,now=Date.now(),requestKey=null) {
  if (!value || typeof value!=='object' || Array.isArray(value) ||
      !UUID.test(shopId||'') || value.scope!==shopId ||
      (requestKey!==null && value.requestKey!==requestKey) ||
      !UUID.test(value.jobId||'') || !UUID.test(value.mediaAssetId||'') ||
      typeof value.url!=='string' || value.expiresInSeconds!==60 ||
      value.approvedModel!==false || !Number.isSafeInteger(value.createdAt) ||
      !Number.isFinite(now) || now<value.createdAt ||
      now-value.createdAt>=SAFE_CLIENT_LIFETIME_MS) return null
  return value
}
