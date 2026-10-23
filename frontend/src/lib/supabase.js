// RetailGrowthAI-only lightweight Supabase Auth v1 + PostgREST client.
// No service-role keys, no client-side authorization assumptions.
// Use a publishable key and let PostgreSQL RLS enforce every tenant boundary.
const STORAGE_KEY = 'retailgrowthai-auth-v1'
const ALLOWED_TABLES = new Set(['shops', 'shop_memberships', 'business_profiles', 'media_assets', 'shop_subscriptions'])

const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const IMAGE_TYPES = { 'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp' }
const LICENSES = new Set(['owned', 'cc0', 'royalty_free', 'commercial'])

async function verifyImageBytes(file) {
  if (!file || typeof file.slice !== 'function' || !IMAGE_TYPES[file.type] ||
      !Number.isSafeInteger(file.size) || file.size < 100 || file.size > 25 * 1024 * 1024) {
    throw new Error('Choose a PNG, JPEG or WebP image between 100 bytes and 25 MB.')
  }
  const signature = new Uint8Array(await file.slice(0, 12).arrayBuffer())
  const check = file.type === 'image/png'
    ? [137,80,78,71,13,10,26,10].every((b,i) => signature[i] === b)
    : file.type === 'image/jpeg'
      ? [255,216,255].every((b,i) => signature[i] === b)
      : [82,73,70,70].every((b,i) => signature[i] === b) &&
        [87,69,66,80].every((b,i) => signature[i+8] === b)
  if (!check) throw new Error('Image bytes do not match the declared MIME type.')
}


