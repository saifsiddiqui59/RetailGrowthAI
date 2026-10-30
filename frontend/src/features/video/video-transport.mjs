// Feature #4 authenticated browser-to-backend transport. Additive, DEFAULT OFF.
// The coordinator supplies versioned v2 route builders only after registering
// authorized Azure HTTP routes and service-only claim/ledger methods.
// Never call the existing v1 /campaigns/:id/renders endpoint with a v2 draft.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const FINISHED = new Set(['SUCCEEDED', 'FAILED'])
const STATES = new Set(['QUEUED', 'RUNNING', ...FINISHED])
const PATH = /^\/(?:[a-zA-Z0-9_-]+\/)*[a-zA-Z0-9_-]+$/

export function canonicalVideoId(value) {
  if (typeof value !== 'string' || !UUID.test(value) || value.toLowerCase() !== value) {
    throw Error('Expected a canonical resource ID')
  }
  return value
}

export function trustedVideoPath(path) {
  if (typeof path !== 'string' || !PATH.test(path) || path.includes('..') ||
      path.startsWith('//') || path.startsWith('/api/')) {
    throw Error('Invalid versioned video API path')
  }
  return '/api' + path
}

export function privateVideoUrl(value, supabaseOrigin, shopId, jobId) {
  const shop = canonicalVideoId(shopId)
  const job = canonicalVideoId(jobId)
  if (typeof value !== 'string' || !value || !supabaseOrigin) {
    throw Error('Private video download was not returned')
  }
  let url, trusted
  try {
    url = new URL(value)
    trusted = new URL(supabaseOrigin)
  } catch { throw Error('Invalid private video URL') }
  if (url.origin !== trusted.origin || url.protocol !== 'https:' || url.username ||
      url.password || url.hash || !url.searchParams.get('token') ||
      trusted.protocol !== 'https:' || trusted.username || trusted.password) {
    throw Error('Unsigned or untrusted video URL')
  }
  // The v2 private worker stores tenant/job/lease.mp4 in the existing bucket.
  // Ignore neither the shop nor job ID: a valid token for some other tenant
  // is not a valid result for the active editor.
  const prefix = '/storage/v1/object/sign/retailgrowth-media/'
  if (!url.pathname.startsWith(prefix)) throw Error('Not a signed private media object')
  let objectKey
  try { objectKey = decodeURIComponent(url.pathname.slice(prefix.length)) }
  catch { throw Error('Malformed signed media path') }
  if (!new RegExp('^' + shop + '/renders/' + job + '/[0-9a-f-]{36}\\.mp4$').test(objectKey) ||
      objectKey.includes('//') || objectKey.includes('..')) {
    throw Error('Signed video does not belong to the selected render job')
  }
  return url.toString()
}

export function privateMediaPreviewUrl(value, supabaseOrigin, shopId) {
  const shop = canonicalVideoId(shopId)
  if (typeof value !== 'string' || typeof supabaseOrigin !== 'string') {
    throw Error('Private source preview is unavailable')
  }
  let url, trusted
  try {
    url = new URL(value)
    trusted = new URL(supabaseOrigin)
  } catch { throw Error('Private source preview URL invalid') }
  if (url.protocol !== 'https:' || trusted.protocol !== 'https:' ||
      url.origin !== trusted.origin || url.username || url.password ||
      url.hash || !url.searchParams.get('token')) {
    throw Error('Source preview must have a tenant-private signed URL')
  }
  const prefix = '/storage/v1/object/sign/retailgrowth-media/'
  if (!url.pathname.startsWith(prefix)) throw Error('Source preview is not private Storage media')
  let path
  try { path = decodeURIComponent(url.pathname.slice(prefix.length)) }
  catch { throw Error('Malformed private preview path') }
  const parts = path.split('/')
  if (parts[0] !== shop || parts.length < 3 ||
      parts.some(part => !part || part === '.' || part === '..') ||
      path.includes('\\') || path.includes('%') ||
      !/^[a-zA-Z0-9._/-]+$/.test(path)) {
    throw Error('Source preview belongs to another shop or unsafe path')
  }
  return url.toString()
}

export function parseVideoJob(data, shopId, expectedId = null) {
  const shop = canonicalVideoId(shopId)
  if (data === null || typeof data !== 'object' || Array.isArray(data) ||
      data.shop_id !== shop || !STATES.has(data.status)) {
    throw Error('Video job response failed tenant/status verification')
  }
  const id = canonicalVideoId(data.job_id)
  if (expectedId && id !== canonicalVideoId(expectedId)) {
    throw Error('Video job response did not match the requested job')
  }
  return { job_id: id, shop_id: shop, status: data.status,
    error_code: typeof data.error_code === 'string' ? data.error_code.slice(0, 70) : null }
}

