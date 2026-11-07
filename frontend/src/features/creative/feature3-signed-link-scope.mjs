/** Render-time tenant/expiry fence for already issued short-lived private PNG URLs.
 * Client controls cannot invalidate an already copied Storage token; the
 * server's JWT/RLS checks and 60-second expiry remain the authoritative gates.
 */
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
export const SAFE_CLIENT_LIFETIME_MS=55_000
const PNG_FILE=/^[a-f0-9]{64}\.png$/

/** Defense-in-depth at the last render boundary, after the API adapter's
 * authoritative exact configured Storage-origin check. Never allow an
 * injected URL, foreign shop/job path, or extra query parameter into an href.
 * This does not revoke previously issued signed URLs.
 */
function scopedSignedPNGUrl(raw,shopId,jobId) {
  if(typeof raw!=='string'||raw.length>8192)return false
  let url
  try { url=new URL(raw) } catch { return false }
  const prefix='/storage/v1/object/sign/retailgrowth-media/'+shopId+
    '/feature3/gpu/'+jobId+'/'
  const token=url.searchParams.get('token')
  return url.protocol==='https:' &&
    url.hostname.endsWith('.supabase.co') &&
    url.hostname.length>'.supabase.co'.length &&
    !url.username && !url.password && !url.port && !url.hash &&
    url.pathname.startsWith(prefix) &&
    PNG_FILE.test(url.pathname.slice(prefix.length)) &&
    [...url.searchParams.keys()].length===1 &&
    typeof token==='string' && token.length>0 && token.length<=4096 &&
    !/[\x00-\x1f\x7f]/.test(token)
}

export function scopedFeature3GeneratedLink(value,shopId,now=Date.now(),requestKey=null) {
  if (!value || typeof value!=='object' || Array.isArray(value) ||
      !UUID.test(shopId||'') || value.scope!==shopId ||
      (requestKey!==null && value.requestKey!==requestKey) ||
      !UUID.test(value.jobId||'') || !UUID.test(value.mediaAssetId||'') ||
      !scopedSignedPNGUrl(value.url,shopId,value.jobId) ||
      value.expiresInSeconds!==60 ||
      value.approvedModel!==false || !Number.isSafeInteger(value.createdAt) ||
      !Number.isFinite(now) || now<value.createdAt ||
      now-value.createdAt>=SAFE_CLIENT_LIFETIME_MS) return null
  return value
}
