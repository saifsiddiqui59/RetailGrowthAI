/** Source-only Feature3 generated PNG binary client (NO public route mounted).
 *
 * The future coordinator-approved HTTPS endpoint must return private bytes
 * from Feature3RevocablePNGReader with fresh user-JWT tenant+source rights
 * and the exact Feature3PrivateBinaryHTTP integrity headers. Never use an
 * expiring signed Storage URL or infer image approval from a successful GET.
 */
const ID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
const SHA = /^[a-f0-9]{64}$/
const MAX = 25 * 1024 * 1024
const PNG_MAGIC = [137,80,78,71,13,10,26,10]

export function createFeature3PrivatePNGClient({baseUrl,tokenProvider,fetchImpl=fetch}) {
  const origin = new URL(baseUrl)
  if (origin.protocol !== 'https:' || !origin.hostname ||
      origin.username || origin.password || origin.search || origin.hash ||
      !['','/'].includes(origin.pathname)) {
    throw Error('Private output API requires exact HTTPS application origin')
  }
  if (typeof tokenProvider !== 'function' || typeof fetchImpl !== 'function') {
    throw Error('Signed retailer JWT and bounded binary fetch required')
  }
  return Object.freeze({
    async get(shopId,jobId) {
      if (!ID.test(shopId) || !ID.test(jobId)) throw Error('Invalid private generated job')
      const token = await tokenProvider()
      if (typeof token !== 'string' || token.length < 12 || token.length > 8192 ||
          /[\s\x00-\x1f\x7f]/.test(token) ||
          token.startsWith('sb_secret_') || token.startsWith('sb_publishable_')) {
        throw Error('Please sign in again')
      }
      const url = origin.origin+'/api/shops/'+shopId+
        '/feature3-gpu-jobs/'+jobId+'/private-png'
      // One GET. Do not replay an uncertain response or issue signed links.
      const response = await fetchImpl(url,{
        method:'GET',cache:'no-store',redirect:'error',
        credentials:'omit',referrerPolicy:'no-referrer',
        headers:{Authorization:'Bearer '+token,Accept:'image/png'},
      })
      if (!response || response.ok!==true || response.status!==200 ||
          response.redirected===true ||
          (typeof response.url === 'string' && response.url && response.url!==url)) {
        throw Error('Private generated-image download denied or unavailable')
      }
      const headers = response.headers
      if (!headers || typeof headers.get !== 'function') {
        throw Error('Private output integrity headers unavailable')
      }
      const length=headers.get('content-length')
      const media=headers.get('x-feature3-media-asset-id')
      const digest=headers.get('x-feature3-image-sha256')
      const mime=headers.get('content-type')
      const cache=headers.get('cache-control')
      if (headers.get('x-feature3-shop-id')!==shopId ||
          headers.get('x-feature3-job-id')!==jobId ||
          !ID.test(media||'') || !SHA.test(digest||'') ||
          typeof length!=='string' || !/^[0-9]+$/.test(length) ||
          Number(length)<100 || Number(length)>MAX ||
          mime!=='image/png' || typeof cache!=='string' ||
          !/(?:^|,)\s*no-store(?:\s*,|$)/i.test(cache) ||
          headers.get('x-content-type-options')!=='nosniff' ||
          headers.get('location') !== null) {
        throw Error('Untrusted private generated-image receipt')
      }
      const array = await response.arrayBuffer()
      if (!(array instanceof ArrayBuffer) || array.byteLength!==Number(length) ||
          array.byteLength>MAX) {
        throw Error('Private image bytes changed in transit')
      }
      const binary = new Uint8Array(array)
      if (!PNG_MAGIC.every((value,index)=>binary[index]===value)) {
        throw Error('Invalid generated PNG signature')
      }
      if (!globalThis.crypto?.subtle?.digest) {
        throw Error('Private image SHA verification unavailable')
      }
      const hashed = await globalThis.crypto.subtle.digest('SHA-256',array)
      const computed = Array.from(new Uint8Array(hashed),byte=>
        byte.toString(16).padStart(2,'0')).join('')
      if (computed!==digest) throw Error('Generated image SHA mismatch')
      return Object.freeze({
        shopId,jobId,mediaAssetId:media,imageSha256:digest,
        blob:new Blob([array],{type:'image/png'}),
        private:true,publishApproved:false,approvedModel:false,
      })
    },
  })
}