export function createVideoTransport({ enabled = false, baseUrl, tokenProvider, fetchImpl = fetch,
  routes, supabaseOrigin, timeoutMs = 12000 }) {
  if (enabled !== true) return null
  if (typeof tokenProvider !== 'function' || typeof fetchImpl !== 'function' ||
      !routes || typeof routes.create !== 'function' ||
      typeof routes.status !== 'function' || typeof routes.download !== 'function') {
    throw Error('Versioned, coordinator-approved video routes and auth are required')
  }
  if (!Number.isInteger(timeoutMs) || timeoutMs < 500 || timeoutMs > 30000) {
    throw Error('Invalid video GET timeout')
  }
  let origin
  try {
    const u = new URL(baseUrl)
    if (u.protocol !== 'https:' || u.username || u.password || u.pathname !== '/' ||
        u.search || u.hash) throw Error()
    origin = u.origin
  } catch { throw Error('Video backend must be a bare HTTPS origin') }

  async function request(method, path, payload, signal) {
    const token = await tokenProvider()
    if (typeof token !== 'string' || token.length < 10 || /[\s\r\n]/.test(token)) {
      throw Error('Sign in to your business before using Video Studio')
    }
    const endpoint = origin + trustedVideoPath(path)
    // Mutating POST is intentionally NEVER timed out and NEVER retried here:
    // Azure may have committed it without returning the acknowledgement.
    // GET can be retried manually by polling; no automatic cross-tenant fallback.
    const controller = method === 'GET' ? new AbortController() : null
    const timer = controller ? setTimeout(() => controller.abort(), timeoutMs) : null
    function abortParent() { controller?.abort() }
    if (signal?.aborted) throw Error('Video request cancelled')
    if (signal && controller) signal.addEventListener('abort', abortParent, { once: true })
    try {
      const response = await fetchImpl(endpoint, {
        method, redirect: 'error', cache: 'no-store',
        headers: { Authorization: 'Bearer ' + token,
          ...(payload === undefined ? {} : { 'Content-Type': 'application/json' }) },
        ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
        ...(controller ? { signal: controller.signal } : {}),
      })
      if (!response || typeof response.ok !== 'boolean') throw Error('Invalid video service response')
      const data = await response.json().catch(() => null)
      if (!response.ok) {
        const err = new Error(response.status === 401 ? 'Your session expired. Sign in again.' :
          response.status === 403 || response.status === 404 ? 'This video is not available to your business.' :
          response.status === 402 || response.status === 429 ? 'Video plan or usage quota does not allow this job.' :
          response.status === 503 ? 'Video service unavailable. Check job status before resubmitting.' :
          'Video request failed. Check job status before resubmitting.')
        err.status = response.status
        throw err
      }
      return { data, status: response.status }
    } finally {
      if (timer !== null) clearTimeout(timer)
      if (signal && controller) signal.removeEventListener('abort', abortParent)
    }
  }

  return Object.freeze({
    async create({ shopId, campaignId, draft, approvalId }) {
      const shop = canonicalVideoId(shopId)
      const campaign = canonicalVideoId(campaignId)
      if (!draft || typeof draft !== 'object' || draft.shop_id !== shop ||
          draft.version !== 'rg_video_v2' || typeof approvalId !== 'string' ||
          !/^[a-zA-Z0-9_-]{1,100}$/.test(approvalId)) {
        throw Error('Authenticated, reviewed video draft is required')
      }
      // This is an intent to create. The backend MUST reconstruct the
      // approved creative_reel_v1 request from saved DB media/script/revision.
      const out = await request('POST', routes.create(campaign),
        { shop_id: shop, campaign_id: campaign, approval_id: approvalId, draft })
      if (out.status !== 202 && out.status !== 200) {
        throw Error('Render job was not acknowledged')
      }
      return parseVideoJob(out.data, shop)
    },
    async status({ jobId, shopId, signal }) {
      const job = canonicalVideoId(jobId)
      const out = await request('GET', routes.status(job), undefined, signal)
      return parseVideoJob(out.data, shopId, job)
    },
    async download({ jobId, shopId, signal }) {
      const job = canonicalVideoId(jobId)
      const out = await request('GET', routes.download(job), undefined, signal)
      if (out.data?.job_id !== job || out.data?.shop_id !== canonicalVideoId(shopId)) {
        throw Error('Download receipt did not match active business and job')
      }
      return privateVideoUrl(out.data?.url, supabaseOrigin, shopId, job)
    },
  })
}