export function createRetailClient({
  url = import.meta.env?.VITE_SUPABASE_URL,
  key = import.meta.env?.VITE_SUPABASE_PUBLISHABLE_KEY,
  storage = typeof window === 'undefined' ? null : window.sessionStorage,
  fetchImpl = (...args) => fetch(...args),
  clock = () => Date.now(),
  uuidFactory = () => crypto.randomUUID(),
} = {}) {
  const configured = Boolean(url && key && /^https:\/\//.test(url))
  const origin = configured ? url.replace(/\/+$/, '') : ''
  let session = null
  try {
    session = JSON.parse(storage?.getItem(STORAGE_KEY) || 'null')
  } catch { storage?.removeItem(STORAGE_KEY) }
  let refreshing = null

  function ensureConfigured() {
    if (!configured) throw new Error('RetailGrowthAI Supabase URL and publishable key are not configured')
  }
  function setSession(value) {
    session = value?.access_token && value?.refresh_token
      ? {
          access_token: value.access_token,
          refresh_token: value.refresh_token,
          expires_at: value.expires_at || Math.floor(clock() / 1000) + (value.expires_in || 3600),
        }
      : null
    if (session) storage?.setItem(STORAGE_KEY, JSON.stringify(session))
    else storage?.removeItem(STORAGE_KEY)
  }
  async function send(path, { method = 'GET', body, token, query, headers = {} } = {}) {
    ensureConfigured()
    const target = new URL(origin + path)
    if (query) for (const [name, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) target.searchParams.set(name, String(value))
    }
    const response = await fetchImpl(target.toString(), {
      method,
      headers: {
        apikey: key,
        ...(token ? { Authorization: 'Bearer ' + token } : {}),
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...headers,
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
    const result = response.status === 204 ? null : await response.json().catch(() => null)
    if (!response.ok) {
      const message = result?.msg || result?.error_description || result?.message || result?.error || 'Supabase request failed'
      const error = new Error(message)
      error.status = response.status
      throw error
    }
    return result
  }
  function requireSession() {
    if (!session?.access_token) throw new Error('Sign in before accessing shop data')
    return session
  }
  async function refresh() {
    requireSession()
    if (!refreshing) {
      const oldToken = session.refresh_token
      refreshing = send('/auth/v1/token', {
        method: 'POST', query: { grant_type: 'refresh_token' }, body: { refresh_token: oldToken },
      }).then((data) => {
        // An in-flight refresh must not restore a deliberately cleared session.
        if (session?.refresh_token !== oldToken) throw new Error('Session changed')
        setSession(data)
        return session.access_token
      }).catch((error) => {
        if (session?.refresh_token === oldToken) setSession(null)
        throw error
      }).finally(() => { refreshing = null })
    }
    return refreshing
  }
  async function accessToken() {
    const current = requireSession()
    if (current.expires_at * 1000 - clock() <= 60_000) return refresh()
    return current.access_token
  }
  async function authRequest(path, opts = {}) {
    return send('/auth/v1/' + path, opts)
  }
  async function signIn(email, password) {
    const data = await authRequest('token', {
      method: 'POST', query: { grant_type: 'password' }, body: { email, password },
    })
    setSession(data)
    if (!session) throw new Error('Sign-in did not return a valid session')
    return data.user
  }
  async function signUp(email, password) {
    // Do not fall back to Supabase's project Site URL (often localhost:3000)
    // when a retailer signs up from the deployed single-login website.
    // This destination must also be allowlisted in Auth > URL Configuration.
    const redirectTo = typeof window === 'undefined' ? undefined
      : new URL('/account', window.location.origin).toString()
    const data = await authRequest('signup', {
      method: 'POST', body: { email, password },
      ...(redirectTo ? { query: { redirect_to: redirectTo } } : {}),
    })
    if (data?.access_token) setSession(data)
    return data
  }
  async function getUser() {
    return authRequest('user', { token: await accessToken() })
  }
  async function signOut() {
    const token = session?.access_token
    // Local session is always destroyed even if network revocation fails.
    setSession(null)
    if (token) {
      try { await authRequest('logout', { method: 'POST', token }) }
      catch { /* Access token will expire; never rehydrate the local session. */ }
    }
  }
  async function table(name, { method = 'GET', query = {}, body, returnMinimal = false } = {}) {
    if (!ALLOWED_TABLES.has(name)) throw new Error('Table is not exposed by RetailGrowthAI foundation client')
    return send('/rest/v1/' + name, {
      method, query, body, token: await accessToken(),
      headers: method === 'POST' ? { Prefer: returnMinimal ? 'return=minimal' : 'return=representation' }
        : method === 'PATCH' ? { Prefer: 'return=representation' } : {},
    })
  }
  async function listShops() {
    // Membership and shop lists are separately enforced by RLS, never by a supplied user_id.
    const memberships = await table('shop_memberships', {
      query: { select: 'shop_id,role,active', active: 'eq.true' },
    })
    const shops = await table('shops', { query: { select: 'id,name,slug,timezone,owner_user_id' } })
    return shops.map((shop) => ({ ...shop, membership: memberships.find((m) => m.shop_id === shop.id) || null }))
      .filter((shop) => shop.membership?.active)
  }
  async function createShop({ name, slug, timezone = 'Asia/Kolkata' }) {
    if (!name?.trim() || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug || '')) {
      throw new Error('Enter a business name and a lowercase hyphenated shop slug')
    }
    const user = await getUser()
    const id = uuidFactory()
    if (!UUID_V4.test(id)) throw new Error('Unable to generate a valid business ID')
    // The OWNER membership is created by an AFTER INSERT trigger. Returning
    // the new row in this same INSERT would require an RLS SELECT before the
    // membership exists, causing SQLSTATE 42501. Insert with minimal output,
    // then read through the now-established membership as normal.
    await table('shops', {
      method: 'POST', body: { id, owner_user_id: user.id, name: name.trim(), slug, timezone },
      returnMinimal: true,
    })
    const rows = await table('shops', {
      query: { select: 'id,name,slug,timezone', id: 'eq.' + id, limit: '1' },
    })
    if (!Array.isArray(rows) || rows.length !== 1 || rows[0].id !== id) {
      throw new Error('Business created but access verification is pending. Refresh Account before retrying.')
    }
    return rows[0]
  }
  async function getShopSubscription(shopId) {
    if (!UUID_V4.test(shopId || '')) throw new Error('Invalid selected business')
    const rows = await table('shop_subscriptions', {
      query: {
        select: 'shop_id,plan_code,status,valid_from,valid_until,period_start,period_end',
        shop_id: 'eq.' + shopId, limit: '1',
      },
    })
    if (!Array.isArray(rows) || rows.length > 1 ||
        (rows.length === 1 && rows[0].shop_id !== shopId)) {
      throw new Error('Subscription information is temporarily unavailable')
    }
    return rows[0] || null
  }
  // HEAD + count=exact asks PostgREST to count RLS-visible rows only.
  // No service key or client-side cross-tenant total is ever supplied.
  async function countShopRows(name, shopId, additional = {}) {
    if (!['campaigns', 'render_jobs', 'shop_usage_reservations'].includes(name) ||
        !UUID_V4.test(shopId || '')) {
      throw new Error('Invalid shop metrics query')
    }
    const params = new URLSearchParams({
      select: 'id', shop_id: 'eq.' + shopId, ...additional,
    })
    // shop_id remains authoritative even if extra filters were supplied.
    params.set('shop_id', 'eq.' + shopId)
    // shop_usage_reservations does not have an id column.
    if (name === 'shop_usage_reservations') params.set('select', 'job_id')
    const response = await fetchImpl(origin + '/rest/v1/' + name + '?' + params, {
      method: 'HEAD',
      headers: { apikey: key, Authorization: 'Bearer ' + await accessToken(),
        Prefer: 'count=exact' },
    })
    if (!response.ok) throw new Error('Your live business metrics are unavailable.')
    const range = response.headers.get('content-range')
    const parsed = /^(\d+)-(\d+)\/(\d+)$/.exec(range || '') ||
      /^\*\/(\d+)$/.exec(range || '')
    const count = parsed && Number(parsed[parsed.length - 1])
    if (!Number.isSafeInteger(count) || count < 0) {
      throw new Error('Verified count was not returned by Supabase.')
    }
    return count
  }
  async function getShopMetrics(shopId) {
    if (!UUID_V4.test(shopId || '')) throw new Error('Invalid business')
    const [campaigns, drafts, reelsReady, rendersProcessing] = await Promise.all([
      countShopRows('campaigns', shopId),
      countShopRows('campaigns', shopId, { status: 'eq.DRAFT' }),
      countShopRows('render_jobs', shopId, { status: 'eq.SUCCEEDED' }),
      countShopRows('render_jobs', shopId, { status: 'in.(QUEUED,RUNNING)' }),
    ])
    return { campaigns, drafts, reelsReady, rendersProcessing }
  }
  async function getShopUsage(shopId, periodStart) {
    if (!UUID_V4.test(shopId || '') || typeof periodStart !== 'string' ||
        !Number.isFinite(Date.parse(periodStart))) {
      throw new Error('Invalid subscription usage scope')
    }
    const [campaign, render] = await Promise.all([
      countShopRows('shop_usage_reservations', shopId, {
        operation: 'eq.campaign', period_start: 'eq.' + periodStart,
      }),
      countShopRows('shop_usage_reservations', shopId, {
        operation: 'eq.render', period_start: 'eq.' + periodStart,
      }),
    ])
    return { campaign, render }
  }
  // Platform admin RPCs use the SAME user JWT. The trusted database checks
  // retail_private.platform_admins for each call; email/metadata never grant access.
  async function platformRpc(name, body = {}) {
    if (!['retail_platform_me', 'retail_platform_summary',
          'retail_platform_shops', 'retail_platform_set_subscription',
          'retail_onboarding_status', 'retail_platform_onboarding_requests',
          'retail_platform_review_onboarding'].includes(name)) {
      throw new Error('Unsupported platform operation')
    }
    return send('/rest/v1/rpc/' + name, {
      method: 'POST', body, token: await accessToken(),
    })
  }
  async function isPlatformAdmin() {
    const result = await platformRpc('retail_platform_me')
    if (typeof result !== 'boolean') throw new Error('Invalid platform identity response')
    return result
  }
  async function getPlatformSummary() {
    return platformRpc('retail_platform_summary')
  }
  async function listPlatformShops(limit = 25, offset = 0) {
    if (!Number.isInteger(limit) || limit < 1 || limit > 50 ||
        !Number.isInteger(offset) || offset < 0 || offset > 5000) {
      throw new Error('Invalid platform page size')
    }
    return platformRpc('retail_platform_shops', { p_limit: limit, p_offset: offset })
  }
  async function setPlatformSubscription({ shopId, planCode, status, validUntil, reason }) {
    if (!UUID_V4.test(shopId || '') || !['STARTER', 'GROWTH', 'BUSINESS'].includes(planCode) ||
        !['ACTIVE', 'SUSPENDED'].includes(status) ||
        !Number.isFinite(Date.parse(validUntil)) ||
        typeof reason !== 'string' || reason.trim().length < 10 || reason.trim().length > 300) {
      throw new Error('Invalid privileged subscription request')
    }
    return platformRpc('retail_platform_set_subscription', {
      p_shop_id: shopId, p_plan_code: planCode, p_status: status,
      p_valid_until: new Date(validUntil).toISOString(), p_reason: reason.trim(),
    })
  }
  async function getOnboardingStatus() {
    const result = await platformRpc('retail_onboarding_status')
    if (!result || !['PENDING','APPROVED','REJECTED'].includes(result.status) ||
        typeof result.approval_required !== 'boolean') {
      throw new Error('Unable to verify onboarding status.')
    }
    return result
  }
  async function listPlatformOnboardingRequests(status = 'PENDING') {
    if (!['PENDING','APPROVED','REJECTED'].includes(status)) {
      throw new Error('Invalid review status')
    }
    const items = await platformRpc('retail_platform_onboarding_requests', {
      p_status: status, p_limit: 40,
    })
    if (!Array.isArray(items)) throw new Error('Invalid approval queue response')
    return items
  }
  async function reviewPlatformOnboarding(userId, approve, reason) {
    if (!UUID_V4.test(userId || '') || typeof approve !== 'boolean' ||
        typeof reason !== 'string' || reason.trim().length < 10 ||
        reason.trim().length > 300) {
      throw new Error('Provide a valid account and an audit reason of 10–300 characters')
    }
    return platformRpc('retail_platform_review_onboarding', {
      p_user_id: userId, p_approve: approve, p_reason: reason.trim(),
    })
  }
  async function getBusinessProfile(shopId) {
    const rows = await table('business_profiles', {
      query: { select: '*', shop_id: 'eq.' + shopId, limit: '1' },
    })
    return rows[0] || null
  }
  async function updateBusinessProfile(shopId, values) {
    const editable = ['business_name', 'category', 'description', 'brand_voice', 'city', 'website_url', 'contact_email']
    const body = Object.fromEntries(editable.filter((field) => Object.hasOwn(values, field)).map((field) => [field, values[field]]))
    if (!Object.keys(body).length) throw new Error('No editable fields provided')
    body.updated_at = new Date(clock()).toISOString()
    const rows = await table('business_profiles', {
      method: 'PATCH', query: { shop_id: 'eq.' + shopId, select: '*' }, body,
    })
    // A zero-row update can indicate RLS denial (not always a thrown error).
    if (!rows?.length) throw new Error('Business profile not found or you do not have edit permission')
    return rows[0]
  }
  async function uploadImageAsset(shopId, { file, licenseName, licenseUrl = '',
                                              attribution = '', confirmedRights = false }) {
    ensureConfigured()
    if (!UUID_V4.test(shopId) || !confirmedRights) {
      throw new Error('Select a business and confirm commercial media rights.')
    }
    if (!LICENSES.has(licenseName) || typeof attribution !== 'string' ||
        attribution.trim().length < 10 || attribution.trim().length > 500 ||
        typeof licenseUrl !== 'string' || licenseUrl.length > 500) {
      throw new Error('Provide your license type and a meaningful evidence/attribution note.')
    }
    if (licenseName !== 'owned') {
      try {
        const url = new URL(licenseUrl)
        if (url.protocol !== 'https:' || !url.hostname || url.username || url.password) {
          throw new Error('invalid license evidence URL')
        }
      } catch {
        throw new Error('Non-owned media requires an HTTPS license evidence URL.')
      }
    }
    await verifyImageBytes(file)
    const newId = uuidFactory()
    if (!UUID_V4.test(newId)) throw new Error('Invalid generated upload ID')
    const objectPath = shopId + '/uploads/' + newId + IMAGE_TYPES[file.type]
    const token = await accessToken()
    const response = await fetchImpl(origin + '/storage/v1/object/retailgrowth-media/' + objectPath, {
      method: 'POST', redirect: 'error',
      headers: {
        apikey: key, Authorization: 'Bearer ' + token, 'Content-Type': file.type,
        'x-upsert': 'false',
      },
      body: file,
    })
    if (!response.ok) throw new Error('Private image upload was rejected.')
    // Registration is a restricted, per-user JWT RPC: Postgres checks Storage
    // object owner, membership, size and MIME. A failed RPC can leave a private
    // orphan; do not delete on an ambiguous network failure after an insert.
    const assetId = await send('/rest/v1/rpc/register_uploaded_image', {
      method: 'POST', token: await accessToken(),
      body: {
        p_shop_id: shopId, p_object_path: objectPath, p_license_name: licenseName,
        p_license_url: licenseUrl || null, p_attribution: attribution.trim(),
      },
    })
    if (!UUID_V4.test(assetId || '')) {
      throw new Error('Uploaded privately but asset registration was denied. Contact support.')
    }
    return { id: assetId, shop_id: shopId, mime_type: file.type,
      license_name: licenseName, object_path: objectPath }
  }

  async function listMediaAssets(shopId) {
    if (!/^[0-9a-f]{8}-[0-9a-f-]{27,}$/.test(shopId || '')) throw new Error('Invalid shop ID')
    const rows = await table('media_assets', {
      query: { select: 'id,shop_id,source,license_name,mime_type',
        shop_id: 'eq.' + shopId, order: 'created_at.desc', limit: '100' },
    })
    return rows.filter(row => row.shop_id === shopId && row.license_name)
  }
  return {
    configured, getStoredSession: () => session, getAccessToken: accessToken,
    signIn, signUp, signOut, getUser,
    listShops, createShop, getShopSubscription, getShopMetrics, getShopUsage,
    isPlatformAdmin, getPlatformSummary, listPlatformShops, setPlatformSubscription,
    getOnboardingStatus, listPlatformOnboardingRequests, reviewPlatformOnboarding, getBusinessProfile, updateBusinessProfile, listMediaAssets, uploadImageAsset,
  }
}

// Lazy creation: unconfigured Vite/CI builds can still render their mock workspace.
let sharedClient
export function getRetailClient() {
  if (!sharedClient) sharedClient = createRetailClient()
  return sharedClient
}
